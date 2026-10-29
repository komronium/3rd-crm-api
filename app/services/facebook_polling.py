import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app.core.config import settings
from app.db.session import SessionLocal, engine
from app.services.facebook_lead_service import FacebookLeadService
from app.services.facebook_settings_service import FacebookSettingsService

logger = logging.getLogger(__name__)

MAX_BACKOFF_SECONDS = 1800
MIN_LIMIT = 5
POLL_LOCK_KEY = 7351002  # arbitrary constant: "this deployment's Facebook poller"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _is_token_error(exc: Exception) -> bool:
    detail = str(getattr(exc, "detail", exc))
    return any(
        marker in detail
        for marker in (
            '"code":190',
            "Error validating access token",
            "Cannot parse access token",
            "Invalid OAuth access token",
        )
    )


def _is_too_much_data(exc: Exception) -> bool:
    detail = str(getattr(exc, "detail", exc))
    return "reduce the amount of data" in detail


async def import_once(db, since: datetime, limit: int) -> dict | None:
    """One import round. Returns None when Facebook is not configured (nothing to do)."""
    access_token, page_id = FacebookSettingsService.get_effective_credentials(db)
    if not page_id or not access_token:
        return None
    return await FacebookLeadService.import_leads(db, form_id=str(page_id), since=since, limit=limit)


async def facebook_lead_polling_loop() -> None:
    """
    Periodically imports leads from Facebook Lead Ads into the local DB.

    The API runs several worker processes and each starts this loop; a PostgreSQL advisory lock makes sure only one
    of them talks to Facebook per round. Credentials (token / page id) are re-read from the DB every round, so they
    can be changed from the frontend. A failing round backs off (up to 30 minutes) and logs one line instead of a
    full traceback every minute; "too much data" answers halve the page size.
    """
    interval = max(int(settings.FACEBOOK_POLL_INTERVAL_SECONDS), 10)
    lookback = max(int(settings.FACEBOOK_POLL_LOOKBACK_SECONDS), 60)
    configured_limit = max(int(settings.FACEBOOK_IMPORT_LIMIT_PER_FORM), 1)
    limit = configured_limit
    failures = 0

    logger.info("Facebook polling loop started. interval=%ss lookback=%ss limit=%s", interval, lookback, limit)

    while True:
        delay = interval
        try:
            with engine.connect() as lock_conn:
                transaction = lock_conn.begin()
                try:
                    if engine.dialect.name == "postgresql":
                        got = lock_conn.execute(
                            text("select pg_try_advisory_xact_lock(:k)"), {"k": POLL_LOCK_KEY}
                        ).scalar()
                    else:
                        got = True
                    if got:
                        db = SessionLocal()
                        try:
                            result = await import_once(db, _utc_now() - timedelta(seconds=lookback), limit)
                        finally:
                            db.close()
                        if result is not None:
                            if failures:
                                logger.info("Facebook import works again after %s failed rounds.", failures)
                            failures = 0
                            limit = min(configured_limit, limit * 2)
                            logger.info(
                                "Facebook import done. fetched=%s created=%s skipped=%s errors=%s",
                                result.get("fetched"), result.get("created"), result.get("skipped"),
                                len(result.get("errors") or []),
                            )
                finally:
                    transaction.rollback()   # also releases the advisory lock
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            failures += 1
            if _is_token_error(exc):
                logger.error(
                    "Facebook access token is invalid or expired: enter a valid token in the CRM settings "
                    "(a system-user token does not expire). Retrying in %ss.", MAX_BACKOFF_SECONDS,
                )
                delay = MAX_BACKOFF_SECONDS
            elif _is_too_much_data(exc) and limit > MIN_LIMIT:
                limit = max(MIN_LIMIT, limit // 2)
                logger.warning("Facebook asked for less data per request: page size is now %s.", limit)
            else:
                logger.warning("Facebook import failed (%s in a row): %s", failures, str(exc)[:300])
                delay = min(interval * (2 ** min(failures, 6)), MAX_BACKOFF_SECONDS)

        await asyncio.sleep(delay)

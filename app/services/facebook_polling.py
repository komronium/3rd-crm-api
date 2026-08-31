import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.facebook_lead_service import FacebookLeadService
from app.services.facebook_settings_service import FacebookSettingsService

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def facebook_lead_polling_loop() -> None:
    """
    Periodically imports leads from Facebook Lead Ads into local DB.
    Safe to run continuously; dedup is handled by Lead.external_id unique constraint.

    Credentials (access token / page id) can be set via .env or entered later
    through the frontend, so they are re-read from the DB on every iteration
    instead of being checked once at startup.
    """
    interval = max(int(settings.FACEBOOK_POLL_INTERVAL_SECONDS), 10)
    lookback = max(int(settings.FACEBOOK_POLL_LOOKBACK_SECONDS), 60)
    limit = max(int(settings.FACEBOOK_IMPORT_LIMIT_PER_FORM), 1)

    logger.info(
        "Facebook polling loop started. interval=%ss lookback=%ss limit=%s",
        interval,
        lookback,
        limit,
    )

    while True:
        db = SessionLocal()
        try:
            access_token, page_id = FacebookSettingsService.get_effective_credentials(db)
            if not page_id:
                logger.info("Facebook polling skipped: FACEBOOK_PAGE_ID not set.")
            elif not access_token:
                logger.info("Facebook polling skipped: FACEBOOK_ACCESS_TOKEN not set.")
            else:
                since = _utc_now() - timedelta(seconds=lookback)
                result = await FacebookLeadService.import_leads(
                    db,
                    form_id=str(page_id),
                    since=since,
                    limit=limit,
                )
                logger.info(
                    "Facebook import done. fetched=%s created=%s skipped=%s errors=%s",
                    result.get("fetched"),
                    result.get("created"),
                    result.get("skipped"),
                    len(result.get("errors") or []),
                )
        except Exception:
            logger.exception("Facebook import failed")
        finally:
            db.close()

        await asyncio.sleep(interval)


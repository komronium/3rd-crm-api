from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.facebook_setting import FacebookSetting
from app.schemas.facebook_setting import FacebookSettingUpdate


class FacebookSettingsService:
    @staticmethod
    def _get_or_create(db: Session) -> FacebookSetting:
        setting = db.query(FacebookSetting).first()
        if not setting:
            setting = FacebookSetting()
            db.add(setting)
            db.commit()
            db.refresh(setting)
        return setting

    @staticmethod
    def get_settings(db: Session) -> FacebookSetting:
        return FacebookSettingsService._get_or_create(db)

    @staticmethod
    def update_settings(db: Session, payload: FacebookSettingUpdate) -> FacebookSetting:
        setting = FacebookSettingsService._get_or_create(db)
        data = payload.model_dump(exclude_unset=True)
        if "access_token" in data:
            setting.access_token = data["access_token"]
        if "page_id" in data:
            setting.page_id = data["page_id"]
        db.commit()
        db.refresh(setting)
        return setting

    @staticmethod
    def get_effective_credentials(db: Session) -> tuple[str | None, str | None]:
        """
        Returns (access_token, page_id), preferring values entered via the
        frontend (DB) and falling back to .env when a DB value is not set.
        """
        setting = FacebookSettingsService._get_or_create(db)

        access_token = setting.access_token
        if not access_token and settings.FACEBOOK_ACCESS_TOKEN:
            access_token = settings.FACEBOOK_ACCESS_TOKEN.get_secret_value()

        page_id = setting.page_id or settings.FACEBOOK_PAGE_ID

        return access_token, page_id

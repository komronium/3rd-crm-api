from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_admin_user, get_db
from app.schemas.facebook_setting import FacebookSettingOut, FacebookSettingUpdate
from app.services.facebook_settings_service import FacebookSettingsService

router = APIRouter(
    prefix="/api/v1/settings/facebook",
    tags=["Facebook Settings"],
    dependencies=[Depends(get_admin_user)],
)


def _to_out(setting) -> FacebookSettingOut:
    return FacebookSettingOut(
        page_id=setting.page_id,
        access_token_set=bool(setting.access_token),
    )


@router.get("/", response_model=FacebookSettingOut)
def get_facebook_settings(db: Session = Depends(get_db)) -> FacebookSettingOut:
    return _to_out(FacebookSettingsService.get_settings(db))


@router.put("/", response_model=FacebookSettingOut)
def update_facebook_settings(
    payload: FacebookSettingUpdate, db: Session = Depends(get_db)
) -> FacebookSettingOut:
    return _to_out(FacebookSettingsService.update_settings(db, payload))

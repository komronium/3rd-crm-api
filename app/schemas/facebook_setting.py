from pydantic import BaseModel


class FacebookSettingOut(BaseModel):
    page_id: str | None = None
    access_token_set: bool


class FacebookSettingUpdate(BaseModel):
    access_token: str | None = None
    page_id: str | None = None

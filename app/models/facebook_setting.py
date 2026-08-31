from sqlalchemy import Column, String

from app.db.base import Base


class FacebookSetting(Base):
    access_token = Column(String(length=512), nullable=True)
    page_id = Column(String(length=128), nullable=True)

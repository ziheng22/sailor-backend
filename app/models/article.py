
from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String, Text, func

from ..database import Base

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(128), unique=True, nullable=True, index=True)
    title = Column(String(128), nullable=False)
    member_names = Column(Text, default="[]")
    completed_at = Column(DateTime, nullable=True)
    cover = Column(String(256), default="")
    type = Column(String(32), default="工作室动态")
    tags = Column(Text, default="[]")
    published_at = Column(Date, nullable=True)
    is_displayed = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    body = Column(Text, default="")
    updated_by = Column(String(64), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

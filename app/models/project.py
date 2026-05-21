
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, func

from ..database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(128), unique=True, nullable=True, index=True)
    name = Column(String(128), nullable=False)
    summary = Column(String(256), default="")
    status = Column(String(32), default="Planning")
    category = Column(String(64), default="")
    cover = Column(String(256), default="")
    tech = Column(Text, default="[]")
    members = Column(Text, default="[]")
    links = Column(Text, default="{}")
    is_displayed = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    body = Column(Text, default="")
    updated_by = Column(String(64), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

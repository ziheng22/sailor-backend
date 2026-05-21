
from sqlalchemy import Column, Integer, String, Text, DateTime, func

from ..database import Base

class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(128), unique=True, nullable=True, index=True)
    status = Column(String(16), nullable=False, default="current")
    name = Column(String(64), nullable=False)
    points_total = Column(Integer, nullable=False, default=0)
    role = Column(String(64), default="")
    grade = Column(String(32), default="")
    group = Column(String(64), default="")
    avatar = Column(String(256), default="")
    intro = Column(String(256), default="")
    message = Column(String(512), default="")
    skills = Column(Text, default="[]")
    projects = Column(Text, default="[]")
    sort_order = Column(Integer, default=0)
    body = Column(Text, default="")
    updated_by = Column(String(64), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

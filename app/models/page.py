
from sqlalchemy import Column, Integer, String, Text, DateTime, func

from ..database import Base

class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(32), unique=True, nullable=False)  # index | join | contact
    title = Column(String(64), default="")
    description = Column(String(256), default="")
    body = Column(Text, default="")
    updated_by = Column(String(64), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

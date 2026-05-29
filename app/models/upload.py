
from sqlalchemy import Column, Integer, String, DateTime, func

from ..database import Base

class Upload(Base):
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(256), nullable=False)
    original_name = Column(String(256), default="")
    mime_type = Column(String(64), default="")
    size = Column(Integer, default=0)
    url = Column(String(512), default="")
    created_at = Column(DateTime, server_default=func.now())

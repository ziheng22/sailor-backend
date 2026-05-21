
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func

from ..database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False, index=True)
    grade = Column(String(32), nullable=False)
    role = Column(String(16), nullable=False, default="member")  # member | admin
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    password_hash = Column(String(128), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

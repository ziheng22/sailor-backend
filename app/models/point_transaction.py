
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from ..database import Base

class PointTransaction(Base):
    __tablename__ = "point_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    delta = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    reason = Column(String(256), default="")
    granted_by = Column(String(64), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


from datetime import datetime

from pydantic import BaseModel, Field

class PointAwardRequest(BaseModel):
    member_id: int
    points: int = Field(..., description="正数奖励，负数扣减")
    reason: str = ""

class PointTransactionOut(BaseModel):
    id: int
    member_id: int
    delta: int
    balance_after: int
    reason: str
    granted_by: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True

class LeaderboardEntry(BaseModel):
    rank: int
    member_id: int
    name: str
    grade: str
    group: str
    role: str = ""
    points_total: int = 0

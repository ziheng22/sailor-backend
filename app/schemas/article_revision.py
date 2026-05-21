
from datetime import datetime

from pydantic import BaseModel

class ArticleRevisionOut(BaseModel):
    id: int
    article_id: int
    action: str
    title: str
    body: str
    member_names: str = "[]"
    completed_at: datetime | None = None
    updated_by: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True

class ArticleRevisionPublicOut(BaseModel):
    id: int
    article_id: int
    action: str
    title: str
    body: str
    member_names: str = "[]"
    updated_by: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True

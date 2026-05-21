
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PageBase(BaseModel):
    slug: str
    title: str = ""
    description: str = ""
    body: str = ""

class PageUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    body: Optional[str] = None
    updated_by: Optional[str] = None

class PageOut(PageBase):
    id: int
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ProjectBase(BaseModel):
    slug: Optional[str] = None
    name: str
    summary: str = ""
    status: str = "Planning"
    category: str = ""
    cover: str = ""
    tech: str = "[]"
    members: str = "[]"
    links: str = "{}"
    is_displayed: bool = True
    sort_order: int = 0
    body: str = ""

class ProjectCreate(ProjectBase):
    updated_by: str = ""

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None
    cover: Optional[str] = None
    tech: Optional[str] = None
    members: Optional[str] = None
    links: Optional[str] = None
    is_displayed: Optional[bool] = None
    sort_order: Optional[int] = None
    body: Optional[str] = None
    updated_by: Optional[str] = None

class ProjectOut(ProjectBase):
    id: int
    updated_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


from datetime import datetime
from typing import Optional

from pydantic import BaseModel

class MemberBase(BaseModel):
    slug: Optional[str] = None
    status: str = "current"
    name: str
    role: str = ""
    grade: str = ""
    group: str = ""
    avatar: str = ""
    intro: str = ""
    message: str = ""
    skills: str = "[]"
    projects: str = "[]"
    sort_order: int = 0
    body: str = ""

class MemberCreate(MemberBase):
    updated_by: str = ""

class MemberUpdate(BaseModel):
    slug: Optional[str] = None
    status: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    grade: Optional[str] = None
    group: Optional[str] = None
    avatar: Optional[str] = None
    intro: Optional[str] = None
    message: Optional[str] = None
    skills: Optional[str] = None
    projects: Optional[str] = None
    sort_order: Optional[int] = None
    body: Optional[str] = None
    updated_by: Optional[str] = None

class MemberSelfUpdate(BaseModel):

    role: Optional[str] = None
    grade: Optional[str] = None
    group: Optional[str] = None
    avatar: Optional[str] = None
    intro: Optional[str] = None
    message: Optional[str] = None
    skills: Optional[str] = None
    projects: Optional[str] = None
    sort_order: Optional[int] = None
    body: Optional[str] = None

class MemberOut(MemberBase):
    id: int
    points_total: int = 0
    updated_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

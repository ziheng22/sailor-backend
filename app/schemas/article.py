
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from ..utils.json_fields import validate_json_array

class ArticleBase(BaseModel):
    title: str
    slug: Optional[str] = None
    type: str = "工作室动态"
    tags: str = "[]"
    member_names: str = "[]"
    published_at: Optional[date] = None
    completed_at: Optional[datetime] = None
    is_displayed: bool = True
    sort_order: int = 0
    body: str = ""

    @field_validator("tags", "member_names", mode="before")
    @classmethod
    def validate_json_lists(cls, value: str, info):
        if value is None:
            return "[]"
        return validate_json_array(value, info.field_name)

class ArticleCreate(ArticleBase):
    updated_by: str = ""

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    type: Optional[str] = None
    tags: Optional[str] = None
    member_names: Optional[str] = None
    published_at: Optional[date] = None
    completed_at: Optional[datetime] = None
    is_displayed: Optional[bool] = None
    sort_order: Optional[int] = None
    body: Optional[str] = None
    updated_by: Optional[str] = None

    @field_validator("tags", "member_names", mode="before")
    @classmethod
    def validate_json_lists(cls, value: str | None, info):
        if value is None:
            return None
        return validate_json_array(value, info.field_name)

class ArticleOut(ArticleBase):
    id: int
    updated_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ArticlePublicOut(BaseModel):

    id: int
    title: str
    slug: Optional[str] = None
    type: str = "工作室动态"
    tags: str = "[]"
    member_names: str = "[]"
    published_at: Optional[date] = None
    is_displayed: bool = True
    sort_order: int = 0
    body: str = ""
    updated_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator("tags", "member_names", mode="before")
    @classmethod
    def validate_json_lists(cls, value: str, info):
        if value is None:
            return "[]"
        return validate_json_array(value, info.field_name)

    class Config:
        from_attributes = True

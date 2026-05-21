
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UploadOut(BaseModel):
    id: int
    filename: str
    original_name: str
    mime_type: str
    size: int
    url: str
    public_url: str = ""
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UploadListOut(BaseModel):
    items: list[UploadOut]
    total: int
    limit: int
    offset: int

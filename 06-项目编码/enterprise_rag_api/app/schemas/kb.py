from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class KBCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str = ""


class KBUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    description: Optional[str] = None


class KBOut(BaseModel):
    id: str
    name: str
    description: str
    is_archived: bool
    doc_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

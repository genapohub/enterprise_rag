from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel

DocumentStatus = Literal[
    "uploaded",
    "parsing",
    "parse_failed",
    "chunking",
    "indexing",
    "ready",
    "index_failed",
]


class DocumentOut(BaseModel):
    id: str
    kb_id: str
    name: str
    content_type: str
    size_bytes: int
    status: DocumentStatus
    fail_reason: Optional[str] = None
    is_archived: bool
    chunk_count: int
    created_at: datetime
    updated_at: datetime
    indexed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

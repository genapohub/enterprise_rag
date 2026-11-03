from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ConvCreate(BaseModel):
    kb_id: str
    title: Optional[str] = Field(default=None, max_length=256)


class ConversationOut(BaseModel):
    id: str
    kb_id: str
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AskRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class CitationOut(BaseModel):
    doc_id: str
    doc_name: str
    chunk_id: str
    snippet: str
    page: Optional[int] = None
    score: Optional[float] = None


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    citations: List[CitationOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class AskResult(BaseModel):
    user_message: MessageOut
    assistant_message: MessageOut

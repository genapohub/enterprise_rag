from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class Envelope(BaseModel, Generic[T]):
    code: int = 0
    data: Optional[T] = None
    message: str = "ok"


class PageResult(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int = 1
    page_size: int = 20


class OkData(BaseModel):
    ok: bool = True

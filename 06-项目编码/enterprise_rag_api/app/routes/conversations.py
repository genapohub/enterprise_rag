import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.response import ok
from app.schemas.conversation import ConvCreate, AskRequest
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])
logger = logging.getLogger(__name__)


def _svc(db: Session = Depends(get_db)) -> ConversationService:
    return ConversationService(db)


@router.get("")
def list_convs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    kb_id: Optional[str] = None,
    user: User = Depends(get_current_user),
    svc: ConversationService = Depends(_svc),
):
    return ok(svc.list(user, page, page_size, kb_id).model_dump())


@router.post("")
def create_conv(body: ConvCreate, user: User = Depends(get_current_user), svc: ConversationService = Depends(_svc)):
    return ok(svc.create(body, user).model_dump())


@router.get("/{conv_id}")
def get_conv(conv_id: str, user: User = Depends(get_current_user), svc: ConversationService = Depends(_svc)):
    return ok(svc.get(conv_id, user).model_dump())


@router.delete("/{conv_id}")
def delete_conv(conv_id: str, user: User = Depends(get_current_user), svc: ConversationService = Depends(_svc)):
    svc.delete(conv_id, user)
    return ok({"ok": True})


@router.get("/{conv_id}/messages")
def list_messages(
    conv_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    svc: ConversationService = Depends(_svc),
):
    return ok(svc.list_messages(conv_id, user, page, page_size).model_dump())


@router.post("/{conv_id}/messages")
def ask(conv_id: str, body: AskRequest, user: User = Depends(get_current_user), svc: ConversationService = Depends(_svc)):
    return ok(svc.ask(conv_id, body.content, user).model_dump())


@router.post("/{conv_id}/messages:stream")
def ask_stream(conv_id: str, body: AskRequest, user: User = Depends(get_current_user), svc: ConversationService = Depends(_svc)):
    svc.stream_stub(conv_id, user)

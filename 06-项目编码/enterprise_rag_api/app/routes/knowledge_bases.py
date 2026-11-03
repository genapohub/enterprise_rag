import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.response import ok
from app.schemas.kb import KBCreate, KBUpdate
from app.services.kb_service import KBService

router = APIRouter(prefix="/api/v1/knowledge-bases", tags=["knowledge-bases"])
logger = logging.getLogger(__name__)


def _svc(db: Session = Depends(get_db)) -> KBService:
    return KBService(db)


@router.get("")
def list_kbs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_archived: bool = False,
    user: User = Depends(get_current_user),
    svc: KBService = Depends(_svc),
):
    data = svc.list(page, page_size, include_archived)
    return ok(data.model_dump())


@router.post("")
def create_kb(body: KBCreate, user: User = Depends(get_current_user), svc: KBService = Depends(_svc)):
    return ok(svc.create(body, user).model_dump())


@router.get("/{kb_id}")
def get_kb(kb_id: str, user: User = Depends(get_current_user), svc: KBService = Depends(_svc)):
    return ok(svc.get(kb_id).model_dump())


@router.patch("/{kb_id}")
def update_kb(kb_id: str, body: KBUpdate, user: User = Depends(get_current_user), svc: KBService = Depends(_svc)):
    return ok(svc.update(kb_id, body, user).model_dump())


@router.post("/{kb_id}/archive")
def archive_kb(kb_id: str, user: User = Depends(get_current_user), svc: KBService = Depends(_svc)):
    return ok(svc.set_archived(kb_id, True, user).model_dump())


@router.post("/{kb_id}/unarchive")
def unarchive_kb(kb_id: str, user: User = Depends(get_current_user), svc: KBService = Depends(_svc)):
    return ok(svc.set_archived(kb_id, False, user).model_dump())

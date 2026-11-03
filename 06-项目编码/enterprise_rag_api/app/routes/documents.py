import logging
from fastapi import APIRouter, Depends, File, UploadFile, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.response import ok
from app.services.document_service import DocumentService

router = APIRouter(tags=["documents"])
logger = logging.getLogger(__name__)


def _svc(db: Session = Depends(get_db)) -> DocumentService:
    return DocumentService(db)


@router.get("/api/v1/knowledge-bases/{kb_id}/documents")
def list_docs(
    kb_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    svc: DocumentService = Depends(_svc),
):
    return ok(svc.list(kb_id, page, page_size).model_dump())


@router.post("/api/v1/knowledge-bases/{kb_id}/documents")
async def upload_doc(
    kb_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    svc: DocumentService = Depends(_svc),
):
    data = await svc.upload(kb_id, file, user, sync_index=True)
    return ok(data.model_dump())


@router.get("/api/v1/documents/{doc_id}")
def get_doc(doc_id: str, user: User = Depends(get_current_user), svc: DocumentService = Depends(_svc)):
    return ok(svc.get(doc_id).model_dump())


@router.post("/api/v1/documents/{doc_id}/archive")
def archive_doc(doc_id: str, user: User = Depends(get_current_user), svc: DocumentService = Depends(_svc)):
    return ok(svc.set_archived(doc_id, True, user).model_dump())


@router.post("/api/v1/documents/{doc_id}/unarchive")
def unarchive_doc(doc_id: str, user: User = Depends(get_current_user), svc: DocumentService = Depends(_svc)):
    return ok(svc.set_archived(doc_id, False, user).model_dump())


@router.delete("/api/v1/documents/{doc_id}")
def delete_doc(doc_id: str, user: User = Depends(get_current_user), svc: DocumentService = Depends(_svc)):
    svc.delete(doc_id, user)
    return ok({"ok": True})


@router.post("/api/v1/documents/{doc_id}/reindex")
def reindex_doc(doc_id: str, user: User = Depends(get_current_user), svc: DocumentService = Depends(_svc)):
    return ok(svc.reindex(doc_id, user).model_dump())

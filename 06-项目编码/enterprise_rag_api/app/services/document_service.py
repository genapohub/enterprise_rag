import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Set
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.config import get_settings
from app.exceptions import NotFound, Forbidden, BadRequest, Conflict
from app.models.user import User
from app.models.document import Document
from app.repositories.document_repo import DocumentRepository
from app.repositories.chunk_repo import ChunkRepository
from app.repositories.kb_repo import KBRepository
from app.schemas.document import DocumentOut
from app.schemas.common import PageResult
from app.services.indexing_service import IndexingService
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)
ALLOWED: Set[str] = {".pdf", ".docx", ".md", ".txt"}


class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DocumentRepository(db)
        self.chunks = ChunkRepository(db)
        self.kbs = KBRepository(db)
        self.settings = get_settings()

    def list(self, kb_id: str, page: int, page_size: int) -> PageResult[DocumentOut]:
        if not self.kbs.get(kb_id):
            raise NotFound("知识库不存在")
        items, total = self.repo.list_by_kb(kb_id, page, page_size)
        return PageResult(
            items=[DocumentOut.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get(self, doc_id: str) -> DocumentOut:
        doc = self.repo.get(doc_id)
        if not doc:
            raise NotFound("文档不存在")
        return DocumentOut.model_validate(doc)

    async def upload(self, kb_id: str, file: UploadFile, user: User, sync_index: bool = True) -> DocumentOut:
        if user.role != "admin":
            raise Forbidden("需要管理员权限")
        kb = self.kbs.get(kb_id)
        if not kb:
            raise NotFound("知识库不存在")
        if kb.is_archived:
            raise Conflict("知识库已归档，无法上传")
        name = file.filename or "unnamed.txt"
        suffix = Path(name).suffix.lower()
        if suffix not in ALLOWED:
            raise BadRequest("仅支持 pdf/docx/md/txt")
        raw = await file.read()
        max_bytes = self.settings.max_upload_mb * 1024 * 1024
        if len(raw) > max_bytes:
            raise BadRequest(f"文件超过 {self.settings.max_upload_mb}MB 限制")
        upload_root = Path(self.settings.upload_dir) / kb_id
        upload_root.mkdir(parents=True, exist_ok=True)
        doc_id = str(uuid.uuid4())
        storage = upload_root / f"{doc_id}{suffix}"
        storage.write_bytes(raw)
        doc = Document(
            id=doc_id,
            kb_id=kb_id,
            name=name,
            content_type=file.content_type or "application/octet-stream",
            size_bytes=len(raw),
            storage_path=str(storage),
            status="uploaded",
            created_by=user.id,
        )
        doc = self.repo.create(doc)
        logger.info("doc uploaded id=%s name=%s", doc.id, name)
        if sync_index:
            doc = IndexingService(self.db).run(doc.id)
        return DocumentOut.model_validate(doc)

    def set_archived(self, doc_id: str, archived: bool, user: User) -> DocumentOut:
        if user.role != "admin":
            raise Forbidden("需要管理员权限")
        doc = self.repo.get(doc_id)
        if not doc:
            raise NotFound("文档不存在")
        doc.is_archived = archived
        self.repo.save(doc)
        # mark vectors archived via delete from index when archived
        vs = VectorStore(self.settings)
        if archived:
            vs.delete_by_doc(doc.id)
        elif doc.status == "ready":
            # re-index to restore vectors
            IndexingService(self.db).run(doc.id)
            doc = self.repo.get(doc_id)
        return DocumentOut.model_validate(doc)

    def delete(self, doc_id: str, user: User) -> None:
        if user.role != "admin":
            raise Forbidden("需要管理员权限")
        doc = self.repo.get(doc_id)
        if not doc:
            raise NotFound("文档不存在")
        doc.deleted_at = datetime.now(timezone.utc)
        self.repo.save(doc)
        self.chunks.delete_by_doc(doc.id)
        VectorStore(self.settings).delete_by_doc(doc.id)
        logger.info("doc deleted id=%s", doc_id)

    def reindex(self, doc_id: str, user: User) -> DocumentOut:
        if user.role != "admin":
            raise Forbidden("需要管理员权限")
        doc = self.repo.get(doc_id)
        if not doc:
            raise NotFound("文档不存在")
        if doc.status not in ("parse_failed", "index_failed", "ready", "uploaded"):
            raise Conflict(f"当前状态 {doc.status} 不可重索引")
        doc = IndexingService(self.db).run(doc.id)
        return DocumentOut.model_validate(doc)

import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.exceptions import NotFound, Forbidden, Conflict
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase
from app.repositories.kb_repo import KBRepository
from app.schemas.kb import KBCreate, KBUpdate, KBOut
from app.schemas.common import PageResult

logger = logging.getLogger(__name__)


class KBService:
    def __init__(self, db: Session):
        self.repo = KBRepository(db)

    def _to_out(self, kb: KnowledgeBase) -> KBOut:
        out = KBOut.model_validate(kb)
        out.doc_count = self.repo.doc_count(kb.id)
        return out

    def list(self, page: int, page_size: int, include_archived: bool) -> PageResult[KBOut]:
        items, total = self.repo.list_page(page, page_size, include_archived)
        return PageResult(items=[self._to_out(i) for i in items], total=total, page=page, page_size=page_size)

    def get(self, kb_id: str) -> KBOut:
        kb = self.repo.get(kb_id)
        if not kb:
            raise NotFound("知识库不存在")
        return self._to_out(kb)

    def create(self, body: KBCreate, user: User) -> KBOut:
        if user.role != "admin":
            raise Forbidden("需要管理员权限")
        kb = KnowledgeBase(name=body.name, description=body.description or "", created_by=user.id)
        kb = self.repo.create(kb)
        logger.info("kb created id=%s by=%s", kb.id, user.username)
        return self._to_out(kb)

    def update(self, kb_id: str, body: KBUpdate, user: User) -> KBOut:
        if user.role != "admin":
            raise Forbidden("需要管理员权限")
        kb = self.repo.get(kb_id)
        if not kb:
            raise NotFound("知识库不存在")
        if body.name is not None:
            kb.name = body.name
        if body.description is not None:
            kb.description = body.description
        return self._to_out(self.repo.save(kb))

    def set_archived(self, kb_id: str, archived: bool, user: User) -> KBOut:
        if user.role != "admin":
            raise Forbidden("需要管理员权限")
        kb = self.repo.get(kb_id)
        if not kb:
            raise NotFound("知识库不存在")
        kb.is_archived = archived
        return self._to_out(self.repo.save(kb))

    def require_active_kb(self, kb_id: str) -> KnowledgeBase:
        kb = self.repo.get(kb_id)
        if not kb:
            raise NotFound("知识库不存在")
        if kb.is_archived:
            raise Conflict("知识库已归档")
        return kb

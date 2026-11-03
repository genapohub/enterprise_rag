from typing import List, Optional, Tuple
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document


class KBRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, kb_id: str) -> Optional[KnowledgeBase]:
        return self.db.get(KnowledgeBase, kb_id)

    def create(self, kb: KnowledgeBase) -> KnowledgeBase:
        self.db.add(kb)
        self.db.commit()
        self.db.refresh(kb)
        return kb

    def save(self, kb: KnowledgeBase) -> KnowledgeBase:
        self.db.add(kb)
        self.db.commit()
        self.db.refresh(kb)
        return kb

    def list_page(
        self, page: int, page_size: int, include_archived: bool = False
    ) -> Tuple[List[KnowledgeBase], int]:
        q = select(KnowledgeBase)
        cq = select(func.count()).select_from(KnowledgeBase)
        if not include_archived:
            q = q.where(KnowledgeBase.is_archived.is_(False))
            cq = cq.where(KnowledgeBase.is_archived.is_(False))
        total = self.db.scalar(cq) or 0
        items = list(
            self.db.scalars(q.order_by(KnowledgeBase.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
        )
        return items, total

    def doc_count(self, kb_id: str) -> int:
        return (
            self.db.scalar(
                select(func.count())
                .select_from(Document)
                .where(and_(Document.kb_id == kb_id, Document.deleted_at.is_(None)))
            )
            or 0
        )

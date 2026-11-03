from typing import List, Optional, Tuple
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from app.models.document import Document


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, doc_id: str) -> Optional[Document]:
        doc = self.db.get(Document, doc_id)
        if doc and doc.deleted_at is not None:
            return None
        return doc

    def create(self, doc: Document) -> Document:
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def save(self, doc: Document) -> Document:
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def list_by_kb(self, kb_id: str, page: int, page_size: int) -> Tuple[List[Document], int]:
        cond = and_(Document.kb_id == kb_id, Document.deleted_at.is_(None))
        total = self.db.scalar(select(func.count()).select_from(Document).where(cond)) or 0
        items = list(
            self.db.scalars(
                select(Document)
                .where(cond)
                .order_by(Document.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return items, total

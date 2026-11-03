from typing import List
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from app.models.chunk import Chunk, MessageCitation


class ChunkRepository:
    def __init__(self, db: Session):
        self.db = db

    def replace_for_doc(self, chunks: List[Chunk], doc_id: str) -> List[Chunk]:
        self.db.execute(delete(Chunk).where(Chunk.doc_id == doc_id))
        for c in chunks:
            self.db.add(c)
        self.db.commit()
        for c in chunks:
            self.db.refresh(c)
        return chunks

    def delete_by_doc(self, doc_id: str) -> None:
        self.db.execute(delete(Chunk).where(Chunk.doc_id == doc_id))
        self.db.commit()

    def list_by_ids(self, ids: List[str]) -> List[Chunk]:
        if not ids:
            return []
        return list(self.db.scalars(select(Chunk).where(Chunk.id.in_(ids))))

    def search_text(self, kb_id: str, query: str, limit: int = 5) -> List[Chunk]:
        """Fallback lexical search for stub vector mode."""
        q = select(Chunk).where(Chunk.kb_id == kb_id)
        rows = list(self.db.scalars(q.limit(200)))
        query_l = query.lower()
        scored = []
        for c in rows:
            text_l = c.text.lower()
            score = 0.0
            for token in query_l.replace("?", " ").split():
                if token and token in text_l:
                    score += 1.0
            if score > 0:
                scored.append((score, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:limit]]

    def add_citations(self, citations: List[MessageCitation]) -> None:
        for c in citations:
            self.db.add(c)
        self.db.commit()

    def list_citations(self, message_id: str) -> List[MessageCitation]:
        return list(
            self.db.scalars(select(MessageCitation).where(MessageCitation.message_id == message_id))
        )

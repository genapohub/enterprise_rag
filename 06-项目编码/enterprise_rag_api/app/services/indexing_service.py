"""Document index pipeline: parsing → chunking → indexing → ready|failed."""
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models.document import Document
from app.models.chunk import Chunk
from app.repositories.document_repo import DocumentRepository
from app.repositories.chunk_repo import ChunkRepository
from app.services.parser import extract_text
from app.services.chunker import split_text
from app.services.embedding import EmbeddingClient
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)


class IndexingService:
    def __init__(self, db: Session):
        self.db = db
        self.docs = DocumentRepository(db)
        self.chunks = ChunkRepository(db)
        self.settings = get_settings()
        self.embedder = EmbeddingClient(self.settings)
        self.vectors = VectorStore(self.settings)

    def run(self, doc_id: str) -> Document:
        doc = self.docs.get(doc_id)
        if not doc:
            raise RuntimeError("document missing")
        try:
            doc.status = "parsing"
            doc.fail_reason = None
            self.docs.save(doc)

            text = extract_text(doc.storage_path, doc.name)

            doc.status = "chunking"
            self.docs.save(doc)
            pieces = split_text(text, self.settings.chunk_size, self.settings.chunk_overlap)
            if not pieces:
                raise RuntimeError("切块结果为空")

            chunk_rows = [
                Chunk(kb_id=doc.kb_id, doc_id=doc.id, chunk_index=i, text=p, source_page=None)
                for i, p in enumerate(pieces)
            ]
            chunk_rows = self.chunks.replace_for_doc(chunk_rows, doc.id)

            doc.status = "indexing"
            self.docs.save(doc)

            vectors = self.embedder.embed([c.text for c in chunk_rows])
            points = []
            for c, vec in zip(chunk_rows, vectors):
                points.append(
                    {
                        "id": c.id,
                        "vector": vec,
                        "payload": {
                            "kb_id": c.kb_id,
                            "doc_id": c.doc_id,
                            "chunk_id": c.id,
                            "chunk_index": c.chunk_index,
                            "text": c.text[:500],
                            "is_archived": False,
                        },
                    }
                )
            self.vectors.upsert(points)

            doc.status = "ready"
            doc.chunk_count = len(chunk_rows)
            doc.indexed_at = datetime.now(timezone.utc)
            doc.fail_reason = None
            self.docs.save(doc)
            logger.info("index ready doc=%s chunks=%s backend=%s", doc.id, doc.chunk_count, self.vectors.backend)
            return doc
        except Exception as exc:  # noqa: BLE001
            logger.exception("index failed doc=%s", doc_id)
            doc = self.docs.get(doc_id)
            if not doc:
                raise
            reason = str(exc)[:500]
            if doc.status in ("parsing", "uploaded"):
                doc.status = "parse_failed"
            else:
                doc.status = "index_failed"
            doc.fail_reason = reason
            self.docs.save(doc)
            return doc

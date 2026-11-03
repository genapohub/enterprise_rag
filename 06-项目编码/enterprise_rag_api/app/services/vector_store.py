"""Vector store: in-memory stub (default) or Qdrant when reachable + not forced stub."""
from typing import Dict, List, Optional, Tuple
import logging
from app.config import Settings

logger = logging.getLogger(__name__)


class MemoryVectorStore:
    def __init__(self):
        self._points: Dict[str, dict] = {}  # point_id(=chunk_id) -> payload+vector

    def upsert(self, points: List[dict]) -> None:
        for p in points:
            self._points[p["id"]] = p

    def delete_by_doc(self, doc_id: str) -> None:
        dead = [k for k, v in self._points.items() if v.get("payload", {}).get("doc_id") == doc_id]
        for k in dead:
            del self._points[k]

    def search(self, kb_id: str, vector: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        scored = []
        for pid, p in self._points.items():
            payload = p.get("payload") or {}
            if payload.get("kb_id") != kb_id:
                continue
            if payload.get("is_archived"):
                continue
            score = _cosine(vector, p.get("vector") or [])
            scored.append((pid, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


_MEMORY = MemoryVectorStore()


class VectorStore:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.backend = "memory"
        self._qdrant = None
        if not settings.use_embedding_stub():
            # try qdrant only when not in pure stub mode; still fall back silently
            try:
                from qdrant_client import QdrantClient
                from qdrant_client.http import models as qm

                client = QdrantClient(url=settings.qdrant_url, timeout=2.0)
                # lightweight ping
                client.get_collections()
                self._qdrant = client
                self._qm = qm
                self.backend = "qdrant"
                self._ensure_collection()
            except Exception as exc:  # noqa: BLE001
                logger.warning("Qdrant unavailable, using memory vector store: %s", exc)

    def _ensure_collection(self) -> None:
        assert self._qdrant is not None
        name = self.settings.qdrant_collection
        existing = [c.name for c in self._qdrant.get_collections().collections]
        if name not in existing:
            self._qdrant.create_collection(
                collection_name=name,
                vectors_config=self._qm.VectorParams(size=self.settings.embedding_dim, distance=self._qm.Distance.COSINE),
            )

    def upsert(self, points: List[dict]) -> None:
        if self.backend == "memory" or self._qdrant is None:
            _MEMORY.upsert(points)
            return
        self._qdrant.upsert(
            collection_name=self.settings.qdrant_collection,
            points=[
                self._qm.PointStruct(id=p["id"], vector=p["vector"], payload=p["payload"])
                for p in points
            ],
        )

    def delete_by_doc(self, doc_id: str) -> None:
        if self.backend == "memory" or self._qdrant is None:
            _MEMORY.delete_by_doc(doc_id)
            return
        self._qdrant.delete(
            collection_name=self.settings.qdrant_collection,
            points_selector=self._qm.FilterSelector(
                filter=self._qm.Filter(must=[self._qm.FieldCondition(key="doc_id", match=self._qm.MatchValue(value=doc_id))])
            ),
        )

    def search(self, kb_id: str, vector: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        if self.backend == "memory" or self._qdrant is None:
            return _MEMORY.search(kb_id, vector, top_k)
        hits = self._qdrant.search(
            collection_name=self.settings.qdrant_collection,
            query_vector=vector,
            limit=top_k,
            query_filter=self._qm.Filter(
                must=[
                    self._qm.FieldCondition(key="kb_id", match=self._qm.MatchValue(value=kb_id)),
                    self._qm.FieldCondition(key="is_archived", match=self._qm.MatchValue(value=False)),
                ]
            ),
        )
        return [(str(h.id), float(h.score)) for h in hits]

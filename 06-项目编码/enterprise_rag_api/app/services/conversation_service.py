import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from app.config import get_settings
from app.exceptions import NotFound, Forbidden, Conflict, AppError
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.models.chunk import MessageCitation
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.kb_repo import KBRepository
from app.repositories.chunk_repo import ChunkRepository
from app.repositories.document_repo import DocumentRepository
from app.schemas.conversation import (
    ConvCreate,
    ConversationOut,
    AskResult,
    MessageOut,
    CitationOut,
)
from app.schemas.common import PageResult
from app.services.embedding import EmbeddingClient
from app.services.vector_store import VectorStore
from app.services.llm import LLMClient, NO_HIT

logger = logging.getLogger(__name__)


class ConversationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ConversationRepository(db)
        self.kbs = KBRepository(db)
        self.chunks = ChunkRepository(db)
        self.docs = DocumentRepository(db)
        self.settings = get_settings()

    def list(self, user: User, page: int, page_size: int, kb_id: Optional[str]) -> PageResult[ConversationOut]:
        items, total = self.repo.list_for_user(user.id, page, page_size, kb_id)
        return PageResult(
            items=[ConversationOut.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def create(self, body: ConvCreate, user: User) -> ConversationOut:
        kb = self.kbs.get(body.kb_id)
        if not kb:
            raise NotFound("知识库不存在")
        if kb.is_archived:
            raise Conflict("知识库已归档，无法新建会话")
        conv = Conversation(kb_id=body.kb_id, user_id=user.id, title=body.title or "新对话")
        conv = self.repo.create(conv)
        return ConversationOut.model_validate(conv)

    def get(self, conv_id: str, user: User) -> ConversationOut:
        conv = self._owned(conv_id, user)
        return ConversationOut.model_validate(conv)

    def delete(self, conv_id: str, user: User) -> None:
        conv = self._owned(conv_id, user)
        self.repo.delete(conv)

    def list_messages(self, conv_id: str, user: User, page: int, page_size: int) -> PageResult[MessageOut]:
        self._owned(conv_id, user)
        items, total = self.repo.list_messages(conv_id, page, page_size)
        outs = []
        for m in items:
            cites = self.chunks.list_citations(m.id)
            outs.append(
                MessageOut(
                    id=m.id,
                    role=m.role,
                    content=m.content,
                    created_at=m.created_at,
                    citations=[
                        CitationOut(
                            doc_id=c.doc_id,
                            doc_name=c.doc_name,
                            chunk_id=c.chunk_id,
                            snippet=c.snippet,
                            page=c.page,
                            score=c.score,
                        )
                        for c in cites
                    ],
                )
            )
        return PageResult(items=outs, total=total, page=page, page_size=page_size)

    def ask(self, conv_id: str, content: str, user: User) -> AskResult:
        conv = self._owned(conv_id, user)
        kb = self.kbs.get(conv.kb_id)
        if not kb or kb.is_archived:
            raise Conflict("知识库不可用")

        user_msg = self.repo.add_message(Message(conversation_id=conv.id, role="user", content=content))

        embedder = EmbeddingClient(self.settings)
        vectors = VectorStore(self.settings)
        qvec = embedder.embed([content])[0]
        hits = vectors.search(conv.kb_id, qvec, top_k=5)

        # fallback lexical if vector miss (stub edge)
        chunk_scores = []
        if hits:
            id_list = [h[0] for h in hits]
            found = {c.id: c for c in self.chunks.list_by_ids(id_list)}
            for cid, score in hits:
                c = found.get(cid)
                if not c:
                    continue
                doc = self.docs.get(c.doc_id)
                if not doc or doc.is_archived or doc.status != "ready":
                    continue
                chunk_scores.append((c, doc, score))
        if not chunk_scores:
            for c in self.chunks.search_text(conv.kb_id, content, limit=5):
                doc = self.docs.get(c.doc_id)
                if not doc or doc.is_archived or doc.status != "ready":
                    continue
                chunk_scores.append((c, doc, 0.5))

        contexts = [c.text for c, _, _ in chunk_scores]
        answer = LLMClient(self.settings).answer(content, contexts)

        asst = self.repo.add_message(Message(conversation_id=conv.id, role="assistant", content=answer))
        citations_out: List[CitationOut] = []
        if chunk_scores and answer != NO_HIT:
            rows = []
            for c, doc, score in chunk_scores[:5]:
                snippet = c.text[:240]
                rows.append(
                    MessageCitation(
                        message_id=asst.id,
                        chunk_id=c.id,
                        doc_id=doc.id,
                        doc_name=doc.name,
                        snippet=snippet,
                        page=c.source_page,
                        score=float(score),
                    )
                )
                citations_out.append(
                    CitationOut(
                        doc_id=doc.id,
                        doc_name=doc.name,
                        chunk_id=c.id,
                        snippet=snippet,
                        page=c.source_page,
                        score=float(score),
                    )
                )
            self.chunks.add_citations(rows)
        # product: successful grounded answer should have >=1 citation when contexts exist
        if contexts and answer != NO_HIT and not citations_out:
            # should not happen; keep structure
            pass

        conv.title = content[:40] if conv.title == "新对话" else conv.title
        self.repo.save(conv)
        logger.info("ask conv=%s cites=%s", conv.id, len(citations_out))
        return AskResult(
            user_message=MessageOut(
                id=user_msg.id, role="user", content=user_msg.content, citations=[], created_at=user_msg.created_at
            ),
            assistant_message=MessageOut(
                id=asst.id, role="assistant", content=answer, citations=citations_out, created_at=asst.created_at
            ),
        )

    def stream_stub(self, conv_id: str, user: User) -> None:
        self._owned(conv_id, user)
        raise AppError(50001, "流式问答尚未实现（SSE stub）", status_code=501)

    def _owned(self, conv_id: str, user: User) -> Conversation:
        conv = self.repo.get(conv_id)
        if not conv:
            raise NotFound("会话不存在")
        if conv.user_id != user.id and user.role != "admin":
            raise Forbidden("不能访问他人会话")
        return conv

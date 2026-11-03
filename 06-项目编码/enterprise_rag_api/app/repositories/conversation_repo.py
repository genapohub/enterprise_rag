from typing import List, Optional, Tuple
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from app.models.conversation import Conversation, Message


class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, conv_id: str) -> Optional[Conversation]:
        return self.db.get(Conversation, conv_id)

    def create(self, conv: Conversation) -> Conversation:
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def save(self, conv: Conversation) -> Conversation:
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def delete(self, conv: Conversation) -> None:
        self.db.delete(conv)
        self.db.commit()

    def list_for_user(
        self, user_id: str, page: int, page_size: int, kb_id: Optional[str] = None
    ) -> Tuple[List[Conversation], int]:
        cond = [Conversation.user_id == user_id]
        if kb_id:
            cond.append(Conversation.kb_id == kb_id)
        where = and_(*cond)
        total = self.db.scalar(select(func.count()).select_from(Conversation).where(where)) or 0
        items = list(
            self.db.scalars(
                select(Conversation)
                .where(where)
                .order_by(Conversation.updated_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return items, total

    def add_message(self, msg: Message) -> Message:
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def list_messages(self, conv_id: str, page: int, page_size: int) -> Tuple[List[Message], int]:
        cond = Message.conversation_id == conv_id
        total = self.db.scalar(select(func.count()).select_from(Message).where(cond)) or 0
        items = list(
            self.db.scalars(
                select(Message)
                .where(cond)
                .order_by(Message.created_at.asc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return items, total

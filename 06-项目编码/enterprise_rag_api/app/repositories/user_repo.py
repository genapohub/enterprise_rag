from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self.db.get(User, user_id)

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.scalar(select(User).where(User.username == username))

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def list_page(self, page: int, page_size: int) -> Tuple[List[User], int]:
        total = self.db.scalar(select(func.count()).select_from(User)) or 0
        items = list(
            self.db.scalars(
                select(User).order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
            )
        )
        return items, total

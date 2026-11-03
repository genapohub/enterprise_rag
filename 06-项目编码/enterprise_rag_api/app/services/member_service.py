from sqlalchemy.orm import Session
from app.exceptions import Forbidden
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.member import MemberOut
from app.schemas.common import PageResult


class MemberService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def list(self, user: User, page: int, page_size: int) -> PageResult[MemberOut]:
        if user.role != "admin":
            raise Forbidden("需要管理员权限")
        items, total = self.repo.list_page(page, page_size)
        return PageResult(
            items=[MemberOut.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
        )

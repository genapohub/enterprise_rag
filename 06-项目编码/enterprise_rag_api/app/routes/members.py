import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.response import ok
from app.services.member_service import MemberService

router = APIRouter(prefix="/api/v1/members", tags=["members"])
logger = logging.getLogger(__name__)


@router.get("")
def list_members(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = MemberService(db).list(user, page, page_size)
    return ok(data.model_dump())

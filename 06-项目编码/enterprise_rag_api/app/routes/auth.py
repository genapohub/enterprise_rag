import logging
from fastapi import APIRouter, Depends
from app.deps import get_auth_service, get_current_user, client_ip
from app.models.user import User
from app.response import ok
from app.schemas.auth import LoginRequest, RefreshRequest, UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/login")
def login(body: LoginRequest, ip: str = Depends(client_ip), auth: AuthService = Depends(get_auth_service)):
    data = auth.login(body, client_ip=ip)
    return ok(data.model_dump())


@router.post("/refresh")
def refresh(body: RefreshRequest, auth: AuthService = Depends(get_auth_service)):
    data = auth.refresh(body.refresh_token)
    return ok(data.model_dump())


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return ok(UserOut.model_validate(user).model_dump())

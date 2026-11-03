from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService

_bearer = HTTPBearer(auto_error=False)


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
    auth: AuthService = Depends(get_auth_service),
) -> User:
    if cred is None or not cred.credentials:
        from app.exceptions import Unauthorized

        raise Unauthorized()
    return auth.get_current_user(cred.credentials)


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"

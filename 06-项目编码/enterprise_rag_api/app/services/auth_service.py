import logging
import time
from collections import defaultdict, deque
from sqlalchemy.orm import Session
from app.config import get_settings
from app.exceptions import Unauthorized, RateLimited, Forbidden
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginRequest, TokenData, UserOut
from app.services.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)

logger = logging.getLogger(__name__)
_login_hits: dict[str, deque] = defaultdict(deque)


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.settings = get_settings()

    def ensure_bootstrap_admin(self) -> None:
        if self.users.get_by_username(self.settings.bootstrap_admin_user):
            return
        user = User(
            username=self.settings.bootstrap_admin_user,
            display_name=self.settings.bootstrap_admin_display,
            password_hash=hash_password(self.settings.bootstrap_admin_password),
            role="admin",
            is_active=True,
        )
        self.users.create(user)
        logger.info("bootstrap admin created: %s", user.username)

    def _rate_limit_login(self, key: str) -> None:
        now = time.time()
        q = _login_hits[key]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= 10:
            raise RateLimited("登录过于频繁，请稍后再试")
        q.append(now)

    def login(self, body: LoginRequest, client_ip: str = "unknown") -> TokenData:
        self._rate_limit_login(client_ip + ":" + body.username)
        user = self.users.get_by_username(body.username)
        if not user or not user.is_active or not verify_password(body.password, user.password_hash):
            logger.warning("login failed user=%s ip=%s", body.username, client_ip)
            raise Unauthorized("用户名或密码错误")
        access, expires_in = create_access_token(user.id)
        refresh = create_refresh_token(user.id)
        logger.info("login ok user=%s", user.username)
        return TokenData(
            access_token=access,
            refresh_token=refresh,
            expires_in=expires_in,
            user=UserOut.model_validate(user),
        )

    def refresh(self, refresh_token: str) -> TokenData:
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
        except ValueError as exc:
            raise Unauthorized("refresh token 无效") from exc
        user = self.users.get_by_id(payload["sub"])
        if not user or not user.is_active:
            raise Unauthorized("用户不可用")
        access, expires_in = create_access_token(user.id)
        new_refresh = create_refresh_token(user.id)
        return TokenData(
            access_token=access,
            refresh_token=new_refresh,
            expires_in=expires_in,
            user=UserOut.model_validate(user),
        )

    def get_current_user(self, token: str) -> User:
        try:
            payload = decode_token(token, expected_type="access")
        except ValueError as exc:
            raise Unauthorized("access token 无效") from exc
        user = self.users.get_by_id(payload["sub"])
        if not user or not user.is_active:
            raise Unauthorized("用户不可用")
        return user

    @staticmethod
    def require_admin(user: User) -> None:
        if user.role != "admin":
            raise Forbidden("需要管理员权限")

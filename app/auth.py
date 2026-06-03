
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models.user import User

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)

@dataclass
class AuthUser:

    user_id: int
    name: str
    grade: str
    role: str
    member_id: int | None

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def display_name(self) -> str:
        return f"{self.grade} {self.name}".strip()

def verify_member_invite_code(code: str) -> bool:
    return code == settings.invite_code

def verify_admin_invite_code(code: str) -> bool:
    return code == settings.admin_invite_code

def create_access_token(user_id: int, name: str, grade: str, role: str, member_id: int | None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "user_id": user_id,
        "name": name,
        "grade": grade,
        "role": role,
        "member_id": member_id,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])

def _payload_to_auth_user(payload: dict) -> AuthUser:
    if "user_id" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效令牌")
    return AuthUser(
        user_id=int(payload["user_id"]),
        name=str(payload.get("name", "")),
        grade=str(payload.get("grade", "")),
        role=str(payload.get("role", "member")),
        member_id=payload.get("member_id"),
    )

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> AuthUser:
    try:
        return _payload_to_auth_user(decode_token(credentials.credentials))
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效令牌")

def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_security),
) -> AuthUser | None:
    if not credentials:
        return None
    try:
        return _payload_to_auth_user(decode_token(credentials.credentials))
    except JWTError:
        return None

def require_admin(
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AuthUser:
    db_user = db.get(User, user.user_id)
    if not db_user or db_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user

def require_member(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if user.is_admin:
        return user
    if user.role != "member":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
    return user

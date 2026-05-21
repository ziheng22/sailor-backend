
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import (
    AuthUser,
    create_access_token,
    get_current_user,
    verify_admin_invite_code,
    verify_member_invite_code,
)
from ..database import get_db
from ..models.member import Member
from ..models.user import User
from ..passwords import hash_password, validate_password, verify_password
from ..services.member_link import ensure_user_member_link, resolve_member_id

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginRequest(BaseModel):
    invite_code: str
    name: str
    password: str

class RegisterRequest(BaseModel):
    invite_code: str
    name: str
    grade: str = ""
    password: str = Field(min_length=6)

class InitializePasswordRequest(BaseModel):
    invite_code: str
    name: str
    password: str = Field(min_length=6)

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)

class UserOut(BaseModel):
    id: int
    name: str
    grade: str
    role: str
    member_id: int | None = None

    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

def _user_response(user: User, token: str) -> AuthResponse:
    return AuthResponse(
        access_token=token,
        user=UserOut(
            id=user.id,
            name=user.name,
            grade=user.grade,
            role=user.role,
            member_id=user.member_id,
        ),
    )

def _issue_token(user: User) -> str:
    return create_access_token(user.id, user.name, user.grade, user.role, user.member_id)

def _authenticate_user(user: User | None, password: str) -> User:
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账号不存在")
    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="该账号尚未设置密码，请使用「首次设置密码」",
        )
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="密码错误")
    return user

@router.get("/me", response_model=UserOut, summary="当前登录用户")
def me(user: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)):
    db_user = db.get(User, user.user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    ensure_user_member_link(db, db_user)
    return UserOut(
        id=db_user.id,
        name=db_user.name,
        grade=db_user.grade,
        role=db_user.role,
        member_id=db_user.member_id,
    )

@router.post("/login", response_model=AuthResponse, summary="登录", description="姓名 + 密码 + 邀请码；管理员与成员邀请码不同。")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请输入姓名")

    if verify_admin_invite_code(data.invite_code):
        user = db.query(User).filter(User.name == name, User.role == "admin").first()
        user = _authenticate_user(user, data.password)
        return _user_response(user, _issue_token(user))

    if not verify_member_invite_code(data.invite_code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邀请码错误")

    user = db.query(User).filter(User.name == name, User.role == "member").first()
    user = _authenticate_user(user, data.password)
    ensure_user_member_link(db, user)
    return _user_response(user, _issue_token(user))

@router.post("/register", response_model=AuthResponse, status_code=201, summary="注册")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请输入姓名")
    try:
        validate_password(data.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    password_hash = hash_password(data.password)

    if verify_admin_invite_code(data.invite_code):
        if db.query(User).filter(User.name == name, User.role == "admin").first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该管理员已注册")
        user = User(
            name=name,
            grade="管理员",
            role="admin",
            member_id=None,
            password_hash=password_hash,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return _user_response(user, _issue_token(user))

    if not verify_member_invite_code(data.invite_code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邀请码错误")

    if not data.grade.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请选择入学年份")

    if db.query(User).filter(User.name == name, User.role == "member").first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该姓名已注册，请直接登录")

    member_id = resolve_member_id(db, name)
    user = User(
        name=name,
        grade=data.grade.strip(),
        role="member",
        member_id=member_id,
        password_hash=password_hash,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _user_response(user, _issue_token(user))

@router.post("/initialize-password", response_model=AuthResponse, summary="首次设置密码", description="为已存在但未设置密码的旧账号设置密码。")
def initialize_password(data: InitializePasswordRequest, db: Session = Depends(get_db)):
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请输入姓名")

    role = "admin" if verify_admin_invite_code(data.invite_code) else "member"
    if role == "member" and not verify_member_invite_code(data.invite_code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邀请码错误")

    user = db.query(User).filter(User.name == name, User.role == role).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账号不存在，请先注册")
    if user.password_hash:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该账号已设置密码，请直接登录")

    user.password_hash = hash_password(data.password)
    db.commit()
    db.refresh(user)
    return _user_response(user, _issue_token(user))

@router.post("/change-password", status_code=204, summary="修改密码")
def change_password(
    data: ChangePasswordRequest,
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_user = db.get(User, user.user_id)
    if not db_user or not verify_password(data.current_password, db_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="当前密码错误")
    db_user.password_hash = hash_password(data.new_password)
    db.commit()

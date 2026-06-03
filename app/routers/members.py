
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pathlib import Path
from sqlalchemy.orm import Session

from ..auth import AuthUser, require_admin, require_member
from ..database import get_db
from ..models.member import Member
from ..models.user import User
from ..schemas.member import MemberCreate, MemberOut, MemberSelfUpdate, MemberUpdate
from ..services.member_link import ensure_user_member_link
from ..services.slug_assign import ensure_unique_slug
from ..utils.grade_year import member_list_sort_key
from ..utils.mdx_io import write_mdx

router = APIRouter(prefix="/api/members", tags=["members"])
admin = APIRouter(prefix="/api/admin/members", tags=["admin-members"], dependencies=[Depends(require_admin)])
member = APIRouter(prefix="/api/member", tags=["member-profile"], dependencies=[Depends(require_member)])

import os

CONTENT_DIR = Path(os.environ.get("CONTENT_DIR", str(Path(__file__).resolve().parent.parent.parent / "contents" / "studio")))

_STATUS_SUBDIR = {
    "current": "current-members",
    "alumni": "alumni",
    "teacher": "teachers",
}


def _sync_member_mdx(m: Member) -> None:
    """将成员数据写回 MDX 文件，确保 Git 可同步"""
    subdir = _STATUS_SUBDIR.get(m.status, "current-members")
    out_dir = CONTENT_DIR / subdir
    slug = m.slug or m.name
    path = out_dir / f"{slug}.mdx"

    import json

    skills = m.skills
    if isinstance(skills, str):
        try:
            skills = json.loads(skills)
        except (json.JSONDecodeError, TypeError):
            skills = []

    projects = m.projects
    if isinstance(projects, str):
        try:
            projects = json.loads(projects)
        except (json.JSONDecodeError, TypeError):
            projects = []

    fm = {
        "title": m.name,
        "role": m.role or "",
        "grade": m.grade or "",
        "group": m.group or "",
        "avatar": m.avatar or "",
        "intro": m.intro or "",
        "message": m.message or "",
        "skills": list(skills) if skills else [],
        "projects": list(projects) if projects else [],
        "order": m.sort_order or 0,
    }
    write_mdx(path, fm, m.body or "")

@router.get("", response_model=list[MemberOut], summary="成员列表", description="公开。可用 query `status=current|alumni` 筛选。")
def list_members(
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
):
    q = db.query(Member)
    if status_filter:
        q = q.filter(Member.status == status_filter)
    members = q.all()
    members.sort(key=lambda m: member_list_sort_key(m.grade, m.sort_order or 0, m.id))
    return members

@router.get("/by-slug/{slug}", response_model=MemberOut, summary="按 slug 获取成员")
def get_member_by_slug(slug: str, db: Session = Depends(get_db)):
    m = db.query(Member).filter(Member.slug == slug).first()
    if not m:
        raise HTTPException(status_code=404, detail="成员不存在")
    return m

@router.get("/{member_id}", response_model=MemberOut, summary="按数字 ID 获取成员")
def get_member(member_id: int, db: Session = Depends(get_db)):
    m = db.get(Member, member_id)
    if not m:
        raise HTTPException(status_code=404, detail="成员不存在")
    return m

def _member_for_user(db: Session, auth_user: AuthUser) -> Member:
    db_user = db.get(User, auth_user.user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    ensure_user_member_link(db, db_user)
    if db_user.member_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="未关联成员档案，请确认登录姓名与成员卡片姓名一致，或联系管理员",
        )
    m = db.get(Member, db_user.member_id)
    if not m:
        raise HTTPException(status_code=404, detail="成员档案不存在")
    return m

@member.get("/profile", response_model=MemberOut, summary="我的成员档案")
def get_my_profile(user: AuthUser = Depends(require_member), db: Session = Depends(get_db)):
    return _member_for_user(db, user)

@member.put("/profile", response_model=MemberOut, summary="更新我的档案")
def update_my_profile(
    data: MemberSelfUpdate,
    user: AuthUser = Depends(require_member),
    db: Session = Depends(get_db),
):
    m = _member_for_user(db, user)

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(m, key, value)
    m.updated_by = user.display_name
    db.commit()
    db.refresh(m)
    _sync_member_mdx(m)
    return m

@admin.get("", response_model=list[MemberOut], summary="成员列表（管理员）")
def admin_list_members(
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
):
    q = db.query(Member)
    if status_filter:
        q = q.filter(Member.status == status_filter)
    members = q.all()
    members.sort(key=lambda m: member_list_sort_key(m.grade, m.sort_order or 0, m.id))
    return members

@admin.post("", response_model=MemberOut, status_code=201, summary="创建成员")
def create_member(data: MemberCreate, user: AuthUser = Depends(require_admin), db: Session = Depends(get_db)):
    payload = data.model_dump()
    payload["updated_by"] = user.display_name
    base_slug = payload.pop("slug", None) or payload["name"]
    payload["slug"] = ensure_unique_slug(db, Member, base_slug)
    m = Member(**payload)
    db.add(m)
    db.commit()
    db.refresh(m)
    _sync_member_mdx(m)
    return m

@admin.put("/{member_id}", response_model=MemberOut, summary="更新成员")
def update_member(
    member_id: int,
    data: MemberUpdate,
    user: AuthUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    m = db.get(Member, member_id)
    if not m:
        raise HTTPException(status_code=404, detail="成员不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(m, key, value)
    m.updated_by = user.display_name
    db.commit()
    db.refresh(m)
    _sync_member_mdx(m)
    return m

@admin.delete("/{member_id}", status_code=204, summary="删除成员")
def delete_member(member_id: int, db: Session = Depends(get_db)):
    m = db.get(Member, member_id)
    if not m:
        raise HTTPException(status_code=404, detail="成员不存在")
    # 删除对应的 MDX 文件
    subdir = _STATUS_SUBDIR.get(m.status, "current-members")
    slug = m.slug or m.name
    mdx_path = CONTENT_DIR / subdir / f"{slug}.mdx"
    if mdx_path.exists():
        os.remove(mdx_path)
    db.delete(m)
    db.commit()

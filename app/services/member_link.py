
from sqlalchemy.orm import Session

from ..models.member import Member
from ..models.user import User

def resolve_member_id(db: Session, name: str) -> int | None:
    trimmed = name.strip()
    if not trimmed:
        return None
    member = (
        db.query(Member)
        .filter(Member.name == trimmed, Member.status == "current")
        .first()
    )
    if not member:
        member = db.query(Member).filter(Member.name == trimmed).first()
    return member.id if member else None

def ensure_user_member_link(db: Session, user: User) -> bool:
    if user.role != "member" or user.member_id is not None:
        return False
    member_id = resolve_member_id(db, user.name)
    if member_id is None:
        return False
    user.member_id = member_id
    db.commit()
    db.refresh(user)
    return True

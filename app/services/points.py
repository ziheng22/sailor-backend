
from sqlalchemy.orm import Session

from ..models.member import Member
from ..models.point_transaction import PointTransaction

def award_points(
    db: Session,
    member_id: int,
    delta: int,
    reason: str,
    granted_by: str,
) -> PointTransaction:
    if delta == 0:
        raise ValueError("积分变动不能为 0")

    member = db.get(Member, member_id)
    if not member:
        raise ValueError("成员不存在")

    next_balance = (member.points_total or 0) + delta
    if next_balance < 0:
        raise ValueError("积分不足，无法扣减")

    member.points_total = next_balance
    tx = PointTransaction(
        member_id=member_id,
        delta=delta,
        balance_after=next_balance,
        reason=(reason or "").strip()[:256],
        granted_by=granted_by,
    )
    db.add(tx)
    db.flush()
    return tx

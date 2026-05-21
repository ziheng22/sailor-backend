
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..auth import AuthUser, require_admin, require_member
from ..database import get_db
from ..models.member import Member
from ..models.point_transaction import PointTransaction
from ..schemas.point import LeaderboardEntry, PointAwardRequest, PointTransactionOut
from ..services.leaderboard import build_leaderboard
from ..services.points import award_points

router = APIRouter(prefix="/api/points", tags=["points"], dependencies=[Depends(require_member)])
admin = APIRouter(prefix="/api/admin/points", tags=["admin-points"], dependencies=[Depends(require_admin)])

@router.get("/leaderboard", response_model=list[LeaderboardEntry], summary="积分榜排名")
def leaderboard(
    status_filter: str = Query("current", alias="status"),
    db: Session = Depends(get_db),
):
    return build_leaderboard(db, status_filter)

@router.get("/history", response_model=list[PointTransactionOut], summary="积分流水")
def point_history(
    member_id: int | None = Query(None, description="不传则返回工作室全员最近积分变动"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(PointTransaction)
    if member_id is not None:
        q = q.filter(PointTransaction.member_id == member_id)
    return q.order_by(PointTransaction.created_at.desc(), PointTransaction.id.desc()).limit(limit).all()

@router.get("/member/{member_id}", response_model=LeaderboardEntry, summary="某成员积分摘要")
def member_points_summary(member_id: int, db: Session = Depends(get_db)):
    member = db.get(Member, member_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="成员不存在")
    board = build_leaderboard(db, member.status)
    entry = next((row for row in board if row.member_id == member.id), None)
    if entry:
        return entry
    return LeaderboardEntry(
        rank=0,
        member_id=member.id,
        name=member.name,
        grade=member.grade or "",
        group=member.group or "",
        role=member.role or "",
        points_total=int(member.points_total or 0),
    )

@admin.post("/award", response_model=PointTransactionOut, status_code=201, summary="下发积分")
def admin_award_points(
    data: PointAwardRequest,
    user: AuthUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        tx = award_points(db, data.member_id, data.points, data.reason, user.display_name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    db.refresh(tx)
    return tx

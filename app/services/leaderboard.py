
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.member import Member
from ..schemas.point import LeaderboardEntry

def build_leaderboard(db: Session, status: str = "current") -> list[LeaderboardEntry]:
    members = (
        db.query(Member)
        .filter(Member.status == status)
        .order_by(
            func.coalesce(Member.points_total, 0).desc(),
            Member.sort_order,
            Member.name,
            Member.id,
        )
        .all()
    )

    entries: list[LeaderboardEntry] = []
    rank = 0
    prev_points: int | None = None
    all_zero = not members or all(int(m.points_total or 0) == 0 for m in members)

    for index, member in enumerate(members):
        points = int(member.points_total or 0)
        if all_zero:
            rank = index + 1
        elif prev_points is None or points < prev_points:
            rank = index + 1
            prev_points = points
        entries.append(
            LeaderboardEntry(
                rank=rank,
                member_id=member.id,
                name=member.name,
                grade=member.grade or "",
                group=member.group or "",
                role=member.role or "",
                points_total=points,
            )
        )
    return entries

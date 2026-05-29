
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy.orm import Session

from ..models.article import Article
from ..models.member import Member
from ..models.project import Project
from ..utils.mdx_io import parse_mdx
from .slug_assign import ensure_unique_slug

@dataclass
class SlugSyncReport:
    members_updated: int = 0
    projects_updated: int = 0
    articles_updated: int = 0
    skipped: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"members={self.members_updated}, projects={self.projects_updated}, "
            f"articles={self.articles_updated}, skipped={len(self.skipped)}"
        )

def _assign_slug(db: Session, model, row, target_slug: str, report: SlugSyncReport, label: str) -> None:
    if row.slug == target_slug:
        return
    new_slug = ensure_unique_slug(db, model, target_slug, exclude_id=row.id)
    if new_slug != target_slug:
        report.skipped.append(f"{label}: slug '{target_slug}' taken, got '{new_slug}'")
    row.slug = new_slug

def _find_member(db: Session, status: str, stem: str, title: str) -> Member | None:
    by_slug = db.query(Member).filter(Member.slug == stem, Member.status == status).first()
    if by_slug:
        return by_slug
    return db.query(Member).filter(Member.name == title, Member.status == status).first()

def sync_slugs_from_content(db: Session, content_dir: Path) -> SlugSyncReport:
    report = SlugSyncReport()
    root = Path(content_dir)
    if not root.exists():
        report.skipped.append(f"CONTENT_DIR not found: {root}")
        return report

    for status, subdir in [("current", "current-members"), ("alumni", "alumni")]:
        member_dir = root / subdir
        if not member_dir.exists():
            continue
        for f in sorted(member_dir.glob("*.mdx")):
            data, _ = parse_mdx(f)
            stem = f.stem
            title = str(data.get("title", stem))
            row = _find_member(db, status, stem, title)
            if not row:
                report.skipped.append(f"member[{status}] no match: {stem} ({title})")
                continue
            before = row.slug
            _assign_slug(db, Member, row, stem, report, f"member:{title}")
            if row.slug != before:
                report.members_updated += 1

    proj_dir = root / "projects"
    if proj_dir.exists():
        for f in sorted(proj_dir.glob("*.mdx")):
            data, _ = parse_mdx(f)
            stem = f.stem
            title = str(data.get("title", stem))
            row = db.query(Project).filter((Project.slug == stem) | (Project.name == title)).first()
            if not row:
                report.skipped.append(f"project no match: {stem} ({title})")
                continue
            before = row.slug
            _assign_slug(db, Project, row, stem, report, f"project:{title}")
            if row.slug != before:
                report.projects_updated += 1

    notes_dir = root / "notes"
    if notes_dir.exists():
        for f in sorted(notes_dir.glob("*.mdx")):
            data, _ = parse_mdx(f)
            stem = f.stem
            title = str(data.get("title", stem))
            row = db.query(Article).filter((Article.slug == stem) | (Article.title == title)).first()
            if not row:
                report.skipped.append(f"article no match: {stem} ({title})")
                continue
            before = row.slug
            _assign_slug(db, Article, row, stem, report, f"article:{title}")
            if row.slug != before:
                report.articles_updated += 1

    db.commit()
    return report

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.passwords import hash_password
from app.database import engine, SessionLocal, Base
from app.models.member import Member
from app.models.project import Project
from app.models.article import Article
from app.models.page import Page
from app.models.user import User
from app.services.slug_assign import ensure_unique_slug
from app.utils.mdx_io import parse_mdx

_repo_root = Path(__file__).resolve().parent
_default_content = _repo_root / "contents" / "studio"
_legacy_paths = [
    _repo_root.parent / "sailor-frontend" / "contents" / "studio",
    _repo_root.parent / "posthog.com" / "contents" / "studio",
]
CONTENT_DIR = Path(settings.content_dir or os.environ.get("CONTENT_DIR", str(_default_content)))
if not CONTENT_DIR.exists():
    for legacy in _legacy_paths:
        if legacy.exists():
            CONTENT_DIR = legacy
            break

def _upsert_member_slug(db, row: Member, stem: str) -> None:
    if row.slug != stem:
        row.slug = ensure_unique_slug(db, Member, stem, exclude_id=row.id)

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    page_files = {
        "index": CONTENT_DIR / "index.mdx",
        "join": CONTENT_DIR / "join.mdx",
        "contact": CONTENT_DIR / "contact.mdx",
    }
    for slug, path in page_files.items():
        if path.exists() and not db.query(Page).filter(Page.slug == slug).first():
            data, body = parse_mdx(path)
            db.add(Page(slug=slug, title=data.get("title", slug),
                        description=data.get("description", ""), body=body))

    for status, subdir in [("current", "current-members"), ("alumni", "alumni"), ("teacher", "teachers")]:
        member_dir = CONTENT_DIR / subdir
        if not member_dir.exists():
            continue
        for f in sorted(member_dir.glob("*.mdx")):
            data, body = parse_mdx(f)
            name = data.get("title", f.stem)
            slug = f.stem
            existing = db.query(Member).filter(Member.slug == slug).first()
            if not existing:
                existing = db.query(Member).filter(Member.name == name, Member.status == status).first()
            if existing:
                _upsert_member_slug(db, existing, slug)
                continue
            db.add(Member(
                slug=slug,
                status=status,
                name=name,
                role=data.get("role", ""),
                grade=data.get("grade", ""),
                group=data.get("group", ""),
                avatar=data.get("avatar", ""),
                intro=data.get("intro", ""),
                message=data.get("message", ""),
                skills=json.dumps(data.get("skills", []) if isinstance(data.get("skills"), list) else [], ensure_ascii=False),
                projects=json.dumps(data.get("projects", []) if isinstance(data.get("projects"), list) else [], ensure_ascii=False),
                sort_order=int(data.get("order", 0)),
                body=body,
            ))

    proj_dir = CONTENT_DIR / "projects"
    if proj_dir.exists():
        for f in sorted(proj_dir.glob("*.mdx")):
            data, body = parse_mdx(f)
            name = data.get("title", f.stem)
            slug = f.stem
            existing = db.query(Project).filter((Project.slug == slug) | (Project.name == name)).first()
            if existing:
                if existing.slug != slug:
                    existing.slug = ensure_unique_slug(db, Project, slug, exclude_id=existing.id)
                continue
            db.add(Project(
                slug=slug,
                name=name,
                summary=data.get("summary", ""),
                status=data.get("status", "Planning"),
                category=data.get("category", ""),
                cover=data.get("cover", ""),
                tech=json.dumps(data.get("tech", []) if isinstance(data.get("tech"), list) else [], ensure_ascii=False),
                members=json.dumps(data.get("members", []) if isinstance(data.get("members"), list) else [], ensure_ascii=False),
                links=json.dumps(data.get("links", {}) if isinstance(data.get("links"), dict) else {}, ensure_ascii=False),
                is_displayed=True,
                sort_order=0,
                body=body,
            ))

    notes_dir = CONTENT_DIR / "notes"
    if notes_dir.exists():
        for f in sorted(notes_dir.glob("*.mdx")):
            data, body = parse_mdx(f)
            title = data.get("title", f.stem)
            slug = f.stem
            existing = db.query(Article).filter((Article.slug == slug) | (Article.title == title)).first()
            if existing:
                if existing.slug != slug:
                    existing.slug = ensure_unique_slug(db, Article, slug, exclude_id=existing.id)
                continue
            raw_names = data.get("member_names") or data.get("members") or []
            if isinstance(raw_names, list):
                member_names = json.dumps([str(n) for n in raw_names], ensure_ascii=False)
            else:
                member_names = "[]"
            published_at = None
            if data.get("date"):
                try:
                    from datetime import date
                    published_at = date.fromisoformat(data["date"])
                except ValueError:
                    pass
            db.add(Article(
                slug=slug,
                title=title,
                member_names=member_names,
                type=data.get("type", "工作室动态"),
                tags=json.dumps(data.get("tags", []) if isinstance(data.get("tags"), list) else [], ensure_ascii=False),
                published_at=published_at,
                is_displayed=True,
                sort_order=0,
                body=body,
            ))

    if not db.query(User).filter(User.role == "admin").first():
        admin_password = settings.seed_admin_password
        db.add(
            User(
                name=settings.seed_admin_name,
                grade="管理员",
                role="admin",
                member_id=None,
                password_hash=hash_password(admin_password),
            )
        )
        print(
            f"Created admin user: {settings.seed_admin_name} "
            f"(password from SEED_ADMIN_PASSWORD, admin invite: {settings.admin_invite_code})"
        )

    db.commit()
    db.close()
    print("Seed complete. Run: python sync_slugs.py  (to align slugs with MDX filenames)")

if __name__ == "__main__":
    seed()

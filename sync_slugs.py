
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.database import SessionLocal
from app.services.slug_sync import sync_slugs_from_content

_repo_root = Path(__file__).resolve().parent.parent
_default = _repo_root / "contents" / "studio"
_legacy = _repo_root.parent / "sailor-studio" / "contents" / "studio"

def resolve_content_dir() -> Path:
    if settings.content_dir:
        return Path(settings.content_dir)
    env = os.environ.get("CONTENT_DIR")
    if env:
        return Path(env)
    if _default.exists():
        return _default
    if _legacy.exists():
        return _legacy
    return _default

if __name__ == "__main__":
    content_dir = resolve_content_dir()
    db = SessionLocal()
    try:
        report = sync_slugs_from_content(db, content_dir)
        print(f"Slug sync from {content_dir}")
        print(report.summary())
        for line in report.skipped[:20]:
            print(f"  - {line}")
        if len(report.skipped) > 20:
            print(f"  ... and {len(report.skipped) - 20} more")
    finally:
        db.close()

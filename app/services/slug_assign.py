
from sqlalchemy.orm import Session

from ..utils.slug import slugify

def ensure_unique_slug(db: Session, model, base_slug: str, exclude_id: int | None = None) -> str:
    """
    将标题/文件名转为 URL 安全字符串。
    exclude_id：更新自身记录时不把当前行的 slug 算作冲突。
    """
    slug = slugify(base_slug)
    candidate = slug
    suffix = 2
    while True:
        existing = db.query(model).filter(model.slug == candidate).first()
        if not existing or (exclude_id is not None and existing.id == exclude_id):
            break
        candidate = f"{slug}-{suffix}"
        suffix += 1
    return candidate

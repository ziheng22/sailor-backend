
from datetime import date, datetime

from ..auth import AuthUser
from ..models.article import Article
from ..utils.json_fields import validate_json_array

ADMIN_ONLY_FIELDS = frozenset({"completed_at", "is_displayed"})

def parse_completed_at(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    if isinstance(value, str) and value.strip():
        text = value.strip().replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            return None
    return None

def prepare_article_payload(data: dict, user: AuthUser) -> dict:
    payload = dict(data)
    payload.pop("updated_by", None)

    if "member_names" in payload and payload["member_names"] is not None:
        payload["member_names"] = validate_json_array(payload["member_names"], "member_names")

    if "tags" in payload and payload["tags"] is not None:
        payload["tags"] = validate_json_array(payload["tags"], "tags")

    if not user.is_admin:
        for key in ADMIN_ONLY_FIELDS:
            payload.pop(key, None)
    elif "completed_at" in payload:
        payload["completed_at"] = parse_completed_at(payload["completed_at"])

    if "published_at" in payload and isinstance(payload["published_at"], str):
        text = payload["published_at"].strip()
        payload["published_at"] = text if text else None

    return payload

def apply_article_fields(article: Article, payload: dict, editor: str) -> None:
    for key, value in payload.items():
        setattr(article, key, value)
    article.updated_by = editor

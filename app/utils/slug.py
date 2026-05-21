
import re
import unicodedata

def slugify(text: str, fallback: str = "item") -> str:
    value = unicodedata.normalize("NFKC", (text or "").strip().lower())
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    value = re.sub(r"[\s_]+", "-", value).strip("-")
    return value or fallback

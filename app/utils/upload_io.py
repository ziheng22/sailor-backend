
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from ..config import settings

BLOCKED_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".com", ".msi", ".scr", ".ps1", ".sh", ".bash",
    ".php", ".phtml", ".asp", ".aspx", ".jsp", ".js", ".mjs", ".html", ".htm",
    ".svgz",
}

DEFAULT_ALLOWED = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
    ".pdf", ".mp4", ".webm", ".mov",
    ".mp3", ".wav", ".ogg",
    ".zip", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
}

def allowed_extensions() -> set[str]:
    raw = settings.upload_allowed_extensions.strip()
    if not raw:
        return DEFAULT_ALLOWED
    return {e if e.startswith(".") else f".{e}" for e in raw.split(",") if e.strip()}

def validate_upload(file: UploadFile, size: int) -> str:
    if size <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件为空")
    if size > settings.upload_max_bytes:
        max_mb = settings.upload_max_bytes // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件超过 {max_mb}MB 限制",
        )

    original = (file.filename or "").strip()
    ext = Path(original).suffix.lower()
    if not ext:
        mime = (file.content_type or "").lower()
        if mime.startswith("image/"):
            ext = "." + mime.split("/", 1)[1].split("+", 1)[0]
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无法识别文件类型")

    if ext in BLOCKED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不允许上传该类型文件")
    if ext not in allowed_extensions():
        allowed = ", ".join(sorted(allowed_extensions()))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"仅支持以下扩展名：{allowed}",
        )
    return ext

def build_stored_name(ext: str) -> str:
    return f"{uuid.uuid4().hex}{ext}"

def upload_dir() -> Path:
    path = Path(settings.upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()

def public_url(path: str) -> str:
    base = (settings.public_base_url or "").strip().rstrip("/")
    if not base:
        return path
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"{base}{path}"

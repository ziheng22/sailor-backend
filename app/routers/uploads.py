
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..auth import require_admin
from ..config import settings
from ..database import get_db
from ..models.upload import Upload
from ..schemas.upload import UploadListOut, UploadOut
from ..utils.upload_io import (
    build_stored_name,
    public_url,
    upload_dir,
    validate_upload,
)

router = APIRouter(prefix="/api/admin/uploads", tags=["admin-uploads"], dependencies=[Depends(require_admin)])

def _to_upload_out(rec: Upload) -> UploadOut:
    data = UploadOut.model_validate(rec)
    return data.model_copy(update={"public_url": public_url(rec.url)})

@router.get("", response_model=UploadListOut, summary="上传文件列表")
def list_uploads(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    limit = min(max(limit, 1), 200)
    offset = max(offset, 0)
    q = db.query(Upload).order_by(Upload.created_at.desc(), Upload.id.desc())
    total = q.count()
    rows = q.offset(offset).limit(limit).all()
    return UploadListOut(
        items=[_to_upload_out(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )

@router.get("/{upload_id}", response_model=UploadOut, summary="获取上传记录")
def get_upload(upload_id: int, db: Session = Depends(get_db)):
    rec = db.get(Upload, upload_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")
    return _to_upload_out(rec)

@router.post("", response_model=UploadOut, status_code=status.HTTP_201_CREATED, summary="上传文件")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    ext = validate_upload(file, len(content))

    stored_name = build_stored_name(ext)
    file_path = upload_dir() / stored_name
    file_path.write_bytes(content)

    rec = Upload(
        filename=stored_name,
        original_name=Path(file.filename or "").name,
        mime_type=file.content_type or "",
        size=len(content),
        url=f"/uploads/{stored_name}",
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return _to_upload_out(rec)

@router.delete("/{upload_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除上传文件")
def delete_upload(upload_id: int, db: Session = Depends(get_db)):
    rec = db.get(Upload, upload_id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")

    disk_path = upload_dir() / rec.filename
    if disk_path.is_file():
        disk_path.unlink()

    db.delete(rec)
    db.commit()
    return None

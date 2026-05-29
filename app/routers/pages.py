from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import AuthUser, require_admin
from ..database import get_db
from ..models.page import Page
from ..schemas.page import PageOut, PageUpdate

ADMIN_PAGE_SLUGS = frozenset({"index", "join", "contact"})

router = APIRouter(prefix="/api/pages", tags=["pages"])
admin = APIRouter(prefix="/api/admin/pages", tags=["admin-pages"], dependencies=[Depends(require_admin)])

@router.get("/{slug}", response_model=PageOut, summary="获取静态页", description="slug: index | join | contact")
def get_page(slug: str, db: Session = Depends(get_db)):
    page = db.query(Page).filter(Page.slug == slug).first()
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    return page

@admin.get("", response_model=list[PageOut], summary="静态页列表")
def admin_list_pages(db: Session = Depends(get_db)):
    return db.query(Page).order_by(Page.slug).all()

@admin.put("/{slug}", response_model=PageOut, summary="更新静态页")
def update_page(
    slug: str,
    data: PageUpdate,
    user: AuthUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if slug not in ADMIN_PAGE_SLUGS:
        raise HTTPException(status_code=400, detail="该页面不允许通过此接口修改")
    page = db.query(Page).filter(Page.slug == slug).first()
    if not page:
        page = Page(slug=slug, title=slug, description="", body="")
        db.add(page)
        db.flush()
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(page, key, value)
    page.updated_by = user.display_name
    db.commit()
    db.refresh(page)
    return page

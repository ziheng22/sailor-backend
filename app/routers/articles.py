
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import AuthUser, get_optional_user, require_admin, require_member
from ..database import get_db
from ..models.article import Article
from ..models.article_revision import ArticleRevision
from ..schemas.article import ArticleCreate, ArticleOut, ArticleUpdate
from ..schemas.article_revision import ArticleRevisionOut
from ..services.article_apply import apply_article_fields, prepare_article_payload
from ..services.article_serialize import serialize_article, serialize_articles, serialize_revisions
from ..services.revisions import record_article_revision
from ..services.slug_assign import ensure_unique_slug

router = APIRouter(prefix="/api/articles", tags=["articles"])
admin = APIRouter(prefix="/api/admin/articles", tags=["admin-articles"], dependencies=[Depends(require_admin)])
member = APIRouter(prefix="/api/member/articles", tags=["member-articles"], dependencies=[Depends(require_member)])

def _get_by_slug(db: Session, slug: str) -> Article:
    article = db.query(Article).filter(Article.slug == slug).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    return article

def _get_by_id(db: Session, article_id: int) -> Article:
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    return article

def _list_revisions(db: Session, article_id: int) -> list[ArticleRevision]:
    return (
        db.query(ArticleRevision)
        .filter(ArticleRevision.article_id == article_id)
        .order_by(ArticleRevision.created_at.desc(), ArticleRevision.id.desc())
        .all()
    )

def _create_article(db: Session, data: ArticleCreate, user: AuthUser) -> Article:
    try:
        payload = prepare_article_payload(data.model_dump(), user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    payload["updated_by"] = user.display_name
    base_slug = payload.pop("slug", None) or payload["title"]
    payload["slug"] = ensure_unique_slug(db, Article, base_slug)
    article = Article(**payload)
    db.add(article)
    db.flush()
    record_article_revision(db, article, "create", user.display_name)
    db.commit()
    db.refresh(article)
    return article

def _update_article(db: Session, article: Article, data: ArticleUpdate, user: AuthUser) -> Article:
    try:
        payload = prepare_article_payload(data.model_dump(exclude_unset=True), user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if "slug" in payload and payload["slug"]:
        payload["slug"] = ensure_unique_slug(db, Article, payload["slug"])
    apply_article_fields(article, payload, user.display_name)
    record_article_revision(db, article, "update", user.display_name)
    db.commit()
    db.refresh(article)
    return article

@router.get("", summary="航海日志列表", description="公开。带 Bearer token 时响应含截止时间 completed_at。")
def list_articles(
    db: Session = Depends(get_db),
    user: AuthUser | None = Depends(get_optional_user),
):
    articles = (
        db.query(Article)
        .filter(Article.is_displayed.is_(True))
        .order_by(Article.published_at.desc().nullslast(), Article.sort_order, Article.id)
        .all()
    )
    return serialize_articles(articles, user)

@router.get("/by-slug/{slug}", summary="按 slug 获取日志")
def get_article_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    user: AuthUser | None = Depends(get_optional_user),
):
    return serialize_article(_get_by_slug(db, slug), user)

@router.get("/by-slug/{slug}/revisions", summary="修订历史（按 slug）", description="登录后可见截止时间字段。")
def list_revisions_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    user: AuthUser | None = Depends(get_optional_user),
):
    article = _get_by_slug(db, slug)
    return serialize_revisions(_list_revisions(db, article.id), user)

@router.get("/{article_id}", summary="按 ID 获取日志")
def get_article(
    article_id: int,
    db: Session = Depends(get_db),
    user: AuthUser | None = Depends(get_optional_user),
):
    return serialize_article(_get_by_id(db, article_id), user)

@router.get("/{article_id}/revisions", summary="修订历史（按 ID）")
def list_article_revisions(
    article_id: int,
    db: Session = Depends(get_db),
    user: AuthUser | None = Depends(get_optional_user),
):
    _get_by_id(db, article_id)
    return serialize_revisions(_list_revisions(db, article_id), user)

@member.post("", response_model=ArticleOut, status_code=201, summary="创建日志")
def member_create_article(
    data: ArticleCreate,
    user: AuthUser = Depends(require_member),
    db: Session = Depends(get_db),
):
    return _create_article(db, data, user)

@member.put("/{article_id}", response_model=ArticleOut, summary="更新日志")
def member_update_article(
    article_id: int,
    data: ArticleUpdate,
    user: AuthUser = Depends(require_member),
    db: Session = Depends(get_db),
):
    return _update_article(db, _get_by_id(db, article_id), data, user)

@member.put("/by-slug/{slug}", response_model=ArticleOut, summary="按 slug 更新日志")
def member_update_article_by_slug(
    slug: str,
    data: ArticleUpdate,
    user: AuthUser = Depends(require_member),
    db: Session = Depends(get_db),
):
    return _update_article(db, _get_by_slug(db, slug), data, user)

@member.get("/{article_id}/revisions", response_model=list[ArticleRevisionOut], summary="修订历史（成员）")
def member_list_revisions(article_id: int, db: Session = Depends(get_db)):
    _get_by_id(db, article_id)
    return _list_revisions(db, article_id)

@admin.get("", response_model=list[ArticleOut], summary="日志列表（管理员）")
def admin_list_articles(db: Session = Depends(get_db)):
    return db.query(Article).order_by(Article.published_at.desc().nullslast(), Article.sort_order, Article.id).all()

@admin.post("", response_model=ArticleOut, status_code=201, summary="创建日志")
def admin_create_article(
    data: ArticleCreate,
    user: AuthUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return _create_article(db, data, user)

@admin.put("/{article_id}", response_model=ArticleOut, summary="更新日志")
def admin_update_article(
    article_id: int,
    data: ArticleUpdate,
    user: AuthUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return _update_article(db, _get_by_id(db, article_id), data, user)

@admin.put("/by-slug/{slug}", response_model=ArticleOut, summary="按 slug 更新日志")
def admin_update_article_by_slug(
    slug: str,
    data: ArticleUpdate,
    user: AuthUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return _update_article(db, _get_by_slug(db, slug), data, user)

@admin.delete("/{article_id}", status_code=204, summary="删除日志")
def admin_delete_article(article_id: int, db: Session = Depends(get_db)):
    article = _get_by_id(db, article_id)
    db.delete(article)
    db.commit()

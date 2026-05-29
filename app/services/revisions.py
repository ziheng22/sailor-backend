
from sqlalchemy.orm import Session

from ..models.article import Article
from ..models.article_revision import ArticleRevision

def record_article_revision(
    db: Session,
    article: Article,
    action: str,
    updated_by: str,
) -> None:
    db.add(
        ArticleRevision(
            article_id=article.id,
            action=action,
            title=article.title,
            body=article.body or "",
            member_names=article.member_names or "[]",
            completed_at=article.completed_at,
            updated_by=updated_by,
        )
    )

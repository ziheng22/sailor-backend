
from ..auth import AuthUser
from ..models.article import Article
from ..models.article_revision import ArticleRevision
from ..schemas.article import ArticleOut, ArticlePublicOut
from ..schemas.article_revision import ArticleRevisionOut, ArticleRevisionPublicOut

def serialize_article(article: Article, user: AuthUser | None) -> ArticleOut | ArticlePublicOut:
    if user is not None:
        return ArticleOut.model_validate(article)
    return ArticlePublicOut.model_validate(article)

def serialize_articles(articles: list[Article], user: AuthUser | None) -> list[ArticleOut | ArticlePublicOut]:
    return [serialize_article(article, user) for article in articles]

def serialize_revision(
    revision: ArticleRevision, user: AuthUser | None
) -> ArticleRevisionOut | ArticleRevisionPublicOut:
    if user is not None:
        return ArticleRevisionOut.model_validate(revision)
    return ArticleRevisionPublicOut.model_validate(revision)

def serialize_revisions(
    revisions: list[ArticleRevision], user: AuthUser | None
) -> list[ArticleRevisionOut | ArticleRevisionPublicOut]:
    return [serialize_revision(revision, user) for revision in revisions]

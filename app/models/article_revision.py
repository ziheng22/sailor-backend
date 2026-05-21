
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func

from ..database import Base

class ArticleRevision(Base):
    __tablename__ = "article_revisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(16), nullable=False)  # create | update
    title = Column(String(128), nullable=False)
    body = Column(Text, default="")
    member_names = Column(Text, default="[]")
    completed_at = Column(DateTime, nullable=True)
    updated_by = Column(String(64), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

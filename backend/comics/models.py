from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from lit_club_app.backend.db.base import Base


class ComicChapter(Base):
    __tablename__ = "comic_chapters"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    number = Column(Integer, nullable=False)
    is_public = Column(Boolean, nullable=False, default=False)
    cover = Column(String, nullable=True)
    pages = relationship("ComicPage", cascade="all, delete-orphan", order_by="ComicPage.number")

    __table_args__ = (CheckConstraint("number > 0", name="comic_chapter_positive_number"),)


class ComicPage(Base):
    __tablename__ = "comic_pages"

    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey("comic_chapters.id", ondelete="CASCADE"), nullable=False, index=True)
    number = Column(Integer, nullable=False)
    image = Column(String, nullable=False)

    __table_args__ = (CheckConstraint("number > 0", name="comic_page_positive_number"),)

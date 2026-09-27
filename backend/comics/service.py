from io import BytesIO
from pathlib import Path
from uuid import uuid4
import warnings

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from lit_club_app.backend.comics.models import ComicChapter, ComicPage
from lit_club_app.backend.comics.schemas import ChapterWrite
from lit_club_app.backend.common.enums import Roles
from lit_club_app.backend.core.config import settings


def storage_dir() -> Path:
    # Outside the publicly mounted uploads directory: every image requires auth.
    return settings.upload_dir.parent / "comic_uploads"


def get_chapter(db: Session, chapter_id: int, user) -> ComicChapter:
    chapter = db.get(ComicChapter, chapter_id)
    if chapter is None or (not chapter.is_public and user.role != Roles.ADMIN):
        raise HTTPException(404, "Глава не найдена")
    return chapter


def list_chapters(db: Session, user):
    query = select(ComicChapter).options(selectinload(ComicChapter.pages))
    if user.role != Roles.ADMIN:
        query = query.where(ComicChapter.is_public.is_(True))
    return db.scalars(query.order_by(ComicChapter.number, ComicChapter.id)).all()


def serialize(chapter: ComicChapter):
    base = f"/comics/chapters/{chapter.id}"
    return {
        "id": chapter.id, "title": chapter.title, "number": chapter.number,
        "is_public": chapter.is_public, "page_count": len(chapter.pages),
        "cover_url": f"{base}/cover?v={chapter.cover}" if chapter.cover else None,
        "pages": [
            {"id": page.id, "number": page.number,
             "image_url": f"{base}/pages/{page.id}/image?v={page.image}"}
            for page in sorted(chapter.pages, key=lambda page: (page.number, page.id))
        ],
    }


async def save_image(file: UploadFile, created: list[Path]) -> str:
    data = await file.read(20 * 1024 * 1024 + 1)
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(413, "Изображение должно быть не больше 20 МБ")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as image:
                extension = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}.get(image.format)
                if extension is None:
                    raise HTTPException(400, "Допустимы изображения JPEG, PNG и WebP")
                image.verify()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise HTTPException(400, "Файл не является корректным изображением")
    directory = storage_dir()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{uuid4().hex}{extension}"
    created.append(path)
    path.write_bytes(data)
    return path.name


async def save_chapter(db: Session, chapter: ComicChapter, payload: ChapterWrite,
                       cover: UploadFile | None, files: list[UploadFile]):
    existing = {page.id: page for page in chapter.pages}
    for page in payload.pages:
        if page.id is not None and page.id not in existing:
            raise HTTPException(400, "Страница не принадлежит этой главе")
        if page.id is None and page.file_index is None:
            raise HTTPException(400, "Для новой страницы нужно изображение")
        if page.file_index is not None and page.file_index >= len(files):
            raise HTTPException(400, "Не найден файл страницы")

    created: list[Path] = []
    obsolete = {page.image for page in chapter.pages}
    if chapter.cover:
        obsolete.add(chapter.cover)
    try:
        chapter.title = payload.title
        chapter.number = payload.number
        chapter.is_public = payload.is_public
        if cover is not None:
            chapter.cover = await save_image(cover, created)
        pages = []
        for item in payload.pages:
            page = existing[item.id] if item.id is not None else ComicPage()
            page.number = item.number
            if item.file_index is not None:
                page.image = await save_image(files[item.file_index], created)
            pages.append(page)
        chapter.pages = pages
        db.add(chapter)
        db.commit()
    except Exception:
        db.rollback()
        for path in created:
            path.unlink(missing_ok=True)
        raise

    obsolete.difference_update(page.image for page in chapter.pages)
    obsolete.discard(chapter.cover)
    for name in obsolete:
        (storage_dir() / name).unlink(missing_ok=True)
    return serialize(chapter)

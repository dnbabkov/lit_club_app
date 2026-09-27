from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from lit_club_app.backend.api.dependencies import get_current_user, get_db
from lit_club_app.backend.comics import service
from lit_club_app.backend.comics.models import ComicChapter
from lit_club_app.backend.comics.schemas import ChapterRead, ChapterSummary, ChapterWrite
from lit_club_app.backend.common.enums import Roles
from lit_club_app.backend.users.models import User

router = APIRouter(prefix="/comics/chapters", tags=["comics"])


def require_admin(user: User = Depends(get_current_user)):
    if user.role != Roles.ADMIN:
        raise HTTPException(403, "Редактировать комикс может только администратор")
    return user


def parse_payload(payload: str = Form(...)) -> ChapterWrite:
    try:
        return ChapterWrite.model_validate_json(payload)
    except ValidationError:
        raise HTTPException(422, "Проверьте название, положительные номера и уникальность номеров страниц")


@router.get("", response_model=list[ChapterSummary])
def chapters(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return [service.serialize(chapter) for chapter in service.list_chapters(db, user)]


@router.post("", response_model=ChapterRead, status_code=201)
async def create_chapter(payload: ChapterWrite = Depends(parse_payload),
                         cover: UploadFile | None = File(None), files: list[UploadFile] = File(default=[]),
                         db: Session = Depends(get_db), user: User = Depends(require_admin)):
    return await service.save_chapter(db, ComicChapter(), payload, cover, files)


@router.get("/{chapter_id}", response_model=ChapterRead)
def chapter(chapter_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.serialize(service.get_chapter(db, chapter_id, user))


@router.post("/{chapter_id}", response_model=ChapterRead)
async def update_chapter(chapter_id: int, payload: ChapterWrite = Depends(parse_payload),
                         cover: UploadFile | None = File(None), files: list[UploadFile] = File(default=[]),
                         db: Session = Depends(get_db), user: User = Depends(require_admin)):
    return await service.save_chapter(db, service.get_chapter(db, chapter_id, user), payload, cover, files)


def image_response(name: str | None):
    if not name or not (service.storage_dir() / name).is_file():
        raise HTTPException(404, "Изображение не найдено")
    return FileResponse(service.storage_dir() / name, headers={"Cache-Control": "private, no-store"})


@router.get("/{chapter_id}/cover")
def cover_image(chapter_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return image_response(service.get_chapter(db, chapter_id, user).cover)


@router.get("/{chapter_id}/pages/{page_id}/image")
def page_image(chapter_id: int, page_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    chapter = service.get_chapter(db, chapter_id, user)
    page = next((page for page in chapter.pages if page.id == page_id), None)
    return image_response(page.image if page else None)

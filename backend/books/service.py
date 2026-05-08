from collections import defaultdict
from pathlib import Path
from typing import Sequence

from fastapi import UploadFile
from sqlalchemy.orm import Session

from lit_club_app.backend.books.models import Book
from lit_club_app.backend.books.repository import BookRepository
from lit_club_app.backend.books.schemas import BookWithReviewsRead, BookRead, BooksRead, CanDeleteBookRead
from lit_club_app.backend.common.enums import Roles, UploadedFileTypes
from lit_club_app.backend.core.config import settings
from lit_club_app.backend.core.exceptions import BookNotFoundError, EmptyDescriptionError, BookAlreadyExistsError, \
    NotYourBookError, UserNotFoundError, CantDeleteNominatedBookError, BookFileNotFoundError
from lit_club_app.backend.files.constants import ALLOWED_BOOK_COVER_CONTENT_TYPES, ALLOWED_BOOK_COVER_EXTENSIONS, \
    ALLOWED_BOOK_FILE_CONTENT_TYPES, ALLOWED_BOOK_FILE_EXTENSIONS
from lit_club_app.backend.files.models import UploadedFile
from lit_club_app.backend.files.repository import FileRepository
from lit_club_app.backend.files.schemas import BookFileRead
from lit_club_app.backend.files.service import file_service
from lit_club_app.backend.reviews.models import Review
from lit_club_app.backend.reviews.repository import ReviewRepository
from lit_club_app.backend.reviews.service import review_service
from lit_club_app.backend.selections.repository import NominationRepository
from lit_club_app.backend.users.models import User
from lit_club_app.backend.users.repository import UserRepository


class BookService:
    def __init__(self):
        self.book_repo = BookRepository()
        self.review_repo = ReviewRepository()
        self.user_repo = UserRepository()
        self.nomination_repo = NominationRepository()
        self.file_repo = FileRepository()

    def can_user_delete_book(self, db: Session, book: Book, user: User) -> bool:
        nominated_book_ids = set(self.nomination_repo.get_all_nominated_books(db=db))
        is_nominated = book.id in nominated_book_ids

        has_delete_rights = (
                book.user_id is None
                or book.user_id == user.id
                or user.role == Roles.ADMIN
                or user.role == Roles.MODERATOR
        )

        return has_delete_rights and not is_nominated

    def create_book(self, db: Session, title: str, author: str, description: str | None, user_id: int) -> Book:
        book = self.book_repo.get_by_norm_title_and_author(db=db, norm_title=title.strip().lower(), norm_author=author.strip().lower())
        if book is not None:
            raise BookAlreadyExistsError()
        return self.book_repo.create_book(db=db, title=title, author=author, description=description, user_id=user_id)

    def get_book(self, db: Session, book_id: int) -> Book:
        book = self.book_repo.get_by_id(db=db, book_id=book_id)
        if book is None:
            raise BookNotFoundError()
        return book

    def get_all_books(self, db: Session) -> Sequence[Book]:
        return self.book_repo.get_all_books(db=db)

    def update_book_fields(self, db: Session, title: str, author: str, book_id: int, user: User) -> Book:
        book = self.book_repo.get_by_id(db=db, book_id=book_id)
        if book is None:
            raise BookNotFoundError()
        if book.user_id is not None and book.user_id != user.id and user.role != Roles.ADMIN and user.role != Roles.MODERATOR:
            raise NotYourBookError()
        book = self.book_repo.update_book_fields(db=db, title=title, author=author, book_id=book_id)
        return book

    def delete_book(self, db: Session, book_id: int, user: User) -> None:
        book = self.book_repo.get_by_id(db=db, book_id=book_id)
        nominations = set(self.nomination_repo.get_all_nominated_books(db=db))
        if book.id in nominations:
            raise CantDeleteNominatedBookError()
        if book is None:
            raise BookNotFoundError()
        if self.can_user_delete_book(db=db, book=book,user=user):
            return self.book_repo.delete_book(db=db, book_id=book_id)
        else:
            raise NotYourBookError()

    def assign_user_to_book(self, db: Session, book_id: int, user_id: int) -> Book:
        user = self.user_repo.get_by_id(db=db, user_id=user_id)
        if user is None:
            raise UserNotFoundError()
        book = self.book_repo.assign_user_to_book(db=db, book_id=book_id, user=user)
        return book

    def add_description_to_book(self, db: Session, book_id: int, description: str, user: User) -> Book:
        book = self.book_repo.get_by_id(db=db, book_id=book_id)
        if book is None:
            raise BookNotFoundError()
        if book.user_id is not None and book.user_id != user.id and user.role != Roles.ADMIN and user.role != Roles.MODERATOR:
            raise NotYourBookError()
        if not description.strip():
            raise EmptyDescriptionError()
        return self.book_repo.add_description(db=db, book=book, description=description)

    def get_finished_books(self, db: Session) -> Sequence[Book]:
        return self.book_repo.get_finished_books_unique(db=db)

    def get_finished_books_with_reviews(self, db: Session) -> list[BookWithReviewsRead]:
        finished_books = self.book_repo.get_finished_books_unique(db=db)
        book_ids = [book.id for book in finished_books]

        reviews = review_service.get_reviews_for_books(db=db, book_ids=book_ids)

        reviews_by_book_id: dict[int, list[Review]] = defaultdict(list)
        for review in reviews:
            reviews_by_book_id[review.book_id].append(review)

        results = []
        for book in finished_books:
            book_reviews = reviews_by_book_id.get(book.id, [])
            review_reads = review_service.to_reviews_read(db=db, reviews=book_reviews)

            result = {
                "book": self.to_book_read(db=db, book=book),
                "reviews": review_reads,
            }
            results.append(BookWithReviewsRead.model_validate(result))

        return results

    def to_books_read(self, db: Session, books: Sequence[Book], user: User) -> BooksRead:
        return BooksRead.model_validate(
            {
                "books": [CanDeleteBookRead.model_validate({
                    "book": self.to_book_read(db=db, book=book),
                    "can_delete": self.can_user_delete_book(db=db, book=book, user=user)
                }) for book in books]
            }
        )

    def to_book_read(self, db: Session, book: Book) -> BookRead:

        cover_url = None
        book_file_read = None

        if book.cover_file_id is not None:
            cover_file = self.file_repo.get_by_id(db=db, file_id=book.cover_file_id)
            if cover_file is not None:
                cover_url = f"{settings.public_uploads_url}/books/covers/{book.id}/{cover_file.stored_filename}"

        if book.book_file_id is not None:
            book_file = self.file_repo.get_by_id(db=db, file_id=book.book_file_id)
            if book_file is not None:
                book_file_read = BookFileRead(
                    id=book_file.id,
                    original_filename=book_file.original_filename,
                    content_type=book_file.content_type,
                    size_bytes=book_file.size_bytes,
                    download_url= f"/books/{book.id}/file/download"
                )

        return BookRead.model_validate(
            {
                "id": book.id,
                "title": book.title,
                "author": book.author,
                "description": book.description,
                "user_id": book.user_id,

                "cover_url": cover_url,
                "book_file": book_file_read
            }
        )

    async def upload_book_cover(self, db: Session, book_id: int, file: UploadFile, current_user: User) -> BookRead:

        book = self.book_repo.get_by_id(db=db, book_id=book_id)
        if book is None:
            raise BookNotFoundError()

        if current_user.role != Roles.ADMIN and current_user.role != Roles.MODERATOR and book.user_id is not None and book.user_id != current_user.id:
            raise NotYourBookError()

        old_cover_file = None

        if book.cover_file_id is not None:
            old_cover_file = self.file_repo.get_by_id(db=db, file_id=book.cover_file_id)

        old_cover_path = old_cover_file.storage_path if old_cover_file is not None else None

        new_file_path: str | None = None

        try:
            saved_file = await file_service.save_uploaded_file(
                file=file,
                relative_dir=f"books/covers/{book.id}",
                allowed_content_types=ALLOWED_BOOK_COVER_CONTENT_TYPES,
                allowed_extensions=ALLOWED_BOOK_COVER_EXTENSIONS,
                max_size_bytes=settings.max_cover_size_bytes
            )

            new_file_path = saved_file.storage_path

            uploaded_file = self.file_repo.create_file_record(
                db=db,
                original_filename=saved_file.original_filename,
                stored_filename=saved_file.stored_filename,
                storage_path=saved_file.storage_path,
                content_type=saved_file.content_type,
                size_bytes=saved_file.size_bytes,
                file_kind=UploadedFileTypes.BOOK_COVER
            )

            self.book_repo.set_book_cover(db=db, book=book, uploaded_file=uploaded_file)

            if old_cover_file is not None:
                self.file_repo.delete_file_record(db=db, uploaded_file=old_cover_file)
            db.commit()
        except Exception:
            db.rollback()
            if new_file_path is not None:
                file_service.delete_file_safely(new_file_path)

            raise

        if old_cover_path is not None:
            file_service.delete_file_safely(old_cover_path)

        return self.to_book_read(db=db, book=book)

    def delete_book_cover(self, db: Session, book_id: int, current_user: User) -> BookRead:
        book = self.book_repo.get_by_id(db=db, book_id=book_id)

        if book is None:
            raise BookNotFoundError()

        if (current_user.role != Roles.ADMIN and current_user.role != Roles.MODERATOR and book.user_id is not None and book.user_id != current_user.id
        ):
            raise NotYourBookError()

        if book.cover_file_id is None:
            return self.to_book_read(db=db, book=book)

        old_cover_file = self.file_repo.get_by_id(db=db, file_id=book.cover_file_id)

        if old_cover_file is None:
            self.book_repo.set_book_cover(db=db, book=book, uploaded_file=None)
            db.commit()

            return self.to_book_read(db=db, book=book)

        old_cover_path = old_cover_file.storage_path

        try:
            self.book_repo.set_book_cover(db=db, book=book, uploaded_file=None)
            self.file_repo.delete_file_record(db=db, uploaded_file=old_cover_file)
            db.commit()
        except Exception:
            db.rollback()
            raise

        file_service.delete_file_safely(old_cover_path)

        return self.to_book_read(db=db, book=book)

    async def upload_book_file(self, db: Session, book_id: int, file: UploadFile, current_user: User) -> BookRead:

        book = self.book_repo.get_by_id(db=db, book_id=book_id)
        if book is None:
            raise BookNotFoundError()

        if current_user.role != Roles.ADMIN and current_user.role != Roles.MODERATOR and book.user_id is not None and book.user_id != current_user.id:
            raise NotYourBookError()

        old_book_file = None

        if book.book_file_id is not None:
            old_book_file = self.file_repo.get_by_id(db=db, file_id=book.book_file_id)

        old_book_file_path = old_book_file.storage_path if old_book_file is not None else None

        new_file_path: str | None = None

        try:
            saved_file = await file_service.save_uploaded_file(
                file=file,
                relative_dir=f"books/files/{book.id}",
                allowed_content_types=ALLOWED_BOOK_FILE_CONTENT_TYPES,
                allowed_extensions=ALLOWED_BOOK_FILE_EXTENSIONS,
                max_size_bytes=settings.max_book_file_size_bytes,
            )

            new_file_path = saved_file.storage_path

            uploaded_file = self.file_repo.create_file_record(
                db=db,
                original_filename=saved_file.original_filename,
                stored_filename=saved_file.stored_filename,
                storage_path=saved_file.storage_path,
                content_type=saved_file.content_type,
                size_bytes=saved_file.size_bytes,
                file_kind=UploadedFileTypes.BOOK_FILE,
            )
            self.book_repo.set_book_file(db=db, book=book, uploaded_file=uploaded_file)
            if old_book_file is not None:
                self.file_repo.delete_file_record(db=db, uploaded_file=old_book_file)
            db.commit()

        except Exception:
            db.rollback()
            if new_file_path is not None:
                file_service.delete_file_safely(new_file_path)
            raise

        if old_book_file_path is not None:
            file_service.delete_file_safely(old_book_file_path)

        return self.to_book_read(db=db, book=book)

    def delete_book_file(self, db: Session, book_id: int, current_user: User) -> BookRead:
        book = self.book_repo.get_by_id(db=db, book_id=book_id)
        if book is None:
            raise BookNotFoundError()
        if (current_user.role != Roles.ADMIN and current_user.role != Roles.MODERATOR and book.user_id is not None and book.user_id != current_user.id):
            raise NotYourBookError()
        if book.book_file_id is None:
            return self.to_book_read(db=db, book=book)
        old_book_file = self.file_repo.get_by_id(db=db, file_id=book.book_file_id)
        if old_book_file is None:
            self.book_repo.set_book_file(db=db, book=book, uploaded_file=None)
            db.commit()
            return self.to_book_read(db=db, book=book)
        old_book_file_path = old_book_file.storage_path
        try:
            self.book_repo.set_book_file(db=db, book=book, uploaded_file=None)
            self.file_repo.delete_file_record(db=db, uploaded_file=old_book_file)
            db.commit()
        except Exception:
            db.rollback()
            raise
        file_service.delete_file_safely(old_book_file_path)
        return self.to_book_read(db=db, book=book)

    def get_book_file_for_download(self, db: Session, book_id: int) -> UploadedFile:
        book = self.book_repo.get_by_id(db=db, book_id=book_id)
        if book is None:
            raise BookNotFoundError()
        if book.book_file_id is None:
            raise BookFileNotFoundError()
        book_file = self.file_repo.get_by_id(db=db, file_id=book.book_file_id)
        if book_file is None:
            raise BookFileNotFoundError()
        if book_file.file_kind != UploadedFileTypes.BOOK_FILE:
            raise BookFileNotFoundError()

        file_path = Path(book_file.storage_path)
        if not file_path.exists() or not file_path.is_file():
            raise BookFileNotFoundError()
        return book_file

book_service = BookService()
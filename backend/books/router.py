from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from lit_club_app.backend.api.dependencies import get_db, get_current_user
from lit_club_app.backend.books.schemas import BooksRead, BookRead, BookChangeDescription, BookCreate, \
    BookWithReviewsRead, BookAssignUser, CanDeleteBookRead
from lit_club_app.backend.books.service import book_service
from lit_club_app.backend.common.enums import Roles
from lit_club_app.backend.core.exceptions import BookNotFoundError, EmptyDescriptionError, BookAlreadyExistsError, \
    NotYourBookError, UserNotFoundError, AlreadyAssignedError, CantDeleteNominatedBookError
from lit_club_app.backend.reviews.schemas import ReviewRead
from lit_club_app.backend.reviews.service import review_service
from lit_club_app.backend.users.models import User

router = APIRouter(prefix="/books", tags=["books"])

@router.get("/", response_model=BooksRead)
def get_books(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        books = book_service.get_all_books(db=db)
        return book_service.to_books_read(db=db, books=books, user=user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.get("/finished", response_model=BooksRead)
def get_finished_books(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        books = book_service.get_finished_books(db=db)
        return book_service.to_books_read(db=db, books=books, user=user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.get("/finished-with-reviews", response_model=list[BookWithReviewsRead], dependencies=[Depends(get_current_user)])
def get_finished_with_reviews(db: Session = Depends(get_db)):
    try:
        return book_service.get_finished_books_with_reviews(db=db)
    except BookNotFoundError:
        raise HTTPException(status_code=404, detail="Book not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.patch("/{book_id}/description", response_model=BookRead)
def change_description(book_id: int, payload: BookChangeDescription, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return book_service.add_description_to_book(db=db, book_id=book_id, description=payload.description, user=user)
    except BookNotFoundError:
        raise HTTPException(status_code=404, detail="Book not found")
    except EmptyDescriptionError:
        raise HTTPException(status_code=400, detail="Description cannot be empty")
    except NotYourBookError:
        raise HTTPException(status_code=403, detail="You can't do that")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.post("/", response_model=BookRead)
def create_book(payload: BookCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return book_service.create_book(db=db, title=payload.title, author=payload.author, description=payload.description, user_id = user.id)
    except BookAlreadyExistsError:
        raise HTTPException(status_code=409, detail="Book already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.get("/{book_id}", response_model=BookRead, dependencies=[Depends(get_current_user)])
def get_book(book_id: int, db: Session = Depends(get_db)):
    try:
        book = book_service.get_book(db=db, book_id=book_id)
        return book
    except BookNotFoundError:
        raise HTTPException(status_code=404, detail="Book not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.get("/{book_id}/reviews", response_model=list[ReviewRead], dependencies=[Depends(get_current_user)])
def get_book_reviews(book_id: int, db: Session = Depends(get_db)):
    try:
        reviews = review_service.get_reviews_for_book(db=db, book_id=book_id)
        return review_service.to_reviews_read(db=db, reviews=reviews)
    except BookNotFoundError:
        raise HTTPException(status_code=404, detail="Book not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.patch("/{book_id}", response_model=BookRead)
def update_book_fields(book_id: int, title: str, author: str,db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return book_service.update_book_fields(db=db, title=title, author=author, book_id=book_id, user = user)
    except BookNotFoundError:
        raise HTTPException(status_code=404, detail="Book not found")
    except NotYourBookError:
        raise HTTPException(status_code=403, detail="You can't do that")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.delete("/{book_id}", status_code=204)
def delete_book(book_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        book_service.delete_book(db=db, book_id=book_id, user=user)
    except BookNotFoundError:
        raise HTTPException(status_code=404, detail="Book not found")
    except NotYourBookError:
        raise HTTPException(status_code=403, detail="You don't have the rights to do that")
    except CantDeleteNominatedBookError:
        raise HTTPException(status_code=403, detail="Can't delete a book that has been nominated for a meeting")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.patch("/{book_id}/user", response_model=BookRead)
def assign(book_id: int, payload: BookAssignUser, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != Roles.ADMIN:
        raise HTTPException(status_code=403, detail="You don't have the rights to do that")
    try:
        return book_service.assign_user_to_book(db=db, book_id=book_id, user_id=payload.user_id)
    except BookNotFoundError:
        raise HTTPException(status_code=404, detail="Book not found")
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="No such user found")
    except AlreadyAssignedError:
        raise HTTPException(status_code=409, detail="Book already has an owner")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")
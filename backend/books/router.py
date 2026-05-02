from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from lit_club_app.backend.api.dependencies import get_db, get_current_user
from lit_club_app.backend.books.schemas import BooksRead, BookRead, BookChangeDescription, BookCreate, BookWithReviewsRead
from lit_club_app.backend.books.service import book_service
from lit_club_app.backend.core.exceptions import BookNotFoundError, EmptyDescriptionError, BookAlreadyExistsError
from lit_club_app.backend.reviews.schemas import ReviewRead
from lit_club_app.backend.reviews.service import review_service

router = APIRouter(prefix="/books", tags=["books"])

@router.get("/", response_model=BooksRead, dependencies=[Depends(get_current_user)])
def get_books(db: Session = Depends(get_db)):
    try:
        books = book_service.get_all_books(db=db)
        return book_service.to_books_read(db=db, books=books)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.get("/finished", response_model=BooksRead, dependencies=[Depends(get_current_user)])
def get_finished_books(db: Session = Depends(get_db)):
    try:
        books = book_service.get_finished_books(db=db)
        return book_service.to_books_read(db=db, books=books)
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

@router.patch("/{book_id}/description", response_model=BookRead, dependencies=[Depends(get_current_user)])
def change_description(book_id: int, payload: BookChangeDescription, db: Session = Depends(get_db)):
    try:
        return book_service.add_description_to_book(db=db, book_id=book_id,description=payload.description)
    except BookNotFoundError:
        raise HTTPException(status_code=404, detail="Book not found")
    except EmptyDescriptionError:
        raise HTTPException(status_code=400, detail="Description cannot be empty")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.post("/", response_model=BookRead, dependencies=[Depends(get_current_user)])
def create_book(payload: BookCreate, db: Session = Depends(get_db)):
    try:
        return book_service.create_book(db=db, title=payload.title, author=payload.author, description=payload.description)
    except BookAlreadyExistsError:
        raise HTTPException(status_code=409, detail="Book already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.get("/{book_id}", response_model=BookRead, dependencies=[Depends(get_current_user)])
def get_book(book_id: int, db: Session = Depends(get_db)):
    try:
        return book_service.get_book(db=db, book_id=book_id)
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
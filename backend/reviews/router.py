from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from lit_club_app.backend.api.dependencies import get_db, get_current_user
from lit_club_app.backend.core.exceptions import BookNotFoundError
from lit_club_app.backend.reviews.schemas import ReviewRead, ReviewCreate
from lit_club_app.backend.reviews.service import review_service
from lit_club_app.backend.users.models import User

router = APIRouter(prefix="/reviews", tags=["reviews"])

@router.post("/", response_model=ReviewRead)
def create_review(payload: ReviewCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        review = review_service.create_or_update_review(db=db, user_id=current_user.id, book_id=payload.book_id, rating=payload.rating, anonymous=payload.anonymous, review_text=payload.review_text)
        return review_service.to_review_read(db=db, review=review)
    except BookNotFoundError:
        raise HTTPException(status_code=404, detail="Book not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.get("/book/{book_id}", response_model=ReviewRead)
def get_review(book_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        review = review_service.get_book_review_for_user(db=db, book_id=book_id, user_id=current_user.id)
        if review is None:
            raise HTTPException(status_code=404, detail="Review not found")
        return review_service.to_review_read(db=db, review=review)
    except BookNotFoundError:
        raise HTTPException(status_code=404, detail="Book not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")
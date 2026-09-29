from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from lit_club_app.backend.api.dependencies import get_current_user, get_db
from lit_club_app.backend.core.exceptions import BookNotFoundError
from lit_club_app.backend.quotes.schemas import QuoteCreate, QuoteRead, QuoteUpdate, RandomQuoteRead
from lit_club_app.backend.quotes.service import quote_service
from lit_club_app.backend.users.models import User

router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.get("/book/{book_id}", response_model=list[QuoteRead])
def get_book_quotes(book_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return quote_service.get_for_book(db, book_id)
    except BookNotFoundError:
        raise HTTPException(status_code=404, detail="Book not found")


@router.get("/random", response_model=RandomQuoteRead)
def get_random_quote(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    quote = quote_service.get_random(db)
    if quote is None:
        raise HTTPException(status_code=404, detail="Цитат пока нет")
    return quote


@router.post("/", response_model=QuoteRead, status_code=201)
def create_quote(payload: QuoteCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return quote_service.create(db, payload.book_id, user.id, payload.text)
    except BookNotFoundError:
        raise HTTPException(status_code=404, detail="Book not found")


@router.patch("/{quote_id}", response_model=QuoteRead)
def update_quote(quote_id: int, payload: QuoteUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        quote = quote_service.update(db, quote_id, user, payload.text)
        if quote is None:
            raise HTTPException(status_code=404, detail="Quote not found")
        return quote
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not allowed to edit this quote")


@router.delete("/{quote_id}", status_code=204)
def delete_quote(quote_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        deleted = quote_service.delete(db, quote_id, user)
        if deleted is None:
            raise HTTPException(status_code=404, detail="Quote not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not allowed to delete this quote")

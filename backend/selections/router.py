from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from lit_club_app.backend.api.dependencies import get_db, get_current_user
from lit_club_app.backend.users.models import User
from lit_club_app.backend.common.enums import Roles
from lit_club_app.backend.selections.schemas import (
    BookSelectionCreate,
    BookSelectionRead,
    NominationCreate,
    NominationUpdate,
    NominationRead,
    VoteCreate,
    VoteCountRead,
    WinnerSelectionStateRead,
    WinnerSelectRead, NominationCommentUpdate, CurrentSelectionRead, CurrentUserVotesRead, NominationBookUpdate
)
from lit_club_app.backend.selections.service import selection_service
from lit_club_app.backend.core.exceptions import (
    MeetingNotFoundError,
    BookSelectionNotFoundError,
    BookSelectionExistsError,
    NominationsNotOpenError,
    NoNominationsError,
    NoVotesError,
    IncorrectVotingStatus,
    NominationNotFoundError,
    UserAlreadyNominatedError,
    VotingNotOpenError,
    WrongNominationError,
    NoNominationVotesError,
    SessionNotFoundError,
    IncorrectSessionStatusError,
    NoEligibleNominationsError,
    SessionNotReadyToFinalizeError,
    NoWinnerFinalizeError,
    BookNotFoundError,
)

router = APIRouter(prefix="/selections", tags=["selections"])

@router.post("/", response_model=BookSelectionRead, status_code=201)
def create_selection(payload: BookSelectionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != Roles.MODERATOR:
        raise HTTPException(status_code=403, detail="Moderator access required")
    try:
        book_selection = selection_service.create_selection(db=db, meeting_id=payload.meeting_id)
        return book_selection
    except MeetingNotFoundError:
        raise HTTPException(status_code=404, detail="Meeting not found")
    except BookSelectionExistsError:
        raise HTTPException(status_code=409, detail="This selection already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.get("/current", response_model=CurrentSelectionRead, dependencies=[Depends(get_current_user)])
def get_current_selection(db: Session = Depends(get_db)):
    try:
        return selection_service.get_current_selection(db=db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.post("/{selection_id}/open_voting", response_model=BookSelectionRead)
def open_voting(selection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != Roles.MODERATOR:
        raise HTTPException(status_code=403, detail="Moderator access required")
    try:
        book_selection = selection_service.open_voting(db=db, selection_id=selection_id)
        return book_selection
    except BookSelectionNotFoundError:
        raise HTTPException(status_code=404, detail="Book selection not found")
    except IncorrectVotingStatus:
        raise HTTPException(status_code=409, detail="Wrong voting status")
    except NoNominationsError:
        raise HTTPException(status_code=409, detail="Can't start an empty vote")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.post("/{selection_id}/close_voting", response_model=BookSelectionRead)
def close_voting(selection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != Roles.MODERATOR:
        raise HTTPException(status_code=403, detail="Moderator access required")
    try:
        book_selection = selection_service.close_voting(db=db, selection_id=selection_id)
        return book_selection
    except BookSelectionNotFoundError:
        raise HTTPException(status_code=404, detail="Book selection not found")
    except IncorrectVotingStatus:
        raise HTTPException(status_code=409, detail="Voting not open")
    except NoVotesError:
        raise HTTPException(status_code=409, detail="Selection has no votes")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")


@router.post("/{selection_id}/nominations", response_model=NominationRead, status_code=201)
def create_nomination(selection_id: int, payload: NominationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        nomination = selection_service.create_nomination(db=db, selection_id=selection_id, user_id=current_user.id, title=payload.title, author=payload.author, comment = payload.comment)
        return selection_service.to_nomination_read(db=db, nomination=nomination)
    except BookSelectionNotFoundError:
        raise HTTPException(status_code=404, detail="Book selection not found")
    except NominationsNotOpenError:
        raise HTTPException(status_code=409, detail="Nominations not open")
    except UserAlreadyNominatedError:
        raise HTTPException(status_code=409, detail="User already has a nomination")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.patch("/{selection_id}/nominations/me/book", response_model=NominationRead)
def update_user_nomination_book(
    selection_id: int,
    payload: NominationBookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        nomination = selection_service.update_user_nomination_book(
            db=db,
            selection_id=selection_id,
            user_id=current_user.id,
            title=payload.title,
            author=payload.author,
        )
        return selection_service.to_nomination_read(db=db, nomination=nomination)
    except BookSelectionNotFoundError:
        raise HTTPException(status_code=404, detail="Book selection not found")
    except NominationNotFoundError:
        raise HTTPException(status_code=404, detail="Nomination not found")
    except NominationsNotOpenError:
        raise HTTPException(status_code=409, detail="Nominations not open")
    except BookNotFoundError:
        raise HTTPException(status_code=404, detail="Book not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.patch("/{selection_id}/nominations/me/change-book", response_model=NominationRead)
def change_user_nomination_book(
    selection_id: int,
    payload: NominationBookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        nomination = selection_service.change_user_nomination_book(
            db=db,
            selection_id=selection_id,
            user_id=current_user.id,
            title=payload.title,
            author=payload.author,
        )
        return selection_service.to_nomination_read(db=db, nomination=nomination)
    except BookSelectionNotFoundError:
        raise HTTPException(status_code=404, detail="Book selection not found")
    except NominationNotFoundError:
        raise HTTPException(status_code=404, detail="Nomination not found")
    except NominationsNotOpenError:
        raise HTTPException(status_code=409, detail="Nominations not open")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.patch("/{selection_id}/nominations/me/comment", response_model=NominationRead)
def update_user_nomination_comment(selection_id: int, payload: NominationCommentUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        nomination = selection_service.update_user_nomination_comment(db=db, selection_id=selection_id, user_id=current_user.id, comment=payload.comment)
        return selection_service.to_nomination_read(db=db, nomination=nomination)
    except BookSelectionNotFoundError:
        raise HTTPException(status_code=404, detail="Book selection not found")
    except NominationNotFoundError:
        raise HTTPException(status_code=404, detail="Nomination not found")
    except NominationsNotOpenError:
        raise HTTPException(status_code=409, detail="Nominations not open")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")


@router.get("/{selection_id}/nominations", response_model=list[NominationRead], dependencies=[Depends(get_current_user)])
def get_nominations_for_selection(selection_id: int, db: Session = Depends(get_db)):
    try:
        nominations = selection_service.get_nominations_for_selection(db=db, selection_id=selection_id)
        return selection_service.to_nominations_read(db=db, nominations=nominations)
    except BookSelectionNotFoundError:
        raise HTTPException(status_code=404, detail="Book selection not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.post("/{selection_id}/votes", response_model=list[VoteCountRead])
def vote_for_nominations(selection_id: int, payload: VoteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        selection_service.vote_for_nominations(db=db, selection_id=selection_id, user_id=current_user.id, nomination_ids=payload.nomination_ids)
        vote_counts = selection_service.get_vote_counts_for_selection(db=db, selection_id=selection_id)
        return [VoteCountRead(nomination_id=nomination_id, vote_count=vote_count) for nomination_id, vote_count in vote_counts]
    except BookSelectionNotFoundError:
        raise HTTPException(status_code=404, detail="Book selection not found")
    except VotingNotOpenError:
        raise HTTPException(status_code=409, detail="Voting is not open")
    except NoNominationVotesError:
        raise HTTPException(status_code=400, detail="No nominations selected for voting")
    except NominationNotFoundError:
        raise HTTPException(status_code=404, detail="Nomination not found")
    except WrongNominationError:
        raise HTTPException(status_code=400, detail="Nomination does not belong to this selection")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.get("/{selection_id}/votes", response_model=list[VoteCountRead], dependencies=[Depends(get_current_user)])
def get_vote_counts_for_selection(selection_id: int, db: Session = Depends(get_db)):
    try:
        vote_counts = selection_service.get_vote_counts_for_selection(db=db, selection_id=selection_id)
        return [VoteCountRead(nomination_id=nomination_id, vote_count=vote_count) for nomination_id, vote_count in vote_counts]
    except BookSelectionNotFoundError:
        raise HTTPException(status_code=404, detail="Book selection not found")
    except VotingNotOpenError:
        raise HTTPException(status_code=409, detail="Voting has not started yet")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.get("/{selection_id}/votes/me", response_model=CurrentUserVotesRead)
def get_current_user_votes_for_selection(
    selection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return selection_service.get_current_user_vote_ids_for_selection(
            db=db,
            selection_id=selection_id,
            user_id=current_user.id,
        )
    except BookSelectionNotFoundError:
        raise HTTPException(status_code=404, detail="Book selection not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")


@router.post("/{selection_id}/winner-selection/start", response_model=WinnerSelectionStateRead)
def start_winner_selection(selection_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != Roles.MODERATOR:
        raise HTTPException(status_code=403, detail="Moderator access required")

    try:
        return selection_service.start_winner_selection(db=db, selection_id=selection_id)
    except BookSelectionNotFoundError:
        raise HTTPException(status_code=404, detail="Book selection not found")
    except IncorrectVotingStatus:
        raise HTTPException(status_code=409, detail="Winner selection can start only after voting is closed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.post("/winner-selection/{session_id}/advance", response_model=WinnerSelectionStateRead)
def advance_winner_selection_step(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != Roles.MODERATOR:
        raise HTTPException(status_code=403, detail="Moderator access required")

    try:
        return selection_service.advance_winner_selection_step(db=db, session_id=session_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Winner selection session not found")
    except IncorrectSessionStatusError:
        raise HTTPException(status_code=409, detail="Winner selection session is not in progress")
    except BookSelectionNotFoundError:
        raise HTTPException(status_code=404, detail="Book selection not found")
    except NoNominationsError:
        raise HTTPException(status_code=409, detail="No nominations found for this selection")
    except NoEligibleNominationsError:
        raise HTTPException(status_code=409, detail="No eligible nominations left for this step")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.get("/winner-selection/{session_id}", response_model=WinnerSelectionStateRead, dependencies=[Depends(get_current_user)],)
def get_winner_selection_state(session_id: int, db: Session = Depends(get_db)):
    try:
        return selection_service.get_winner_selection_state(db=db, session_id=session_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Winner selection session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.post("/winner-selection/{session_id}/finalize", response_model=WinnerSelectRead)
def finalize_winner_selection(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != Roles.MODERATOR:
        raise HTTPException(status_code=403, detail="Moderator access required")
    try:
        return selection_service.finalize_winner_selection(db=db, session_id=session_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="Winner selection session not found")
    except SessionNotReadyToFinalizeError:
        raise HTTPException(status_code=409, detail="Winner selection session is not ready to finalize")
    except NoWinnerFinalizeError:
        raise HTTPException(status_code=409, detail="Winner has not been determined yet")
    except NominationNotFoundError:
        raise HTTPException(status_code=404, detail="Winning nomination not found")
    except BookSelectionNotFoundError:
        raise HTTPException(status_code=404, detail="Book selection not found")
    except MeetingNotFoundError:
        raise HTTPException(status_code=404, detail="Meeting not found")
    except BookNotFoundError:
        raise HTTPException(status_code=404, detail="Book not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")
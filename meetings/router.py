from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from lit_club_app.api.dependencies import get_db, get_current_user
from lit_club_app.users.models import User
from lit_club_app.common.enums import Roles
from lit_club_app.meetings.schemas import (
    MeetingCreate,
    MeetingRead,
    MeetingScheduleUpdate,
    MeetingWithSelectionRead,
)
from lit_club_app.meetings.service import meeting_service
from lit_club_app.core.exceptions import (
    MeetingNotFoundError,
    LatestMeetingNotFinishedError,
    ScheduleInThePastError,
    CantFinishMeetingError,
    LatestMeetingNotStartedError,
)

router = APIRouter(prefix="/meetings", tags=["meetings"])

@router.post("/", response_model=MeetingRead, status_code=201)
def create_meeting(payload: MeetingCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != Roles.MODERATOR:
        raise HTTPException(status_code=403, detail="Moderator access required")
    try:
        meeting = meeting_service.create_meeting(db=db, status=payload.status, book_id=payload.book_id, scheduled_for=payload.scheduled_for)
        return meeting
    except LatestMeetingNotFinishedError:
        raise HTTPException(status_code=409, detail="Last meeting is not finished")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.get("/", response_model=list[MeetingRead], dependencies=[Depends(get_current_user)])
def get_all_meetings(db: Session = Depends(get_db)):
    try:
        meetings = meeting_service.get_all_meetings(db=db)
        return meetings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.get("/latest", response_model=MeetingRead, dependencies=[Depends(get_current_user)])
def get_latest_meeting(db: Session = Depends(get_db)):
    try:
        meeting = meeting_service.get_latest_meeting(db=db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    return meeting

@router.post("/start-next", response_model=MeetingWithSelectionRead)
def start_next(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != Roles.MODERATOR:
        raise HTTPException(status_code=403, detail="Moderator access required")
    try:
        return meeting_service.start_next(db=db)
    except LatestMeetingNotStartedError:
        raise HTTPException(status_code=409, detail="Can't start next before last one is scheduled")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.get("/year/{year}", response_model=list[MeetingRead], dependencies=[Depends(get_current_user)])
def get_meetings_by_year(year: int, db: Session = Depends(get_db)):
    return meeting_service.get_meetings_by_year(db=db, year=year)

@router.get("/{meeting_id}", response_model=MeetingRead, dependencies=[Depends(get_current_user)])
def get_meeting_by_id(meeting_id: int, db: Session = Depends(get_db)):
    try:
        return meeting_service.get_meeting_by_id(db=db, meeting_id=meeting_id)
    except MeetingNotFoundError:
        raise HTTPException(status_code=404, detail="Meeting not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.patch("/{meeting_id}/schedule", response_model=MeetingRead)
def schedule_meeting(meeting_id: int, payload: MeetingScheduleUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != Roles.MODERATOR:
        raise HTTPException(status_code=403, detail="Moderator access required")
    try:
        return meeting_service.schedule_meeting(db=db, meeting_id=meeting_id, scheduled_for=payload.scheduled_for)
    except MeetingNotFoundError:
        raise HTTPException(status_code=404, detail="Meeting not found")
    except ScheduleInThePastError:
        raise HTTPException(status_code=400, detail="Can't schedule before current date")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")

@router.post("/{meeting_id}/finish", response_model=MeetingRead)
def finish_meeting(meeting_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != Roles.MODERATOR:
        raise HTTPException(status_code=403, detail="Moderator access required")
    try:
        return meeting_service.finish_meeting(db=db, meeting_id=meeting_id)
    except MeetingNotFoundError:
        raise HTTPException(status_code=404, detail="Meeting not found")
    except CantFinishMeetingError:
        raise HTTPException(status_code=409, detail="Wrong meeting status")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unknown error: {e}")


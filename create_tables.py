from lit_club_app.db.base import Base
from lit_club_app.db.session import engine
from lit_club_app.users.models import User
from lit_club_app.books.models import Book
from lit_club_app.meetings.models import Meeting
from lit_club_app.selections.models import BookSelection, Vote, Nomination

Base.metadata.create_all(bind=engine)
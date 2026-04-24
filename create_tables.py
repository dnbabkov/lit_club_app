from lit_club_app.db.base import Base
from lit_club_app.db.session import engine
from lit_club_app.users.models import User

Base.metadata.create_all(bind=engine)
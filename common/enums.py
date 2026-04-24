import enum

class Roles(enum.Enum):
    MEMBER = "member"
    MODERATOR = "moderator"

class MeetingStatus(enum.Enum):
    BOOK_SELECTION = "book_selection"
    SCHEDULED = "scheduled"
    FINISHED = "finished"

class BookSelectionStatus(enum.Enum):
    NOMINATIONS_OPEN = "nominations_open"
    VOTING_OPEN = "voting_open"
    VOTING_CLOSED = "voting_closed"
    WINNER_SELECTED = "winner_selected"
class AppError(Exception):
    pass


class UserServiceError(AppError):
    pass

class UsernameAlreadyExistsError(UserServiceError):
    pass

class TelegramLoginAlreadyExistsError(UserServiceError):
    pass

class UserNotFoundError(UserServiceError):
    pass

class InvalidPasswordError(UserServiceError):
    pass

class EmptyTelegramLoginError(UserServiceError):
    pass


class MeetingError(AppError):
    pass

class MeetingNotFoundError(MeetingError):
    pass

class LatestMeetingNotFinishedError(MeetingError):
    pass

class MeetingAlreadyScheduledError(MeetingError):
    pass

class ScheduleInThePastError(MeetingError):
    pass

class CantFinishMeetingError(MeetingError):
    pass

class LatestMeetingNotStartedError(MeetingError):
    pass

class SelectionError(AppError):
    """Base class for book selection process errors."""
    pass

class BookSelectionNotFoundError(SelectionError):
    pass

class NominationsNotOpenError(SelectionError):
    """Raised when someone tries to nominate while nominations are closed."""
    pass

class VotingNotOpenError(SelectionError):
    """Raised when someone tries to vote while voting is not open."""
    pass

class VotingAlreadyClosedError(SelectionError):
    """Raised when an action requires open voting, but voting is already closed."""
    pass

class WinnerAlreadySelectedError(SelectionError):
    """Raised when winner has already been fixed for this selection."""
    pass

class WinnerSelectionNotAllowedError(SelectionError):
    """Base class for winner selection restrictions."""
    pass

class WinnerCannotBeSelectedBeforeVotingClosedError(WinnerSelectionNotAllowedError):
    pass

class NoNominationsError(WinnerSelectionNotAllowedError):
    pass

class NoVotesError(WinnerSelectionNotAllowedError):
    pass


class NominationError(SelectionError):
    """Base class for nomination-related errors."""
    pass

class NominationNotFoundError(NominationError):
    pass

class UserAlreadyNominatedError(NominationError):
    """Raised when user tries to create a second nomination in the same selection."""
    pass

class NominationUpdateForbiddenError(NominationError):
    """Raised when user tries to change nomination after voting has started."""
    pass


class VoteError(SelectionError):
    """Base class for voting-related errors."""
    pass

class DuplicateVoteError(VoteError):
    """Raised when user tries to vote twice for the same nomination."""
    pass

class BookSelectionExistsError(SelectionError):
    pass

class IncorrectVotingStatus(VoteError):
    pass

class WrongNominationError(NominationError):
    pass

class NoNominationVotesError(VoteError):
    pass

class WinnerSelectionError(AppError):
    pass

class SessionNotFoundError(WinnerSelectionError):
    pass

class IncorrectSessionStatusError(WinnerSelectionError):
    pass

class NoEligibleNominationsError(WinnerSelectionError):
    pass

class SessionNotReadyToFinalizeError(WinnerSelectionError):
    pass

class NoWinnerFinalizeError(WinnerSelectionError):
    pass

class BookError(AppError):
    pass

class BookNotFoundError(BookError):
    pass

class EmptyDescriptionError(BookError):
    pass

class BookAlreadyExistsError(BookError):
    pass

class NotYourBookError(BookError):
    pass

class AlreadyAssignedError(BookError):
    pass

class CantDeleteNominatedBookError(BookError):
    pass
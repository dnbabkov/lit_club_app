class UserServiceError(Exception):
    pass

class UsernameAlreadyExistsError(UserServiceError):
    pass

class TelegramLoginAlreadyExistsError(UserServiceError):
    pass

class UserNotFoundError(UserServiceError):
    pass

class InvalidPasswordError(UserServiceError):
    pass
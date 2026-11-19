from src.domain.shared.exceptions import DomainError


class UserAlreadyExistsError(DomainError):
    def __init__(self, email: str) -> None:
        super().__init__(f"User with email {email} already exists.")


class UserNotFoundError(DomainError):
    def __init__(self, user_id: str) -> None:
        super().__init__(f"User {user_id} not found.")


class InvalidEmailError(DomainError):
    def __init__(self, email: str) -> None:
        super().__init__(f"Invalid email format: {email}")

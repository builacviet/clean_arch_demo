from src.domain.shared.exceptions import DomainError


class InvalidEmailError(DomainError):
    def __init__(self, email: str) -> None:
        super().__init__(f"Invalid email format: '{email}'.")


class UserAlreadyExistsError(DomainError):
    def __init__(self, email: str) -> None:
        super().__init__(f"User with email '{email}' already exists.")


class UserNotFoundError(DomainError):
    def __init__(self, user_id: str) -> None:
        super().__init__(f"User with ID '{user_id}' was not found.")


class UserCannotPlaceOrderError(DomainError):
    def __init__(self, user_id: str, reason: str) -> None:
        super().__init__(f"User '{user_id}' cannot place order: {reason}")

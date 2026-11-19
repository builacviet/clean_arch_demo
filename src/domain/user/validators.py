from src.domain.user.exceptions import InvalidEmailError

BLOCKED_DOMAINS = {"tempmail.com", "10minutemail.com"}


def validate_custom_email(email: str) -> None:
    """Hàm tự viết ném ra DomainException nếu email không hợp lệ."""
    if "@" not in email:
        raise InvalidEmailError(email)

    local, domain = email.rsplit("@", 1)
    if not local or "." not in domain:
        raise InvalidEmailError(email)

    if domain in BLOCKED_DOMAINS:
        raise InvalidEmailError(email)

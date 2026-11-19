import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.domain.user.exceptions import InvalidEmailError


@dataclass
class User:
    email: str
    hashed_password: str
    full_name: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if "@" not in self.email or "." not in self.email:
            raise InvalidEmailError(self.email)

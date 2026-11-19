import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.domain.user.exceptions import UserCannotPlaceOrderError
from src.domain.user.validators import validate_custom_email


@dataclass
class User:
    email: str
    hashed_password: str
    full_name: str
    is_active: bool = True
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        self.email = self.email.strip().lower()
        validate_custom_email(self.email)

    def ensure_can_place_order(self) -> None:
        if not self.is_active:
            raise UserCannotPlaceOrderError(str(self.id), "Account is inactive.")

import uuid
from typing import Protocol

from src.domain.user.entities import User


class IUserRepository(Protocol):
    async def get_by_id(self, user_id: uuid.UUID) -> User | None: ...
    async def get_by_email(self, email: str) -> User | None: ...
    async def save(self, user: User) -> User: ...


class ISyncUserRepository(Protocol):
    def get_recent_users(self, limit: int = 10) -> list[User]: ...


class IPasswordHasher(Protocol):
    def hash(self, plain_password: str) -> str: ...


class IExternalNotifier(Protocol):
    async def notify_user_registered(self, user: User) -> None: ...

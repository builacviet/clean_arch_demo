import uuid
from dataclasses import dataclass
from datetime import datetime

from src.application.user.ports import ISyncUserRepository


@dataclass(frozen=True)
class RecentUserItemOutput:
    user_id: uuid.UUID
    email: str
    full_name: str
    created_at: datetime


class GetRecentUsersUseCase:
    def __init__(self, user_repo: ISyncUserRepository) -> None:
        self._user_repo = user_repo

    def execute(self, limit: int = 10) -> list[RecentUserItemOutput]:
        users = self._user_repo.get_recent_users(limit=limit)
        return [
            RecentUserItemOutput(
                user_id=user.id,
                email=user.email,
                full_name=user.full_name,
                created_at=user.created_at,
            )
            for user in users
        ]

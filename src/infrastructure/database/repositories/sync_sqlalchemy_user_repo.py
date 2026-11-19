from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.domain.user.entities import User
from src.infrastructure.database.models import UserModel


class SyncSqlAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_recent_users(self, limit: int = 10) -> list[User]:
        stmt = select(UserModel).order_by(desc(UserModel.created_at)).limit(limit)
        models = self._session.scalars(stmt).all()
        return [
            User(
                id=m.id,
                email=m.email,
                hashed_password=m.hashed_password,
                full_name=m.full_name,
                created_at=m.created_at,
            )
            for m in models
        ]

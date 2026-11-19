import logging
from typing import Any

from src.application.user.use_cases.get_recent_users import GetRecentUsersUseCase
from src.infrastructure.database.repositories.sync_sqlalchemy_user_repo import (
    SyncSqlAlchemyUserRepository,
)
from src.presentation.dependencies.database import db_factory
from src.presentation.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="users.fetch_top_10_recent")
def fetch_top_10_recent_users_task() -> list[dict[str, Any]]:
    # Tận dụng Sync Session Factory đã dựng sẵn
    with db_factory.get_sync_session() as session:
        repo = SyncSqlAlchemyUserRepository(session=session)
        use_case = GetRecentUsersUseCase(user_repo=repo)
        recent_users = use_case.execute(limit=10)

    result = [
        {
            "user_id": str(u.user_id),
            "email": u.email,
            "full_name": u.full_name,
            "created_at": u.created_at.isoformat(),
        }
        for u in recent_users
    ]
    logger.info("Fetched %d recent users", len(result))
    return result

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.user.use_cases.register_user import RegisterUserUseCase
from src.infrastructure.config.app_config import get_app_config
from src.infrastructure.database.repositories.sqlalchemy_user_repo import SqlAlchemyUserRepository
from src.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from src.infrastructure.external.httpx_notifier import HttpxExternalNotifier
from src.infrastructure.security.bcrypt_hasher import SimplePasswordHasher
from src.presentation.dependencies.database import get_db_session


def get_register_user_use_case(
    session: AsyncSession = Depends(get_db_session),
) -> RegisterUserUseCase:
    config = get_app_config()
    return RegisterUserUseCase(
        uow=SqlAlchemyUnitOfWork(session=session),
        user_repo=SqlAlchemyUserRepository(session=session),
        password_hasher=SimplePasswordHasher(),
        external_notifier=HttpxExternalNotifier(webhook_url=config.WEBHOOK_URL),
    )

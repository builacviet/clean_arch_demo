from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.config.app_config import get_app_config
from src.infrastructure.database.session_factory import PostgresSessionFactory

_config = get_app_config()
db_factory = PostgresSessionFactory(config=_config)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in db_factory.get_async_session():
        yield session

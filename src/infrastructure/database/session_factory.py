from collections.abc import AsyncGenerator, Generator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from src.infrastructure.config.app_config import AppConfig


class PostgresSessionFactory:
    """Factory quản lý vòng đời Engine và Session cho cả Async (API) và Sync (Worker/CLI)."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._async_engine: AsyncEngine | None = None
        self._async_session_maker: async_sessionmaker[AsyncSession] | None = None
        self._sync_engine: Engine | None = None
        self._sync_session_maker: sessionmaker[Session] | None = None

    @property
    def async_engine(self) -> AsyncEngine:
        if self._async_engine is None:
            self._async_engine = create_async_engine(
                self._config.DATABASE_ASYNC_URL,
                pool_size=self._config.DB_POOL_SIZE,
                max_overflow=self._config.DB_MAX_OVERFLOW,
                echo=self._config.DB_ECHO,
                pool_pre_ping=True,
            )
        return self._async_engine

    @property
    def sync_engine(self) -> Engine:
        if self._sync_engine is None:
            self._sync_engine = create_engine(
                self._config.DATABASE_SYNC_URL,
                pool_size=self._config.DB_POOL_SIZE,
                max_overflow=self._config.DB_MAX_OVERFLOW,
                echo=self._config.DB_ECHO,
                pool_pre_ping=True,
            )
        return self._sync_engine

    def create_async_session_maker(self) -> async_sessionmaker[AsyncSession]:
        if self._async_session_maker is None:
            self._async_session_maker = async_sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
            )
        return self._async_session_maker

    def create_sync_session_maker(self) -> sessionmaker[Session]:
        if self._sync_session_maker is None:
            self._sync_session_maker = sessionmaker(
                bind=self.sync_engine,
                class_=Session,
                expire_on_commit=False,
                autoflush=False,
            )
        return self._sync_session_maker

    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        session_factory = self.create_async_session_maker()
        async with session_factory() as session:
            yield session

    @contextmanager
    def get_sync_session(self) -> Generator[Session, None, None]:
        session_factory = self.create_sync_session_maker()
        with session_factory() as session:
            yield session

    async def dispose_all(self) -> None:
        if self._async_engine is not None:
            await self._async_engine.dispose()
        if self._sync_engine is not None:
            self._sync_engine.dispose()

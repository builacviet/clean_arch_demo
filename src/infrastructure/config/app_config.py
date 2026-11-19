from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_ASYNC_URL: str
    DATABASE_SYNC_URL: str
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672/"
    WEBHOOK_URL: str = "https://partner.com"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False


@lru_cache
def get_app_config() -> AppConfig:
    return AppConfig()  # type: ignore[call-arg]

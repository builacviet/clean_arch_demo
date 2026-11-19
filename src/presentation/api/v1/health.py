import asyncio
import logging

import aio_pika
from fastapi import APIRouter, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.infrastructure.config.app_config import get_app_config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> dict[str, str]:
    """Kiểm tra tiến trình ứng dụng còn sống."""
    return {"status": "alive"}


async def _check_postgres(database_url: str) -> bool:
    engine = create_async_engine(database_url, pool_pre_ping=True)
    try:
        async with asyncio.timeout(2.0):
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception("PostgreSQL readiness check failed")
        return False
    finally:
        await engine.dispose()


async def _check_rabbitmq(amqp_url: str) -> bool:
    try:
        async with asyncio.timeout(2.0):
            connection = await aio_pika.connect_robust(amqp_url)
            await connection.close()
        return True
    except Exception:
        logger.exception("RabbitMQ readiness check failed")
        return False


@router.get("/ready")
async def readiness_check(response: Response) -> dict[str, object]:
    """Kiểm tra kết nối PostgreSQL và RabbitMQ."""
    config = get_app_config()

    db_ok, mq_ok = await asyncio.gather(
        _check_postgres(config.DATABASE_ASYNC_URL),
        _check_rabbitmq(config.RABBITMQ_URL),
    )

    is_ready = db_ok and mq_ok
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if is_ready else "degraded",
        "dependencies": {
            "postgresql": "up" if db_ok else "down",
            "rabbitmq": "up" if mq_ok else "down",
        },
    }

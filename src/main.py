import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.infrastructure.observability.logger import configure_logging
from src.presentation.api.middlewares.correlation import CorrelationIdMiddleware
from src.presentation.api.v1.health import router as health_router
from src.presentation.api.v1.order_router import router as order_router
from src.presentation.api.v1.user_router import router as user_router
from src.presentation.dependencies.database import db_factory

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting Clean Architecture API...")
    yield
    logger.info("Shutting down Clean Architecture API, disposing DB pools...")
    await db_factory.dispose_all()


app = FastAPI(title="Clean Architecture API", lifespan=lifespan)

app.add_middleware(CorrelationIdMiddleware)

app.include_router(health_router)
app.include_router(user_router)
app.include_router(order_router)

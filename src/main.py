from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.presentation.api.v1.order_router import router as order_router
from src.presentation.api.v1.user_router import router as user_router
from src.presentation.dependencies.database import db_factory


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: Có thể kiểm tra kết nối DB hoặc khởi tạo tài nguyên tại đây
    yield
    # Shutdown: Tự động đóng toàn bộ connection pool của PostgreSQL
    await db_factory.dispose_all()


app = FastAPI(title="Clean Architecture API", lifespan=lifespan)

app.include_router(user_router)
app.include_router(order_router)

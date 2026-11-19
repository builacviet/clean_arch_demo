from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.order.use_cases.create_order import CreateOrderUseCase
from src.infrastructure.config.app_config import get_app_config
from src.infrastructure.database.repositories.sqlalchemy_order_repo import SqlAlchemyOrderRepository
from src.infrastructure.database.repositories.sqlalchemy_user_repo import SqlAlchemyUserRepository
from src.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from src.infrastructure.messaging.rabbitmq_publisher import RabbitMQOrderPublisher
from src.presentation.dependencies.database import get_db_session


def get_create_order_use_case(
    session: AsyncSession = Depends(get_db_session),
) -> CreateOrderUseCase:
    config = get_app_config()
    return CreateOrderUseCase(
        uow=SqlAlchemyUnitOfWork(session=session),
        user_repo=SqlAlchemyUserRepository(session=session),
        order_repo=SqlAlchemyOrderRepository(session=session),
        event_publisher=RabbitMQOrderPublisher(amqp_url=config.RABBITMQ_URL),
    )

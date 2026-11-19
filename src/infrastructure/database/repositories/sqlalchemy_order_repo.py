from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.order.entities import Order
from src.infrastructure.database.models import OrderItemModel, OrderModel


class SqlAlchemyOrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, order: Order) -> Order:
        order_model = OrderModel(
            id=order.id,
            user_id=order.user_id,
            status=order.status,
            total_amount=order.total_amount,
            created_at=order.created_at,
            items=[
                OrderItemModel(
                    product_id=i.product_id,
                    quantity=i.quantity,
                    unit_price=i.unit_price,
                )
                for i in order.items
            ],
        )
        self._session.add(order_model)
        await self._session.flush()
        return order

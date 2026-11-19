from typing import Protocol

from src.domain.order.entities import Order


class IOrderRepository(Protocol):
    async def save(self, order: Order) -> Order: ...


class IOrderEventPublisher(Protocol):
    async def publish_order_created(self, order: Order) -> None: ...

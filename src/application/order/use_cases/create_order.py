import uuid
from dataclasses import dataclass
from decimal import Decimal

from src.application.order.ports import IOrderEventPublisher, IOrderRepository
from src.application.shared.unit_of_work import IUnitOfWork
from src.application.user.ports import IUserRepository
from src.domain.order.entities import Order, OrderItem
from src.domain.user.exceptions import UserNotFoundError


@dataclass(frozen=True)
class CreateOrderItemInput:
    product_id: str
    quantity: int
    unit_price: Decimal


@dataclass(frozen=True)
class CreateOrderInput:
    user_id: uuid.UUID
    items: list[CreateOrderItemInput]


@dataclass(frozen=True)
class CreateOrderOutput:
    order_id: uuid.UUID
    user_id: uuid.UUID
    total_amount: Decimal
    status: str


class CreateOrderUseCase:
    def __init__(
        self,
        uow: IUnitOfWork,
        user_repo: IUserRepository,
        order_repo: IOrderRepository,
        event_publisher: IOrderEventPublisher,
    ) -> None:
        self._uow = uow
        self._user_repo = user_repo
        self._order_repo = order_repo
        self._event_publisher = event_publisher

    async def execute(self, input_data: CreateOrderInput) -> CreateOrderOutput:
        async with self._uow:
            user = await self._user_repo.get_by_id(input_data.user_id)
            if user is None:
                raise UserNotFoundError(str(input_data.user_id))

            user.ensure_can_place_order()

            domain_items = [
                OrderItem(
                    product_id=i.product_id,
                    quantity=i.quantity,
                    unit_price=i.unit_price,
                )
                for i in input_data.items
            ]
            new_order = Order(user_id=user.id, items=domain_items)

            saved_order = await self._order_repo.save(new_order)
            await self._uow.commit()

        await self._event_publisher.publish_order_created(saved_order)

        return CreateOrderOutput(
            order_id=saved_order.id,
            user_id=saved_order.user_id,
            total_amount=saved_order.total_amount,
            status=saved_order.status,
        )

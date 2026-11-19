import unittest
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock

from src.application.order.use_cases.create_order import (
    CreateOrderInput,
    CreateOrderItemInput,
    CreateOrderUseCase,
)
from src.domain.order.exceptions import EmptyOrderError, InvalidItemQuantityError
from src.domain.user.entities import User
from src.domain.user.exceptions import UserNotFoundError


class TestCreateOrderUseCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.mock_uow = AsyncMock()
        self.mock_user_repo = AsyncMock()
        self.mock_order_repo = AsyncMock()
        self.mock_publisher = AsyncMock()

        self.use_case = CreateOrderUseCase(
            uow=self.mock_uow,
            user_repo=self.mock_user_repo,
            order_repo=self.mock_order_repo,
            event_publisher=self.mock_publisher,
        )

    async def test_create_order_success(self) -> None:
        """Tạo đơn hàng thành công: tính đúng tổng tiền, lưu DB và bắn event RabbitMQ."""
        user = User(
            email="buyer@example.com",
            hashed_password="hashed_pw",
            full_name="Buyer",
        )
        self.mock_user_repo.get_by_id.return_value = user
        self.mock_order_repo.save.side_effect = lambda order: order

        input_data = CreateOrderInput(
            user_id=user.id,
            items=[
                CreateOrderItemInput(
                    product_id="PROD-01", quantity=2, unit_price=Decimal("150.00")
                ),
                CreateOrderItemInput(product_id="PROD-02", quantity=1, unit_price=Decimal("50.50")),
            ],
        )
        result = await self.use_case.execute(input_data)

        self.assertEqual(result.user_id, user.id)
        self.assertEqual(result.total_amount, Decimal("350.50"))
        self.assertEqual(result.status, "PENDING")
        self.mock_order_repo.save.assert_awaited_once()
        self.mock_uow.commit.assert_awaited_once()
        self.mock_publisher.publish_order_created.assert_awaited_once()

    async def test_create_order_user_not_found_raises_error(self) -> None:
        """User không tồn tại: ném UserNotFoundError và không bắn sự kiện RabbitMQ."""
        self.mock_user_repo.get_by_id.return_value = None

        input_data = CreateOrderInput(
            user_id=uuid.uuid4(),
            items=[
                CreateOrderItemInput(
                    product_id="PROD-01", quantity=1, unit_price=Decimal("100.00")
                ),
            ],
        )

        with self.assertRaises(UserNotFoundError):
            await self.use_case.execute(input_data)

        self.mock_order_repo.save.assert_not_awaited()
        self.mock_publisher.publish_order_created.assert_not_awaited()

    async def test_create_order_empty_items_raises_domain_error(self) -> None:
        """Giỏ hàng rỗng: Domain Entity chặn ngay với EmptyOrderError."""
        user = User(email="buyer@example.com", hashed_password="pw", full_name="Buyer")
        self.mock_user_repo.get_by_id.return_value = user

        input_data = CreateOrderInput(user_id=user.id, items=[])

        with self.assertRaises(EmptyOrderError):
            await self.use_case.execute(input_data)

        self.mock_order_repo.save.assert_not_awaited()

    async def test_create_order_invalid_quantity_raises_domain_error(self) -> None:
        """Số lượng sản phẩm <= 0: ném InvalidItemQuantityError."""
        user = User(email="buyer@example.com", hashed_password="pw", full_name="Buyer")
        self.mock_user_repo.get_by_id.return_value = user

        input_data = CreateOrderInput(
            user_id=user.id,
            items=[
                CreateOrderItemInput(
                    product_id="PROD-01", quantity=0, unit_price=Decimal("100.00")
                ),
            ],
        )

        with self.assertRaises(InvalidItemQuantityError):
            await self.use_case.execute(input_data)

        self.mock_order_repo.save.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import AsyncMock, MagicMock

from src.application.user.use_cases.register_user import (
    RegisterUserInput,
    RegisterUserUseCase,
)
from src.domain.user.entities import User
from src.domain.user.exceptions import InvalidEmailError, UserAlreadyExistsError


class TestRegisterUserUseCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.mock_uow = AsyncMock()
        self.mock_user_repo = AsyncMock()
        self.mock_hasher = MagicMock()
        self.mock_hasher.hash.return_value = "hashed_secret_123"
        self.mock_notifier = AsyncMock()

        self.use_case = RegisterUserUseCase(
            uow=self.mock_uow,
            user_repo=self.mock_user_repo,
            password_hasher=self.mock_hasher,
            external_notifier=self.mock_notifier,
        )

    async def test_register_user_success(self) -> None:
        """Đăng ký thành công: lưu DB, commit UoW và gọi API thông báo ngoài."""
        self.mock_user_repo.get_by_email.return_value = None
        self.mock_user_repo.save.side_effect = lambda user: user

        input_data = RegisterUserInput(
            email="viet@example.com",
            password="plain_password",
            full_name="Bui Lac Viet",
        )
        result = await self.use_case.execute(input_data)

        self.assertEqual(result.email, "viet@example.com")
        self.assertEqual(result.full_name, "Bui Lac Viet")
        self.mock_hasher.hash.assert_called_once_with("plain_password")
        self.mock_user_repo.save.assert_awaited_once()
        self.mock_uow.commit.assert_awaited_once()
        self.mock_notifier.notify_user_registered.assert_awaited_once()

    async def test_register_user_duplicate_email_raises_error(self) -> None:
        """Email đã tồn tại: ném lỗi UserAlreadyExistsError và không lưu DB."""
        existing_user = User(
            email="viet@example.com",
            hashed_password="old_hash",
            full_name="Existing User",
        )
        self.mock_user_repo.get_by_email.return_value = existing_user

        input_data = RegisterUserInput(
            email="viet@example.com",
            password="plain_password",
            full_name="Bui Lac Viet",
        )

        with self.assertRaises(UserAlreadyExistsError):
            await self.use_case.execute(input_data)

        self.mock_user_repo.save.assert_not_awaited()
        self.mock_uow.commit.assert_not_awaited()
        self.mock_notifier.notify_user_registered.assert_not_awaited()

    async def test_register_user_external_api_failure_does_not_fail_use_case(self) -> None:
        """API đối tác bên ngoài lỗi: DB vẫn commit và UseCase vẫn trả về kết quả thành công."""
        self.mock_user_repo.get_by_email.return_value = None
        self.mock_user_repo.save.side_effect = lambda user: user
        self.mock_notifier.notify_user_registered.side_effect = RuntimeError("Webhook timeout")

        input_data = RegisterUserInput(
            email="viet@example.com",
            password="plain_password",
            full_name="Bui Lac Viet",
        )
        result = await self.use_case.execute(input_data)

        self.assertEqual(result.email, "viet@example.com")
        self.mock_uow.commit.assert_awaited_once()

    async def test_register_user_invalid_email_raises_domain_error(self) -> None:
        """Email sai định dạng: Domain Entity tự chặn và ném InvalidEmailError."""
        self.mock_user_repo.get_by_email.return_value = None

        input_data = RegisterUserInput(
            email="invalid-email-format",
            password="plain_password",
            full_name="Bui Lac Viet",
        )

        with self.assertRaises(InvalidEmailError):
            await self.use_case.execute(input_data)

        self.mock_user_repo.save.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()

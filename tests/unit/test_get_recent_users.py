import unittest
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.application.user.use_cases.get_recent_users import GetRecentUsersUseCase
from src.domain.user.entities import User


class TestGetRecentUsersUseCase(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_user_repo = MagicMock()
        self.use_case = GetRecentUsersUseCase(user_repo=self.mock_user_repo)

    def test_get_recent_users_returns_mapped_outputs(self) -> None:
        now = datetime.now(timezone.utc)
        user_1 = User(
            id=uuid.uuid4(),
            email="u1@example.com",
            hashed_password="h1",
            full_name="User One",
            created_at=now,
        )
        self.mock_user_repo.get_recent_users.return_value = [user_1]

        results = self.use_case.execute(limit=10)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].user_id, user_1.id)
        self.assertEqual(results[0].email, "u1@example.com")
        self.mock_user_repo.get_recent_users.assert_called_once_with(limit=10)


if __name__ == "__main__":
    unittest.main()

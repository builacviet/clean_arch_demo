import logging
import uuid
from dataclasses import dataclass

from src.application.shared.unit_of_work import IUnitOfWork
from src.application.user.ports import (
    IExternalNotifier,
    IPasswordHasher,
    IUserRepository,
)
from src.domain.user.entities import User
from src.domain.user.exceptions import UserAlreadyExistsError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RegisterUserInput:
    email: str
    password: str
    full_name: str


@dataclass(frozen=True)
class RegisterUserOutput:
    user_id: uuid.UUID
    email: str
    full_name: str


class RegisterUserUseCase:
    def __init__(
        self,
        uow: IUnitOfWork,
        user_repo: IUserRepository,
        password_hasher: IPasswordHasher,
        external_notifier: IExternalNotifier,
    ) -> None:
        self._uow = uow
        self._user_repo = user_repo
        self._password_hasher = password_hasher
        self._external_notifier = external_notifier

    async def execute(self, input_data: RegisterUserInput) -> RegisterUserOutput:
        async with self._uow:
            if await self._user_repo.get_by_email(input_data.email) is not None:
                raise UserAlreadyExistsError(input_data.email)

            new_user = User(
                email=input_data.email,
                hashed_password=self._password_hasher.hash(input_data.password),
                full_name=input_data.full_name,
            )
            saved_user = await self._user_repo.save(new_user)
            await self._uow.commit()

        try:
            await self._external_notifier.notify_user_registered(saved_user)
        except Exception as exc:
            logger.error("External notify failed for user %s: %s", saved_user.id, exc)

        return RegisterUserOutput(
            user_id=saved_user.id,
            email=saved_user.email,
            full_name=saved_user.full_name,
        )

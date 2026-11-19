import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from src.application.user.use_cases.register_user import (
    RegisterUserInput,
    RegisterUserUseCase,
)
from src.domain.shared.exceptions import DomainError
from src.domain.user.exceptions import UserAlreadyExistsError
from src.presentation.dependencies.user_deps import get_register_user_use_case

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=64)
    full_name: str = Field(..., min_length=2, max_length=100)

    @field_validator("password")
    @classmethod
    def check_password_strength(cls, v: str) -> str:
        # Ví dụ: Không cho phép mật khẩu chứa khoảng trắng
        if " " in v:
            raise ValueError("Mật khẩu không được chứa khoảng trắng")

        # Ví dụ: Phải có ít nhất 1 chữ số
        if not any(char.isdigit() for char in v):
            raise ValueError("Mật khẩu phải chứa ít nhất 1 chữ số")

        return v

    @field_validator("full_name")
    @classmethod
    def clean_full_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Họ tên không được chỉ chứa khoảng trắng")
        return cleaned


class RegisterResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    full_name: str


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    body: RegisterRequest,
    use_case: RegisterUserUseCase = Depends(get_register_user_use_case),
) -> RegisterResponse:
    try:
        result = await use_case.execute(
            RegisterUserInput(email=body.email, password=body.password, full_name=body.full_name)
        )
        return RegisterResponse(
            user_id=result.user_id, email=result.email, full_name=result.full_name
        )
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except DomainError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

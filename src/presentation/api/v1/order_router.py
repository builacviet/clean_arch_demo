import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.application.order.use_cases.create_order import (
    CreateOrderInput,
    CreateOrderItemInput,
    CreateOrderUseCase,
)
from src.domain.shared.exceptions import DomainError
from src.domain.user.exceptions import UserNotFoundError
from src.presentation.dependencies.order_deps import get_create_order_use_case

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


class OrderItemRequest(BaseModel):
    product_id: str
    quantity: int
    unit_price: Decimal


class CreateOrderRequest(BaseModel):
    user_id: uuid.UUID
    items: list[OrderItemRequest]


class CreateOrderResponse(BaseModel):
    order_id: uuid.UUID
    user_id: uuid.UUID
    total_amount: Decimal
    status: str


@router.post("/", response_model=CreateOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    body: CreateOrderRequest,
    use_case: CreateOrderUseCase = Depends(get_create_order_use_case),
) -> CreateOrderResponse:
    try:
        input_dto = CreateOrderInput(
            user_id=body.user_id,
            items=[
                CreateOrderItemInput(
                    product_id=i.product_id,
                    quantity=i.quantity,
                    unit_price=i.unit_price,
                )
                for i in body.items
            ],
        )
        result = await use_case.execute(input_dto)
        return CreateOrderResponse(
            order_id=result.order_id,
            user_id=result.user_id,
            total_amount=result.total_amount,
            status=result.status,
        )
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DomainError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

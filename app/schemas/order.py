import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import field_validator

from app.models.order import OrderStatus
from app.schemas.base import BaseSchema


class OrderBase(BaseSchema):
    title: str
    amount: Decimal


class OrderCreate(OrderBase):
    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("订单金额必须大于 0")
        return v


class OrderUpdate(BaseSchema):
    title: str | None = None
    amount: Decimal | None = None
    status: OrderStatus | None = None


class OrderResponse(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    amount: Decimal
    status: OrderStatus
    created_at: datetime
    updated_at: datetime

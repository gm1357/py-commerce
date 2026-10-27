from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field

from api.models import OrderStatus


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    product_name: str
    unit_price: int
    quantity: int

    @computed_field  # type: ignore[prop-decorator]
    @property
    def subtotal(self) -> int:
        return self.unit_price * self.quantity


class OrderUserOut(BaseModel):
    """Who placed the order. Shown to admins, who see everyone's orders."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: OrderStatus
    total: int
    created_at: datetime
    updated_at: datetime
    user: OrderUserOut
    items: list[OrderItemOut]


class OrderPage(BaseModel):
    items: list[OrderOut]
    total: int
    page: int
    page_size: int
    pages: int


class OrderStatusIn(BaseModel):
    status: OrderStatus

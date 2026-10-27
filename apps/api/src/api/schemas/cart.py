from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, computed_field

from api.schemas.product import ProductOut


class CartItemIn(BaseModel):
    quantity: Annotated[int, Field(ge=1, le=99)]


class CartItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product: ProductOut
    quantity: int

    # Computed fields are part of the response (and the OpenAPI schema) but never input.
    @computed_field  # type: ignore[prop-decorator]
    @property
    def subtotal(self) -> int:
        return self.product.price * self.quantity


class CartOut(BaseModel):
    items: list[CartItemOut]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total(self) -> int:
        return sum(item.subtotal for item in self.items)

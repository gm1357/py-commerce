from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


class ProductIn(BaseModel):
    """Editable product fields, used to both create and update a product."""

    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    description: Annotated[str | None, Field(max_length=2000)] = None
    price: Annotated[int, Field(ge=0, description="Price in cents")]
    stock: Annotated[int, Field(ge=0, description="Units available to buy")]


class ProductOut(ProductIn):
    model_config = ConfigDict(from_attributes=True)

    description: str | None  # always present in responses (no default), unlike ProductIn
    id: int
    created_at: datetime
    updated_at: datetime


class ProductPage(BaseModel):
    items: list[ProductOut]
    total: int
    page: int
    page_size: int
    pages: int

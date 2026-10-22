from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

ProductName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class ProductIn(BaseModel):
    """Editable product fields, used to both create and update a product."""

    name: ProductName
    description: str | None = Field(default=None, max_length=2000)
    price: int = Field(ge=0, description="Price in cents")


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

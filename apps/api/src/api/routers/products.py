import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.db.session import SessionDep
from api.models import Product
from api.schemas.product import ProductIn, ProductOut, ProductPage
from api.services import products as product_service

router = APIRouter(prefix="/products", tags=["products"])


async def get_product_or_404(product_id: int, session: SessionDep) -> Product:
    product = await product_service.get_product(session, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    return product


ProductDep = Annotated[Product, Depends(get_product_or_404)]


@router.get("", response_model=ProductPage)
async def list_products(
    session: SessionDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> ProductPage:
    products, total = await product_service.list_products(session, page, page_size)
    return ProductPage(
        items=[ProductOut.model_validate(p) for p in products],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size),
    )


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product: ProductDep) -> Product:
    return product


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(data: ProductIn, session: SessionDep) -> Product:
    return await product_service.create_product(session, data)


@router.put("/{product_id}", response_model=ProductOut)
async def update_product(product: ProductDep, data: ProductIn, session: SessionDep) -> Product:
    return await product_service.update_product(session, product, data)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product: ProductDep, session: SessionDep) -> None:
    await product_service.soft_delete_product(session, product)

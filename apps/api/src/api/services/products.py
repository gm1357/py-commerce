from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Product
from api.schemas.product import ProductIn

# Soft-deleted products are invisible everywhere.
ACTIVE = Product.deleted_at.is_(None)


async def list_products(
    session: AsyncSession, page: int, page_size: int
) -> tuple[list[Product], int]:
    total = await session.scalar(select(func.count()).select_from(Product).where(ACTIVE)) or 0
    result = await session.scalars(
        select(Product)
        .where(ACTIVE)
        # Newest first; id breaks ties between rows inserted in the same transaction.
        .order_by(Product.created_at.desc(), Product.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result), total


async def get_product(session: AsyncSession, product_id: int) -> Product | None:
    return await session.scalar(select(Product).where(Product.id == product_id, ACTIVE))


async def create_product(session: AsyncSession, data: ProductIn) -> Product:
    product = Product(**data.model_dump())
    session.add(product)
    await session.commit()
    return product


async def update_product(session: AsyncSession, product: Product, data: ProductIn) -> Product:
    for field, value in data.model_dump().items():
        setattr(product, field, value)
    await session.commit()
    return product


async def soft_delete_product(session: AsyncSession, product: Product) -> None:
    product.deleted_at = datetime.now(UTC)
    await session.commit()

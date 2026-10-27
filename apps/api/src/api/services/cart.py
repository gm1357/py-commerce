from sqlalchemy import Select, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from api.core.errors import InsufficientStockError
from api.models import CartItem, Product, User
from api.services.products import ACTIVE


def cart_query(user: User) -> Select[CartItem]:
    """The user's cart rows with their products, skipping soft-deleted products.

    contains_eager fills `CartItem.product` from the inner join, instead of a second query.
    """
    return (
        select(CartItem)
        .join(CartItem.product)
        .where(CartItem.user_id == user.id, ACTIVE)
        .options(contains_eager(CartItem.product))
        .order_by(CartItem.created_at, CartItem.id)
    )


async def get_cart(session: AsyncSession, user: User) -> list[CartItem]:
    return list(await session.scalars(cart_query(user)))


async def set_item(session: AsyncSession, user: User, product: Product, quantity: int) -> None:
    # Fails early for a nicer UX. Nothing is reserved: checkout checks stock again under a lock.
    if quantity > product.stock:
        raise InsufficientStockError(product.name, product.stock)

    item = await session.scalar(
        select(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == product.id)
    )
    if item is None:
        session.add(CartItem(user_id=user.id, product_id=product.id, quantity=quantity))
    else:
        item.quantity = quantity
    await session.commit()


async def remove_item(session: AsyncSession, user: User, product_id: int) -> None:
    await session.execute(
        delete(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == product_id)
    )
    await session.commit()

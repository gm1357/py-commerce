from sqlalchemy import Select, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from api.core.errors import EmptyCartError, InsufficientStockError, InvalidStatusTransitionError
from api.models import CartItem, Order, OrderItem, OrderStatus, Product, Role, User
from api.services.cart import cart_query

# Which statuses each status can move to. Shipped and cancelled orders are final.
ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {OrderStatus.PAID, OrderStatus.CANCELLED},
    OrderStatus.PAID: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED: set(),
    OrderStatus.CANCELLED: set(),
}

# Everything OrderOut reads. selectinload fetches all items in one extra query (a join would
# repeat each order row per item); joinedload is fine for the one-to-one user.
_with_details = (selectinload(Order.items), joinedload(Order.user))


async def checkout(session: AsyncSession, user: User) -> Order:
    """Turn the user's cart into a pending order, all or nothing."""
    # FOR UPDATE locks the product rows until commit, so two checkouts can't both buy the last
    # unit. Locking in product id order means two carts never wait on each other in a cycle.
    # populate_existing overwrites any copy already in the session with the freshly locked row.
    cart = list(
        await session.scalars(
            cart_query(user)
            .order_by(None)
            .order_by(Product.id)
            .with_for_update(of=Product)
            .execution_options(populate_existing=True)
        )
    )
    if not cart:
        raise EmptyCartError()
    # Check everything before changing anything. Raising leaves the transaction uncommitted,
    # and the session rolls it back (releasing the locks) when the request ends.
    for item in cart:
        if item.quantity > item.product.stock:
            raise InsufficientStockError(item.product.name, item.product.stock)

    for item in cart:
        item.product.stock -= item.quantity
    order = Order(
        user=user,
        total=sum(item.product.price * item.quantity for item in cart),
        items=[
            OrderItem(
                product_id=item.product.id,
                product_name=item.product.name,
                unit_price=item.product.price,
                quantity=item.quantity,
            )
            for item in cart
        ],
    )
    session.add(order)
    # Also clears rows for soft-deleted products, which cart_query skipped.
    await session.execute(delete(CartItem).where(CartItem.user_id == user.id))
    await session.commit()
    return order


def _visible_to(user: User) -> Select[Order]:
    query = select(Order)
    return query if user.role == Role.ADMIN else query.where(Order.user_id == user.id)


async def list_orders(
    session: AsyncSession, user: User, page: int, page_size: int, status: OrderStatus | None
) -> tuple[list[Order], int]:
    """Admins see every order; everyone else sees only their own."""
    query = _visible_to(user)
    if status is not None:
        query = query.where(Order.status == status)
    total = await session.scalar(select(func.count()).select_from(query.subquery())) or 0
    result = await session.scalars(
        query.options(*_with_details)
        .order_by(Order.created_at.desc(), Order.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result), total


async def get_order(session: AsyncSession, order_id: int) -> Order | None:
    return await session.scalar(select(Order).where(Order.id == order_id).options(*_with_details))


async def change_status(session: AsyncSession, order: Order, status: OrderStatus) -> Order:
    # Re-read the status with the row locked: two simultaneous cancels would otherwise both
    # see "pending" and both put the stock back.
    await session.refresh(order, ["status"], with_for_update=True)
    if status not in ALLOWED_TRANSITIONS[order.status]:
        raise InvalidStatusTransitionError(order.status, status)

    if status == OrderStatus.CANCELLED:
        for item in order.items:
            # `stock = stock + n` runs in the database, so it can't overwrite a concurrent change.
            await session.execute(
                update(Product)
                .where(Product.id == item.product_id)
                .values(stock=Product.stock + item.quantity)
            )
    order.status = status
    await session.commit()
    return order

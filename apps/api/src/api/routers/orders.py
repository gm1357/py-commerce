import math
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from api.core.auth import CurrentUserDep, require_admin
from api.db.session import SessionDep
from api.models import Order, OrderStatus, Role
from api.schemas.common import CONFLICT
from api.schemas.order import OrderOut, OrderPage, OrderStatusIn
from api.services import orders as order_service
from api.services.notifications import send_order_confirmation

router = APIRouter(prefix="/orders", tags=["orders"])

admin_only = [Depends(require_admin)]


async def get_visible_order_or_404(
    order_id: int, session: SessionDep, user: CurrentUserDep
) -> Order:
    order = await order_service.get_order(session, order_id)
    # Someone else's order is a 404, not a 403: it shouldn't reveal that the id exists.
    if order is None or (user.role != Role.ADMIN and order.user_id != user.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    return order


VisibleOrderDep = Annotated[Order, Depends(get_visible_order_or_404)]


@router.post(
    "/checkout",
    response_model=OrderOut,
    status_code=status.HTTP_201_CREATED,
    responses=CONFLICT,
)
async def checkout(
    session: SessionDep, user: CurrentUserDep, background_tasks: BackgroundTasks
) -> Order:
    order = await order_service.checkout(session, user)
    # Runs after the response is sent, so the user doesn't wait on it.
    background_tasks.add_task(send_order_confirmation, order.id, user.email)
    return order


@router.get("", response_model=OrderPage)
async def list_orders(
    session: SessionDep,
    user: CurrentUserDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    order_status: Annotated[OrderStatus | None, Query(alias="status")] = None,
) -> OrderPage:
    """Your orders, newest first. Admins get everyone's."""
    orders, total = await order_service.list_orders(session, user, page, page_size, order_status)
    return OrderPage(
        items=[OrderOut.model_validate(o) for o in orders],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size),
    )


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order: VisibleOrderDep) -> Order:
    return order


@router.post("/{order_id}/cancel", response_model=OrderOut, responses=CONFLICT)
async def cancel_order(order: VisibleOrderDep, session: SessionDep) -> Order:
    """Cancel a pending or paid order and put its stock back."""
    return await order_service.change_status(session, order, OrderStatus.CANCELLED)


@router.patch("/{order_id}", response_model=OrderOut, responses=CONFLICT, dependencies=admin_only)
async def update_order_status(
    order: VisibleOrderDep, data: OrderStatusIn, session: SessionDep
) -> Order:
    return await order_service.change_status(session, order, data.status)

from fastapi import APIRouter, status

from api.core.auth import CurrentUserDep
from api.db.session import SessionDep
from api.models import User
from api.routers.products import ProductDep
from api.schemas.cart import CartItemIn, CartItemOut, CartOut
from api.schemas.common import CONFLICT
from api.services import cart as cart_service

router = APIRouter(prefix="/cart", tags=["cart"])


async def build_cart(session: SessionDep, user: User) -> CartOut:
    items = await cart_service.get_cart(session, user)
    return CartOut(items=[CartItemOut.model_validate(item) for item in items])


@router.get("", response_model=CartOut)
async def get_cart(session: SessionDep, user: CurrentUserDep) -> CartOut:
    return await build_cart(session, user)


@router.put("/items/{product_id}", response_model=CartOut, responses=CONFLICT)
async def set_cart_item(
    product: ProductDep, data: CartItemIn, session: SessionDep, user: CurrentUserDep
) -> CartOut:
    """Set how many of a product are in the cart. Sending the same request twice is harmless."""
    await cart_service.set_item(session, user, product, data.quantity)
    return await build_cart(session, user)


@router.delete("/items/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_cart_item(product_id: int, session: SessionDep, user: CurrentUserDep) -> None:
    await cart_service.remove_item(session, user, product_id)

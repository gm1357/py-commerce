from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Product, Role, User

LoginAs = Callable[..., Awaitable[User]]
MakeProduct = Callable[..., Awaitable[Product]]


@pytest.fixture
async def user_client(client: AsyncClient, login_as: LoginAs) -> AsyncClient:
    await login_as(Role.USER)
    return client


async def test_cart_requires_sign_in(client: AsyncClient, make_product: MakeProduct) -> None:
    product = await make_product()

    assert (await client.get("/cart")).status_code == 401
    put = await client.put(f"/cart/items/{product.id}", json={"quantity": 1})
    assert put.status_code == 401
    assert (await client.delete(f"/cart/items/{product.id}")).status_code == 401


async def test_empty_cart(user_client: AsyncClient) -> None:
    assert (await user_client.get("/cart")).json() == {"items": [], "total": 0}


async def test_set_item_adds_then_replaces_quantity(
    user_client: AsyncClient, make_product: MakeProduct
) -> None:
    chair = await make_product(name="Chair", price=1000)
    lamp = await make_product(name="Lamp", price=250)

    await user_client.put(f"/cart/items/{chair.id}", json={"quantity": 2})
    await user_client.put(f"/cart/items/{lamp.id}", json={"quantity": 1})
    response = await user_client.put(f"/cart/items/{chair.id}", json={"quantity": 3})

    assert response.status_code == 200
    cart = response.json()
    assert [(i["product"]["name"], i["quantity"], i["subtotal"]) for i in cart["items"]] == [
        ("Chair", 3, 3000),  # replaced, not 2 + 3
        ("Lamp", 1, 250),
    ]
    assert cart["total"] == 3250
    assert (await user_client.get("/cart")).json() == cart


async def test_set_item_for_missing_product_returns_404(user_client: AsyncClient) -> None:
    response = await user_client.put("/cart/items/999999", json={"quantity": 1})

    assert response.status_code == 404


async def test_set_item_above_stock_returns_409(
    user_client: AsyncClient, make_product: MakeProduct
) -> None:
    product = await make_product(name="Lamp", stock=2)

    response = await user_client.put(f"/cart/items/{product.id}", json={"quantity": 3})

    assert response.status_code == 409
    assert response.json() == {"detail": "Only 2 of 'Lamp' left in stock"}
    assert (await user_client.get("/cart")).json()["items"] == []


@pytest.mark.parametrize("quantity", [0, -1, 100])
async def test_set_item_rejects_invalid_quantity(
    user_client: AsyncClient, make_product: MakeProduct, quantity: int
) -> None:
    product = await make_product()

    response = await user_client.put(f"/cart/items/{product.id}", json={"quantity": quantity})

    assert response.status_code == 422


async def test_remove_item_is_idempotent(
    user_client: AsyncClient, make_product: MakeProduct
) -> None:
    product = await make_product()
    await user_client.put(f"/cart/items/{product.id}", json={"quantity": 1})

    assert (await user_client.delete(f"/cart/items/{product.id}")).status_code == 204
    assert (await user_client.delete(f"/cart/items/{product.id}")).status_code == 204
    assert (await user_client.get("/cart")).json()["items"] == []


async def test_soft_deleted_product_disappears_from_cart(
    user_client: AsyncClient, make_product: MakeProduct, session: AsyncSession
) -> None:
    product = await make_product()
    await user_client.put(f"/cart/items/{product.id}", json={"quantity": 1})

    product.deleted_at = datetime.now(UTC)
    await session.commit()

    assert (await user_client.get("/cart")).json() == {"items": [], "total": 0}


async def test_carts_are_per_user(
    client: AsyncClient, login_as: LoginAs, make_product: MakeProduct
) -> None:
    product = await make_product()
    await login_as(Role.USER)
    await client.put(f"/cart/items/{product.id}", json={"quantity": 1})

    await login_as(Role.USER, email="other@example.com")

    assert (await client.get("/cart")).json()["items"] == []

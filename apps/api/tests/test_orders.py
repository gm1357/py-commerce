import logging
from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Product, Role, User

LoginAs = Callable[..., Awaitable[User]]
MakeProduct = Callable[..., Awaitable[Product]]


async def checkout(client: AsyncClient, *lines: tuple[Product, int]) -> dict[str, Any]:
    for product, quantity in lines:
        response = await client.put(f"/cart/items/{product.id}", json={"quantity": quantity})
        assert response.status_code == 200, response.text
    response = await client.post("/orders/checkout")
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


async def stock_of(session: AsyncSession, product: Product) -> int:
    await session.refresh(product)  # read the database, not the object cached in the session
    return product.stock


async def test_checkout_creates_order_and_takes_stock(
    client: AsyncClient, login_as: LoginAs, make_product: MakeProduct, session: AsyncSession
) -> None:
    user = await login_as(Role.USER)
    chair = await make_product(name="Chair", price=1000, stock=5)
    lamp = await make_product(name="Lamp", price=250, stock=1)

    order = await checkout(client, (chair, 2), (lamp, 1))

    assert order["status"] == "pending"
    assert order["total"] == 2250
    assert order["user"] == {"id": user.id, "name": user.name, "email": user.email}
    assert [
        (i["product_name"], i["unit_price"], i["quantity"], i["subtotal"]) for i in order["items"]
    ] == [
        ("Chair", 1000, 2, 2000),
        ("Lamp", 250, 1, 250),
    ]
    assert (await stock_of(session, chair), await stock_of(session, lamp)) == (3, 0)
    assert (await client.get("/cart")).json()["items"] == []
    assert (await client.get(f"/orders/{order['id']}")).json() == order


async def test_order_keeps_name_and_price_from_checkout(
    client: AsyncClient, login_as: LoginAs, make_product: MakeProduct, session: AsyncSession
) -> None:
    await login_as(Role.USER)
    product = await make_product(name="Chair", price=1000)
    order = await checkout(client, (product, 1))

    product.name, product.price = "Renamed", 9999
    await session.commit()

    item = (await client.get(f"/orders/{order['id']}")).json()["items"][0]
    assert (item["product_name"], item["unit_price"]) == ("Chair", 1000)


async def test_checkout_empty_cart_returns_409(client: AsyncClient, login_as: LoginAs) -> None:
    await login_as(Role.USER)

    response = await client.post("/orders/checkout")

    assert response.status_code == 409
    assert response.json() == {"detail": "Your cart is empty"}


async def test_checkout_with_too_little_stock_changes_nothing(
    client: AsyncClient, login_as: LoginAs, make_product: MakeProduct, session: AsyncSession
) -> None:
    await login_as(Role.USER)
    chair = await make_product(name="Chair", stock=5)
    lamp = await make_product(name="Lamp", stock=2)
    await client.put(f"/cart/items/{chair.id}", json={"quantity": 1})
    await client.put(f"/cart/items/{lamp.id}", json={"quantity": 2})
    lamp.stock = 1  # someone else bought one after it went in the cart
    await session.commit()

    response = await client.post("/orders/checkout")

    assert response.status_code == 409
    assert response.json() == {"detail": "Only 1 of 'Lamp' left in stock"}
    assert (await stock_of(session, chair), await stock_of(session, lamp)) == (5, 1)
    assert len((await client.get("/cart")).json()["items"]) == 2
    assert (await client.get("/orders")).json()["total"] == 0


async def test_checkout_sends_confirmation_in_background(
    client: AsyncClient,
    login_as: LoginAs,
    make_product: MakeProduct,
    caplog: pytest.LogCaptureFixture,
) -> None:
    user = await login_as(Role.USER)
    caplog.set_level(logging.INFO, logger="api.services.notifications")

    order = await checkout(client, (await make_product(), 1))

    # The test client waits for background tasks to finish before returning the response.
    assert f"order {order['id']} sent to {user.email}" in caplog.text


async def test_orders_require_sign_in(client: AsyncClient) -> None:
    assert (await client.get("/orders")).status_code == 401
    assert (await client.post("/orders/checkout")).status_code == 401


async def test_users_list_only_their_own_orders_and_admins_list_all(
    client: AsyncClient, login_as: LoginAs, make_product: MakeProduct
) -> None:
    product = await make_product(stock=10)
    await login_as(Role.USER)
    first = await checkout(client, (product, 1))
    second = await checkout(client, (product, 1))
    await login_as(Role.USER, email="other@example.com")
    other = await checkout(client, (product, 1))

    own = (await client.get("/orders")).json()
    await login_as(Role.ADMIN)
    everyone = (await client.get("/orders")).json()

    assert [o["id"] for o in own["items"]] == [other["id"]]
    assert [o["id"] for o in everyone["items"]] == [other["id"], second["id"], first["id"]]
    assert (everyone["total"], everyone["pages"]) == (3, 1)


async def test_list_orders_filters_by_status(
    client: AsyncClient, login_as: LoginAs, make_product: MakeProduct
) -> None:
    await login_as(Role.USER)
    product = await make_product()
    kept = await checkout(client, (product, 1))
    cancelled = await checkout(client, (product, 1))
    await client.post(f"/orders/{cancelled['id']}/cancel")

    pending = (await client.get("/orders", params={"status": "pending"})).json()

    assert [o["id"] for o in pending["items"]] == [kept["id"]]
    assert (await client.get("/orders", params={"status": "lost"})).status_code == 422


async def test_other_users_order_is_not_found(
    client: AsyncClient, login_as: LoginAs, make_product: MakeProduct
) -> None:
    await login_as(Role.USER)
    order = await checkout(client, (await make_product(), 1))
    url = f"/orders/{order['id']}"

    await login_as(Role.USER, email="other@example.com")

    assert (await client.get(url)).status_code == 404
    assert (await client.post(f"{url}/cancel")).status_code == 404
    assert (await client.get("/orders/999999")).status_code == 404


async def test_admin_moves_order_through_statuses(
    client: AsyncClient, login_as: LoginAs, make_product: MakeProduct
) -> None:
    await login_as(Role.USER)
    order = await checkout(client, (await make_product(), 1))
    url = f"/orders/{order['id']}"
    await login_as(Role.ADMIN)

    paid = await client.patch(url, json={"status": "paid"})
    shipped = await client.patch(url, json={"status": "shipped"})
    back = await client.patch(url, json={"status": "pending"})

    assert (paid.status_code, paid.json()["status"]) == (200, "paid")
    assert (shipped.status_code, shipped.json()["status"]) == (200, "shipped")
    assert back.status_code == 409
    assert back.json() == {"detail": "Cannot change a shipped order to pending"}


async def test_admin_cannot_skip_payment(
    client: AsyncClient, login_as: LoginAs, make_product: MakeProduct
) -> None:
    await login_as(Role.USER)
    order = await checkout(client, (await make_product(), 1))
    await login_as(Role.ADMIN)

    response = await client.patch(f"/orders/{order['id']}", json={"status": "shipped"})

    assert response.status_code == 409


async def test_only_admins_change_status(
    client: AsyncClient, login_as: LoginAs, make_product: MakeProduct
) -> None:
    await login_as(Role.USER)
    order = await checkout(client, (await make_product(), 1))

    response = await client.patch(f"/orders/{order['id']}", json={"status": "paid"})

    assert response.status_code == 403
    assert (await client.get(f"/orders/{order['id']}")).json()["status"] == "pending"


async def test_cancel_restores_stock(
    client: AsyncClient, login_as: LoginAs, make_product: MakeProduct, session: AsyncSession
) -> None:
    await login_as(Role.USER)
    product = await make_product(stock=5)
    order = await checkout(client, (product, 3))

    response = await client.post(f"/orders/{order['id']}/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert await stock_of(session, product) == 5


async def test_cancel_twice_returns_409_and_restores_stock_once(
    client: AsyncClient, login_as: LoginAs, make_product: MakeProduct, session: AsyncSession
) -> None:
    await login_as(Role.USER)
    product = await make_product(stock=5)
    order = await checkout(client, (product, 3))

    await client.post(f"/orders/{order['id']}/cancel")
    again = await client.post(f"/orders/{order['id']}/cancel")

    assert again.status_code == 409
    assert await stock_of(session, product) == 5


async def test_admin_can_cancel_paid_order_but_not_shipped(
    client: AsyncClient, login_as: LoginAs, make_product: MakeProduct
) -> None:
    await login_as(Role.USER)
    product = await make_product()
    paid = await checkout(client, (product, 1))
    shipped = await checkout(client, (product, 1))
    await login_as(Role.ADMIN)
    await client.patch(f"/orders/{paid['id']}", json={"status": "paid"})
    for status in ("paid", "shipped"):
        await client.patch(f"/orders/{shipped['id']}", json={"status": status})

    assert (await client.post(f"/orders/{paid['id']}/cancel")).status_code == 200
    assert (await client.post(f"/orders/{shipped['id']}/cancel")).status_code == 409

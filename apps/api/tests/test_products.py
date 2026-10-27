from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from httpx import AsyncClient

from api.models import Role

PRODUCT = {"name": "Steel Chair", "description": "Sturdy.", "price": 1299, "stock": 5}


async def create(client: AsyncClient, **overrides: Any) -> dict[str, Any]:
    response = await client.post("/products", json={**PRODUCT, **overrides})
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


async def test_create_product(admin_client: AsyncClient) -> None:
    product = await create(admin_client, name="  Steel Chair  ")

    assert product["name"] == "Steel Chair"  # whitespace stripped
    assert product["description"] == "Sturdy."
    assert product["price"] == 1299
    assert product["stock"] == 5
    assert {"id", "created_at", "updated_at"} <= product.keys()
    assert "deleted_at" not in product


async def test_create_product_without_description(admin_client: AsyncClient) -> None:
    product = await create(admin_client, description=None)

    assert product["description"] is None


@pytest.mark.parametrize(
    "overrides",
    [
        {"price": -1},
        {"stock": -1},
        {"stock": None},
        {"name": ""},
        {"name": "   "},
        {"name": "x" * 201},
        {"price": 9.99},
    ],
)
async def test_create_product_rejects_invalid_input(
    admin_client: AsyncClient, overrides: dict[str, Any]
) -> None:
    response = await admin_client.post("/products", json={**PRODUCT, **overrides})

    assert response.status_code == 422


async def test_get_product(admin_client: AsyncClient) -> None:
    product = await create(admin_client)

    response = await admin_client.get(f"/products/{product['id']}")

    assert response.status_code == 200
    assert response.json() == product


async def test_get_missing_product_returns_404(client: AsyncClient) -> None:
    response = await client.get("/products/999999")

    assert response.status_code == 404


async def test_list_products_paginates_newest_first(admin_client: AsyncClient) -> None:
    created = [await create(admin_client, name=f"Product {i}") for i in range(12)]

    first = (await admin_client.get("/products")).json()
    second = (await admin_client.get("/products", params={"page": 2})).json()

    assert (first["total"], first["pages"], first["page_size"]) == (12, 2, 10)
    assert [p["id"] for p in first["items"]] == [p["id"] for p in reversed(created)][:10]
    assert [p["id"] for p in second["items"]] == [created[1]["id"], created[0]["id"]]


async def test_list_products_when_empty(client: AsyncClient) -> None:
    body = (await client.get("/products")).json()

    assert body == {"items": [], "total": 0, "page": 1, "page_size": 10, "pages": 0}


@pytest.mark.parametrize("params", [{"page": 0}, {"page_size": 0}, {"page_size": 101}])
async def test_list_products_rejects_invalid_pagination(
    client: AsyncClient, params: dict[str, int]
) -> None:
    response = await client.get("/products", params=params)

    assert response.status_code == 422


async def test_update_product(admin_client: AsyncClient) -> None:
    product = await create(admin_client)
    changes = {"name": "Oak Table", "description": None, "price": 4500, "stock": 0}

    response = await admin_client.put(f"/products/{product['id']}", json=changes)

    assert response.status_code == 200
    assert response.json() | changes == response.json()
    assert (await admin_client.get(f"/products/{product['id']}")).json()["name"] == "Oak Table"


async def test_update_missing_product_returns_404(admin_client: AsyncClient) -> None:
    response = await admin_client.put("/products/999999", json=PRODUCT)

    assert response.status_code == 404


async def test_delete_product_is_soft_and_hides_it(admin_client: AsyncClient) -> None:
    product = await create(admin_client)
    url = f"/products/{product['id']}"

    assert (await admin_client.delete(url)).status_code == 204
    assert (await admin_client.get(url)).status_code == 404
    assert (await admin_client.put(url, json=PRODUCT)).status_code == 404
    assert (await admin_client.delete(url)).status_code == 404
    assert (await admin_client.get("/products")).json()["total"] == 0


async def test_product_reads_are_public(admin_client: AsyncClient) -> None:
    product = await create(admin_client)
    admin_client.cookies.clear()

    assert (await admin_client.get("/products")).status_code == 200
    assert (await admin_client.get(f"/products/{product['id']}")).status_code == 200


@pytest.mark.parametrize(("method", "path"), [("POST", ""), ("PUT", "/{id}"), ("DELETE", "/{id}")])
async def test_product_writes_require_admin(
    client: AsyncClient, login_as: Callable[[Role], Awaitable[Any]], method: str, path: str
) -> None:
    await login_as(Role.ADMIN)
    product = await create(client)
    url = "/products" + path.format(id=product["id"])

    client.cookies.clear()
    anonymous = await client.request(method, url, json=PRODUCT)
    await login_as(Role.USER)
    regular_user = await client.request(method, url, json=PRODUCT)

    assert anonymous.status_code == 401
    assert regular_user.status_code == 403
    assert (await client.get(f"/products/{product['id']}")).json() == product  # untouched

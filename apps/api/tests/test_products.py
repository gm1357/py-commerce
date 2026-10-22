from typing import Any

import pytest
from httpx import AsyncClient

PRODUCT = {"name": "Steel Chair", "description": "Sturdy.", "price": 1299}


async def create(client: AsyncClient, **overrides: Any) -> dict[str, Any]:
    response = await client.post("/products", json={**PRODUCT, **overrides})
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


async def test_create_product(client: AsyncClient) -> None:
    product = await create(client, name="  Steel Chair  ")

    assert product["name"] == "Steel Chair"  # whitespace stripped
    assert product["description"] == "Sturdy."
    assert product["price"] == 1299
    assert {"id", "created_at", "updated_at"} <= product.keys()
    assert "deleted_at" not in product


async def test_create_product_without_description(client: AsyncClient) -> None:
    product = await create(client, description=None)

    assert product["description"] is None


@pytest.mark.parametrize(
    "overrides",
    [{"price": -1}, {"name": ""}, {"name": "   "}, {"name": "x" * 201}, {"price": 9.99}],
)
async def test_create_product_rejects_invalid_input(
    client: AsyncClient, overrides: dict[str, Any]
) -> None:
    response = await client.post("/products", json={**PRODUCT, **overrides})

    assert response.status_code == 422


async def test_get_product(client: AsyncClient) -> None:
    product = await create(client)

    response = await client.get(f"/products/{product['id']}")

    assert response.status_code == 200
    assert response.json() == product


async def test_get_missing_product_returns_404(client: AsyncClient) -> None:
    response = await client.get("/products/999999")

    assert response.status_code == 404


async def test_list_products_paginates_newest_first(client: AsyncClient) -> None:
    created = [await create(client, name=f"Product {i}") for i in range(12)]

    first = (await client.get("/products")).json()
    second = (await client.get("/products", params={"page": 2})).json()

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


async def test_update_product(client: AsyncClient) -> None:
    product = await create(client)
    changes = {"name": "Oak Table", "description": None, "price": 4500}

    response = await client.put(f"/products/{product['id']}", json=changes)

    assert response.status_code == 200
    assert response.json() | changes == response.json()
    assert (await client.get(f"/products/{product['id']}")).json()["name"] == "Oak Table"


async def test_update_missing_product_returns_404(client: AsyncClient) -> None:
    response = await client.put("/products/999999", json=PRODUCT)

    assert response.status_code == 404


async def test_delete_product_is_soft_and_hides_it(client: AsyncClient) -> None:
    product = await create(client)
    url = f"/products/{product['id']}"

    assert (await client.delete(url)).status_code == 204
    assert (await client.get(url)).status_code == 404
    assert (await client.put(url, json=PRODUCT)).status_code == 404
    assert (await client.delete(url)).status_code == 404
    assert (await client.get("/products")).json()["total"] == 0

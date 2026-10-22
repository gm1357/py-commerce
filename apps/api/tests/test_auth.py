from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import UserSession

SIGNUP = {"name": "Ada Lovelace", "email": "ada@example.com", "password": "correct-horse"}


async def signup(client: AsyncClient, **overrides: Any) -> dict[str, Any]:
    response = await client.post("/auth/signup", json={**SIGNUP, **overrides})
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


async def test_signup_creates_regular_user_and_signs_in(client: AsyncClient) -> None:
    user = await signup(client, email="Ada@Example.com", role="admin")

    assert user["email"] == "ada@example.com"  # lowercased
    assert user["role"] == "user"  # a role in the payload is ignored
    assert {"id", "name", "created_at", "updated_at"} <= user.keys()
    assert "password" not in user and "password_hash" not in user
    assert (await client.get("/auth/me")).json() == user


async def test_signup_sets_http_only_session_cookie(client: AsyncClient) -> None:
    response = await client.post("/auth/signup", json=SIGNUP)

    cookie = response.headers["set-cookie"].lower()
    assert cookie.startswith("session_id=")
    assert "httponly" in cookie
    assert "samesite=lax" in cookie


async def test_signup_rejects_taken_email_case_insensitively(client: AsyncClient) -> None:
    await signup(client)

    response = await client.post("/auth/signup", json={**SIGNUP, "email": "ADA@example.com"})

    assert response.status_code == 409


@pytest.mark.parametrize(
    "overrides", [{"email": "not-an-email"}, {"password": "short"}, {"name": "   "}]
)
async def test_signup_rejects_invalid_input(client: AsyncClient, overrides: dict[str, Any]) -> None:
    response = await client.post("/auth/signup", json={**SIGNUP, **overrides})

    assert response.status_code == 422


async def test_login(client: AsyncClient) -> None:
    user = await signup(client)
    client.cookies.clear()

    response = await client.post(
        "/auth/login", json={"email": "ADA@example.com", "password": SIGNUP["password"]}
    )

    assert response.status_code == 200
    assert response.json() == user
    assert (await client.get("/auth/me")).json() == user


@pytest.mark.parametrize(
    "credentials",
    [
        {"email": SIGNUP["email"], "password": "wrong-password"},
        {"email": "nobody@example.com", "password": SIGNUP["password"]},
    ],
)
async def test_login_rejects_bad_credentials(
    client: AsyncClient, credentials: dict[str, str]
) -> None:
    await signup(client)
    client.cookies.clear()

    response = await client.post("/auth/login", json=credentials)

    assert response.status_code == 401
    assert "set-cookie" not in response.headers


async def test_me_requires_a_valid_session(client: AsyncClient) -> None:
    assert (await client.get("/auth/me")).status_code == 401

    client.cookies.set("session_id", "made-up-token")
    assert (await client.get("/auth/me")).status_code == 401


async def test_logout_ends_the_session(client: AsyncClient) -> None:
    await signup(client)
    token = client.cookies["session_id"]

    response = await client.post("/auth/logout")

    assert response.status_code == 204
    assert "session_id" not in client.cookies
    # The session is gone server-side too, not just from the browser.
    client.cookies.set("session_id", token)
    assert (await client.get("/auth/me")).status_code == 401


async def test_logout_without_session(client: AsyncClient) -> None:
    assert (await client.post("/auth/logout")).status_code == 204


async def test_expired_session_is_rejected(client: AsyncClient, session: AsyncSession) -> None:
    await signup(client)

    await session.execute(
        update(UserSession).values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
    )

    assert (await client.get("/auth/me")).status_code == 401

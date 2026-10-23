"""Test fixtures: a dedicated test database, and one rolled-back transaction per test.

Routes call `session.commit()`; with join_transaction_mode="create_savepoint" those commits
only release savepoints inside the outer transaction, which is rolled back after each test.
"""

from collections.abc import AsyncIterator, Awaitable, Callable

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from api.core.auth import SESSION_COOKIE
from api.core.config import get_settings
from api.db.base import Base
from api.db.session import get_session
from api.main import app
from api.models import Role, User
from api.schemas.user import SignupIn
from api.services import auth as auth_service

TEST_DATABASE_URL = make_url(get_settings().database_url).set(database="pycommerce_test")


async def _create_test_database() -> None:
    admin = create_async_engine(
        TEST_DATABASE_URL.set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    async with admin.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": TEST_DATABASE_URL.database},
        )
        if not exists:
            await conn.execute(text(f'CREATE DATABASE "{TEST_DATABASE_URL.database}"'))
    await admin.dispose()


@pytest.fixture(scope="session")
async def engine() -> AsyncIterator[AsyncEngine]:
    await _create_test_database()
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with engine.connect() as conn:
        transaction = await conn.begin()
        session = AsyncSession(
            bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False
        )
        yield session
        await session.close()
        await transaction.rollback()


@pytest.fixture
async def client(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def override_get_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


LoginAs = Callable[[Role], Awaitable[User]]


@pytest.fixture
def login_as(client: AsyncClient, session: AsyncSession) -> LoginAs:
    """Create a user with the given role and sign `client` in as them."""

    async def login_as(role: Role) -> User:
        data = SignupIn(name=f"Test {role}", email=f"{role}@example.com", password="password123")
        user = await auth_service.create_user(session, data, role=role)
        user_session = await auth_service.create_session(session, user)
        client.cookies.set(SESSION_COOKIE, user_session.id)
        return user

    return login_as


@pytest.fixture
async def admin_client(client: AsyncClient, login_as: LoginAs) -> AsyncClient:
    await login_as(Role.ADMIN)
    return client

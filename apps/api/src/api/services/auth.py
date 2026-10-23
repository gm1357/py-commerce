import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.config import get_settings
from api.core.security import DUMMY_HASH, hash_password, verify_password
from api.models import Role, User, UserSession
from api.schemas.user import SignupIn


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    return await session.scalar(select(User).where(User.email == email))


async def create_user(session: AsyncSession, data: SignupIn, role: Role = Role.USER) -> User:
    user = User(
        name=data.name, email=data.email, password_hash=hash_password(data.password), role=role
    )
    session.add(user)
    await session.commit()
    return user


async def authenticate(session: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(session, email)
    if user is None:
        verify_password(password, DUMMY_HASH)
        return None
    return user if verify_password(password, user.password_hash) else None


async def create_session(session: AsyncSession, user: User) -> UserSession:
    expires_at = datetime.now(UTC) + timedelta(days=get_settings().session_ttl_days)
    user_session = UserSession(id=secrets.token_urlsafe(32), user=user, expires_at=expires_at)
    session.add(user_session)
    await session.commit()
    return user_session


async def get_session_user(session: AsyncSession, token: str) -> User | None:
    user_session = await session.scalar(
        select(UserSession).where(
            UserSession.id == token, UserSession.expires_at > datetime.now(UTC)
        )
    )
    return user_session.user if user_session else None


async def delete_session(session: AsyncSession, token: str) -> None:
    await session.execute(delete(UserSession).where(UserSession.id == token))
    await session.commit()

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyCookie

from api.db.session import SessionDep
from api.models import Role, User
from api.services import auth as auth_service

SESSION_COOKIE = "session_id"

# auto_error=False: a missing cookie yields None, so each dependency picks its own error.
session_cookie = APIKeyCookie(name=SESSION_COOKIE, auto_error=False)
SessionTokenDep = Annotated[str | None, Depends(session_cookie)]


async def get_current_user(session: SessionDep, token: SessionTokenDep) -> User:
    user = await auth_service.get_session_user(session, token) if token else None
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def require_admin(user: CurrentUserDep) -> User:
    if user.role != Role.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin role required")
    return user


AdminDep = Annotated[User, Depends(require_admin)]

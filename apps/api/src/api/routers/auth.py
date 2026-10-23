from fastapi import APIRouter, HTTPException, Response, status

from api.core.auth import SESSION_COOKIE, CurrentUserDep, SessionTokenDep
from api.core.config import get_settings
from api.db.session import SessionDep
from api.models import User
from api.schemas.user import LoginIn, SignupIn, UserOut
from api.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.session_ttl_days * 24 * 60 * 60,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
    )


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def signup(data: SignupIn, response: Response, session: SessionDep) -> User:
    if await auth_service.get_user_by_email(session, data.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = await auth_service.create_user(session, data)
    user_session = await auth_service.create_session(session, user)
    set_session_cookie(response, user_session.id)
    return user


@router.post("/login", response_model=UserOut)
async def login(data: LoginIn, response: Response, session: SessionDep) -> User:
    user = await auth_service.authenticate(session, data.email, data.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    user_session = await auth_service.create_session(session, user)
    set_session_cookie(response, user_session.id)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response, session: SessionDep, token: SessionTokenDep) -> None:
    if token:
        await auth_service.delete_session(session, token)
    response.delete_cookie(
        SESSION_COOKIE, httponly=True, samesite="lax", secure=get_settings().cookie_secure
    )


@router.get("/me", response_model=UserOut)
async def get_me(user: CurrentUserDep) -> User:
    return user

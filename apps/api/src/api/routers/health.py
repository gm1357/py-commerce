from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from api.db.session import SessionDep

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    database: Literal["ok", "error"]


@router.get("/health", response_model=HealthResponse)
async def get_health(session: SessionDep) -> HealthResponse:
    try:
        await session.execute(text("SELECT 1"))
        database: Literal["ok", "error"] = "ok"
    except (SQLAlchemyError, OSError):
        database = "error"
    return HealthResponse(status="ok", database=database)

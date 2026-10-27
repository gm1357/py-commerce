from typing import Any

from pydantic import BaseModel


class ErrorOut(BaseModel):
    """Body of an error response, e.g. `{"detail": "Your cart is empty"}`."""

    detail: str


# For a route's `responses=`: documents the 409 (and its body) in the OpenAPI schema, so the
# generated client types `error` for it.
CONFLICT: dict[int | str, dict[str, Any]] = {409: {"model": ErrorOut}}

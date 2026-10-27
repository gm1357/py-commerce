from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from api.core.config import get_settings
from api.core.errors import DomainError
from api.routers import auth, cart, health, orders, products


def generate_operation_id(route: APIRoute) -> str:
    # "<tag>-<function name>" -> generated TS client gets names like `healthGetHealth`
    return f"{route.tags[0]}-{route.name}"


app = FastAPI(title="py-commerce API", generate_unique_id_function=generate_operation_id)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(DomainError)
async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)

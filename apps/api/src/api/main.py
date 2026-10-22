from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from api.core.config import get_settings
from api.routers import health, products


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

app.include_router(health.router)
app.include_router(products.router)

"""Create a default user and an admin in the dev database. Safe to run more than once."""

import asyncio

from api.db.session import SessionLocal, engine
from api.models import Role
from api.schemas.user import SignupIn
from api.services import auth as auth_service

# Dev-only credentials, documented in the README.
USERS = [
    (SignupIn(name="Default User", email="user@example.com", password="password123"), Role.USER),
    (SignupIn(name="Admin", email="admin@example.com", password="admin12345"), Role.ADMIN),
]


async def main() -> None:
    async with SessionLocal() as session:
        for data, role in USERS:
            if await auth_service.get_user_by_email(session, data.email):
                print(f"Skipped {data.email} (already exists)")
                continue
            await auth_service.create_user(session, data, role=role)
            print(f"Created {role} {data.email} / {data.password}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

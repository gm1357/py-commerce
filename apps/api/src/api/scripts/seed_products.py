"""Insert mock products into the dev database. Each run adds COUNT more products."""

import asyncio
import random

from api.db.session import SessionLocal, engine
from api.models import Product

COUNT = 50

ADJECTIVES = ["Ergonomic", "Rustic", "Sleek", "Handmade", "Vintage", "Modern", "Compact", "Deluxe"]
MATERIALS = ["Steel", "Oak", "Cotton", "Leather", "Granite", "Bamboo", "Wool", "Ceramic"]
NOUNS = ["Chair", "Table", "Lamp", "Backpack", "Mug", "Blanket", "Shelf", "Clock", "Vase", "Desk"]


def build_products(count: int, rng: random.Random) -> list[Product]:
    products = []
    for _ in range(count):
        adjective, material, noun = rng.choice(ADJECTIVES), rng.choice(MATERIALS), rng.choice(NOUNS)
        products.append(
            Product(
                name=f"{adjective} {material} {noun}",
                description=f"A {adjective.lower()} {noun.lower()} made of quality "
                f"{material.lower()}. Built to last and easy to love.",
                price=rng.randint(199, 49_999),
                stock=rng.randint(0, 50),
            )
        )
    return products


async def main() -> None:
    async with SessionLocal() as session:
        session.add_all(build_products(COUNT, random.Random()))
        await session.commit()
    await engine.dispose()
    print(f"Inserted {COUNT} products")


if __name__ == "__main__":
    asyncio.run(main())

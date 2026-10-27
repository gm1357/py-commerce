from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db.base import Base
from api.models.product import Product


class CartItem(Base):
    """One product in a user's cart. Each user has at most one row per product."""

    __tablename__ = "cart_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        UniqueConstraint("user_id", "product_id"),
    )
    # See Product: fetch server-generated timestamps via RETURNING (async forbids implicit IO).
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Not eager: queries load it with contains_eager() over an inner join, because checkout
    # locks the product rows (FOR UPDATE), which Postgres refuses on a LEFT OUTER JOIN.
    product: Mapped[Product] = relationship()

# Re-export every model so `import api.models` registers all tables on Base.metadata
# (Alembic autogenerate relies on this).
from api.models.cart import CartItem
from api.models.order import Order, OrderItem, OrderStatus
from api.models.product import Product
from api.models.session import UserSession
from api.models.user import Role, User

__all__ = [
    "CartItem",
    "Order",
    "OrderItem",
    "OrderStatus",
    "Product",
    "Role",
    "User",
    "UserSession",
]

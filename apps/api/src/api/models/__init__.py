# Re-export every model so `import api.models` registers all tables on Base.metadata
# (Alembic autogenerate relies on this).
from api.models.product import Product
from api.models.session import UserSession
from api.models.user import Role, User

__all__ = ["Product", "Role", "User", "UserSession"]

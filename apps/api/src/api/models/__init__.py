# Re-export every model so `import api.models` registers all tables on Base.metadata
# (Alembic autogenerate relies on this).
from api.models.product import Product

__all__ = ["Product"]

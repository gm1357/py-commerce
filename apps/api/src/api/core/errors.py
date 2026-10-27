"""Business-rule errors raised by services.

Services don't know about HTTP, so they raise these instead of HTTPException. The handler
registered in main.py turns them into `{"detail": ...}` responses, the same shape FastAPI uses
for HTTPException, so clients parse every error the same way.
"""


class DomainError(Exception):
    status_code = 409

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class EmptyCartError(DomainError):
    def __init__(self) -> None:
        super().__init__("Your cart is empty")


class InsufficientStockError(DomainError):
    def __init__(self, product_name: str, available: int) -> None:
        super().__init__(f"Only {available} of '{product_name}' left in stock")


class InvalidStatusTransitionError(DomainError):
    def __init__(self, current: str, requested: str) -> None:
        super().__init__(f"Cannot change a {current} order to {requested}")

import logging

logger = logging.getLogger(__name__)


def send_order_confirmation(order_id: int, email: str) -> None:
    """Stand-in for sending an email. Runs as a background task, after the response is sent."""
    logger.info("Order confirmation for order %s sent to %s", order_id, email)

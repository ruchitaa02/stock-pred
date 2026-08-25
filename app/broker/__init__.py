from app.broker.base import BrokerInterface
from app.broker.fyers_client import FyersClient
from app.broker.angel_client import AngelOneClient
from app.broker.mock_client import MockBrokerClient
from app.utils.config import Config
from app.utils.logger import logger

def get_broker_client() -> BrokerInterface:
    """Factory function returning the configured broker client instance."""
    broker_type = Config.BROKER.upper()
    logger.info(f"Initializing broker client: {broker_type}")

    if broker_type == "FYERS":
        client = FyersClient()
        if client.connect():
            return client
        logger.warning("Fyers connection failed. Falling back to MockBrokerClient.")
        
    elif broker_type == "ANGEL":
        client = AngelOneClient()
        if client.connect():
            return client
        logger.warning("Angel One connection failed. Falling back to MockBrokerClient.")

    # Default / Fallback: Mock Broker Client
    client = MockBrokerClient()
    client.connect()
    return client

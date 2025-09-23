import logging
from .base import BrokerBase

logger = logging.getLogger(__name__)

class OKXBroker(BrokerBase):
    name = "okx"

    def __init__(self, api_key: str = None, api_secret: str = None, passphrase: str = None, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.testnet = testnet

    async def place_order(self, symbol: str, side: str, quantity: float, price: float = None, order_type: str = "market"):
        logger.info(f"[OKX] place_order {symbol} {side} qty={quantity} type={order_type} price={price}")
        return {"status": "ok", "order_id": f"okx_{symbol}_123"}

    async def close_position(self, symbol: str):
        logger.info(f"[OKX] close_position {symbol}")
        return {"status": "ok"}

    async def get_balance(self):
        return {"total": 10000.0, "available": 9400.0}


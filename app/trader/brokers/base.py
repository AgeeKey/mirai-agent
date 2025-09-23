class BrokerBase:
    """Common interface for broker connectors"""

    name = "base"

    async def place_order(self, symbol: str, side: str, quantity: float, price: float = None, order_type: str = "market"):
        raise NotImplementedError

    async def close_position(self, symbol: str):
        raise NotImplementedError

    async def get_position(self, symbol: str):
        return None

    async def get_balance(self):
        return {"total": 0.0, "available": 0.0}


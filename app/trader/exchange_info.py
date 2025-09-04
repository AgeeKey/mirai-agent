"""
Exchange information and trading filters for Binance UMFutures
"""

import logging
from decimal import ROUND_DOWN, Decimal
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ExchangeInfo:
    """
    Manages exchange information and trading filters for Binance UMFutures
    Implements strict validation for tickSize, stepSize, and minQty
    """

    def __init__(self):
        # Default trading filters for common symbols (in real implementation, fetch from API)
        self.trading_filters = {
            "BTCUSDT": {
                "tickSize": "0.1",
                "stepSize": "0.001",
                "minQty": "0.001",
                "maxQty": "1000",
                "minNotional": "5",
            },
            "ETHUSDT": {
                "tickSize": "0.01",
                "stepSize": "0.001",
                "minQty": "0.001",
                "maxQty": "10000",
                "minNotional": "5",
            },
            "ADAUSDT": {
                "tickSize": "0.0001",
                "stepSize": "1",
                "minQty": "1",
                "maxQty": "9000000",
                "minNotional": "5",
            },
        }

    def get_symbol_filters(self, symbol: str) -> Dict[str, str]:
        """Get trading filters for a symbol"""
        if symbol not in self.trading_filters:
            # Use BTCUSDT defaults for unknown symbols
            logger.warning(f"No filters found for {symbol}, using BTCUSDT defaults")
            return self.trading_filters["BTCUSDT"].copy()

        return self.trading_filters[symbol].copy()

    def validate_price(self, symbol: str, price: float) -> float:
        """
        Validate and adjust price according to tickSize filter
        Uses strict rounding to avoid -1013 errors
        """
        filters = self.get_symbol_filters(symbol)
        tick_size = Decimal(filters["tickSize"])

        # Convert price to Decimal for precise calculation
        price_decimal = Decimal(str(price))

        # Use strict rounding to nearest tick to avoid precision errors
        # Round to nearest tick, then ensure it's properly formatted
        adjusted_price = (price_decimal / tick_size).quantize(
            Decimal("1"), rounding=ROUND_DOWN
        ) * tick_size

        result = float(adjusted_price)

        if result != price:
            logger.info(f"Price adjusted for {symbol}: {price} -> {result} (tickSize: {tick_size})")

        return result

    def validate_quantity(self, symbol: str, quantity: float) -> float:
        """
        Validate and adjust quantity according to stepSize and minQty filters
        Uses strict rounding to avoid -1013 errors
        """
        filters = self.get_symbol_filters(symbol)
        step_size = Decimal(filters["stepSize"])
        min_qty = Decimal(filters["minQty"])
        max_qty = Decimal(filters["maxQty"])

        # Convert quantity to Decimal for precise calculation
        qty_decimal = Decimal(str(quantity))

        # Check minimum quantity
        if qty_decimal < min_qty:
            logger.warning(f"Quantity {quantity} below minimum {min_qty} for {symbol}")
            qty_decimal = min_qty

        # Check maximum quantity
        if qty_decimal > max_qty:
            logger.warning(f"Quantity {quantity} above maximum {max_qty} for {symbol}")
            qty_decimal = max_qty

        # Use strict rounding to nearest step to avoid precision errors
        # Round down to nearest step
        adjusted_qty = (qty_decimal / step_size).quantize(
            Decimal("1"), rounding=ROUND_DOWN
        ) * step_size

        # Ensure we don't go below minimum after rounding
        if adjusted_qty < min_qty:
            adjusted_qty = min_qty

        result = float(adjusted_qty)

        if result != quantity:
            logger.info(
                f"Quantity adjusted for {symbol}: {quantity} -> {result} (stepSize: {step_size})"
            )

        return result

    def validate_notional(self, symbol: str, price: float, quantity: float) -> bool:
        """
        Validate that the notional value (price * quantity) meets minimum requirements
        """
        filters = self.get_symbol_filters(symbol)
        min_notional = Decimal(filters["minNotional"])

        notional = Decimal(str(price)) * Decimal(str(quantity))

        if notional < min_notional:
            logger.error(f"Order notional {notional} below minimum {min_notional} for {symbol}")
            return False

        return True

    def validate_order_params(
        self, symbol: str, quantity: float, price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Validate and adjust all order parameters according to exchange filters
        """
        # Validate and adjust quantity
        adjusted_quantity = self.validate_quantity(symbol, quantity)

        result = {"quantity": adjusted_quantity}

        # Validate and adjust price if provided
        if price is not None:
            adjusted_price = self.validate_price(symbol, price)
            result["price"] = adjusted_price

            # Validate notional value
            if not self.validate_notional(symbol, adjusted_price, adjusted_quantity):
                raise ValueError(f"Order does not meet minimum notional requirements for {symbol}")

        return result

    def get_lot_size_precision(self, symbol: str) -> int:
        """Get the precision for quantity (lot size) based on stepSize"""
        filters = self.get_symbol_filters(symbol)
        step_size = filters["stepSize"]

        # Count decimal places
        if "." in step_size:
            return len(step_size.split(".")[1])
        return 0

    def get_price_precision(self, symbol: str) -> int:
        """Get the precision for price based on tickSize"""
        filters = self.get_symbol_filters(symbol)
        tick_size = filters["tickSize"]

        # Count decimal places
        if "." in tick_size:
            return len(tick_size.split(".")[1])
        return 0

    def format_quantity(self, symbol: str, quantity: float) -> str:
        """Format quantity with correct precision"""
        precision = self.get_lot_size_precision(symbol)
        return f"{quantity:.{precision}f}"

    def format_price(self, symbol: str, price: float) -> str:
        """Format price with correct precision"""
        precision = self.get_price_precision(symbol)
        return f"{price:.{precision}f}"

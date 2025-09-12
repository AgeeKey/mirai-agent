"""
Order management with unified MARKET+SL/TP functionality
"""

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from .binance_client import BinanceClient
from .exchange_info import ExchangeInfo

logger = logging.getLogger(__name__)


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_MARKET = "STOP_MARKET"
    TAKE_PROFIT_MARKET = "TAKE_PROFIT_MARKET"


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"


class OrderManager:
    """
    Unified order management system for Binance UMFutures
    Supports MARKET orders with automatic SL/TP placement
    """

    def __init__(self, client: BinanceClient):
        self.client = client
        self.exchange_info = ExchangeInfo()
        self.active_orders = {}
        self.order_history = []

    def place_market_order_with_sltp(
        self,
        symbol: str,
        side: str,
        quantity: float,
        stop_loss_price: float | None = None,
        take_profit_price: float | None = None,
    ) -> dict[str, Any]:
        """
        Place a market order with automatic stop loss and take profit orders
        This is the unified MARKET+SL/TP functionality
        """
        logger.info(f"Placing market order with SL/TP: {side} {quantity} {symbol}")

        try:
            # Validate order parameters
            validated_params = self.exchange_info.validate_order_params(symbol, quantity)
            adjusted_quantity = validated_params["quantity"]

            # Place the main market order
            market_order = self.client.place_order(
                symbol=symbol, side=side, quantity=adjusted_quantity, order_type="MARKET"
            )

            order_result = {
                "main_order": market_order,
                "stop_loss_order": None,
                "take_profit_order": None,
                "status": "success",
            }

            # Store the order
            order_id = market_order.get("orderId", f"DRY_RUN_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}")
            self.active_orders[order_id] = {
                "symbol": symbol,
                "side": side,
                "quantity": adjusted_quantity,
                "type": "MARKET_WITH_SLTP",
                "timestamp": datetime.now(timezone.utc),
                "main_order": market_order,
            }

            # Place stop loss order if specified
            if stop_loss_price:
                try:
                    sl_order = self._place_stop_loss(symbol, side, adjusted_quantity, stop_loss_price)
                    order_result["stop_loss_order"] = sl_order
                    self.active_orders[order_id]["stop_loss_order"] = sl_order
                    logger.info(f"Stop loss order placed at {stop_loss_price}")
                except Exception as e:
                    logger.error(f"Failed to place stop loss: {str(e)}")
                    order_result["sl_error"] = str(e)

            # Place take profit order if specified
            if take_profit_price:
                try:
                    tp_order = self._place_take_profit(symbol, side, adjusted_quantity, take_profit_price)
                    order_result["take_profit_order"] = tp_order
                    self.active_orders[order_id]["take_profit_order"] = tp_order
                    logger.info(f"Take profit order placed at {take_profit_price}")
                except Exception as e:
                    logger.error(f"Failed to place take profit: {str(e)}")
                    order_result["tp_error"] = str(e)

            # Add to history
            self.order_history.append(order_result)

            return order_result

        except Exception as e:
            logger.error(f"Error placing market order with SL/TP: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "main_order": None,
                "stop_loss_order": None,
                "take_profit_order": None,
            }

    def _place_stop_loss(self, symbol: str, original_side: str, quantity: float, stop_price: float) -> dict[str, Any]:
        """Place a stop loss order"""
        # Stop loss side is opposite to original order
        sl_side = OrderSide.SELL.value if original_side == OrderSide.BUY.value else OrderSide.BUY.value

        # Validate stop price
        validated_params = self.exchange_info.validate_order_params(symbol, quantity, stop_price)
        adjusted_stop_price = validated_params["price"]

        return self.client.place_order(
            symbol=symbol,
            side=sl_side,
            quantity=quantity,
            order_type="STOP_MARKET",
            price=adjusted_stop_price,
        )

    def _place_take_profit(self, symbol: str, original_side: str, quantity: float, tp_price: float) -> dict[str, Any]:
        """Place a take profit order"""
        # Take profit side is opposite to original order
        tp_side = OrderSide.SELL.value if original_side == OrderSide.BUY.value else OrderSide.BUY.value

        # Validate take profit price
        validated_params = self.exchange_info.validate_order_params(symbol, quantity, tp_price)
        adjusted_tp_price = validated_params["price"]

        return self.client.place_order(
            symbol=symbol,
            side=tp_side,
            quantity=quantity,
            order_type="TAKE_PROFIT_MARKET",
            price=adjusted_tp_price,
        )

    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> dict[str, Any]:
        """Place a limit order"""
        logger.info(f"Placing limit order: {side} {quantity} {symbol} at {price}")

        try:
            # Validate parameters
            validated_params = self.exchange_info.validate_order_params(symbol, quantity, price)

            order = self.client.place_order(
                symbol=symbol,
                side=side,
                quantity=validated_params["quantity"],
                order_type="LIMIT",
                price=validated_params["price"],
            )

            # Store the order
            order_id = order.get("orderId", f"DRY_RUN_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}")
            self.active_orders[order_id] = {
                "symbol": symbol,
                "side": side,
                "quantity": validated_params["quantity"],
                "price": validated_params["price"],
                "type": "LIMIT",
                "timestamp": datetime.now(timezone.utc),
                "order": order,
            }

            self.order_history.append(order)
            return order

        except Exception as e:
            logger.error(f"Error placing limit order: {str(e)}")
            raise

    def cancel_order(self, symbol: str, order_id: str) -> dict[str, Any]:
        """Cancel an active order"""
        if self.client.dry_run:
            # Simulate order cancellation
            if order_id in self.active_orders:
                del self.active_orders[order_id]
                return {
                    "orderId": order_id,
                    "symbol": symbol,
                    "status": "CANCELED",
                    "dry_run": True,
                }
            else:
                raise ValueError(f"Order {order_id} not found")

        try:
            result = self.client.client.cancel_order(symbol=symbol, orderId=order_id)

            # Remove from active orders
            if order_id in self.active_orders:
                del self.active_orders[order_id]

            return result
        except Exception as e:
            logger.error(f"Error canceling order: {str(e)}")
            raise

    def get_order_status(self, symbol: str, order_id: str) -> dict[str, Any]:
        """Get the status of a specific order"""
        if self.client.dry_run:
            if order_id in self.active_orders:
                order_info = self.active_orders[order_id]
                return {
                    "orderId": order_id,
                    "symbol": symbol,
                    "status": "FILLED",  # Assume filled in dry run
                    "side": order_info["side"],
                    "quantity": order_info["quantity"],
                    "type": order_info["type"],
                    "dry_run": True,
                }
            else:
                raise ValueError(f"Order {order_id} not found")

        try:
            return self.client.client.query_order(symbol=symbol, orderId=order_id)
        except Exception as e:
            logger.error(f"Error querying order status: {str(e)}")
            raise

    def get_active_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        """Get all active orders, optionally filtered by symbol"""
        if symbol:
            return [order for order in self.active_orders.values() if order["symbol"] == symbol]
        return list(self.active_orders.values())

    def get_order_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get order history"""
        return self.order_history[-limit:]

    def calculate_position_size(
        self, symbol: str, risk_amount: float, entry_price: float, stop_loss_price: float
    ) -> float:
        """
        Calculate position size based on risk amount and stop loss distance
        """
        if entry_price <= 0 or stop_loss_price <= 0:
            raise ValueError("Entry price and stop loss price must be positive")

        # Calculate risk per unit
        risk_per_unit = abs(entry_price - stop_loss_price)

        if risk_per_unit == 0:
            raise ValueError("Stop loss price cannot equal entry price")

        # Calculate quantity
        raw_quantity = risk_amount / risk_per_unit

        # Validate and adjust quantity according to exchange filters
        validated_params = self.exchange_info.validate_order_params(symbol, raw_quantity)

        return validated_params["quantity"]

    def cancel_all_orders(self, symbol: str) -> dict[str, Any]:
        """Cancel all open orders for a symbol"""
        return self.client.cancel_all_orders(symbol)

    def close_position(self, symbol: str) -> dict[str, Any]:
        """Close open position with MARKET order (reduceOnly)"""
        return self.client.close_position(symbol)

    def sanity_trade(self, symbol: str = "BTCUSDT") -> dict[str, Any]:
        """
        Place a sanity trade: tiny MARKET order with SL and TP
        Normalized to filters (tickSize/stepSize/minQty)
        """
        logger.info(f"Executing sanity trade for {symbol}")

        try:
            # Get current market data for price reference
            market_data = self.client.get_market_data(symbol)
            current_price = market_data["price"]

            # Use minimum quantity for sanity trade
            filters = self.exchange_info.get_symbol_filters(symbol)
            min_qty = float(filters["minQty"])

            # Calculate SL and TP prices (small spread for safety)
            stop_loss_price = current_price * 0.99  # 1% below current price
            take_profit_price = current_price * 1.01  # 1% above current price

            # Place market order with SL/TP
            result = self.place_market_order_with_sltp(
                symbol=symbol,
                side="BUY",  # Always buy for sanity test
                quantity=min_qty,
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price,
            )

            logger.info(f"Sanity trade completed for {symbol}")
            return result

        except Exception as e:
            logger.error(f"Error in sanity trade for {symbol}: {str(e)}")
            raise


def validate_and_round_qty(symbol: str, qty: float, sl_distance: float, margin: float, leverage: float) -> float:
    """
    Position sizing validator - validates and rounds quantity based on constraints

    Args:
        symbol: Trading symbol (e.g. 'BTCUSDT')
        qty: Desired quantity
        sl_distance: Stop loss distance (price difference)
        margin: Available margin
        leverage: Leverage multiplier

    Returns:
        Safe quantity or raises ValueError if below minimum

    Raises:
        ValueError: If quantity is below exchange minimums
    """
    try:
        # Initialize exchange info to get filters
        exchange_info = ExchangeInfo()

        # Get exchange filters
        filters = exchange_info.get_symbol_filters(symbol)
        min_qty = float(filters["minQty"])
        min_notional = float(filters["minNotional"])

        # Calculate quantity by stop loss (risk-based sizing)
        if sl_distance > 0:
            qty_by_stop = margin / sl_distance  # Risk-based position size
        else:
            qty_by_stop = qty

        # Calculate quantity by margin (margin-based sizing)
        qty_by_margin = margin * leverage

        # Take minimum of both constraints
        safe_qty = min(qty, qty_by_stop, qty_by_margin)

        # Check if quantity meets minimum requirements BEFORE rounding
        if safe_qty < min_qty:
            raise ValueError(f"Quantity {safe_qty} below minQty {min_qty} for {symbol}")

        # Round to exchange step size
        validated_qty = exchange_info.validate_quantity(symbol, safe_qty)

        # Check notional value (assuming current price from exchange info)
        # For this validator, we'll use a mock price since we don't have real-time data
        mock_price = 50000.0  # Mock price for validation
        notional = validated_qty * mock_price

        if notional < min_notional:
            raise ValueError(f"Notional value {notional} below minNotional {min_notional} for {symbol}")

        logger.info(f"Position size validated for {symbol}: {qty} -> {validated_qty}")
        return validated_qty

    except Exception as e:
        logger.error(f"Position sizing validation failed for {symbol}: {str(e)}")
        raise

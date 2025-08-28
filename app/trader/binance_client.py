"""
Binance UMFutures client with DRY_RUN mode support
"""
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from binance.um_futures import UMFutures
    from binance.error import ClientError, ServerError
except ImportError:
    # Fallback for when binance-connector is not installed
    UMFutures = None
    ClientError = Exception
    ServerError = Exception

from .exchange_info import ExchangeInfo


logger = logging.getLogger(__name__)


class BinanceClient:
    """
    Binance UMFutures client with dry-run mode and risk management
    """
    
    def __init__(self, dry_run: bool = True, testnet: bool = True):
        self.dry_run = dry_run
        self.testnet = testnet
        self.exchange_info = ExchangeInfo()
        
        # Get API credentials from environment
        self.api_key = os.getenv('BINANCE_API_KEY', '')
        self.secret_key = os.getenv('BINANCE_SECRET_KEY', '')
        
        # Initialize client if not in dry run mode and credentials are available
        self.client = None
        if not dry_run and self.api_key and self.secret_key:
            try:
                if UMFutures:
                    base_url = "https://testnet.binancefuture.com" if testnet else None
                    self.client = UMFutures(
                        key=self.api_key,
                        secret=self.secret_key,
                        base_url=base_url
                    )
                    logger.info(f"Initialized Binance client (testnet={testnet})")
                else:
                    logger.warning("binance-connector not available, running in simulation mode")
            except Exception as e:
                logger.error(f"Failed to initialize Binance client: {str(e)}")
        else:
            logger.info("Running in dry-run mode")
    
    def test_connection(self) -> bool:
        """Test connection to Binance API"""
        if self.dry_run:
            logger.info("Dry-run mode: simulating successful connection")
            return True
        
        if not self.client:
            logger.error("Client not initialized")
            return False
        
        try:
            self.client.ping()
            logger.info("Binance connection test successful")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get current market data for symbol"""
        if self.dry_run:
            # Return simulated market data
            import random
            base_price = 45000 if symbol == 'BTCUSDT' else 3000
            current_price = base_price * (1 + random.uniform(-0.05, 0.05))
            
            return {
                'symbol': symbol,
                'price': round(current_price, 2),
                'volume': round(random.uniform(1000, 50000), 2),
                'change_24h': round(random.uniform(-0.1, 0.1), 4),
                'timestamp': datetime.utcnow().isoformat()
            }
        
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        try:
            # Get 24hr ticker statistics
            ticker = self.client.ticker_24hr_price_change_statistics(symbol=symbol)
            
            return {
                'symbol': symbol,
                'price': float(ticker['lastPrice']),
                'volume': float(ticker['volume']),
                'change_24h': float(ticker['priceChangePercent']) / 100,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")
            raise
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        if self.dry_run:
            return {
                'totalWalletBalance': '10000.00',
                'totalUnrealizedProfit': '0.00',
                'totalMarginBalance': '10000.00',
                'totalPositionInitialMargin': '0.00',
                'maxWithdrawAmount': '10000.00'
            }
        
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        try:
            return self.client.account()
        except Exception as e:
            logger.error(f"Error fetching account info: {str(e)}")
            raise
    
    def place_order(self, symbol: str, side: str, quantity: float, 
                   order_type: str = 'MARKET', price: Optional[float] = None,
                   stop_loss: Optional[float] = None, 
                   take_profit: Optional[float] = None) -> Dict[str, Any]:
        """
        Place an order with proper filters and risk management
        """
        logger.info(f"Placing {order_type} {side} order for {symbol}: {quantity}")
        
        # Validate and adjust order parameters using exchange info
        try:
            adjusted_params = self.exchange_info.validate_order_params(
                symbol, quantity, price
            )
            quantity = adjusted_params['quantity']
            if price:
                price = adjusted_params['price']
        except Exception as e:
            logger.error(f"Order validation failed: {str(e)}")
            raise
        
        if self.dry_run:
            # Simulate order execution
            order_id = f"DRY_RUN_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            result = {
                'orderId': order_id,
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': quantity,
                'status': 'FILLED',
                'price': price or 'MARKET',
                'timestamp': datetime.utcnow().isoformat(),
                'dry_run': True
            }
            
            # Add stop loss and take profit if specified
            if stop_loss:
                result['stop_loss'] = stop_loss
            if take_profit:
                result['take_profit'] = take_profit
            
            logger.info(f"Dry-run order simulated: {result}")
            return result
        
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        try:
            # Prepare order parameters
            params = {
                'symbol': symbol,
                'side': side,
                'type': order_type,
                'quantity': quantity
            }
            
            if order_type == 'LIMIT':
                if not price:
                    raise ValueError("Price required for LIMIT orders")
                params['price'] = price
                params['timeInForce'] = 'GTC'
            
            # Place the main order
            result = self.client.new_order(**params)
            
            # Place stop loss and take profit orders if specified
            if stop_loss or take_profit:
                self._place_conditional_orders(symbol, side, quantity, stop_loss, take_profit)
            
            logger.info(f"Order placed successfully: {result['orderId']}")
            return result
            
        except (ClientError, ServerError) as e:
            logger.error(f"Binance API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            raise
    
    def _place_conditional_orders(self, symbol: str, side: str, quantity: float,
                                stop_loss: Optional[float] = None,
                                take_profit: Optional[float] = None):
        """Place stop loss and take profit orders"""
        if not self.client:
            return
        
        try:
            if stop_loss:
                # Place stop loss order
                sl_side = 'SELL' if side == 'BUY' else 'BUY'
                self.client.new_order(
                    symbol=symbol,
                    side=sl_side,
                    type='STOP_MARKET',
                    quantity=quantity,
                    stopPrice=stop_loss
                )
                logger.info(f"Stop loss order placed at {stop_loss}")
            
            if take_profit:
                # Place take profit order
                tp_side = 'SELL' if side == 'BUY' else 'BUY'
                self.client.new_order(
                    symbol=symbol,
                    side=tp_side,
                    type='TAKE_PROFIT_MARKET',
                    quantity=quantity,
                    stopPrice=take_profit
                )
                logger.info(f"Take profit order placed at {take_profit}")
                
        except Exception as e:
            logger.error(f"Error placing conditional orders: {str(e)}")
    
    def get_open_positions(self) -> list:
        """Get all open positions"""
        if self.dry_run:
            return []  # No positions in dry run mode
        
        if not self.client:
            raise RuntimeError("Client not initialized")
        
        try:
            positions = self.client.account()['positions']
            return [pos for pos in positions if float(pos['positionAmt']) != 0]
        except Exception as e:
            logger.error(f"Error fetching positions: {str(e)}")
            raise
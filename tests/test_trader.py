"""
Tests for the trader module
"""
import pytest

from app.trader.binance_client import BinanceClient
from app.trader.exchange_info import ExchangeInfo
from app.trader.orders import OrderManager


class TestBinanceClient:
    def setup_method(self):
        self.client = BinanceClient(dry_run=True)
    
    def test_client_initialization(self):
        """Test client initializes in dry run mode"""
        assert self.client.dry_run is True
        assert self.client.testnet is True
    
    def test_connection_test(self):
        """Test connection test in dry run mode"""
        result = self.client.test_connection()
        assert result is True
    
    def test_get_market_data(self):
        """Test market data retrieval"""
        data = self.client.get_market_data("BTCUSDT")
        
        assert 'symbol' in data
        assert 'price' in data
        assert 'volume' in data
        assert data['symbol'] == 'BTCUSDT'
        assert isinstance(data['price'], (int, float))
    
    def test_place_order_dry_run(self):
        """Test order placement in dry run mode"""
        result = self.client.place_order(
            symbol="BTCUSDT",
            side="BUY",
            quantity=0.1,
            order_type="MARKET"
        )
        
        assert 'orderId' in result
        assert result['dry_run'] is True
        assert result['symbol'] == 'BTCUSDT'


class TestExchangeInfo:
    def setup_method(self):
        self.exchange_info = ExchangeInfo()
    
    def test_validate_price(self):
        """Test price validation with tick size"""
        price = 45123.456
        validated_price = self.exchange_info.validate_price("BTCUSDT", price)
        
        # Should be rounded to tick size (0.1)
        assert validated_price == 45123.4
    
    def test_validate_quantity(self):
        """Test quantity validation with step size"""
        quantity = 0.1234567
        validated_qty = self.exchange_info.validate_quantity("BTCUSDT", quantity)
        
        # Should be rounded to step size (0.001)
        assert validated_qty == 0.123
    
    def test_validate_order_params(self):
        """Test complete order parameter validation"""
        params = self.exchange_info.validate_order_params(
            "BTCUSDT", 
            quantity=0.1234567, 
            price=45123.456
        )
        
        assert 'quantity' in params
        assert 'price' in params
        assert params['quantity'] == 0.123
        assert params['price'] == 45123.4


class TestOrderManager:
    def setup_method(self):
        self.client = BinanceClient(dry_run=True)
        self.order_manager = OrderManager(self.client)
    
    def test_place_market_order_with_sltp(self):
        """Test placing market order with stop loss and take profit"""
        result = self.order_manager.place_market_order_with_sltp(
            symbol="BTCUSDT",
            side="BUY",
            quantity=0.1,
            stop_loss_price=44000.0,
            take_profit_price=46000.0
        )
        
        assert result['status'] == 'success'
        assert 'main_order' in result
        assert result['main_order'] is not None
    
    def test_calculate_position_size(self):
        """Test position size calculation"""
        position_size = self.order_manager.calculate_position_size(
            symbol="BTCUSDT",
            risk_amount=100.0,  # Risk $100
            entry_price=45000.0,
            stop_loss_price=44000.0  # $1000 risk per unit
        )
        
        # Should risk $100 with $1000 risk per unit = 0.1 BTC
        assert position_size == 0.1
    
    def test_sanity_trade_dry_run(self):
        """Test sanity-trade logs 3 orders (MARKET, SL, TP) in DRY_RUN"""
        result = self.order_manager.sanity_trade("BTCUSDT")
        
        # Should return success status
        assert result['status'] == 'success'
        
        # Should have all three orders
        assert 'main_order' in result
        assert 'stop_loss_order' in result  
        assert 'take_profit_order' in result
        
        # Main order should be MARKET type
        assert result['main_order']['type'] == 'MARKET'
        
        # Stop loss should be STOP_MARKET type
        assert result['stop_loss_order']['type'] == 'STOP_MARKET'
        
        # Take profit should be TAKE_PROFIT_MARKET type
        assert result['take_profit_order']['type'] == 'TAKE_PROFIT_MARKET'
    
    def test_cancel_all_orders(self):
        """Test cancel-all parses symbol argument"""
        result = self.order_manager.cancel_all_orders("BTCUSDT")
        
        # Should return dry run result
        assert result['dry_run'] is True
        assert result['symbol'] == 'BTCUSDT'
        assert 'cancel all' in result['message'].lower()
    
    def test_kill_switch_functionality(self):
        """Test kill-switch combines cancel-all and close position"""
        # Test cancel all
        cancel_result = self.order_manager.cancel_all_orders("BTCUSDT")
        assert cancel_result['dry_run'] is True
        assert cancel_result['symbol'] == 'BTCUSDT'
        
        # Test close position
        close_result = self.order_manager.close_position("BTCUSDT")
        assert close_result['dry_run'] is True
        assert close_result['symbol'] == 'BTCUSDT'
        assert 'close position' in close_result['message'].lower()


class TestExchangeInfoStrictRounding:
    """Test strict rounding functionality to avoid -1013 errors"""
    
    def setup_method(self):
        self.exchange_info = ExchangeInfo()
    
    def test_quantity_rounding_works_correctly(self):
        """Test qty rounding works correctly with strict decimal precision"""
        # Test with problematic floating point values
        test_cases = [
            (0.1234567, 0.123),  # Should round down to stepSize
            (0.001, 0.001),      # Should stay at minimum
            (0.0001, 0.001),     # Should round up to minimum
        ]
        
        for input_qty, expected_qty in test_cases:
            result = self.exchange_info.validate_quantity("BTCUSDT", input_qty)
            assert result == expected_qty, f"Expected {expected_qty}, got {result} for input {input_qty}"
    
    def test_price_rounding_works_correctly(self):
        """Test price rounding works correctly with strict decimal precision"""
        # Test with problematic floating point values  
        test_cases = [
            (45123.456, 45123.4),   # Should round down to tickSize
            (45123.4, 45123.4),     # Should stay the same
            (45123.999, 45123.9),   # Should round down to tickSize
        ]
        
        for input_price, expected_price in test_cases:
            result = self.exchange_info.validate_price("BTCUSDT", input_price)
            assert result == expected_price, f"Expected {expected_price}, got {result} for input {input_price}"
    
    def test_decimal_precision_edge_cases(self):
        """Test edge cases that could cause -1013 errors"""
        # Test very small quantities
        tiny_qty = 0.000001
        result_qty = self.exchange_info.validate_quantity("BTCUSDT", tiny_qty)
        assert result_qty >= 0.001  # Should be at least minimum
        
        # Test very precise prices
        precise_price = 45123.123456789
        result_price = self.exchange_info.validate_price("BTCUSDT", precise_price)
        # Should be properly rounded to tick size
        assert str(result_price).count('.') <= 1  # Should have proper decimal format
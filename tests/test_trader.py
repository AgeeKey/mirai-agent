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
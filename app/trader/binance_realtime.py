"""
Enhanced Binance API integration with WebSocket support and real-time data
"""

import asyncio
import json
import logging
import os
import websockets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
import threading
from queue import Queue

from .binance_client import BinanceClient

logger = logging.getLogger(__name__)

@dataclass
class MarketTicker:
    """Market ticker data structure"""
    symbol: str
    price: float
    change_24h: float
    change_percent_24h: float
    volume_24h: float
    high_24h: float
    low_24h: float
    open_price: float
    close_price: float
    timestamp: str

@dataclass
class OrderBookData:
    """Order book data structure"""
    symbol: str
    bids: List[tuple[float, float]]  # [(price, quantity), ...]
    asks: List[tuple[float, float]]  # [(price, quantity), ...]
    timestamp: str

@dataclass
class KlineData:
    """Kline/Candlestick data structure"""
    symbol: str
    open_time: int
    close_time: int
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    kline_close_time: int
    quote_asset_volume: float
    number_of_trades: int
    taker_buy_base_asset_volume: float
    taker_buy_quote_asset_volume: float

class BinanceDataStream:
    """
    Real-time data streaming from Binance WebSocket
    """
    
    def __init__(self, testnet: bool = True, dry_run: bool = True):
        self.testnet = testnet
        self.dry_run = dry_run
        self.base_url = "wss://stream.binancefuture.com/ws/" if not testnet else "wss://stream.binancefuture.com/ws/"
        self.ws = None
        self.running = False
        self.callbacks = {}
        self.subscriptions = set()
        
        # Threading for WebSocket management
        self.ws_thread = None
        self.event_loop = None
        
    def add_ticker_callback(self, callback: Callable[[MarketTicker], None]):
        """Add callback for ticker updates"""
        self.callbacks['ticker'] = callback
        
    def add_orderbook_callback(self, callback: Callable[[OrderBookData], None]):
        """Add callback for order book updates"""
        self.callbacks['orderbook'] = callback
        
    def add_kline_callback(self, callback: Callable[[KlineData], None]):
        """Add callback for kline updates"""
        self.callbacks['kline'] = callback
    
    def subscribe_ticker(self, symbol: str):
        """Subscribe to ticker updates for symbol"""
        stream = f"{symbol.lower()}@ticker"
        self.subscriptions.add(stream)
        
    def subscribe_orderbook(self, symbol: str, levels: int = 5):
        """Subscribe to order book updates"""
        stream = f"{symbol.lower()}@depth{levels}"
        self.subscriptions.add(stream)
        
    def subscribe_kline(self, symbol: str, interval: str = "1m"):
        """Subscribe to kline updates"""
        stream = f"{symbol.lower()}@kline_{interval}"
        self.subscriptions.add(stream)
    
    def start(self):
        """Start WebSocket connection in a separate thread"""
        if self.dry_run:
            logger.info("Dry-run mode: Starting simulated data stream")
            self.start_simulation()
            return
            
        if self.running:
            logger.warning("Data stream already running")
            return
            
        self.running = True
        self.ws_thread = threading.Thread(target=self._run_websocket)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        logger.info("Started Binance data stream")
    
    def stop(self):
        """Stop WebSocket connection"""
        self.running = False
        if self.ws:
            asyncio.run_coroutine_threadsafe(self.ws.close(), self.event_loop)
        if self.ws_thread:
            self.ws_thread.join(timeout=5)
        logger.info("Stopped Binance data stream")
    
    def _run_websocket(self):
        """Run WebSocket in asyncio event loop"""
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        self.event_loop.run_until_complete(self._websocket_handler())
    
    async def _websocket_handler(self):
        """Handle WebSocket connection and messages"""
        if not self.subscriptions:
            logger.warning("No subscriptions, nothing to stream")
            return
            
        # Build WebSocket URL with streams
        streams = '/'.join(self.subscriptions)
        url = f"{self.base_url}{streams}"
        
        try:
            async with websockets.connect(url) as websocket:
                self.ws = websocket
                logger.info(f"Connected to Binance WebSocket: {url}")
                
                while self.running:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        await self._handle_message(json.loads(message))
                    except asyncio.TimeoutError:
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        logger.warning("WebSocket connection closed")
                        break
                    except Exception as e:
                        logger.error(f"WebSocket error: {e}")
                        break
                        
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
    
    async def _handle_message(self, data: dict):
        """Handle incoming WebSocket message"""
        try:
            if 'stream' in data and 'data' in data:
                stream = data['stream']
                message_data = data['data']
                
                if '@ticker' in stream:
                    await self._handle_ticker_data(message_data)
                elif '@depth' in stream:
                    await self._handle_orderbook_data(message_data)
                elif '@kline' in stream:
                    await self._handle_kline_data(message_data)
                    
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def _handle_ticker_data(self, data: dict):
        """Handle ticker data"""
        try:
            ticker = MarketTicker(
                symbol=data['s'],
                price=float(data['c']),
                change_24h=float(data['P']),
                change_percent_24h=float(data['P']),
                volume_24h=float(data['v']),
                high_24h=float(data['h']),
                low_24h=float(data['l']),
                open_price=float(data['o']),
                close_price=float(data['c']),
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            
            if 'ticker' in self.callbacks:
                self.callbacks['ticker'](ticker)
                
        except Exception as e:
            logger.error(f"Error processing ticker data: {e}")
    
    async def _handle_orderbook_data(self, data: dict):
        """Handle order book data"""
        try:
            orderbook = OrderBookData(
                symbol=data['s'],
                bids=[(float(bid[0]), float(bid[1])) for bid in data['b']],
                asks=[(float(ask[0]), float(ask[1])) for ask in data['a']],
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            
            if 'orderbook' in self.callbacks:
                self.callbacks['orderbook'](orderbook)
                
        except Exception as e:
            logger.error(f"Error processing orderbook data: {e}")
    
    async def _handle_kline_data(self, data: dict):
        """Handle kline data"""
        try:
            kline_data = data['k']
            kline = KlineData(
                symbol=kline_data['s'],
                open_time=kline_data['t'],
                close_time=kline_data['T'],
                open_price=float(kline_data['o']),
                high_price=float(kline_data['h']),
                low_price=float(kline_data['l']),
                close_price=float(kline_data['c']),
                volume=float(kline_data['v']),
                kline_close_time=kline_data['T'],
                quote_asset_volume=float(kline_data['q']),
                number_of_trades=kline_data['n'],
                taker_buy_base_asset_volume=float(kline_data['V']),
                taker_buy_quote_asset_volume=float(kline_data['Q'])
            )
            
            if 'kline' in self.callbacks:
                self.callbacks['kline'](kline)
                
        except Exception as e:
            logger.error(f"Error processing kline data: {e}")
    
    def start_simulation(self):
        """Start simulation mode with fake data"""
        import random
        import time
        
        def simulate_data():
            symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT']
            
            while self.running:
                for symbol in symbols:
                    # Simulate ticker data
                    if 'ticker' in self.callbacks:
                        base_price = 45000 if symbol == 'BTCUSDT' else 3000 if symbol == 'ETHUSDT' else 1.5
                        price = base_price * (1 + random.uniform(-0.02, 0.02))
                        change = random.uniform(-5, 5)
                        
                        ticker = MarketTicker(
                            symbol=symbol,
                            price=price,
                            change_24h=change,
                            change_percent_24h=change,
                            volume_24h=random.uniform(10000, 100000),
                            high_24h=price * 1.05,
                            low_24h=price * 0.95,
                            open_price=price * 0.98,
                            close_price=price,
                            timestamp=datetime.now(timezone.utc).isoformat()
                        )
                        
                        try:
                            self.callbacks['ticker'](ticker)
                        except Exception as e:
                            logger.error(f"Simulation callback error: {e}")
                
                time.sleep(1)  # Update every second
        
        self.running = True
        self.ws_thread = threading.Thread(target=simulate_data)
        self.ws_thread.daemon = True
        self.ws_thread.start()

class EnhancedBinanceClient(BinanceClient):
    """
    Enhanced Binance client with real-time data streaming
    """
    
    def __init__(self, dry_run: bool = True, testnet: bool = True):
        super().__init__(dry_run, testnet)
        self.data_stream = BinanceDataStream(testnet, dry_run)
        
    def start_realtime_data(self, symbols: List[str], 
                           ticker_callback: Optional[Callable] = None,
                           orderbook_callback: Optional[Callable] = None,
                           kline_callback: Optional[Callable] = None):
        """Start real-time data streaming for symbols"""
        
        if ticker_callback:
            self.data_stream.add_ticker_callback(ticker_callback)
            
        if orderbook_callback:
            self.data_stream.add_orderbook_callback(orderbook_callback)
            
        if kline_callback:
            self.data_stream.add_kline_callback(kline_callback)
        
        # Subscribe to all symbols
        for symbol in symbols:
            self.data_stream.subscribe_ticker(symbol)
            if orderbook_callback:
                self.data_stream.subscribe_orderbook(symbol)
            if kline_callback:
                self.data_stream.subscribe_kline(symbol)
        
        self.data_stream.start()
        logger.info(f"Started real-time data for symbols: {symbols}")
    
    def stop_realtime_data(self):
        """Stop real-time data streaming"""
        self.data_stream.stop()
    
    def get_historical_klines(self, symbol: str, interval: str, 
                             start_time: Optional[str] = None,
                             end_time: Optional[str] = None,
                             limit: int = 500) -> List[KlineData]:
        """Get historical kline data"""
        if self.dry_run:
            # Return simulated historical data
            import random
            klines = []
            base_price = 45000 if symbol == 'BTCUSDT' else 3000
            
            for i in range(limit):
                timestamp = int(datetime.now().timestamp() * 1000) - (i * 60000)  # 1 minute intervals
                open_price = base_price * (1 + random.uniform(-0.1, 0.1))
                high_price = open_price * (1 + random.uniform(0, 0.05))
                low_price = open_price * (1 - random.uniform(0, 0.05))
                close_price = open_price * (1 + random.uniform(-0.03, 0.03))
                
                klines.append(KlineData(
                    symbol=symbol,
                    open_time=timestamp,
                    close_time=timestamp + 60000,
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    volume=random.uniform(100, 1000),
                    kline_close_time=timestamp + 60000,
                    quote_asset_volume=random.uniform(10000, 100000),
                    number_of_trades=random.randint(50, 500),
                    taker_buy_base_asset_volume=random.uniform(50, 500),
                    taker_buy_quote_asset_volume=random.uniform(5000, 50000)
                ))
            
            return klines[::-1]  # Reverse to get chronological order
        
        if not self.client:
            raise RuntimeError("Client not initialized")
            
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            if start_time:
                params['startTime'] = start_time
            if end_time:
                params['endTime'] = end_time
                
            klines_data = self.client.klines(**params)
            
            klines = []
            for kline in klines_data:
                klines.append(KlineData(
                    symbol=symbol,
                    open_time=int(kline[0]),
                    close_time=int(kline[6]),
                    open_price=float(kline[1]),
                    high_price=float(kline[2]),
                    low_price=float(kline[3]),
                    close_price=float(kline[4]),
                    volume=float(kline[5]),
                    kline_close_time=int(kline[6]),
                    quote_asset_volume=float(kline[7]),
                    number_of_trades=int(kline[8]),
                    taker_buy_base_asset_volume=float(kline[9]),
                    taker_buy_quote_asset_volume=float(kline[10])
                ))
            
            return klines
            
        except Exception as e:
            logger.error(f"Error fetching historical klines: {e}")
            raise
    
    def get_multiple_market_data(self, symbols: List[str]) -> Dict[str, MarketTicker]:
        """Get market data for multiple symbols"""
        market_data = {}
        
        for symbol in symbols:
            try:
                data = self.get_market_data(symbol)
                market_data[symbol] = MarketTicker(
                    symbol=symbol,
                    price=data['price'],
                    change_24h=data['change_24h'],
                    change_percent_24h=data['change_24h'],
                    volume_24h=data['volume'],
                    high_24h=data['price'] * 1.05,  # Approximate
                    low_24h=data['price'] * 0.95,   # Approximate
                    open_price=data['price'] * 0.99, # Approximate
                    close_price=data['price'],
                    timestamp=data['timestamp']
                )
            except Exception as e:
                logger.error(f"Failed to get market data for {symbol}: {e}")
                
        return market_data
    
    def to_dict(self, data_obj) -> dict:
        """Convert dataclass to dictionary for JSON serialization"""
        if hasattr(data_obj, '__dict__'):
            return asdict(data_obj)
        return data_obj
"""
Mirai Agent - Unified Broker Connectors (Day 4)
Универсальный интерфейс для подключения к различным брокерам
"""
import asyncio
import logging
import json
import time
import hmac
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from abc import ABC, abstractmethod
import aiohttp
import websockets
import sys
import os

# Добавляем пути для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrokerType(Enum):
    """Типы поддерживаемых брокеров"""
    BINANCE = "binance"
    BYBIT = "bybit"
    OKX = "okx"
    KRAKEN = "kraken"
    COINBASE = "coinbase"
    MOCK = "mock"  # Для тестирования

class OrderType(Enum):
    """Типы ордеров"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    STOP_LIMIT = "stop_limit"

class OrderSide(Enum):
    """Сторона ордера"""
    BUY = "buy"
    SELL = "sell"

class OrderStatus(Enum):
    """Статус ордера"""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"

@dataclass
class BrokerCredentials:
    """Учетные данные брокера"""
    api_key: str
    api_secret: str
    passphrase: Optional[str] = None
    testnet: bool = True
    subaccount: Optional[str] = None

@dataclass
class MarketData:
    """Рыночные данные"""
    symbol: str
    price: float
    bid: float
    ask: float
    volume_24h: float
    change_24h: float
    timestamp: datetime
    
@dataclass
class Order:
    """Ордер"""
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "GTC"  # Good Till Cancelled
    client_order_id: Optional[str] = None
    
    # Заполненные поля после размещения
    order_id: Optional[str] = None
    status: Optional[OrderStatus] = None
    filled_quantity: float = 0.0
    avg_fill_price: Optional[float] = None
    commission: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Position:
    """Позиция"""
    symbol: str
    side: str  # "long" or "short"
    size: float
    entry_price: float
    mark_price: float
    unrealized_pnl: float
    percentage: float
    margin: float
    timestamp: datetime

@dataclass
class Balance:
    """Баланс"""
    asset: str
    free: float
    locked: float
    total: float

class BrokerConnector(ABC):
    """Абстрактный базовый класс для брокерских коннекторов"""
    
    def __init__(self, credentials: BrokerCredentials):
        self.credentials = credentials
        self.connected = False
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws_connection: Optional[websockets.WebSocketServerProtocol] = None
        self.rate_limiter = {}
        
        # Колбэки для событий
        self.on_order_update: Optional[Callable] = None
        self.on_balance_update: Optional[Callable] = None
        self.on_position_update: Optional[Callable] = None
        self.on_market_data: Optional[Callable] = None
        
    @abstractmethod
    async def connect(self) -> bool:
        """Подключение к брокеру"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Отключение от брокера"""
        pass
    
    @abstractmethod
    async def get_account_info(self) -> Dict:
        """Получение информации об аккаунте"""
        pass
    
    @abstractmethod
    async def get_balances(self) -> List[Balance]:
        """Получение балансов"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Получение открытых позиций"""
        pass
    
    @abstractmethod
    async def place_order(self, order: Order) -> Order:
        """Размещение ордера"""
        pass
    
    @abstractmethod
    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Отмена ордера"""
        pass
    
    @abstractmethod
    async def get_order(self, symbol: str, order_id: str) -> Order:
        """Получение информации об ордере"""
        pass
    
    @abstractmethod
    async def get_market_data(self, symbol: str) -> MarketData:
        """Получение рыночных данных"""
        pass
    
    @abstractmethod
    async def subscribe_to_updates(self):
        """Подписка на обновления через WebSocket"""
        pass
    
    def _generate_signature(self, message: str) -> str:
        """Генерация подписи для аутентификации"""
        return hmac.new(
            self.credentials.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
    
    async def _rate_limit(self, endpoint: str, limit: int, window: int):
        """Ограничение скорости запросов"""
        now = time.time()
        if endpoint not in self.rate_limiter:
            self.rate_limiter[endpoint] = []
        
        # Очищаем старые запросы
        self.rate_limiter[endpoint] = [
            req_time for req_time in self.rate_limiter[endpoint]
            if now - req_time < window
        ]
        
        # Проверяем лимит
        if len(self.rate_limiter[endpoint]) >= limit:
            sleep_time = window - (now - self.rate_limiter[endpoint][0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        self.rate_limiter[endpoint].append(now)

class BinanceConnector(BrokerConnector):
    """Коннектор для Binance"""
    
    def __init__(self, credentials: BrokerCredentials):
        super().__init__(credentials)
        self.base_url = "https://testnet.binancefuture.com" if credentials.testnet else "https://fapi.binance.com"
        self.ws_url = "wss://stream.binancefuture.com/ws" if credentials.testnet else "wss://fstream.binance.com/ws"
        
    async def connect(self) -> bool:
        """Подключение к Binance"""
        try:
            self.session = aiohttp.ClientSession()
            
            # Проверяем подключение
            account_info = await self.get_account_info()
            self.connected = True
            logger.info("Успешно подключен к Binance")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка подключения к Binance: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Отключение от Binance"""
        if self.session:
            await self.session.close()
        if self.ws_connection:
            await self.ws_connection.close()
        self.connected = False
        logger.info("Отключен от Binance")
    
    async def get_account_info(self) -> Dict:
        """Получение информации об аккаунте Binance"""
        await self._rate_limit("account", 5, 60)  # 5 запросов в минуту
        
        timestamp = int(time.time() * 1000)
        params = f"timestamp={timestamp}"
        signature = self._generate_signature(params)
        
        url = f"{self.base_url}/fapi/v2/account"
        headers = {"X-MBX-APIKEY": self.credentials.api_key}
        params_with_sig = f"{params}&signature={signature}"
        
        async with self.session.get(f"{url}?{params_with_sig}", headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(f"Binance API error: {response.status} - {error_text}")
    
    async def get_balances(self) -> List[Balance]:
        """Получение балансов Binance"""
        account_info = await self.get_account_info()
        balances = []
        
        for asset_info in account_info.get("assets", []):
            balance = Balance(
                asset=asset_info["asset"],
                free=float(asset_info["availableBalance"]),
                locked=float(asset_info["initialMargin"]),
                total=float(asset_info["marginBalance"])
            )
            balances.append(balance)
        
        return balances
    
    async def get_positions(self) -> List[Position]:
        """Получение позиций Binance"""
        await self._rate_limit("positions", 5, 60)
        
        timestamp = int(time.time() * 1000)
        params = f"timestamp={timestamp}"
        signature = self._generate_signature(params)
        
        url = f"{self.base_url}/fapi/v2/positionRisk"
        headers = {"X-MBX-APIKEY": self.credentials.api_key}
        params_with_sig = f"{params}&signature={signature}"
        
        positions = []
        async with self.session.get(f"{url}?{params_with_sig}", headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                for pos_data in data:
                    if float(pos_data["positionAmt"]) != 0:
                        position = Position(
                            symbol=pos_data["symbol"],
                            side="long" if float(pos_data["positionAmt"]) > 0 else "short",
                            size=abs(float(pos_data["positionAmt"])),
                            entry_price=float(pos_data["entryPrice"]),
                            mark_price=float(pos_data["markPrice"]),
                            unrealized_pnl=float(pos_data["unRealizedProfit"]),
                            percentage=float(pos_data["percentage"]),
                            margin=float(pos_data["isolatedMargin"]),
                            timestamp=datetime.now()
                        )
                        positions.append(position)
            else:
                error_text = await response.text()
                raise Exception(f"Binance positions error: {response.status} - {error_text}")
        
        return positions
    
    async def place_order(self, order: Order) -> Order:
        """Размещение ордера на Binance"""
        await self._rate_limit("orders", 10, 60)  # 10 ордеров в минуту
        
        timestamp = int(time.time() * 1000)
        
        # Подготавливаем параметры ордера
        params = {
            "symbol": order.symbol,
            "side": order.side.value.upper(),
            "type": self._convert_order_type(order.type),
            "quantity": str(order.quantity),
            "timestamp": str(timestamp)
        }
        
        if order.price:
            params["price"] = str(order.price)
        if order.stop_price:
            params["stopPrice"] = str(order.stop_price)
        if order.client_order_id:
            params["newClientOrderId"] = order.client_order_id
        if order.time_in_force:
            params["timeInForce"] = order.time_in_force
        
        # Создаем строку запроса для подписи
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        signature = self._generate_signature(query_string)
        params["signature"] = signature
        
        url = f"{self.base_url}/fapi/v1/order"
        headers = {"X-MBX-APIKEY": self.credentials.api_key}
        
        async with self.session.post(url, data=params, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                
                # Обновляем ордер результатами
                order.order_id = result["orderId"]
                order.status = self._convert_order_status(result["status"])
                order.created_at = datetime.fromtimestamp(result["updateTime"] / 1000)
                
                logger.info(f"Ордер размещен: {order.order_id}")
                return order
            else:
                error_text = await response.text()
                raise Exception(f"Binance order error: {response.status} - {error_text}")
    
    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Отмена ордера на Binance"""
        await self._rate_limit("cancel_order", 10, 60)
        
        timestamp = int(time.time() * 1000)
        params = f"symbol={symbol}&orderId={order_id}&timestamp={timestamp}"
        signature = self._generate_signature(params)
        
        url = f"{self.base_url}/fapi/v1/order"
        headers = {"X-MBX-APIKEY": self.credentials.api_key}
        params_with_sig = f"{params}&signature={signature}"
        
        async with self.session.delete(f"{url}?{params_with_sig}", headers=headers) as response:
            if response.status == 200:
                logger.info(f"Ордер отменен: {order_id}")
                return True
            else:
                error_text = await response.text()
                logger.error(f"Ошибка отмены ордера: {response.status} - {error_text}")
                return False
    
    async def get_order(self, symbol: str, order_id: str) -> Order:
        """Получение информации об ордере"""
        await self._rate_limit("get_order", 10, 60)
        
        timestamp = int(time.time() * 1000)
        params = f"symbol={symbol}&orderId={order_id}&timestamp={timestamp}"
        signature = self._generate_signature(params)
        
        url = f"{self.base_url}/fapi/v1/order"
        headers = {"X-MBX-APIKEY": self.credentials.api_key}
        params_with_sig = f"{params}&signature={signature}"
        
        async with self.session.get(f"{url}?{params_with_sig}", headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                
                order = Order(
                    symbol=data["symbol"],
                    side=OrderSide.BUY if data["side"] == "BUY" else OrderSide.SELL,
                    type=self._convert_binance_order_type(data["type"]),
                    quantity=float(data["origQty"]),
                    price=float(data["price"]) if data["price"] != "0" else None,
                    order_id=data["orderId"],
                    status=self._convert_order_status(data["status"]),
                    filled_quantity=float(data["executedQty"]),
                    avg_fill_price=float(data["avgPrice"]) if data["avgPrice"] != "0" else None,
                    created_at=datetime.fromtimestamp(data["time"] / 1000),
                    updated_at=datetime.fromtimestamp(data["updateTime"] / 1000)
                )
                
                return order
            else:
                error_text = await response.text()
                raise Exception(f"Binance get order error: {response.status} - {error_text}")
    
    async def get_market_data(self, symbol: str) -> MarketData:
        """Получение рыночных данных"""
        await self._rate_limit("market_data", 20, 60)
        
        # Получаем ticker 24hr
        url = f"{self.base_url}/fapi/v1/ticker/24hr"
        params = {"symbol": symbol}
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                
                market_data = MarketData(
                    symbol=data["symbol"],
                    price=float(data["lastPrice"]),
                    bid=float(data["bidPrice"]),
                    ask=float(data["askPrice"]),
                    volume_24h=float(data["volume"]),
                    change_24h=float(data["priceChangePercent"]),
                    timestamp=datetime.now()
                )
                
                return market_data
            else:
                error_text = await response.text()
                raise Exception(f"Binance market data error: {response.status} - {error_text}")
    
    async def subscribe_to_updates(self):
        """Подписка на обновления через WebSocket"""
        if not self.credentials.testnet:
            # Для продакшена нужна отдельная реализация
            logger.warning("WebSocket для продакшена не реализован")
            return
        
        try:
            # Создаем listen key для пользовательских данных
            timestamp = int(time.time() * 1000)
            params = f"timestamp={timestamp}"
            signature = self._generate_signature(params)
            
            url = f"{self.base_url}/fapi/v1/listenKey"
            headers = {"X-MBX-APIKEY": self.credentials.api_key}
            
            async with self.session.post(url, headers=headers) as response:
                if response.status == 200:
                    listen_data = await response.json()
                    listen_key = listen_data["listenKey"]
                    
                    # Подключаемся к WebSocket
                    ws_url = f"{self.ws_url}/{listen_key}"
                    
                    async with websockets.connect(ws_url) as websocket:
                        self.ws_connection = websocket
                        logger.info("WebSocket подключен")
                        
                        async for message in websocket:
                            try:
                                data = json.loads(message)
                                await self._handle_ws_message(data)
                            except Exception as e:
                                logger.error(f"Ошибка обработки WebSocket сообщения: {e}")
                                
        except Exception as e:
            logger.error(f"Ошибка WebSocket подключения: {e}")
    
    async def _handle_ws_message(self, data: Dict):
        """Обработка WebSocket сообщений"""
        event_type = data.get("e")
        
        if event_type == "ORDER_TRADE_UPDATE":
            # Обновление ордера
            order_data = data["o"]
            if self.on_order_update:
                await self.on_order_update(order_data)
                
        elif event_type == "ACCOUNT_UPDATE":
            # Обновление аккаунта
            if self.on_balance_update:
                await self.on_balance_update(data["a"])
                
        elif event_type == "ACCOUNT_CONFIG_UPDATE":
            # Обновление конфигурации
            logger.info("Конфигурация аккаунта обновлена")
    
    def _convert_order_type(self, order_type: OrderType) -> str:
        """Конвертация типа ордера для Binance"""
        mapping = {
            OrderType.MARKET: "MARKET",
            OrderType.LIMIT: "LIMIT",
            OrderType.STOP_LOSS: "STOP_MARKET",
            OrderType.TAKE_PROFIT: "TAKE_PROFIT_MARKET",
            OrderType.STOP_LIMIT: "STOP"
        }
        return mapping.get(order_type, "LIMIT")
    
    def _convert_binance_order_type(self, binance_type: str) -> OrderType:
        """Конвертация типа ордера из Binance"""
        mapping = {
            "MARKET": OrderType.MARKET,
            "LIMIT": OrderType.LIMIT,
            "STOP_MARKET": OrderType.STOP_LOSS,
            "TAKE_PROFIT_MARKET": OrderType.TAKE_PROFIT,
            "STOP": OrderType.STOP_LIMIT
        }
        return mapping.get(binance_type, OrderType.LIMIT)
    
    def _convert_order_status(self, binance_status: str) -> OrderStatus:
        """Конвертация статуса ордера"""
        mapping = {
            "NEW": OrderStatus.OPEN,
            "PARTIALLY_FILLED": OrderStatus.PARTIALLY_FILLED,
            "FILLED": OrderStatus.FILLED,
            "CANCELED": OrderStatus.CANCELLED,
            "REJECTED": OrderStatus.REJECTED,
            "EXPIRED": OrderStatus.EXPIRED
        }
        return mapping.get(binance_status, OrderStatus.PENDING)

class MockConnector(BrokerConnector):
    """Mock коннектор для тестирования"""
    
    def __init__(self, credentials: BrokerCredentials):
        super().__init__(credentials)
        self.mock_balances = [
            Balance("USDT", 10000.0, 0.0, 10000.0),
            Balance("BTC", 0.5, 0.0, 0.5)
        ]
        self.mock_positions = []
        self.mock_orders = {}
        self.order_counter = 1
        
    async def connect(self) -> bool:
        """Mock подключение"""
        self.connected = True
        logger.info("Mock коннектор подключен")
        return True
    
    async def disconnect(self):
        """Mock отключение"""
        self.connected = False
        logger.info("Mock коннектор отключен")
    
    async def get_account_info(self) -> Dict:
        """Mock информация об аккаунте"""
        return {
            "accountType": "FUTURES",
            "balances": [asdict(b) for b in self.mock_balances],
            "canTrade": True,
            "canWithdraw": False,
            "canDeposit": False
        }
    
    async def get_balances(self) -> List[Balance]:
        """Mock балансы"""
        return self.mock_balances.copy()
    
    async def get_positions(self) -> List[Position]:
        """Mock позиции"""
        return self.mock_positions.copy()
    
    async def place_order(self, order: Order) -> Order:
        """Mock размещение ордера"""
        order.order_id = str(self.order_counter)
        order.status = OrderStatus.OPEN
        order.created_at = datetime.now()
        
        self.mock_orders[order.order_id] = order
        self.order_counter += 1
        
        # Симуляция мгновенного исполнения для market ордеров
        if order.type == OrderType.MARKET:
            order.status = OrderStatus.FILLED
            order.filled_quantity = order.quantity
            order.avg_fill_price = order.price or 50000.0  # Mock цена
        
        logger.info(f"Mock ордер размещен: {order.order_id}")
        return order
    
    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Mock отмена ордера"""
        if order_id in self.mock_orders:
            self.mock_orders[order_id].status = OrderStatus.CANCELLED
            logger.info(f"Mock ордер отменен: {order_id}")
            return True
        return False
    
    async def get_order(self, symbol: str, order_id: str) -> Order:
        """Mock получение ордера"""
        if order_id in self.mock_orders:
            return self.mock_orders[order_id]
        raise Exception(f"Ордер {order_id} не найден")
    
    async def get_market_data(self, symbol: str) -> MarketData:
        """Mock рыночные данные"""
        import random
        base_price = 50000.0
        price = base_price + random.uniform(-1000, 1000)
        
        return MarketData(
            symbol=symbol,
            price=price,
            bid=price - 0.5,
            ask=price + 0.5,
            volume_24h=1000000.0,
            change_24h=random.uniform(-5, 5),
            timestamp=datetime.now()
        )
    
    async def subscribe_to_updates(self):
        """Mock подписка на обновления"""
        logger.info("Mock WebSocket подписка активна")

class BrokerManager:
    """Менеджер брокерских подключений"""
    
    def __init__(self):
        self.connectors: Dict[str, BrokerConnector] = {}
        self.active_connector: Optional[str] = None
        
    def add_connector(self, name: str, broker_type: BrokerType, credentials: BrokerCredentials):
        """Добавление коннектора"""
        if broker_type == BrokerType.BINANCE:
            connector = BinanceConnector(credentials)
        elif broker_type == BrokerType.MOCK:
            connector = MockConnector(credentials)
        else:
            raise ValueError(f"Неподдерживаемый тип брокера: {broker_type}")
        
        self.connectors[name] = connector
        logger.info(f"Добавлен коннектор {name} ({broker_type.value})")
    
    async def connect_all(self) -> Dict[str, bool]:
        """Подключение ко всем брокерам"""
        results = {}
        for name, connector in self.connectors.items():
            try:
                results[name] = await connector.connect()
            except Exception as e:
                logger.error(f"Ошибка подключения к {name}: {e}")
                results[name] = False
        return results
    
    async def disconnect_all(self):
        """Отключение от всех брокеров"""
        for name, connector in self.connectors.items():
            try:
                await connector.disconnect()
            except Exception as e:
                logger.error(f"Ошибка отключения от {name}: {e}")
    
    def set_active(self, name: str):
        """Установка активного коннектора"""
        if name in self.connectors:
            self.active_connector = name
            logger.info(f"Активный коннектор: {name}")
        else:
            raise ValueError(f"Коннектор {name} не найден")
    
    def get_active(self) -> BrokerConnector:
        """Получение активного коннектора"""
        if self.active_connector and self.active_connector in self.connectors:
            return self.connectors[self.active_connector]
        raise ValueError("Нет активного коннектора")
    
    async def get_unified_portfolio(self) -> Dict:
        """Получение объединенного портфеля со всех брокеров"""
        portfolio = {
            "total_balance_usd": 0.0,
            "brokers": {},
            "total_positions": 0,
            "total_unrealized_pnl": 0.0
        }
        
        for name, connector in self.connectors.items():
            if not connector.connected:
                continue
            
            try:
                balances = await connector.get_balances()
                positions = await connector.get_positions()
                
                broker_data = {
                    "balances": [asdict(b) for b in balances],
                    "positions": [asdict(p) for p in positions],
                    "balance_usd": sum(b.total for b in balances if b.asset == "USDT"),
                    "unrealized_pnl": sum(p.unrealized_pnl for p in positions)
                }
                
                portfolio["brokers"][name] = broker_data
                portfolio["total_balance_usd"] += broker_data["balance_usd"]
                portfolio["total_positions"] += len(positions)
                portfolio["total_unrealized_pnl"] += broker_data["unrealized_pnl"]
                
            except Exception as e:
                logger.error(f"Ошибка получения данных от {name}: {e}")
                portfolio["brokers"][name] = {"error": str(e)}
        
        return portfolio

# Тестирование брокерских коннекторов
async def test_broker_connectors():
    """Тестирование системы брокерских коннекторов"""
    
    print("=== Тестирование брокерских коннекторов ===\n")
    
    # Инициализация менеджера
    broker_manager = BrokerManager()
    
    # Добавляем Mock коннектор для тестирования
    mock_credentials = BrokerCredentials(
        api_key="test_key",
        api_secret="test_secret",
        testnet=True
    )
    
    broker_manager.add_connector("mock", BrokerType.MOCK, mock_credentials)
    broker_manager.set_active("mock")
    
    # Подключение
    connections = await broker_manager.connect_all()
    print(f"Результаты подключения: {connections}")
    
    # Получение активного коннектора
    active_connector = broker_manager.get_active()
    
    # Тестирование базового функционала
    print("\n=== Тестирование функционала ===")
    
    # Балансы
    balances = await active_connector.get_balances()
    print(f"Балансы: {[asdict(b) for b in balances]}")
    
    # Рыночные данные
    market_data = await active_connector.get_market_data("BTCUSDT")
    print(f"Рыночные данные: {asdict(market_data)}")
    
    # Размещение ордера
    test_order = Order(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        type=OrderType.LIMIT,
        quantity=0.001,
        price=49000.0
    )
    
    placed_order = await active_connector.place_order(test_order)
    print(f"Размещенный ордер: {asdict(placed_order)}")
    
    # Получение ордера
    retrieved_order = await active_connector.get_order("BTCUSDT", placed_order.order_id)
    print(f"Полученный ордер: {asdict(retrieved_order)}")
    
    # Отмена ордера
    cancelled = await active_connector.cancel_order("BTCUSDT", placed_order.order_id)
    print(f"Ордер отменен: {cancelled}")
    
    # Объединенный портфель
    unified_portfolio = await broker_manager.get_unified_portfolio()
    print(f"\nОбъединенный портфель: {json.dumps(unified_portfolio, indent=2, default=str)}")
    
    # Отключение
    await broker_manager.disconnect_all()
    print("\nВсе коннекторы отключены")

if __name__ == "__main__":
    asyncio.run(test_broker_connectors())
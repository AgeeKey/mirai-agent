"""
Mirai Metrics Exporter для Prometheus
Экспорт метрик торговли, AI производительности и системных ресурсов
"""
import time
import psutil
import sqlite3
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from prometheus_client import start_http_server, Gauge, Counter, Histogram, Info
import json
import os
import httpx

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus метрики
class MiraiMetrics:
    def __init__(self):
        # Trading Metrics
        self.pnl_total = Gauge('mirai_pnl_total_usd', 'Total P&L in USD')
        self.pnl_daily = Gauge('mirai_pnl_daily_usd', 'Daily P&L in USD')
        self.pnl_hourly = Gauge('mirai_pnl_hourly_usd', 'Hourly P&L in USD')
        
        self.trades_total = Counter('mirai_trades_total', 'Total number of trades', ['side', 'symbol'])
        self.trades_profit = Counter('mirai_trades_profit_total', 'Profitable trades count')
        self.trades_loss = Counter('mirai_trades_loss_total', 'Loss trades count')
        
        self.win_rate = Gauge('mirai_win_rate_percent', 'Win rate percentage')
        self.drawdown_current = Gauge('mirai_drawdown_current_percent', 'Current drawdown percentage')
        self.drawdown_max = Gauge('mirai_drawdown_max_percent', 'Maximum drawdown percentage')
        
        self.positions_active = Gauge('mirai_positions_active', 'Number of active positions')
        self.positions_size = Gauge('mirai_positions_size_usd', 'Total position size in USD')
        
        # AI Performance Metrics
        self.ai_decisions_total = Counter('mirai_ai_decisions_total', 'Total AI decisions', ['decision_type'])
        self.ai_response_time = Histogram('mirai_ai_response_time_seconds', 'AI response time in seconds')
        self.ai_confidence = Gauge('mirai_ai_confidence_score', 'AI confidence score (0-100)')
        self.ai_success_rate = Gauge('mirai_ai_success_rate_percent', 'AI prediction success rate')
        
        # System Metrics
        self.system_cpu_usage = Gauge('mirai_system_cpu_percent', 'CPU usage percentage')
        self.system_memory_usage = Gauge('mirai_system_memory_percent', 'Memory usage percentage')
        self.system_disk_usage = Gauge('mirai_system_disk_percent', 'Disk usage percentage')
        
        self.api_requests_total = Counter('mirai_api_requests_total', 'Total API requests', ['endpoint', 'method'])
        self.api_response_time = Histogram('mirai_api_response_time_seconds', 'API response time')
        self.api_errors_total = Counter('mirai_api_errors_total', 'Total API errors', ['error_type'])
        
        # Market Data Metrics
        self.market_data_updates = Counter('mirai_market_data_updates_total', 'Market data updates', ['symbol'])
        self.market_volatility = Gauge('mirai_market_volatility', 'Market volatility indicator', ['symbol'])
        
        # Emergency System Metrics
        self.emergency_stops_total = Counter('mirai_emergency_stops_total', 'Total emergency stops')
        self.system_uptime = Gauge('mirai_system_uptime_seconds', 'System uptime in seconds')
        
        # System Info
        self.system_info = Info('mirai_system_info', 'System information')
        self.system_info.info({
            'version': '3.0.0',
            'environment': os.getenv('AGENT_SANDBOX_MODE', 'production'),
            'testnet': os.getenv('BINANCE_TESTNET', 'false'),
            'start_time': datetime.now().isoformat()
        })
        
        self.start_time = time.time()

    def update_system_metrics(self):
        """Обновление системных метрик"""
        try:
            # CPU и память
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            self.system_cpu_usage.set(cpu_percent)
            self.system_memory_usage.set(memory.percent)
            self.system_disk_usage.set(disk.percent)
            
            # Uptime
            uptime = time.time() - self.start_time
            self.system_uptime.set(uptime)
            
            logger.debug(f"Updated system metrics: CPU={cpu_percent}%, Memory={memory.percent}%, Disk={disk.percent}%")
            
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")

    async def update_trading_metrics(self):
        """Обновление торговых метрик из базы данных"""
        try:
            db_path = '/root/mirai-agent/state/mirai.db'
            if not os.path.exists(db_path):
                logger.warning("Trading database not found")
                return
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # P&L метрики
            cursor.execute("""
                SELECT SUM(pnl) as total_pnl, COUNT(*) as total_trades 
                FROM trades WHERE created_at > datetime('now', '-1 day')
            """)
            daily_result = cursor.fetchone()
            
            if daily_result and daily_result[0]:
                self.pnl_daily.set(float(daily_result[0]))
                
            cursor.execute("SELECT SUM(pnl) as total_pnl FROM trades")
            total_result = cursor.fetchone()
            
            if total_result and total_result[0]:
                self.pnl_total.set(float(total_result[0]))
            
            # Win rate
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN pnl > 0 THEN 1 END) * 100.0 / COUNT(*) as win_rate
                FROM trades 
                WHERE created_at > datetime('now', '-7 days')
            """)
            win_rate_result = cursor.fetchone()
            
            if win_rate_result and win_rate_result[0]:
                self.win_rate.set(float(win_rate_result[0]))
            
            # Активные позиции
            cursor.execute("SELECT COUNT(*) FROM positions WHERE status = 'active'")
            active_positions = cursor.fetchone()[0]
            self.positions_active.set(active_positions)
            
            conn.close()
            logger.debug("Updated trading metrics from database")
            
        except Exception as e:
            logger.error(f"Error updating trading metrics: {e}")

    async def update_ai_metrics(self):
        """Обновление AI метрик"""
        try:
            # Запрос к AI Orchestrator
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8080/health", timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # AI confidence и другие метрики
                    if 'ai_confidence' in data:
                        self.ai_confidence.set(data['ai_confidence'])
                    
                    if 'decisions_count' in data:
                        # Здесь можно добавить логику для обновления счетчиков решений
                        pass
                        
                    logger.debug("Updated AI metrics from orchestrator")
                    
        except Exception as e:
            logger.debug(f"AI Orchestrator not available: {e}")

    async def update_market_metrics(self):
        """Обновление рыночных метрик"""
        try:
            # Можно добавить запросы к рыночным данным
            # Пока оставляем заглушку
            pass
            
        except Exception as e:
            logger.error(f"Error updating market metrics: {e}")

class MiraiMetricsCollector:
    def __init__(self, port: int = 9090):
        self.metrics = MiraiMetrics()
        self.port = port
        self.running = False
        
    async def start_collection(self):
        """Запуск сбора метрик"""
        logger.info(f"Starting Mirai metrics collector on port {self.port}")
        
        # Запуск HTTP сервера Prometheus
        start_http_server(self.port)
        
        self.running = True
        
        # Основной цикл сбора метрик
        while self.running:
            try:
                # Обновляем метрики каждые 30 секунд
                self.metrics.update_system_metrics()
                await self.metrics.update_trading_metrics()
                await self.metrics.update_ai_metrics()
                await self.metrics.update_market_metrics()
                
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(30)
    
    def stop_collection(self):
        """Остановка сбора метрик"""
        logger.info("Stopping metrics collection")
        self.running = False

# Функция для интеграции с FastAPI
def create_metrics_middleware():
    """Создание middleware для отслеживания API метрик"""
    metrics = MiraiMetrics()
    
    async def metrics_middleware(request, call_next):
        start_time = time.time()
        
        # Увеличиваем счетчик запросов
        endpoint = request.url.path
        method = request.method
        metrics.api_requests_total.labels(endpoint=endpoint, method=method).inc()
        
        try:
            response = await call_next(request)
            
            # Записываем время ответа
            response_time = time.time() - start_time
            metrics.api_response_time.observe(response_time)
            
            return response
            
        except Exception as e:
            # Записываем ошибки
            metrics.api_errors_total.labels(error_type=type(e).__name__).inc()
            raise
    
    return metrics_middleware

# Основная функция запуска
async def main():
    """Запуск сборщика метрик"""
    collector = MiraiMetricsCollector()
    
    try:
        await collector.start_collection()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        collector.stop_collection()
    except Exception as e:
        logger.error(f"Error in main: {e}")
        collector.stop_collection()

if __name__ == "__main__":
    asyncio.run(main())
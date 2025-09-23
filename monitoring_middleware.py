import time
import asyncio
from datetime import datetime
from typing import Dict, List
from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import psutil

# Метрики Prometheus
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Active connections')
SYSTEM_CPU = Gauge('system_cpu_percent', 'CPU usage percentage')
SYSTEM_MEMORY = Gauge('system_memory_percent', 'Memory usage percentage')
SYSTEM_DISK = Gauge('system_disk_percent', 'Disk usage percentage')

class MonitoringMiddleware:
    def __init__(self, app):
        self.app = app
        # Запускаем фоновую задачу для сбора системных метрик
        asyncio.create_task(self.collect_system_metrics())
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Увеличиваем счетчик активных соединений
        ACTIVE_CONNECTIONS.inc()
        
        start_time = time.time()
        request = Request(scope, receive)
        
        # Обработка запроса
        response_sent = False
        
        async def send_wrapper(message):
            nonlocal response_sent
            if message["type"] == "http.response.start":
                response_sent = True
                status_code = message["status"]
                
                # Записываем метрики
                duration = time.time() - start_time
                REQUEST_DURATION.observe(duration)
                REQUEST_COUNT.labels(
                    method=request.method,
                    endpoint=request.url.path,
                    status=status_code
                ).inc()
                
                ACTIVE_CONNECTIONS.dec()
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)
    
    async def collect_system_metrics(self):
        """Собираем системные метрики каждые 15 секунд"""
        while True:
            try:
                # CPU
                cpu_percent = psutil.cpu_percent(interval=1)
                SYSTEM_CPU.set(cpu_percent)
                
                # Memory
                memory = psutil.virtual_memory()
                SYSTEM_MEMORY.set(memory.percent)
                
                # Disk
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                SYSTEM_DISK.set(disk_percent)
                
            except Exception as e:
                print(f"Ошибка сбора метрик: {e}")
            
            await asyncio.sleep(15)

# Функция для добавления метрик в FastAPI
def add_metrics_endpoint(app):
    @app.get("/metrics")
    async def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    
    @app.post("/api/alerts")
    async def receive_alert(alert_data: dict):
        """Endpoint для получения алертов от Alertmanager"""
        print(f"Получен алерт: {alert_data}")
        # Здесь можно добавить логику отправки в Telegram или другие каналы
        return {"status": "received"}

# Health check с детальной информацией
def add_health_check(app):
    @app.get("/health/detailed")
    async def detailed_health():
        try:
            # Проверяем системные ресурсы
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Проверяем подключение к базе данных
            # (добавить проверку когда будет БД)
            
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": (disk.used / disk.total) * 100,
                    "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
                },
                "services": {
                    "api": "healthy",
                    "database": "checking...",  # будет обновлено
                    "redis": "checking..."      # будет обновлено
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

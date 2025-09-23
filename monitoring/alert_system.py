"""
Mirai Agent - Система алертов
Мониторинг критических событий и отправка уведомлений
"""
import asyncio
import json
import logging
import sqlite3
import os
import time
import httpx
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/mirai-agent/logs/alerts.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Уровни критичности алертов"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertType(Enum):
    """Типы алертов"""
    TRADING = "trading"
    AI = "ai"
    SYSTEM = "system"
    SECURITY = "security"

@dataclass
class Alert:
    """Структура алерта"""
    id: str
    type: AlertType
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Optional[Dict] = None

class AlertRule:
    """Базовый класс для правил алертов"""
    
    def __init__(self, name: str, level: AlertLevel, alert_type: AlertType):
        self.name = name
        self.level = level
        self.alert_type = alert_type
        self.last_triggered = None
        self.cooldown = 300  # 5 минут между повторными алертами
    
    async def check(self, metrics: Dict) -> Optional[Alert]:
        """Проверка условий алерта"""
        raise NotImplementedError
    
    def can_trigger(self) -> bool:
        """Проверка возможности триггера (учет cooldown)"""
        if self.last_triggered is None:
            return True
        return (datetime.now() - self.last_triggered).seconds > self.cooldown

class DrawdownAlert(AlertRule):
    """Алерт превышения drawdown"""
    
    def __init__(self, threshold: float = 10.0):
        super().__init__("Drawdown Alert", AlertLevel.CRITICAL, AlertType.TRADING)
        self.threshold = threshold
    
    async def check(self, metrics: Dict) -> Optional[Alert]:
        trading = metrics.get('trading', {})
        daily_pnl = trading.get('daily_pnl', 0)
        total_pnl = trading.get('total_pnl', 0)
        
        # Проверяем дневной drawdown
        if daily_pnl < -self.threshold and self.can_trigger():
            self.last_triggered = datetime.now()
            return Alert(
                id=f"drawdown_{int(time.time())}",
                type=self.alert_type,
                level=self.level,
                title="Критический Drawdown!",
                message=f"Дневные потери превысили ${self.threshold}. Текущий P&L: ${daily_pnl}",
                timestamp=datetime.now(),
                metadata={"daily_pnl": daily_pnl, "threshold": self.threshold}
            )
        return None

class WinRateAlert(AlertRule):
    """Алерт низкого винрейта"""
    
    def __init__(self, threshold: float = 40.0):
        super().__init__("Win Rate Alert", AlertLevel.WARNING, AlertType.TRADING)
        self.threshold = threshold
    
    async def check(self, metrics: Dict) -> Optional[Alert]:
        trading = metrics.get('trading', {})
        win_rate = trading.get('win_rate', 0)
        
        if win_rate < self.threshold and win_rate > 0 and self.can_trigger():
            self.last_triggered = datetime.now()
            return Alert(
                id=f"winrate_{int(time.time())}",
                type=self.alert_type,
                level=self.level,
                title="Низкий винрейт",
                message=f"Винрейт упал до {win_rate}% (порог: {self.threshold}%)",
                timestamp=datetime.now(),
                metadata={"win_rate": win_rate, "threshold": self.threshold}
            )
        return None

class AIUnavailableAlert(AlertRule):
    """Алерт недоступности AI"""
    
    def __init__(self):
        super().__init__("AI Unavailable", AlertLevel.CRITICAL, AlertType.AI)
        self.cooldown = 60  # 1 минута между проверками
    
    async def check(self, metrics: Dict) -> Optional[Alert]:
        ai = metrics.get('ai', {})
        status = ai.get('status', 'Unknown')
        
        if status != 'Connected' and self.can_trigger():
            self.last_triggered = datetime.now()
            return Alert(
                id=f"ai_unavailable_{int(time.time())}",
                type=self.alert_type,
                level=self.level,
                title="AI Orchestrator недоступен!",
                message=f"Статус AI: {status}. Торговые решения могут быть нарушены.",
                timestamp=datetime.now(),
                metadata={"ai_status": status}
            )
        return None

class SystemResourceAlert(AlertRule):
    """Алерт высокой нагрузки системы"""
    
    def __init__(self, cpu_threshold: float = 90.0, memory_threshold: float = 85.0):
        super().__init__("System Resources", AlertLevel.WARNING, AlertType.SYSTEM)
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
    
    async def check(self, metrics: Dict) -> Optional[Alert]:
        system = metrics.get('system', {})
        cpu_usage = system.get('cpu_usage', 0)
        memory_usage = system.get('memory_usage', 0)
        
        if cpu_usage > self.cpu_threshold and self.can_trigger():
            self.last_triggered = datetime.now()
            return Alert(
                id=f"cpu_high_{int(time.time())}",
                type=self.alert_type,
                level=self.level,
                title="Высокая загрузка CPU",
                message=f"CPU загружен на {cpu_usage}% (порог: {self.cpu_threshold}%)",
                timestamp=datetime.now(),
                metadata={"cpu_usage": cpu_usage, "threshold": self.cpu_threshold}
            )
        
        if memory_usage > self.memory_threshold and self.can_trigger():
            self.last_triggered = datetime.now()
            return Alert(
                id=f"memory_high_{int(time.time())}",
                type=self.alert_type,
                level=self.level,
                title="Высокое использование памяти",
                message=f"Память используется на {memory_usage}% (порог: {self.memory_threshold}%)",
                timestamp=datetime.now(),
                metadata={"memory_usage": memory_usage, "threshold": self.memory_threshold}
            )
        
        return None

class EmergencyStopAlert(AlertRule):
    """Алерт активации emergency stop"""
    
    def __init__(self):
        super().__init__("Emergency Stop", AlertLevel.EMERGENCY, AlertType.SECURITY)
        self.cooldown = 0  # Без cooldown для критических событий
    
    async def check(self, metrics: Dict) -> Optional[Alert]:
        # Проверяем статус emergency stop через API
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8001/emergency/status", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('emergency_stop_active', False):
                        return Alert(
                            id=f"emergency_stop_{int(time.time())}",
                            type=self.alert_type,
                            level=self.level,
                            title="🚨 EMERGENCY STOP АКТИВИРОВАН!",
                            message="Торговля экстренно остановлена. Все позиции закрыты.",
                            timestamp=datetime.now(),
                            metadata=data
                        )
        except Exception as e:
            logger.error(f"Ошибка проверки emergency stop: {e}")
        
        return None

class AlertManager:
    """Менеджер системы алертов"""
    
    def __init__(self):
        self.rules: List[AlertRule] = []
        self.active_alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        self.db_path = "/root/mirai-agent/state/mirai.db"
        self.telegram_enabled = False
        self.setup_rules()
        self.init_database()
    
    def setup_rules(self):
        """Настройка правил алертов"""
        self.rules = [
            DrawdownAlert(threshold=50.0),  # $50 дневной лимит потерь
            WinRateAlert(threshold=35.0),   # Винрейт ниже 35%
            AIUnavailableAlert(),
            SystemResourceAlert(cpu_threshold=85.0, memory_threshold=80.0),
            EmergencyStopAlert()
        ]
        logger.info(f"Настроено {len(self.rules)} правил алертов")
    
    def init_database(self):
        """Инициализация базы данных для алертов"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    type TEXT,
                    level TEXT,
                    title TEXT,
                    message TEXT,
                    timestamp TEXT,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TEXT,
                    metadata TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("База данных алертов инициализирована")
        except Exception as e:
            logger.error(f"Ошибка инициализации БД алертов: {e}")
    
    async def check_alerts(self, metrics: Dict) -> List[Alert]:
        """Проверка всех правил алертов"""
        new_alerts = []
        
        for rule in self.rules:
            try:
                alert = await rule.check(metrics)
                if alert:
                    new_alerts.append(alert)
                    logger.warning(f"Новый алерт: {alert.title} - {alert.message}")
            except Exception as e:
                logger.error(f"Ошибка проверки правила {rule.name}: {e}")
        
        # Сохраняем новые алерты
        for alert in new_alerts:
            await self.save_alert(alert)
            self.active_alerts.append(alert)
            self.alert_history.append(alert)
        
        return new_alerts
    
    async def save_alert(self, alert: Alert):
        """Сохранение алерта в базу данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO alerts 
                (id, type, level, title, message, timestamp, resolved, resolved_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.id,
                alert.type.value,
                alert.level.value,
                alert.title,
                alert.message,
                alert.timestamp.isoformat(),
                alert.resolved,
                alert.resolved_at.isoformat() if alert.resolved_at else None,
                json.dumps(alert.metadata) if alert.metadata else None
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Ошибка сохранения алерта: {e}")
    
    async def send_telegram_alert(self, alert: Alert):
        """Отправка алерта в Telegram"""
        try:
            # Формируем сообщение
            icon = {
                AlertLevel.INFO: "ℹ️",
                AlertLevel.WARNING: "⚠️",
                AlertLevel.CRITICAL: "🚨",
                AlertLevel.EMERGENCY: "🆘"
            }.get(alert.level, "🔔")
            
            message = f"{icon} *{alert.title}*\n\n{alert.message}\n\n_Время: {alert.timestamp.strftime('%H:%M:%S')}_"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8002/send_alert",
                    json={"message": message, "level": alert.level.value},
                    timeout=10
                )
                
                if response.status_code == 200:
                    logger.info(f"Алерт отправлен в Telegram: {alert.title}")
                else:
                    logger.error(f"Ошибка отправки в Telegram: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Ошибка отправки Telegram алерта: {e}")
    
    async def resolve_alert(self, alert_id: str):
        """Разрешение алерта"""
        for alert in self.active_alerts:
            if alert.id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                await self.save_alert(alert)
                self.active_alerts.remove(alert)
                logger.info(f"Алерт разрешен: {alert.title}")
                break
    
    def get_active_alerts(self) -> List[Dict]:
        """Получение активных алертов"""
        return [asdict(alert) for alert in self.active_alerts if not alert.resolved]
    
    def get_alert_history(self, hours: int = 24) -> List[Dict]:
        """Получение истории алертов"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_alerts = [
            asdict(alert) for alert in self.alert_history 
            if alert.timestamp > cutoff
        ]
        return recent_alerts

class AlertService:
    """Сервис мониторинга алертов"""
    
    def __init__(self):
        self.alert_manager = AlertManager()
        self.running = False
        self.check_interval = 30  # Проверка каждые 30 секунд
    
    async def get_metrics(self) -> Dict:
        """Получение метрик для проверки алертов"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:9999/metrics", timeout=5)
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Ошибка получения метрик: {response.status_code}")
                    return {}
        except Exception as e:
            logger.error(f"Ошибка получения метрик: {e}")
            return {}
    
    async def monitor_loop(self):
        """Основной цикл мониторинга"""
        logger.info("Запуск сервиса алертов...")
        self.running = True
        
        while self.running:
            try:
                # Получаем метрики
                metrics = await self.get_metrics()
                
                if metrics:
                    # Проверяем алерты
                    new_alerts = await self.alert_manager.check_alerts(metrics)
                    
                    # Отправляем уведомления
                    for alert in new_alerts:
                        await self.alert_manager.send_telegram_alert(alert)
                
                # Ждем до следующей проверки
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Ошибка в цикле мониторинга: {e}")
                await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """Остановка сервиса"""
        self.running = False
        logger.info("Сервис алертов остановлен")

async def main():
    """Главная функция запуска сервиса алертов"""
    service = AlertService()
    
    try:
        await service.monitor_loop()
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
        service.stop()

if __name__ == "__main__":
    asyncio.run(main())
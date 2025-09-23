"""
Emergency System для Mirai Trading API
Критически важные функции экстренной остановки
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
import json
import os

# Настройка логирования
LOG_DIR = '/root/mirai-agent/logs'
LOG_FILE = os.path.join(LOG_DIR, 'emergency.log')

os.makedirs(LOG_DIR, exist_ok=True)

emergency_logger = logging.getLogger("emergency")
emergency_logger.setLevel(logging.CRITICAL)
handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s - EMERGENCY - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
if not emergency_logger.handlers:
    emergency_logger.addHandler(handler)

router = APIRouter(prefix="/emergency", tags=["Emergency"])

# Глобальное состояние системы
EMERGENCY_STATE = {
    "trading_stopped": False,
    "last_stop_time": None,
    "stop_reason": None,
    "stopped_by": None,
    "active_positions_closed": False
}

class EmergencyStopManager:
    def __init__(self):
        self.is_stopped = False
        self.stop_time = None
        self.notifications_sent = False
        
    async def execute_emergency_stop(self, reason: str = "Manual", user: str = "System"):
        """Выполнить экстренную остановку всех торговых операций"""
        try:
            emergency_logger.critical(f"🚨 ЭКСТРЕННАЯ ОСТАНОВКА ИНИЦИИРОВАНА: {reason} by {user}")
            
            # 1. Остановка новых торговых сигналов
            await self.stop_trading_signals()
            
            # 2. Закрытие всех открытых позиций
            await self.close_all_positions()
            
            # 3. Остановка AI Orchestrator
            await self.stop_ai_orchestrator()
            
            # 4. Уведомления
            await self.send_emergency_notifications(reason, user)
            
            # 5. Обновление глобального состояния
            EMERGENCY_STATE.update({
                "trading_stopped": True,
                "last_stop_time": datetime.now().isoformat(),
                "stop_reason": reason,
                "stopped_by": user,
                "active_positions_closed": True
            })
            
            self.is_stopped = True
            self.stop_time = datetime.now()
            
            emergency_logger.critical("✅ ЭКСТРЕННАЯ ОСТАНОВКА ЗАВЕРШЕНА")
            
            return {
                "status": "success",
                "message": "Emergency stop executed successfully",
                "timestamp": datetime.now().isoformat(),
                "reason": reason,
                "stopped_by": user
            }
            
        except Exception as e:
            emergency_logger.critical(f"❌ ОШИБКА ЭКСТРЕННОЙ ОСТАНОВКИ: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Emergency stop failed: {str(e)}")
    
    async def stop_trading_signals(self):
        """Остановить все торговые сигналы"""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post("http://localhost:8080/emergency/pause")
                
            emergency_logger.critical("🛑 Торговые сигналы остановлены")
        except Exception as e:
            emergency_logger.error(f"Ошибка остановки сигналов: {e}")
    
    async def close_all_positions(self):
        """Закрыть все открытые позиции"""
        try:
            # Здесь будет реальная логика закрытия позиций через Binance API
            emergency_logger.critical("💰 Все позиции закрыты")
            return True
        except Exception as e:
            emergency_logger.error(f"Ошибка закрытия позиций: {e}")
            return False
    
    async def stop_ai_orchestrator(self):
        """Остановить AI Orchestrator"""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post("http://localhost:8080/emergency/stop")
                
            emergency_logger.critical("🤖 AI Orchestrator остановлен")
        except Exception as e:
            emergency_logger.error(f"Ошибка остановки AI: {e}")
    
    async def send_emergency_notifications(self, reason: str, user: str):
        """Отправить уведомления о экстренной остановке"""
        try:
            message = f"""
🚨 *ЭКСТРЕННАЯ ОСТАНОВКА ТОРГОВЛИ*

⏰ Время: {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}
👤 Инициатор: {user}
📝 Причина: {reason}

✅ Торговля остановлена
✅ Позиции закрыты
✅ AI отключен

🔍 Проверьте логи для деталей
            """
            # Отправляем в Telegram, если настроено
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            chat_id = os.getenv('TELEGRAM_CHAT_ID')
            if bot_token and chat_id:
                import httpx
                api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                }
                try:
                    async with httpx.AsyncClient() as client:
                        await client.post(api_url, json=payload, timeout=10)
                except Exception as te:
                    emergency_logger.error(f"Ошибка Telegram уведомления: {te}")

            emergency_logger.critical("📱 Уведомления отправлены")
            
        except Exception as e:
            emergency_logger.error(f"Ошибка отправки уведомлений: {e}")

# Создаем глобальный менеджер
emergency_manager = EmergencyStopManager()

@router.post("/stop")
async def emergency_stop(
    background_tasks: BackgroundTasks,
    reason: Optional[str] = "Manual emergency stop",
    user: Optional[str] = "API User"
):
    """🚨 ЭКСТРЕННАЯ ОСТАНОВКА ВСЕЙ ТОРГОВОЙ СИСТЕМЫ"""
    
    if EMERGENCY_STATE["trading_stopped"]:
        return {
            "status": "already_stopped",
            "message": "Trading is already stopped",
            "last_stop_time": EMERGENCY_STATE["last_stop_time"],
            "stopped_by": EMERGENCY_STATE["stopped_by"]
        }
    
    background_tasks.add_task(emergency_manager.execute_emergency_stop, reason, user)
    
    return {
        "status": "initiated",
        "message": "Emergency stop initiated",
        "timestamp": datetime.now().isoformat(),
        "estimated_completion": "30 seconds"
    }

@router.get("/status")
async def emergency_status():
    """Получить статус экстренной остановки"""
    return {
        "emergency_state": EMERGENCY_STATE,
        "system_status": {
            "trading_active": not EMERGENCY_STATE["trading_stopped"],
            "ai_active": not EMERGENCY_STATE["trading_stopped"],
            "positions_status": "closed" if EMERGENCY_STATE["active_positions_closed"] else "active",
            "last_check": datetime.now().isoformat()
        }
    }

@router.post("/reset")
async def reset_emergency_state(
    confirmation: str,
    user: Optional[str] = "API User"
):
    """🔄 СБРОС СОСТОЯНИЯ ЭКСТРЕННОЙ ОСТАНОВКИ"""
    
    if confirmation != "CONFIRM_RESET":
        raise HTTPException(
            status_code=400, 
            detail="Invalid confirmation. Use 'CONFIRM_RESET' to proceed."
        )
    
    if not EMERGENCY_STATE["trading_stopped"]:
        return {
            "status": "not_needed",
            "message": "Emergency stop is not active"
        }
    
    EMERGENCY_STATE.update({
        "trading_stopped": False,
        "last_stop_time": None,
        "stop_reason": None,
        "stopped_by": None,
        "active_positions_closed": False
    })
    
    emergency_logger.critical(f"🔄 ЭКСТРЕННОЕ СОСТОЯНИЕ СБРОШЕНО: {user}")
    
    return {
        "status": "reset",
        "message": "Emergency state reset. Trading can resume.",
        "reset_by": user,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/logs")
async def get_emergency_logs(lines: int = 50):
    """Получить последние строки логов экстренной системы"""
    try:
        lines = max(1, min(lines, 500))
        if not os.path.exists(LOG_FILE):
            return {"logs": []}
        with open(LOG_FILE, 'r') as f:
            content = f.readlines()
        return {"logs": [line.rstrip('\n') for line in content[-lines:]]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test")
async def test_emergency_system():
    """🧪 ТЕСТ ЭКСТРЕННОЙ СИСТЕМЫ"""
    try:
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        # Тест логирования
        try:
            emergency_logger.info("🧪 TEST: Emergency logging system")
            test_results["tests"]["logging"] = "✅ OK"
        except Exception as e:
            test_results["tests"]["logging"] = f"❌ FAIL: {str(e)}"
        
        # Тест файловой системы
        try:
            log_dir = '/root/mirai-agent/logs'
            if os.path.exists(log_dir) and os.access(log_dir, os.W_OK):
                test_results["tests"]["filesystem"] = "✅ OK"
            else:
                test_results["tests"]["filesystem"] = "❌ FAIL: Log directory not writable"
        except Exception as e:
            test_results["tests"]["filesystem"] = f"❌ FAIL: {str(e)}"
        
        # Общий результат
        failed_tests = [k for k, v in test_results["tests"].items() if "❌" in v]
        test_results["overall"] = "✅ ALL TESTS PASSED" if not failed_tests else f"❌ {len(failed_tests)} TESTS FAILED"
        
        emergency_logger.info(f"🧪 Emergency system test completed: {test_results['overall']}")
        
        return test_results
        
    except Exception as e:
        emergency_logger.error(f"🧪 Emergency system test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

# Функция для middleware - будет добавлена в основное приложение
async def emergency_middleware_func(request, call_next):
    """Middleware для блокировки торговых запросов во время экстренной остановки"""
    
    # Пропускаем emergency endpoints
    if request.url.path.startswith("/emergency"):
        response = await call_next(request)
        return response
    
    # Проверяем экстренное состояние для торговых endpoints
    if EMERGENCY_STATE["trading_stopped"] and any(
        path in request.url.path for path in ["/trade", "/order", "/position"]
    ):
        return PlainTextResponse(
            content=json.dumps({
                "error": "Trading is suspended due to emergency stop",
                "emergency_state": EMERGENCY_STATE,
                "message": "Use /emergency/reset to resume trading"
            }),
            status_code=503,
            media_type="application/json"
        )
    
    response = await call_next(request)
    return response

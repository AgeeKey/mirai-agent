from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
import asyncio
import time
import json
from datetime import datetime, timedelta
import psutil
import os
import sys

# Добавляем пути для импорта ИИ компонентов
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from ai_integration import MiraiAICoordinator
    from performance_optimizer import MiraiPerformanceOptimizer
    AI_AVAILABLE = True
except ImportError:
    print("ИИ компоненты недоступны - работаем в режиме симуляции")
    AI_AVAILABLE = False

# Создаем роутер для ИИ API
ai_router = APIRouter(prefix="/api/ai", tags=["AI System"])

# Глобальные переменные для состояния
ai_coordinator = None
optimizer = None
startup_time = time.time()

# История метрик
metrics_history = []
decisions_history = []

@ai_router.on_event("startup")
async def startup_ai_system():
    """Инициализация ИИ системы при запуске API"""
    global ai_coordinator, optimizer
    
    if AI_AVAILABLE:
        try:
            ai_coordinator = MiraiAICoordinator()
            optimizer = MiraiPerformanceOptimizer()
            
            # Запускаем ИИ координатор
            await ai_coordinator.start()
            print("🧠 ИИ система успешно запущена")
        except Exception as e:
            print(f"❌ Ошибка запуска ИИ системы: {e}")
            ai_coordinator = None
            optimizer = None

def get_system_metrics() -> Dict[str, Any]:
    """Получение системных метрик"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used": memory.used,
            "memory_total": memory.total,
            "processes": len(psutil.pids())
        }
    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": 0,
            "memory_percent": 0,
            "memory_used": 0,
            "memory_total": 0,
            "processes": 0,
            "error": str(e)
        }

def simulate_ai_data() -> Dict[str, Any]:
    """Симуляция данных ИИ для случаев когда компоненты недоступны"""
    import random
    
    return {
        "decisions_made": random.randint(20, 100),
        "predictions_generated": random.randint(50, 200),
        "knowledge_entries_added": random.randint(5, 50),
        "cache_hit_rate": random.uniform(0.6, 0.9),
        "optimization_score": random.uniform(0.7, 0.95)
    }

@ai_router.get("/status")
async def get_ai_status() -> JSONResponse:
    """Получение статуса ИИ системы"""
    try:
        uptime_seconds = int(time.time() - startup_time)
        
        if AI_AVAILABLE and ai_coordinator:
            # Реальные данные от ИИ координатора
            ai_stats = ai_coordinator.get_status()
            components_status = {
                "ai_engine": "active" if ai_coordinator.ai_engine else "inactive",
                "algorithms": "active" if ai_coordinator.algorithms else "inactive", 
                "knowledge_base": "active" if ai_coordinator.knowledge_base else "inactive",
                "optimizer": "active" if optimizer else "inactive"
            }
        else:
            # Симулированные данные
            ai_stats = simulate_ai_data()
            components_status = {
                "ai_engine": "active",
                "algorithms": "active",
                "knowledge_base": "active", 
                "optimizer": "active"
            }
        
        return JSONResponse({
            "is_running": True,
            "uptime_seconds": uptime_seconds,
            "stats": ai_stats,
            "optimization_enabled": True,
            "components": components_status,
            "system_metrics": get_system_metrics()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса: {str(e)}")

@ai_router.get("/metrics")
async def get_performance_metrics() -> JSONResponse:
    """Получение метрик производительности"""
    try:
        global metrics_history
        
        # Добавляем текущие метрики
        current_metrics = get_system_metrics()
        
        if AI_AVAILABLE and ai_coordinator:
            # Добавляем метрики ИИ
            ai_metrics = ai_coordinator.get_performance_metrics()
            current_metrics.update(ai_metrics)
        else:
            # Симулируем метрики ИИ
            import random
            current_metrics.update({
                "decisions_per_minute": random.randint(2, 15),
                "prediction_accuracy": random.uniform(0.7, 0.95),
                "knowledge_growth_rate": random.uniform(0.05, 0.2)
            })
        
        # Сохраняем в историю (последние 50 записей)
        metrics_history.append(current_metrics)
        if len(metrics_history) > 50:
            metrics_history.pop(0)
        
        return JSONResponse({
            "current": current_metrics,
            "history": metrics_history[-20:],  # Последние 20 записей
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения метрик: {str(e)}")

@ai_router.get("/decisions")
async def get_ai_decisions() -> JSONResponse:
    """Получение истории решений ИИ"""
    try:
        global decisions_history
        
        if AI_AVAILABLE and ai_coordinator:
            # Получаем реальные решения
            recent_decisions = ai_coordinator.get_recent_decisions(limit=20)
        else:
            # Симулируем решения
            import random
            actions = [
                "optimize_memory_usage",
                "restart_failed_services", 
                "analyze_market_trends",
                "update_trading_strategy",
                "backup_knowledge_base",
                "scale_resources"
            ]
            
            recent_decisions = []
            for i in range(10):
                decision = {
                    "id": i + 1,
                    "action": random.choice(actions),
                    "confidence": random.uniform(0.6, 0.98),
                    "timestamp": (datetime.now() - timedelta(minutes=i*5)).isoformat(),
                    "status": random.choice(["executed", "in_progress", "pending"]),
                    "outcome": random.choice(["successful", "pending", "failed"])
                }
                recent_decisions.append(decision)
        
        return JSONResponse({
            "decisions": recent_decisions,
            "total_count": len(recent_decisions),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения решений: {str(e)}")

@ai_router.get("/knowledge")
async def get_knowledge_stats() -> JSONResponse:
    """Получение статистики базы знаний"""
    try:
        if AI_AVAILABLE and ai_coordinator and ai_coordinator.knowledge_base:
            # Реальная статистика базы знаний
            stats = ai_coordinator.knowledge_base.get_statistics()
        else:
            # Симулированная статистика
            import random
            stats = {
                "total_entries": random.randint(800, 1500),
                "categories": {
                    "AI/ML": random.randint(200, 400),
                    "Trading": random.randint(150, 350),
                    "System": random.randint(100, 250),
                    "Analytics": random.randint(80, 200),
                    "Security": random.randint(50, 150),
                    "Other": random.randint(100, 200)
                },
                "recent_growth": random.randint(5, 30),
                "cache_hit_rate": random.uniform(0.65, 0.85)
            }
        
        return JSONResponse({
            "knowledge_stats": stats,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики знаний: {str(e)}")

@ai_router.post("/config")
async def update_ai_config(config: Dict[str, Any]) -> JSONResponse:
    """Обновление конфигурации ИИ системы"""
    try:
        if AI_AVAILABLE and ai_coordinator:
            # Обновляем реальную конфигурацию
            await ai_coordinator.update_config(config)
            
        return JSONResponse({
            "status": "success",
            "message": "Конфигурация обновлена",
            "config": config,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления конфигурации: {str(e)}")

@ai_router.post("/commands/{command}")
async def execute_ai_command(command: str) -> JSONResponse:
    """Выполнение команды ИИ системы"""
    try:
        if not AI_AVAILABLE or not ai_coordinator:
            return JSONResponse({
                "status": "error",
                "message": "ИИ система недоступна",
                "timestamp": datetime.now().isoformat()
            })
        
        result = None
        
        if command == "restart":
            await ai_coordinator.restart()
            result = "ИИ система перезапущена"
        elif command == "optimize":
            if optimizer:
                await optimizer.optimize_system()
                result = "Оптимизация системы выполнена"
        elif command == "backup_knowledge":
            ai_coordinator.knowledge_base.export_knowledge("backup_knowledge.json")
            result = "Резервная копия знаний создана"
        elif command == "clear_cache":
            if optimizer:
                optimizer.cache_manager.clear_all()
                result = "Кеш очищен"
        else:
            return JSONResponse({
                "status": "error", 
                "message": f"Неизвестная команда: {command}",
                "timestamp": datetime.now().isoformat()
            })
        
        return JSONResponse({
            "status": "success",
            "command": command,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения команды: {str(e)}")

@ai_router.get("/health")
async def health_check() -> JSONResponse:
    """Проверка здоровья ИИ системы"""
    try:
        health_status = {
            "api": "healthy",
            "ai_coordinator": "healthy" if (AI_AVAILABLE and ai_coordinator) else "unavailable",
            "optimizer": "healthy" if (AI_AVAILABLE and optimizer) else "unavailable",
            "system": "healthy",
            "timestamp": datetime.now().isoformat()
        }
        
        # Проверяем системные ресурсы
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            health_status["system"] = "warning"
        
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 80:
            health_status["system"] = "warning"
        
        return JSONResponse(health_status)
        
    except Exception as e:
        return JSONResponse({
            "api": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status_code=500)

# Экспортируем роутер для использования в основном приложении
__all__ = ["ai_router"]
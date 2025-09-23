"""
Mirai Agent - Alert Management API
API для управления системой алертов
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel

from alert_system import AlertService, AlertLevel, AlertType

app = FastAPI(title="Mirai Alert Management", description="API для управления алертами")

# Глобальный сервис алертов
alert_service = None

class AlertRequest(BaseModel):
    title: str
    message: str
    level: str = "warning"
    alert_type: str = "system"

class AlertConfigRequest(BaseModel):
    rule_name: str
    enabled: bool
    threshold: Optional[float] = None
    cooldown: Optional[int] = None

@app.on_event("startup")
async def startup_event():
    """Инициализация сервиса при запуске"""
    global alert_service
    alert_service = AlertService()
    
    # Запускаем мониторинг в фоне
    asyncio.create_task(alert_service.monitor_loop())

@app.get("/alerts/active")
async def get_active_alerts():
    """Получение активных алертов"""
    if not alert_service:
        raise HTTPException(status_code=503, detail="Alert service not available")
    
    active_alerts = alert_service.alert_manager.get_active_alerts()
    return {
        "status": "success",
        "count": len(active_alerts),
        "alerts": active_alerts
    }

@app.get("/alerts/history")
async def get_alert_history(hours: int = 24):
    """Получение истории алертов"""
    if not alert_service:
        raise HTTPException(status_code=503, detail="Alert service not available")
    
    if hours < 1 or hours > 168:  # Максимум неделя
        raise HTTPException(status_code=400, detail="Hours must be between 1 and 168")
    
    history = alert_service.alert_manager.get_alert_history(hours)
    return {
        "status": "success",
        "period_hours": hours,
        "count": len(history),
        "alerts": history
    }

@app.post("/alerts/resolve/{alert_id}")
async def resolve_alert(alert_id: str):
    """Разрешение алерта"""
    if not alert_service:
        raise HTTPException(status_code=503, detail="Alert service not available")
    
    try:
        await alert_service.alert_manager.resolve_alert(alert_id)
        return {"status": "success", "message": f"Alert {alert_id} resolved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resolving alert: {str(e)}")

@app.post("/alerts/manual")
async def create_manual_alert(alert: AlertRequest):
    """Создание ручного алерта"""
    if not alert_service:
        raise HTTPException(status_code=503, detail="Alert service not available")
    
    try:
        # Проверяем валидность уровня и типа
        try:
            level = AlertLevel(alert.level)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid alert level: {alert.level}")
        
        try:
            alert_type = AlertType(alert.alert_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid alert type: {alert.alert_type}")
        
        # Создаем алерт
        from alert_system import Alert
        import time
        
        manual_alert = Alert(
            id=f"manual_{int(time.time())}",
            type=alert_type,
            level=level,
            title=alert.title,
            message=alert.message,
            timestamp=datetime.now(),
            metadata={"source": "manual"}
        )
        
        # Сохраняем и отправляем
        await alert_service.alert_manager.save_alert(manual_alert)
        alert_service.alert_manager.active_alerts.append(manual_alert)
        await alert_service.alert_manager.send_telegram_alert(manual_alert)
        
        return {
            "status": "success",
            "alert_id": manual_alert.id,
            "message": "Manual alert created and sent"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating alert: {str(e)}")

@app.get("/alerts/rules")
async def get_alert_rules():
    """Получение списка правил алертов"""
    if not alert_service:
        raise HTTPException(status_code=503, detail="Alert service not available")
    
    rules_info = []
    for rule in alert_service.alert_manager.rules:
        rules_info.append({
            "name": rule.name,
            "level": rule.level.value,
            "type": rule.alert_type.value,
            "cooldown": rule.cooldown,
            "last_triggered": rule.last_triggered.isoformat() if rule.last_triggered else None
        })
    
    return {
        "status": "success",
        "count": len(rules_info),
        "rules": rules_info
    }

@app.get("/alerts/stats")
async def get_alert_stats():
    """Получение статистики алертов"""
    if not alert_service:
        raise HTTPException(status_code=503, detail="Alert service not available")
    
    active_count = len(alert_service.alert_manager.get_active_alerts())
    total_count = len(alert_service.alert_manager.alert_history)
    
    # Подсчет по уровням за последние 24 часа
    recent_history = alert_service.alert_manager.get_alert_history(24)
    level_counts = {}
    type_counts = {}
    
    for alert in recent_history:
        level = alert.get('level', 'unknown')
        alert_type = alert.get('type', 'unknown')
        
        level_counts[level] = level_counts.get(level, 0) + 1
        type_counts[alert_type] = type_counts.get(alert_type, 0) + 1
    
    return {
        "status": "success",
        "stats": {
            "active_alerts": active_count,
            "total_alerts": total_count,
            "alerts_24h": len(recent_history),
            "by_level_24h": level_counts,
            "by_type_24h": type_counts
        }
    }

@app.post("/alerts/test")
async def test_alert_system():
    """Тестирование системы алертов"""
    if not alert_service:
        raise HTTPException(status_code=503, detail="Alert service not available")
    
    try:
        # Создаем тестовый алерт
        from alert_system import Alert
        import time
        
        test_alert = Alert(
            id=f"test_{int(time.time())}",
            type=AlertType.SYSTEM,
            level=AlertLevel.INFO,
            title="🧪 Тест системы алертов",
            message="Это тестовое уведомление для проверки работы системы алертов.",
            timestamp=datetime.now(),
            metadata={"source": "test"}
        )
        
        # Отправляем тестовый алерт
        await alert_service.alert_manager.send_telegram_alert(test_alert)
        
        return {
            "status": "success",
            "message": "Test alert sent",
            "alert_id": test_alert.id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending test alert: {str(e)}")

@app.get("/alerts/health")
async def health_check():
    """Проверка здоровья сервиса алертов"""
    if not alert_service:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "message": "Alert service not available"}
        )
    
    return {
        "status": "healthy",
        "running": alert_service.running,
        "check_interval": alert_service.check_interval,
        "rules_count": len(alert_service.alert_manager.rules),
        "timestamp": datetime.now().isoformat()
    }

@app.on_event("shutdown")
async def shutdown_event():
    """Остановка сервиса при завершении"""
    global alert_service
    if alert_service:
        alert_service.stop()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9998)
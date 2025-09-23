# Mirai AI System - API Reference

## 🔗 Полная документация API

### Базовый URL
```
http://localhost:8000/api/ai
```

## 📊 Статус и мониторинг

### GET /status
Получение текущего статуса ИИ системы.

**Запрос:**
```http
GET /api/ai/status
Accept: application/json
```

**Ответ:**
```json
{
  "is_running": true,
  "uptime_seconds": 3600,
  "stats": {
    "decisions_made": 45,
    "predictions_generated": 128,
    "knowledge_entries_added": 23
  },
  "optimization_enabled": true,
  "components": {
    "ai_engine": "active",
    "algorithms": "active",
    "knowledge_base": "active",
    "optimizer": "active"
  },
  "system_metrics": {
    "timestamp": "2025-09-22T11:38:30.125444",
    "cpu_percent": 48.0,
    "memory_percent": 49.2,
    "memory_used": 4294967296,
    "memory_total": 8589934592,
    "processes": 142
  }
}
```

**Статусы компонентов:**
- `active` - Компонент работает нормально
- `warning` - Предупреждение, возможны проблемы
- `error` - Критическая ошибка
- `inactive` - Компонент отключен

### GET /metrics
Получение метрик производительности.

**Запрос:**
```http
GET /api/ai/metrics
Accept: application/json
```

**Ответ:**
```json
{
  "current": {
    "timestamp": "2025-09-22T11:38:30.125444",
    "cpu_percent": 48.0,
    "memory_percent": 49.2,
    "decisions_per_minute": 8,
    "prediction_accuracy": 0.85,
    "knowledge_growth_rate": 0.12
  },
  "history": [
    {
      "time": "10:00",
      "cpu": 25,
      "memory": 45,
      "decisions": 5
    },
    {
      "time": "10:05",
      "cpu": 30,
      "memory": 48,
      "decisions": 8
    }
  ],
  "timestamp": "2025-09-22T11:38:30.153880"
}
```

### GET /health
Проверка здоровья системы.

**Запрос:**
```http
GET /api/ai/health
Accept: application/json
```

**Ответ:**
```json
{
  "api": "healthy",
  "ai_coordinator": "healthy",
  "optimizer": "healthy",
  "system": "healthy",
  "timestamp": "2025-09-22T11:38:30.153880"
}
```

## 🧠 Решения ИИ

### GET /decisions
Получение истории решений ИИ.

**Параметры запроса:**
- `limit` (optional): Количество возвращаемых решений (по умолчанию: 20)
- `offset` (optional): Смещение для пагинации (по умолчанию: 0)
- `status` (optional): Фильтр по статусу (executed, in_progress, pending)

**Запрос:**
```http
GET /api/ai/decisions?limit=10&status=executed
Accept: application/json
```

**Ответ:**
```json
{
  "decisions": [
    {
      "id": 1,
      "action": "optimize_memory_usage",
      "confidence": 0.87,
      "timestamp": "2025-09-22T10:25:30",
      "status": "executed",
      "outcome": "successful",
      "context": {
        "memory_usage": 0.85,
        "trigger": "high_memory_alert"
      }
    },
    {
      "id": 2,
      "action": "restart_failed_services",
      "confidence": 0.95,
      "timestamp": "2025-09-22T10:20:15",
      "status": "executed",
      "outcome": "successful",
      "context": {
        "failed_services": ["web_interface"],
        "trigger": "health_check_failure"
      }
    }
  ],
  "total_count": 45,
  "timestamp": "2025-09-22T11:38:30.153880"
}
```

**Возможные действия (action):**
- `optimize_memory_usage` - Оптимизация использования памяти
- `restart_failed_services` - Перезапуск неработающих сервисов
- `analyze_market_trends` - Анализ рыночных трендов
- `update_trading_strategy` - Обновление торговой стратегии
- `backup_knowledge_base` - Резервное копирование базы знаний
- `scale_resources` - Масштабирование ресурсов

## 📚 База знаний

### GET /knowledge
Получение статистики базы знаний.

**Запрос:**
```http
GET /api/ai/knowledge
Accept: application/json
```

**Ответ:**
```json
{
  "knowledge_stats": {
    "total_entries": 1247,
    "categories": {
      "AI/ML": 324,
      "Trading": 289,
      "System": 198,
      "Analytics": 156,
      "Security": 98,
      "Other": 182
    },
    "recent_growth": 15,
    "cache_hit_rate": 0.78
  },
  "timestamp": "2025-09-22T11:38:30.153880"
}
```

### POST /knowledge/search
Поиск в базе знаний.

**Запрос:**
```http
POST /api/ai/knowledge/search
Content-Type: application/json

{
  "query": "machine learning algorithms",
  "category": "AI/ML",
  "limit": 10
}
```

**Ответ:**
```json
{
  "results": [
    {
      "id": "kb_001",
      "title": "Machine Learning Fundamentals",
      "content": "Introduction to machine learning concepts...",
      "category": "AI/ML",
      "tags": ["ml", "algorithms", "fundamentals"],
      "relevance_score": 0.92,
      "created_at": "2025-09-20T10:30:00"
    }
  ],
  "total_found": 15,
  "query_time": 0.045
}
```

### POST /knowledge/add
Добавление новых знаний.

**Запрос:**
```http
POST /api/ai/knowledge/add
Content-Type: application/json

{
  "title": "New Trading Strategy",
  "content": "Detailed description of the trading strategy...",
  "category": "Trading",
  "tags": ["strategy", "technical-analysis", "crypto"]
}
```

**Ответ:**
```json
{
  "status": "success",
  "knowledge_id": "kb_1234",
  "message": "Knowledge added successfully",
  "timestamp": "2025-09-22T11:38:30.153880"
}
```

## ⚙️ Конфигурация и управление

### POST /config
Обновление конфигурации ИИ системы.

**Запрос:**
```http
POST /api/ai/config
Content-Type: application/json

{
  "decision_interval": 30,
  "learning_interval": 60,
  "confidence_threshold": 0.75,
  "auto_optimization": true,
  "max_parallel_tasks": 4
}
```

**Ответ:**
```json
{
  "status": "success",
  "message": "Конфигурация обновлена",
  "config": {
    "decision_interval": 30,
    "learning_interval": 60,
    "confidence_threshold": 0.75,
    "auto_optimization": true,
    "max_parallel_tasks": 4
  },
  "timestamp": "2025-09-22T11:38:30.153880"
}
```

### POST /commands/{command}
Выполнение системных команд.

**Доступные команды:**
- `restart` - Перезапуск ИИ системы
- `optimize` - Запуск полной оптимизации
- `backup_knowledge` - Создание резервной копии знаний
- `clear_cache` - Очистка всех кешей
- `train_models` - Переобучение ML моделей
- `sync_data` - Синхронизация данных

**Запрос:**
```http
POST /api/ai/commands/optimize
Content-Type: application/json

{
  "parameters": {
    "full_optimization": true,
    "restart_services": false
  }
}
```

**Ответ:**
```json
{
  "status": "success",
  "command": "optimize",
  "result": "Оптимизация системы выполнена",
  "execution_time": 2.45,
  "details": {
    "cache_cleared": true,
    "memory_optimized": true,
    "models_updated": false
  },
  "timestamp": "2025-09-22T11:38:30.153880"
}
```

## 🤖 Алгоритмы и предсказания

### GET /algorithms
Получение информации об алгоритмах.

**Запрос:**
```http
GET /api/ai/algorithms
Accept: application/json
```

**Ответ:**
```json
{
  "algorithms": [
    {
      "id": "algo_001",
      "name": "Mean Reversion Strategy",
      "type": "trading",
      "status": "active",
      "performance": {
        "accuracy": 0.78,
        "profit_factor": 1.45,
        "trades_count": 156
      },
      "last_updated": "2025-09-22T10:00:00"
    }
  ],
  "total_algorithms": 5,
  "active_algorithms": 3
}
```

### POST /algorithms/train
Запуск обучения алгоритмов.

**Запрос:**
```http
POST /api/ai/algorithms/train
Content-Type: application/json

{
  "algorithm_ids": ["algo_001", "algo_002"],
  "training_data": {
    "source": "historical_data",
    "period": "30d",
    "symbols": ["BTCUSDT", "ETHUSDT"]
  }
}
```

**Ответ:**
```json
{
  "status": "started",
  "training_job_id": "train_job_001",
  "estimated_duration": "15 minutes",
  "algorithms_count": 2,
  "timestamp": "2025-09-22T11:38:30.153880"
}
```

### GET /predictions/{symbol}
Получение прогнозов для торгового символа.

**Запрос:**
```http
GET /api/ai/predictions/BTCUSDT
Accept: application/json
```

**Ответ:**
```json
{
  "symbol": "BTCUSDT",
  "predictions": [
    {
      "algorithm": "Mean Reversion",
      "direction": "buy",
      "confidence": 0.82,
      "target_price": 45500.0,
      "time_horizon": "24h",
      "risk_level": "medium"
    },
    {
      "algorithm": "Trend Following",
      "direction": "hold",
      "confidence": 0.65,
      "target_price": 44800.0,
      "time_horizon": "12h",
      "risk_level": "low"
    }
  ],
  "consensus": {
    "direction": "buy",
    "confidence": 0.74,
    "agreement_level": 0.68
  },
  "current_price": 44950.0,
  "timestamp": "2025-09-22T11:38:30.153880"
}
```

## 🚨 Уведомления и события

### GET /events
Получение системных событий.

**Параметры запроса:**
- `level` (optional): Уровень событий (info, warning, error)
- `limit` (optional): Количество событий (по умолчанию: 50)
- `since` (optional): События с определенного времени (ISO 8601)

**Запрос:**
```http
GET /api/ai/events?level=warning&limit=10
Accept: application/json
```

**Ответ:**
```json
{
  "events": [
    {
      "id": "event_001",
      "level": "warning",
      "component": "ai_engine",
      "message": "High CPU usage detected",
      "details": {
        "cpu_percent": 85.2,
        "threshold": 80.0
      },
      "timestamp": "2025-09-22T11:30:00",
      "acknowledged": false
    }
  ],
  "total_events": 25,
  "unacknowledged": 5
}
```

### POST /events/{event_id}/acknowledge
Подтверждение события.

**Запрос:**
```http
POST /api/ai/events/event_001/acknowledge
Content-Type: application/json

{
  "note": "Проблема решена увеличением ресурсов"
}
```

**Ответ:**
```json
{
  "status": "success",
  "event_id": "event_001",
  "acknowledged_by": "system",
  "timestamp": "2025-09-22T11:38:30.153880"
}
```

## 🔒 Аутентификация и безопасность

### Методы аутентификации

**API Key (Рекомендуется):**
```http
Authorization: Bearer your_api_key_here
```

**Basic Auth (Для разработки):**
```http
Authorization: Basic base64(username:password)
```

### Получение API ключа

**Запрос:**
```http
POST /auth/api-key
Content-Type: application/json

{
  "username": "admin",
  "password": "secure_password",
  "description": "AI monitoring dashboard"
}
```

**Ответ:**
```json
{
  "api_key": "mirai_ai_key_abc123...",
  "expires_at": "2025-12-22T11:38:30.153880",
  "permissions": ["read", "write", "admin"]
}
```

## 📝 Коды ответов

### Успешные ответы
- `200 OK` - Запрос выполнен успешно
- `201 Created` - Ресурс создан
- `202 Accepted` - Запрос принят к обработке

### Ошибки клиента
- `400 Bad Request` - Неверный формат запроса
- `401 Unauthorized` - Требуется аутентификация
- `403 Forbidden` - Недостаточно прав
- `404 Not Found` - Ресурс не найден
- `429 Too Many Requests` - Превышен лимит запросов

### Ошибки сервера
- `500 Internal Server Error` - Внутренняя ошибка сервера
- `502 Bad Gateway` - Ошибка шлюза
- `503 Service Unavailable` - Сервис недоступен

### Формат ошибок

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Missing required parameter: query",
    "details": {
      "parameter": "query",
      "expected_type": "string"
    },
    "timestamp": "2025-09-22T11:38:30.153880"
  }
}
```

## 🔄 Лимиты и ограничения

### Rate Limiting
- **Общие запросы**: 1000 запросов/час
- **Обучение алгоритмов**: 10 запросов/час
- **Поиск знаний**: 100 запросов/час
- **Команды системы**: 20 запросов/час

### Размеры данных
- **Максимальный размер запроса**: 10 MB
- **Максимальное количество записей**: 1000 за запрос
- **Максимальная длина контента знаний**: 1 MB

### Заголовки ответа
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1695385200
X-Request-ID: req_abc123
```

## 🧪 Примеры использования

### Python Client

```python
import requests
import json

class MiraiAIClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_status(self):
        response = requests.get(
            f'{self.base_url}/status',
            headers=self.headers
        )
        return response.json()
    
    def search_knowledge(self, query, category=None):
        data = {'query': query}
        if category:
            data['category'] = category
            
        response = requests.post(
            f'{self.base_url}/knowledge/search',
            headers=self.headers,
            json=data
        )
        return response.json()
    
    def execute_command(self, command, parameters=None):
        data = {'parameters': parameters} if parameters else {}
        response = requests.post(
            f'{self.base_url}/commands/{command}',
            headers=self.headers,
            json=data
        )
        return response.json()

# Использование
client = MiraiAIClient('http://localhost:8000/api/ai', 'your_api_key')

# Получение статуса
status = client.get_status()
print(f"System running: {status['is_running']}")

# Поиск знаний
results = client.search_knowledge("machine learning", "AI/ML")
print(f"Found {len(results['results'])} knowledge entries")

# Выполнение команды
result = client.execute_command("optimize", {"full_optimization": True})
print(f"Optimization result: {result['status']}")
```

### JavaScript/Node.js Client

```javascript
class MiraiAIClient {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        };
    }
    
    async getMetrics() {
        const response = await fetch(`${this.baseUrl}/metrics`, {
            headers: this.headers
        });
        return await response.json();
    }
    
    async addKnowledge(title, content, category, tags) {
        const response = await fetch(`${this.baseUrl}/knowledge/add`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                title,
                content,
                category,
                tags
            })
        });
        return await response.json();
    }
}

// Использование
const client = new MiraiAIClient('http://localhost:8000/api/ai', 'your_api_key');

// Получение метрик
client.getMetrics().then(metrics => {
    console.log('Current CPU usage:', metrics.current.cpu_percent);
});

// Добавление знаний
client.addKnowledge(
    'API Documentation',
    'Complete API reference for Mirai AI system',
    'Development',
    ['api', 'documentation', 'reference']
).then(result => {
    console.log('Knowledge added:', result.knowledge_id);
});
```

---

**Документация API обновлена:** 22 сентября 2025 г.
**Версия API:** v1.0
**Поддержка:** ai-support@mirai.system
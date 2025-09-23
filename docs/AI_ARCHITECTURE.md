# Mirai AI System Documentation

## 🧠 Архитектура искусственного интеллекта

### Общий обзор

Система искусственного интеллекта Mirai представляет собой модульную архитектуру, состоящую из нескольких взаимосвязанных компонентов, каждый из которых выполняет специализированные функции в рамках общей ИИ-экосистемы.

## 🏗️ Структура компонентов

### 1. MiraiAdvancedAI (ai_engine.py)
**Основной движок принятия решений**

```python
class MiraiAdvancedAI:
    """Продвинутый ИИ движок для принятия решений"""
    
    async def make_decision(self, context: Dict) -> Dict
    async def analyze_system_state(self) -> Dict
    def learn_from_decision(self, decision: Dict, outcome: str, analysis: Dict)
```

**Возможности:**
- Асинхронное принятие решений на основе контекста
- Анализ состояния системы в реальном времени
- Машинное обучение на основе результатов решений
- Поддержка 6 типов решений: оптимизация системы, торговые стратегии, генерация контента, управление ресурсами, безопасность, задачи разработки

**Конфигурация:**
```yaml
decision_threshold: 0.7  # Минимальный порог уверенности
learning_rate: 0.1       # Скорость обучения
context_window: 100      # Размер окна контекста
```

### 2. IntelligentAlgorithmManager (intelligent_algorithms.py)
**Система управления интеллектуальными алгоритмами**

```python
class IntelligentAlgorithmManager:
    """Менеджер интеллектуальных торговых алгоритмов"""
    
    async def train_algorithms(self, data: List[Dict]) -> bool
    async def generate_predictions(self, symbol: str) -> List[Dict]
    def get_algorithm_performance(self) -> Dict
```

**Алгоритмы:**
- **TradingAlgorithm**: Базовый класс для торговых алгоритмов
- **AnalyticsEngine**: Аналитический движок для обработки данных
- **MarketDataCollector**: Сбор и обработка рыночных данных

**ML модели:**
- RandomForestRegressor для прогнозирования цен
- LinearRegression для трендового анализа
- SVM для классификации рыночных паттернов

### 3. MiraiKnowledgeBase (knowledge_base.py)
**Система управления знаниями**

```python
class MiraiKnowledgeBase:
    """Система управления знаниями с семантическим анализом"""
    
    async def add_knowledge(self, title: str, content: str, category: str, tags: List[str]) -> str
    async def search_knowledge(self, query: str) -> List[Dict]
    def get_statistics(self) -> Dict
```

**Компоненты:**
- **KnowledgeGraph**: Граф знаний для связывания информации
- **SemanticAnalyzer**: Семантический анализ и категоризация
- **Автоматическая индексация**: TF-IDF векторизация для поиска

**База данных:**
```sql
-- Основная таблица знаний
CREATE TABLE knowledge (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT,
    tags TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Граф связей между знаниями
CREATE TABLE knowledge_relations (
    topic1 TEXT,
    topic2 TEXT,
    weight REAL,
    PRIMARY KEY (topic1, topic2)
);
```

### 4. MiraiPerformanceOptimizer (performance_optimizer.py)
**Система оптимизации производительности**

```python
class MiraiPerformanceOptimizer:
    """Оптимизатор производительности ИИ системы"""
    
    def optimize_system(self) -> Dict
    def _collect_performance_metrics(self) -> PerformanceMetrics
    async def parallel_optimize(self, tasks: List) -> List
```

**Подсистемы:**
- **CacheManager**: LRU кеширование с настраиваемым размером
- **MemoryPool**: Пул памяти для оптимизации выделения ресурсов
- **BatchProcessor**: Пакетная обработка для увеличения пропускной способности
- **ParallelExecutor**: Параллельное выполнение задач

**Метрики:**
```python
@dataclass
class PerformanceMetrics:
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_io_read: int
    disk_io_write: int
    network_io_recv: int
    network_io_sent: int
    model_inference_time: float
    decision_making_time: float
    knowledge_query_time: float
```

### 5. MiraiAICoordinator (ai_integration.py)
**Координатор ИИ-системы**

```python
class MiraiAICoordinator:
    """Центральный координатор всех ИИ компонентов"""
    
    async def coordination_cycle(self) -> None
    def stats(self) -> Dict
    async def parallel_task_execution(self, tasks: List[Task]) -> List
```

**Функции координации:**
- Управление жизненным циклом всех ИИ компонентов
- Планирование и распределение задач
- Мониторинг производительности
- Автоматическое восстановление при сбоях

## 🔧 API интерфейсы

### REST API Endpoints

#### AI Status
```http
GET /api/ai/status
Content-Type: application/json

Response:
{
  "is_running": true,
  "uptime_seconds": 3600,
  "stats": {
    "decisions_made": 45,
    "predictions_generated": 128,
    "knowledge_entries_added": 23
  },
  "components": {
    "ai_engine": "active",
    "algorithms": "active",
    "knowledge_base": "active",
    "optimizer": "active"
  }
}
```

#### Performance Metrics
```http
GET /api/ai/metrics
Content-Type: application/json

Response:
{
  "current": {
    "timestamp": "2025-09-22T11:38:30.125444",
    "cpu_percent": 48.0,
    "memory_percent": 49.2,
    "decisions_per_minute": 8
  },
  "history": [...],
  "timestamp": "2025-09-22T11:38:30.153880"
}
```

#### AI Decisions
```http
GET /api/ai/decisions
Content-Type: application/json

Response:
{
  "decisions": [
    {
      "id": 1,
      "action": "optimize_memory_usage",
      "confidence": 0.87,
      "timestamp": "2025-09-22T10:25:30",
      "status": "executed",
      "outcome": "successful"
    }
  ],
  "total_count": 10
}
```

#### Knowledge Base
```http
GET /api/ai/knowledge
Content-Type: application/json

Response:
{
  "knowledge_stats": {
    "total_entries": 1247,
    "categories": {
      "AI/ML": 324,
      "Trading": 289,
      "System": 198
    },
    "recent_growth": 15,
    "cache_hit_rate": 0.78
  }
}
```

#### System Commands
```http
POST /api/ai/commands/{command}
Content-Type: application/json

Available commands:
- restart: Перезапуск ИИ системы
- optimize: Запуск полной оптимизации
- backup_knowledge: Создание резервной копии знаний
- clear_cache: Очистка всех кешей

Response:
{
  "status": "success",
  "command": "optimize",
  "result": "Оптимизация системы выполнена",
  "timestamp": "2025-09-22T11:38:30"
}
```

## 🚀 Развертывание и конфигурация

### Установка зависимостей

```bash
# Создание виртуального окружения
python3 -m venv ai_env
source ai_env/bin/activate

# Установка ML библиотек
pip install numpy pandas scikit-learn

# Дополнительные зависимости
pip install requests aiofiles psutil
```

### Запуск компонентов

```python
# Инициализация ИИ координатора
ai_coordinator = MiraiAICoordinator()

# Запуск основного цикла
await ai_coordinator.coordination_cycle()

# Получение статуса
status = ai_coordinator.stats()
```

### Конфигурационные файлы

**ai_config.yaml:**
```yaml
ai_engine:
  decision_threshold: 0.7
  learning_rate: 0.1
  context_window: 100
  max_decisions_per_minute: 10

knowledge_base:
  max_entries: 10000
  cache_size: 1000
  auto_categorize: true
  search_limit: 50

performance_optimizer:
  cache_size: 1000
  memory_pool_size: 100
  batch_size: 10
  parallel_workers: 4

algorithms:
  training_interval: 3600  # секунды
  prediction_models: ["random_forest", "linear_regression"]
  market_data_sources: ["binance", "local"]
```

## 🔍 Мониторинг и отладка

### Логирование

Все компоненты используют структурированное логирование:

```python
import logging

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Примеры логов
2025-09-22 11:38:30,109 - MiraiAI - INFO - Загружено 0 элементов знаний
2025-09-22 11:38:30,140 - MiraiKnowledgeBase - INFO - 📊 Загружен граф знаний: 0 узлов, 0 рёбер
```

### Веб-дашборд

Доступен по адресу: `http://localhost:8080/ai_dashboard.html`

**Функции дашборда:**
- Мониторинг статуса всех компонентов в реальном времени
- Визуализация метрик производительности
- История принятых решений
- Статистика базы знаний
- Управление конфигурацией системы

### Тестирование

```bash
# Запуск полного набора тестов
python3 test_ai_system_fixed.py

# Запуск отдельных компонентов
python3 -m unittest TestAIEngine
python3 -m unittest TestKnowledgeBase
python3 -m unittest TestPerformanceOptimizer
```

**Отчет о тестировании:**
- Всего тестов: 16
- Успешность: 43.8%
- Основные проблемы: асинхронные методы, совместимость API

## 🛠️ Разработка и расширение

### Добавление нового алгоритма

```python
class CustomTradingAlgorithm(TradingAlgorithm):
    def __init__(self, name: str):
        super().__init__(name, "custom")
    
    async def analyze_market(self, data: Dict) -> Dict:
        # Пользовательская логика анализа
        return {"signal": "buy", "confidence": 0.8}
    
    def train(self, historical_data: List[Dict]):
        # Обучение алгоритма
        pass

# Регистрация в менеджере
algorithm_manager.register_algorithm("custom_algo", CustomTradingAlgorithm)
```

### Расширение базы знаний

```python
# Добавление нового типа знаний
knowledge_base.semantic_analyzer.add_category("custom_category")

# Добавление знаний
await knowledge_base.add_knowledge(
    "Custom Knowledge",
    "Detailed content about custom topic",
    "custom_category",
    ["custom", "knowledge", "ai"]
)
```

### Создание пользовательских метрик

```python
class CustomMetrics:
    def collect_custom_metrics(self) -> Dict:
        return {
            "custom_metric_1": 42,
            "custom_metric_2": "active",
            "timestamp": datetime.now().isoformat()
        }

# Интеграция в координатор
ai_coordinator.add_metrics_collector(CustomMetrics())
```

## 📚 Справочная информация

### Типы решений ИИ

1. **SYSTEM_OPTIMIZATION** - Оптимизация системных ресурсов
2. **TRADING_STRATEGY** - Торговые стратегии и решения
3. **CONTENT_GENERATION** - Генерация контента и документации
4. **RESOURCE_ALLOCATION** - Распределение ресурсов
5. **SECURITY_ACTION** - Действия по безопасности
6. **DEVELOPMENT_TASK** - Задачи разработки

### Категории знаний

- **AI/ML** - Машинное обучение и искусственный интеллект
- **Trading** - Торговые стратегии и рыночная аналитика
- **System** - Системное администрирование
- **Analytics** - Аналитика и статистика
- **Security** - Информационная безопасность
- **Development** - Разработка программного обеспечения

### Коды состояний компонентов

- **active** - Компонент работает нормально
- **warning** - Предупреждение, требует внимания
- **error** - Ошибка, требует вмешательства
- **offline** - Компонент недоступен

## 🔮 Планы развития

### Краткосрочные цели
- [ ] Исправление async/await совместимости
- [ ] Улучшение тестового покрытия
- [ ] Оптимизация производительности ML моделей
- [ ] Расширение веб-дашборда

### Долгосрочные цели
- [ ] Интеграция с внешними AI API (OpenAI, Anthropic)
- [ ] Распределенная архитектура для масштабирования
- [ ] Автономное самообучение и эволюция
- [ ] Интеграция с блокчейн технологиями

---

**Документация обновлена:** 22 сентября 2025 г.
**Версия системы:** Mirai AI v1.0
**Статус:** Активная разработка
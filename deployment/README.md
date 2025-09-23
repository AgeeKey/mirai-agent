# Mirai Agent Production Deployment

Полное руководство по развертыванию Mirai Agent на продакшн серверах с поддержкой двух доменов:
- **aimirai.online** - трейдинг платформа
- **aimirai.info** - онлайн услуги

## 📋 Требования

### Системные требования
- Ubuntu 20.04+ или CentOS 8+
- Docker 20.10+
- Docker Compose 2.0+
- Минимум 4GB RAM
- Минимум 20GB свободного места
- Права root или пользователь в группе docker

### Сетевые требования
- Открытые порты: 80, 443
- DNS записи для доменов указывают на сервер
- Доступ к интернету для SSL сертификатов

## 🚀 Быстрый старт

### 1. Подготовка окружения
```bash
# Клонируйте репозиторий
git clone <repository-url>
cd mirai-agent

# Настройте окружение
./deployment/setup-environment.sh
```

### 2. Развертывание
```bash
# Запустите развертывание
./deployment/deploy-production.sh
```

### 3. Проверка
```bash
# Проверьте статус сервисов
./deployment/manage.sh status

# Проверьте здоровье системы
./deployment/manage.sh health
```

## 📁 Структура deployment

```
deployment/
├── docker-compose.production.yml  # Основной compose файл
├── deploy-production.sh          # Скрипт развертывания
├── setup-environment.sh          # Настройка окружения
├── manage.sh                     # Управление deployment
├── nginx/                        # Nginx конфигурации
│   ├── nginx.conf                # Основная конфигурация
│   ├── aimirai.online.conf       # Трейдинг платформа
│   └── aimirai.info.conf         # Сервисы платформа
└── sql/                          # SQL схемы
    ├── init-databases.sql        # Инициализация БД
    ├── trading-schema.sql        # Схема для трейдинга
    └── services-schema.sql       # Схема для сервисов
```

## 🔧 Управление deployment

### Основные команды
```bash
# Запуск всех сервисов
./deployment/manage.sh start

# Остановка всех сервисов
./deployment/manage.sh stop

# Перезапуск сервисов
./deployment/manage.sh restart

# Просмотр статуса
./deployment/manage.sh status

# Просмотр логов
./deployment/manage.sh logs [service_name]

# Обновление сервисов
./deployment/manage.sh update
```

### Резервное копирование
```bash
# Создание резервной копии
./deployment/manage.sh backup

# Восстановление из резервной копии
./deployment/manage.sh restore /path/to/backup
```

### Масштабирование
```bash
# Масштабирование сервиса
./deployment/manage.sh scale mirai-api-trading 3

# Проверка здоровья
./deployment/manage.sh health
```

## 🌐 Архитектура

### Домены и сервисы

#### aimirai.online (Трейдинг платформа)
- **Nginx Proxy** → API Gateway → Микросервисы
- **Трейдинг API** (порт 8000)
- **Dashboard** (порт 3000)
- **WebSocket** для real-time данных
- **JWT аутентификация**

#### aimirai.info (Онлайн услуги)
- **Public API** для внешних клиентов
- **AI сервисы** (анализ, прогнозы)
- **Аналитика и отчеты**
- **Rate limiting** для API
- **Публичный доступ**

### Компоненты системы

| Сервис | Назначение | Порты |
|--------|------------|-------|
| nginx | Reverse proxy, SSL termination | 80, 443 |
| mirai-api-trading | Trading API для aimirai.online | 8000 |
| mirai-api-services | Services API для aimirai.info | 8080 |
| mirai-dashboard-trading | Web UI для трейдинга | 3000 |
| mirai-dashboard-services | Web UI для сервисов | 3001 |
| postgres | База данных | 5432 |
| redis | Кэш и сессии | 6379 |
| prometheus | Мониторинг | 9090 |
| grafana | Dashboards | 3000 |

## 🔒 Безопасность

### SSL/TLS
- Автоматические Let's Encrypt сертификаты
- Принудительное перенаправление HTTP → HTTPS
- Modern SSL конфигурация (TLS 1.2+)
- HSTS заголовки

### Аутентификация
- JWT токены для API доступа
- Роли и разрешения
- Rate limiting по IP
- API ключи для внешних клиентов

### Сетевая безопасность
- Изолированные Docker сети
- Firewall конфигурация
- Ограничение административного доступа

## 📊 Мониторинг

### Метрики
- **Prometheus** собирает метрики со всех сервисов
- **Grafana** предоставляет dashboards
- **Health checks** для всех компонентов

### Логирование
- Централизованные логи через Fluentd
- Ротация логов
- Structured logging в JSON формате

### Алерты
- Уведомления через Telegram bot
- Email алерты (опционально)
- Webhook интеграции

## 🔄 CI/CD

### Автоматическое развертывание
1. Git push → GitHub Actions
2. Build Docker images
3. Push to registry
4. Deploy to production
5. Health checks
6. Rollback при ошибках

### Blue-Green Deployment
```bash
# Развертывание с zero downtime
./deployment/blue-green-deploy.sh
```

## 🛠️ Troubleshooting

### Проверка логов
```bash
# Логи конкретного сервиса
./deployment/manage.sh logs nginx

# Логи всех сервисов
./deployment/manage.sh logs

# Логи за последний час
docker-compose -f deployment/docker-compose.production.yml logs --since 1h
```

### Общие проблемы

#### Сервис не запускается
```bash
# Проверьте статус
docker-compose -f deployment/docker-compose.production.yml ps

# Проверьте логи ошибок
docker-compose -f deployment/docker-compose.production.yml logs service_name
```

#### SSL проблемы
```bash
# Обновите сертификаты
./deployment/manage.sh ssl-renew

# Проверьте сертификаты
openssl s_client -connect aimirai.online:443
```

#### База данных недоступна
```bash
# Проверьте статус PostgreSQL
docker exec mirai-postgres pg_isready -U mirai_admin

# Перезапустите базу данных
docker-compose -f deployment/docker-compose.production.yml restart postgres
```

## 📈 Производительность

### Оптимизация
- Nginx кэширование статических файлов
- Redis кэширование данных
- Connection pooling для БД
- Gzip сжатие
- CDN для статических активов (опционально)

### Масштабирование
```bash
# Горизонтальное масштабирование API
./deployment/manage.sh scale mirai-api-trading 3
./deployment/manage.sh scale mirai-api-services 2

# Мониторинг нагрузки
./deployment/manage.sh health
```

## 🔧 Конфигурация

### Переменные окружения
Основные настройки в `.env.production`:

```bash
# Базы данных
POSTGRES_ADMIN_PASSWORD=secure_password
POSTGRES_TRADING_PASSWORD=secure_password
POSTGRES_SERVICES_PASSWORD=secure_password

# Безопасность
JWT_SECRET=your_jwt_secret

# Трейдинг
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
BINANCE_TESTNET=true

# Домены
DOMAIN_TRADING=aimirai.online
DOMAIN_SERVICES=aimirai.info
```

### Кастомизация
- Nginx конфигурации в `deployment/nginx/`
- База данных схемы в `deployment/sql/`
- Мониторинг настройки в `deployment/monitoring/`

## 📞 Поддержка

### Contacts
- **Email**: admin@aimirai.info
- **Telegram**: @mirai_support
- **Issues**: GitHub Issues

### Документация
- [API Documentation](../docs/API_DOCUMENTATION.md)
- [Developer Guide](../docs/DEVELOPER_GUIDE.md)
- [Security Guide](../docs/SECURITY.md)

---

**⚠️ Важно**: Перед развертыванием на продакшн обязательно протестируйте на staging окружении!
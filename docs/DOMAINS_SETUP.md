# 🌐 Mirai Domains Configuration

## 📍 Домены проекта

### 🔥 **aimirai.online** - Торговая платформа
- **Назначение**: Основная торговая платформа с AI-агентом
- **Функции**: 
  - Автономная торговля
  - Portfolio management
  - Real-time аналитика
  - API для интеграций
- **Интерфейс**: Профессиональный trading dashboard

### 🎨 **aimirai.info** - Студия Mirai-chan
- **Назначение**: Персональное пространство Mirai-chan
- **Функции**:
  - Личные чаты с Mirai-chan
  - Voice interactions
  - Character development
  - Creative content
- **Интерфейс**: Аниме-стиль, персональный

---

## 🚀 Настройка доменов

### 1. **DNS конфигурация**
Убедитесь, что DNS записи указывают на ваш сервер:
```
aimirai.online      A    212.56.33.1
www.aimirai.online  A    212.56.33.1
aimirai.info        A    212.56.33.1
www.aimirai.info    A    212.56.33.1
```

### 2. **Автоматическая настройка**
```bash
cd /root/mirai-agent
sudo ./scripts/setup_domains.sh
```

**Что будет настроено:**
- ✅ Nginx reverse proxy
- ✅ SSL сертификаты (Let's Encrypt)
- ✅ HTTP→HTTPS редиректы
- ✅ Rate limiting
- ✅ Security headers
- ✅ Автообновление сертификатов

### 3. **Ручная настройка**
```bash
# Установка Nginx
sudo apt update && sudo apt install -y nginx certbot python3-certbot-nginx

# Копирование конфигурации
sudo cp nginx/mirai-domains.conf /etc/nginx/sites-available/mirai-domains
sudo ln -s /etc/nginx/sites-available/mirai-domains /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Получение SSL сертификатов
sudo certbot --nginx -d aimirai.online -d www.aimirai.online
sudo certbot --nginx -d aimirai.info -d www.aimirai.info

# Перезапуск Nginx
sudo nginx -t && sudo systemctl reload nginx
```

---

## 🔄 Маршрутизация трафика

### **aimirai.online** (Trading Platform)
```
https://aimirai.online/          → Next.js Frontend (Port 3000)
https://aimirai.online/api/      → FastAPI Backend (Port 8000)
https://aimirai.online/docs      → API Documentation
https://aimirai.online/ws        → WebSocket (Real-time data)
```

### **aimirai.info** (Mirai-chan Studio)
```
https://aimirai.info/           → Mirai-chan Interface (Port 3000)
https://aimirai.info/api/       → API with studio context
https://aimirai.info/ws         → WebSocket for interactions
```

---

## 🛡️ Безопасность

### **SSL/TLS**
- Автоматические сертификаты Let's Encrypt
- TLS 1.2/1.3 только
- HSTS headers
- Автообновление каждые 60 дней

### **Security Headers**
- X-Frame-Options: SAMEORIGIN
- X-XSS-Protection: 1; mode=block
- X-Content-Type-Options: nosniff
- Content Security Policy

### **Rate Limiting**
- API: 10 req/sec per IP
- Login: 1 req/sec per IP
- Burst protection

---

## 📊 Мониторинг

### **Проверка статуса**
```bash
./scripts/setup_domains.sh status
```

### **Тест доменов**
```bash
./scripts/setup_domains.sh test
```

### **Логи Nginx**
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## 🎯 Различия между доменами

| Функция | aimirai.online | aimirai.info |
|---------|----------------|--------------|
| **Основная цель** | Торговля | Персональный AI |
| **Интерфейс** | Professional UI | Anime-style UI |
| **API Context** | Trading focus | Character focus |
| **WebSocket** | Market data | Chat/Voice |
| **Аудитория** | Трейдеры | Пользователи AI |
| **Функции** | Portfolio, Analytics | Chat, Voice, Personality |

---

## 🔧 Управление

### **Статус сервисов**
```bash
./manage_services.sh status
```

### **Перезапуск**
```bash
sudo systemctl reload nginx
./manage_services.sh restart
```

### **Обновление SSL**
```bash
sudo certbot renew
```

---

## 🎉 Готовые ссылки

После настройки будут доступны:

### 🔥 **Торговая платформа**
- **Main**: https://aimirai.online
- **API Docs**: https://aimirai.online/docs
- **WebSocket**: wss://aimirai.online/ws

### 🎨 **Студия Mirai-chan**
- **Main**: https://aimirai.info
- **Chat API**: https://aimirai.info/api
- **Voice WS**: wss://aimirai.info/ws

---

## 🛠️ Troubleshooting

### **DNS не резолвится**
```bash
nslookup aimirai.online
# Проверьте DNS записи у провайдера
```

### **SSL ошибки**
```bash
sudo certbot certificates
sudo certbot renew --dry-run
```

### **Nginx ошибки**
```bash
sudo nginx -t
sudo journalctl -u nginx -f
```

### **Сервисы не отвечают**
```bash
./manage_services.sh status
ps aux | grep -E "(uvicorn|npm)"
```

**🌐 Ваши домены готовы к работе с полной AI торговой платформой!**
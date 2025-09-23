FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    httpx==0.25.2 \
    pydantic==2.5.0 \
    python-json-logger==2.0.7 \
    websockets==12.0

# Создаем директории
RUN mkdir -p /app/logs /shared/data /shared/reports /shared/knowledge

# Копируем приложение
COPY main.py .

# Создаем пользователя для безопасности
RUN useradd -m -u 1000 orchestrator && \
    chown -R orchestrator:orchestrator /app /shared
USER orchestrator

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Запуск приложения
CMD ["python", "main.py"]
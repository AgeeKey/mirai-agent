FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project root files first
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# Install telegram bot specific dependencies
RUN pip install --no-cache-dir python-telegram-bot>=20.0

# Copy application code with proper structure
COPY app/ /app/app/

# Set the Python path
ENV PYTHONPATH=/app

# Create non-root user for security
RUN useradd -m -u 1001 mirai && \
    chown -R mirai:mirai /app
USER mirai

# Run the telegram bot
CMD ["python", "-m", "app.telegram_bot.main"]
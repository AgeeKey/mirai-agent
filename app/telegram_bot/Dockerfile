FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install telegram bot specific dependencies
RUN pip install --no-cache-dir python-telegram-bot>=20.0

# Copy application code
COPY app/ /app/

# Set the Python path
ENV PYTHONPATH=/app

# Run the telegram bot
CMD ["python", "telegram_bot/main.py"]
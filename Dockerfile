# Multi-stage build for Mirai Agent Web Panel
FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs and state directories
RUN mkdir -p logs state

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV WEB_PORT=8000

# Create non-root user for security
RUN useradd -m -u 1001 mirai && \
    chown -R mirai:mirai /app
USER mirai

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/status || exit 1

# Default command
CMD ["uvicorn", "app.web.api:app", "--host", "0.0.0.0", "--port", "8000"]
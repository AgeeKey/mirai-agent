FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install the package
COPY app/api/pyproject.toml /app/
COPY app/api/mirai_api /app/mirai_api

# Install the package and its dependencies
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -e .

# Create non-root user for security
RUN useradd -m -u 1001 mirai && \
    chown -R mirai:mirai /app
USER mirai

# Add health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

EXPOSE 8000

# Use proper host binding for Docker
CMD ["uvicorn", "mirai_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
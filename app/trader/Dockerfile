FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install the package
COPY app/trader/pyproject.toml /app/
COPY app/trader/mirai_trader /app/mirai_trader

# Install the package and its dependencies
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -e .

# Create non-root user for security
RUN useradd -m -u 1001 mirai && \
    chown -R mirai:mirai /app
USER mirai

# Add health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import mirai_trader; print('healthy')" || exit 1

# Run the trader
CMD ["python", "-m", "mirai_trader.core"]
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install the package
COPY pyproject.toml /app/
COPY mirai_trader /app/mirai_trader

# Install the package and its dependencies
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -e .

# Run the trader
CMD ["python", "-c", "import time; print('mirai-trader up'); time.sleep(3600)"]
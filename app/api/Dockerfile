FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install the package
COPY pyproject.toml /app/
COPY mirai_api /app/mirai_api

# Install the package and its dependencies
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -e .

EXPOSE 8000

# Use proper host binding for Docker
CMD ["uvicorn", "mirai_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
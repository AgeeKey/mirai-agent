FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml /app/
RUN pip install --no-cache-dir -U pip
COPY mirai_trader /app/mirai_trader
CMD ["python","-c","import time; print('mirai-trader up'); time.sleep(3600)"]
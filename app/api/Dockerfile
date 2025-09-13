FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml /app/
RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir -e .
COPY mirai_api /app/mirai_api
EXPOSE 8000
CMD ["uvicorn","mirai_api.main:app","--host","127.0.0.1","--port","8000"]
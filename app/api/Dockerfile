FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml /app/
RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir "uvicorn[standard]" "fastapi"
COPY mirai_api /app/mirai_api
EXPOSE 8000
CMD ["uvicorn","mirai_api.main:app","--host","0.0.0.0","--port","8000"]
from fastapi import FastAPI

app = FastAPI(title="Mirai API")
@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "mirai-api"}
import os

import uvicorn
from fastapi import FastAPI

app = FastAPI(title="Mirai API")

@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "mirai-api"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("WEB_PORT", "8000")))
#!/usr/bin/env python3
"""
Простой автономный HTTP-сервис для проверки работы терминала и пайплайнов.
Без внешних зависимостей (только стандартная библиотека).

Эндпоинты:
  - GET  /healthz  -> {"status":"ok"}
  - GET  /status   -> {"pid":..., "cwd":..., "time":..., "env":{...}}
  - POST /echo     -> эхо-ответ с присланным JSON и длиной тела
  - POST /sum      -> суммирует массив numbers в JSON: {"numbers":[...]} -> {"sum": ...}

Запуск:
  python3 scripts/autonomy_test_server.py [--port 9099]
"""
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse


def _json_response(handler: BaseHTTPRequestHandler, data: dict, code: int = 200):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    server_version = "MiraiAutonomyTest/1.0"

    def log_message(self, fmt, *args):
        # Чистый лаконичный лог в stdout
        sys.stdout.write("[%s] %s\n" % (time.strftime("%H:%M:%S"), fmt % args))

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/healthz":
            return _json_response(self, {"status": "ok", "ts": time.time()})
        if path == "/status":
            data = {
                "pid": os.getpid(),
                "cwd": os.getcwd(),
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "env": {k: v for k, v in os.environ.items() if k.startswith(("PATH", "PYTHON", "MIRAI", "VSCODE", "COPILOT"))},
            }
            return _json_response(self, data)
        return _json_response(self, {"error": "not_found", "path": path}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return _json_response(self, {"error": "invalid_json", "raw_len": len(raw)}, 400)

        if path == "/echo":
            return _json_response(self, {"received": payload, "raw_len": len(raw)})
        if path == "/sum":
            nums = payload.get("numbers", [])
            try:
                s = sum(float(x) for x in nums)
            except Exception:
                return _json_response(self, {"error": "numbers_must_be_numeric"}, 400)
            return _json_response(self, {"sum": s, "count": len(nums)})

        return _json_response(self, {"error": "not_found", "path": path}, 404)


def main(argv: list[str]) -> int:
    port = 9099
    if len(argv) >= 2 and argv[1] in {"-p", "--port"}:
        try:
            port = int(argv[2])
        except Exception:
            print("Invalid port, using default 9099", file=sys.stderr)
            port = 9099

    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"🚀 Autonomy Test Server listening on http://0.0.0.0:{port}")
    print("Endpoints: /healthz, /status, POST /echo, POST /sum")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

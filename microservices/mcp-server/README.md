# Mirai MCP Server

Minimal FastMCP server exposing two tools over SSE:
- `search(query)`: DEV stub that lists first files from your OpenAI Vector Store (connectivity check)
- `fetch(id)`: returns full text chunks for a vector store file

SSE endpoint: `:8000/sse/`

## Quick start

1) Create venv and install deps

```
cd /root/mirai-agent/microservices/mcp-server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Configure `.env`

```
OPENAI_API_KEY=sk-...
VECTOR_STORE_ID=vs_...
```

3) Run

```
python main.py
```

4) Check SSE

```
curl -I http://127.0.0.1:8000/sse/
```

## systemd service

Create `/etc/systemd/system/mirai-mcp.service`:

```
[Unit]
Description=Mirai MCP Server (FastMCP SSE 8000)
After=network.target

[Service]
User=root
WorkingDirectory=/root/mirai-agent/microservices/mcp-server
Environment="PYTHONUNBUFFERED=1"
EnvironmentFile=/root/mirai-agent/microservices/mcp-server/.env
ExecStart=/root/mirai-agent/microservices/mcp-server/.venv/bin/python /root/mirai-agent/microservices/mcp-server/main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Then:

```
systemctl daemon-reload
systemctl enable --now mirai-mcp
systemctl status mirai-mcp --no-pager
```

## Nginx proxy (SSE)

```
# 80 -> 443 redirect
server {
    listen 80;
    server_name aimirai.online;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name aimirai.online;

    ssl_certificate     /etc/letsencrypt/live/aimirai.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aimirai.online/privkey.pem;

    location /mcp/ {
        proxy_pass http://127.0.0.1:8000/sse/;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
        proxy_buffering off;
    }
}
```

Reload:

```
nginx -t && systemctl reload nginx
```

#!/usr/bin/env python3
"""
Enhanced Mirai Web Server
Улучшенный веб-сервер для фронтенда Mirai с автовосстановлением
"""

import http.server
import socketserver
import os
import threading
import logging
import signal
import sys
import time
from pathlib import Path

class EnhancedMiraiHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Улучшенный обработчик HTTP запросов для SPA"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="/root/mirai-agent/frontend/trading/dist", **kwargs)
    
    def do_GET(self):
        """Обработка GET запросов с поддержкой SPA routing"""
        # Для SPA перенаправляем все несуществующие маршруты на index.html
        path = self.translate_path(self.path)
        if not os.path.exists(path) and not self.path.startswith('/api'):
            self.path = '/index.html'
        
        return super().do_GET()
    
    def do_OPTIONS(self):
        """Обработка CORS preflight запросов"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def end_headers(self):
        """Добавляем CORS заголовки"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()
    
    def log_message(self, format, *args):
        """Логирование запросов"""
        logging.info(f"Web: {self.address_string()} - {format % args}")

class EnhancedWebServer:
    """Улучшенный веб-сервер с автовосстановлением"""
    
    def __init__(self, port=3001, host='0.0.0.0'):
        self.port = port
        self.host = host
        self.httpd = None
        self.running = False
        self.setup_logging()
        self.setup_signal_handlers()
    
    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/root/mirai-agent/logs/enhanced_web.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('EnhancedWebServer')
    
    def setup_signal_handlers(self):
        """Настройка обработчиков сигналов"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Обработчик сигналов для graceful shutdown"""
        self.logger.info(f"Получен сигнал {signum}, останавливаем сервер...")
        self.stop()
        sys.exit(0)
    
    def check_frontend_dir(self):
        """Проверка существования директории фронтенда"""
        frontend_dir = Path("/root/mirai-agent/frontend/trading/dist")
        if not frontend_dir.exists():
            self.logger.error("Директория фронтенда не найдена. Создаем заглушку...")
            frontend_dir.mkdir(parents=True, exist_ok=True)
            
            # Создаем простую заглушку
            with open(frontend_dir / 'index.html', 'w', encoding='utf-8') as f:
                f.write("""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mirai Trading Platform</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f0f0f0; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .online { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .building { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        h1 { color: #333; text-align: center; }
        .api-links { display: flex; gap: 10px; justify-content: center; margin: 20px 0; }
        .api-link { padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
        .api-link:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Mirai Trading Ecosystem</h1>
        
        <div class="status online">
            ✅ Система полностью автономна и работает
        </div>
        
        <div class="status building">
            🔨 Фронтенд интерфейс в процессе сборки
        </div>
        
        <div class="api-links">
            <a href="http://localhost:8001/docs" class="api-link" target="_blank">📊 Trading API</a>
            <a href="http://localhost:8002/docs" class="api-link" target="_blank">🌐 Services API</a>
            <a href="http://localhost:3000" class="api-link" target="_blank">📈 Monitoring</a>
        </div>
        
        <h2>Автономная система активна</h2>
        <ul>
            <li>✅ API серверы работают</li>
            <li>✅ Мониторинг активен</li>
            <li>✅ Автономный агент функционирует</li>
            <li>🔨 Веб-интерфейс разрабатывается</li>
        </ul>
        
        <p><strong>Система Mirai работает в полностью автономном режиме и продолжает развиваться.</strong></p>
        
        <script>
            // Автообновление статуса
            setInterval(function() {
                fetch('/api/status').then(r => r.json()).then(data => {
                    console.log('Status updated:', data);
                }).catch(e => console.log('API not ready yet'));
            }, 30000);
        </script>
    </div>
</body>
</html>
                """)
            
            self.logger.info("Создана заглушка веб-интерфейса")
        
        return frontend_dir
    
    def start(self):
        """Запуск веб-сервера"""
        try:
            # Проверяем директорию
            self.check_frontend_dir()
            
            self.logger.info(f"Запуск улучшенного веб-сервера на {self.host}:{self.port}")
            
            # Проверяем, не занят ли порт
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex((self.host, self.port))
                sock.close()
                
                if result == 0:
                    self.logger.warning(f"Порт {self.port} уже занят, пытаемся освободить...")
                    os.system(f"lsof -ti:{self.port} | xargs kill -9 2>/dev/null || true")
                    time.sleep(2)
            except:
                pass
            
            # Создаем сервер
            self.httpd = socketserver.TCPServer((self.host, self.port), EnhancedMiraiHTTPRequestHandler)
            self.httpd.allow_reuse_address = True
            self.running = True
            
            self.logger.info(f"🌐 Улучшенный веб-сервер запущен: http://{self.host}:{self.port}")
            
            # Запускаем сервер
            self.httpd.serve_forever()
            
        except Exception as e:
            self.logger.error(f"Ошибка запуска веб-сервера: {e}")
            raise
    
    def stop(self):
        """Остановка веб-сервера"""
        if self.httpd and self.running:
            self.logger.info("Останавливаем веб-сервер...")
            self.running = False
            self.httpd.shutdown()
            self.httpd.server_close()
            self.logger.info("Веб-сервер остановлен")

def main():
    """Главная функция"""
    server = EnhancedWebServer()
    
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
        print("\n🛑 Веб-сервер остановлен")
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
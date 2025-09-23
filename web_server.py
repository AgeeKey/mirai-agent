#!/usr/bin/env python3
"""
Simple HTTP server for Mirai frontend
Простой веб-сервер для фронтенда Mirai
"""

import http.server
import socketserver
import os
import threading
import logging
from pathlib import Path

class MiraiHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Обработчик HTTP запросов для SPA"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="/root/mirai-agent/frontend/trading/dist", **kwargs)
    
    def do_GET(self):
        """Обработка GET запросов"""
        # Для SPA перенаправляем все несуществующие маршруты на index.html
        path = self.translate_path(self.path)
        if not os.path.exists(path) and not self.path.startswith('/api'):
            self.path = '/index.html'
        
        return super().do_GET()
    
    def log_message(self, format, *args):
        """Логирование запросов"""
        logging.info(f"Web: {self.address_string()} - {format % args}")

def start_web_server(port=3001, host='0.0.0.0'):
    """Запуск веб-сервера"""
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/root/mirai-agent/logs/web_server.log'),
            logging.StreamHandler()
        ]
    )
    
    # Проверяем существование директории с фронтендом
    frontend_dir = Path("/root/mirai-agent/frontend/trading/dist")
    if not frontend_dir.exists():
        logging.error("Директория фронтенда не найдена. Сначала выполните сборку.")
        return
    
    logging.info(f"Запуск веб-сервера на {host}:{port}")
    logging.info(f"Обслуживание файлов из: {frontend_dir}")
    
    try:
        with socketserver.TCPServer((host, port), MiraiHTTPRequestHandler) as httpd:
            logging.info(f"🌐 Веб-сервер запущен: http://{host}:{port}")
            httpd.serve_forever()
    except Exception as e:
        logging.error(f"Ошибка запуска веб-сервера: {e}")

if __name__ == "__main__":
    start_web_server()
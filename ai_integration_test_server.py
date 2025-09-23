#!/usr/bin/env python3
"""
Mirai AI Integration Testing Server
Веб-сервер для тестирования интеграции ИИ-компонентов
"""

import asyncio
import json
import time
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys
import os
import threading

# Добавляем путь для импорта ИИ модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from ai_integration import MiraiAICoordinator
    from ai_engine import MiraiAdvancedAI
    from knowledge_base import MiraiKnowledgeBase
    from performance_optimizer import MiraiPerformanceOptimizer
    AI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ ИИ компоненты недоступны: {e}")
    AI_AVAILABLE = False

class AIIntegrationHandler(BaseHTTPRequestHandler):
    """HTTP обработчик для тестирования ИИ интеграции"""
    
    def __init__(self, *args, ai_coordinator=None, **kwargs):
        self.ai_coordinator = ai_coordinator
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """Подавление стандартных логов HTTP сервера"""
        pass
    
    def do_GET(self):
        """Обработка GET запросов"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/':
            self.serve_dashboard()
        elif path == '/api/status':
            self.serve_api_status()
        elif path == '/api/metrics':
            self.serve_api_metrics()
        elif path == '/api/test-decision':
            self.serve_test_decision()
        elif path == '/api/test-knowledge':
            self.serve_test_knowledge()
        elif path == '/test':
            self.serve_integration_test()
        else:
            self.send_404()
    
    def do_POST(self):
        """Обработка POST запросов"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/api/add-knowledge':
            self.handle_add_knowledge()
        elif path == '/api/make-decision':
            self.handle_make_decision()
        else:
            self.send_404()
    
    def serve_dashboard(self):
        """Обслуживание главной страницы дашборда"""
        html_content = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mirai AI Integration Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-active {
            background-color: #4CAF50;
            animation: pulse 2s infinite;
        }
        .status-inactive {
            background-color: #f44336;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
            transition: background 0.3s;
        }
        .btn:hover {
            background: #45a049;
        }
        .test-result {
            margin-top: 10px;
            padding: 10px;
            border-radius: 5px;
            background: rgba(0, 0, 0, 0.2);
            max-height: 200px;
            overflow-y: auto;
        }
        .log-container {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            max-height: 300px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Mirai AI Integration Test Center</h1>
            <p>Тестирование интеграции ИИ-компонентов</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>🏥 Статус системы</h3>
                <div id="system-status">
                    <div><span class="status-indicator status-active"></span>ИИ Координатор: <span id="coordinator-status">Загрузка...</span></div>
                    <div><span class="status-indicator status-active"></span>ИИ Движок: <span id="engine-status">Загрузка...</span></div>
                    <div><span class="status-indicator status-active"></span>База знаний: <span id="knowledge-status">Загрузка...</span></div>
                    <div><span class="status-indicator status-active"></span>Оптимизатор: <span id="optimizer-status">Загрузка...</span></div>
                </div>
                <button class="btn" onclick="updateStatus()">🔄 Обновить статус</button>
            </div>
            
            <div class="card">
                <h3>📊 Метрики</h3>
                <div id="metrics">
                    <div>Время работы: <span id="uptime">-</span></div>
                    <div>Решений принято: <span id="decisions">-</span></div>
                    <div>Прогнозов создано: <span id="predictions">-</span></div>
                    <div>Знаний добавлено: <span id="knowledge-count">-</span></div>
                </div>
                <button class="btn" onclick="updateMetrics()">📈 Обновить метрики</button>
            </div>
            
            <div class="card">
                <h3>🧠 Тест принятия решений</h3>
                <button class="btn" onclick="testDecision()">🎯 Тест решения</button>
                <div id="decision-result" class="test-result"></div>
            </div>
            
            <div class="card">
                <h3>📚 Тест базы знаний</h3>
                <button class="btn" onclick="testKnowledge()">📖 Тест знаний</button>
                <div id="knowledge-result" class="test-result"></div>
            </div>
        </div>
        
        <div class="card">
            <h3>🔄 Полный интеграционный тест</h3>
            <button class="btn" onclick="runFullIntegrationTest()">🚀 Запустить полный тест</button>
            <div id="full-test-result" class="test-result"></div>
        </div>
        
        <div class="card">
            <h3>📋 Лог операций</h3>
            <div id="log-container" class="log-container"></div>
            <button class="btn" onclick="clearLogs()">🗑️ Очистить логи</button>
        </div>
    </div>

    <script>
        let logContainer = document.getElementById('log-container');
        
        function log(message) {
            const timestamp = new Date().toLocaleTimeString();
            logContainer.innerHTML += `[${timestamp}] ${message}<br>`;
            logContainer.scrollTop = logContainer.scrollHeight;
        }
        
        async function updateStatus() {
            log('🔄 Обновление статуса системы...');
            try {
                const response = await fetch('/api/status');
                const status = await response.json();
                
                document.getElementById('coordinator-status').textContent = status.is_running ? 'Активен' : 'Неактивен';
                document.getElementById('engine-status').textContent = status.components?.ai_engine || 'Неизвестно';
                document.getElementById('knowledge-status').textContent = status.components?.knowledge_base || 'Неизвестно';
                document.getElementById('optimizer-status').textContent = status.components?.optimizer || 'Неизвестно';
                
                log('✅ Статус обновлен успешно');
            } catch (error) {
                log(`❌ Ошибка обновления статуса: ${error.message}`);
            }
        }
        
        async function updateMetrics() {
            log('📊 Загрузка метрик...');
            try {
                const response = await fetch('/api/metrics');
                const metrics = await response.json();
                
                document.getElementById('uptime').textContent = Math.round(metrics.uptime_seconds) + ' сек';
                document.getElementById('decisions').textContent = metrics.stats?.decisions_made || '0';
                document.getElementById('predictions').textContent = metrics.stats?.predictions_generated || '0';
                document.getElementById('knowledge-count').textContent = metrics.stats?.knowledge_entries_added || '0';
                
                log('📈 Метрики обновлены');
            } catch (error) {
                log(`❌ Ошибка загрузки метрик: ${error.message}`);
            }
        }
        
        async function testDecision() {
            log('🧠 Тестирование принятия решений...');
            const resultDiv = document.getElementById('decision-result');
            resultDiv.innerHTML = 'Обработка...';
            
            try {
                const response = await fetch('/api/test-decision');
                const result = await response.json();
                
                resultDiv.innerHTML = `
                    <strong>Результат:</strong><br>
                    Действие: ${result.action}<br>
                    Уверенность: ${(result.confidence * 100).toFixed(1)}%<br>
                    Рекомендации: ${result.recommendations?.join(', ') || 'Нет'}
                `;
                
                log('🎯 Тест решений выполнен успешно');
            } catch (error) {
                resultDiv.innerHTML = `Ошибка: ${error.message}`;
                log(`❌ Ошибка теста решений: ${error.message}`);
            }
        }
        
        async function testKnowledge() {
            log('📚 Тестирование базы знаний...');
            const resultDiv = document.getElementById('knowledge-result');
            resultDiv.innerHTML = 'Обработка...';
            
            try {
                const response = await fetch('/api/test-knowledge');
                const result = await response.json();
                
                resultDiv.innerHTML = `
                    <strong>Результат:</strong><br>
                    ${result.message}<br>
                    Записей в базе: ${result.total_entries || 0}
                `;
                
                log('📖 Тест базы знаний выполнен');
            } catch (error) {
                resultDiv.innerHTML = `Ошибка: ${error.message}`;
                log(`❌ Ошибка теста знаний: ${error.message}`);
            }
        }
        
        async function runFullIntegrationTest() {
            log('🚀 Запуск полного интеграционного теста...');
            const resultDiv = document.getElementById('full-test-result');
            resultDiv.innerHTML = 'Выполнение комплексного тестирования...';
            
            try {
                const response = await fetch('/test');
                const result = await response.json();
                
                let resultHtml = '<strong>Результаты полного теста:</strong><br>';
                result.tests.forEach(test => {
                    const status = test.success ? '✅' : '❌';
                    resultHtml += `${status} ${test.name}: ${test.result}<br>`;
                });
                resultHtml += `<br><strong>Общий результат:</strong> ${result.overall_success ? 'Успех' : 'Есть ошибки'}`;
                
                resultDiv.innerHTML = resultHtml;
                log(`🎯 Полный тест завершен: ${result.overall_success ? 'Успешно' : 'С ошибками'}`);
            } catch (error) {
                resultDiv.innerHTML = `Ошибка: ${error.message}`;
                log(`❌ Ошибка полного теста: ${error.message}`);
            }
        }
        
        function clearLogs() {
            logContainer.innerHTML = '';
            log('🗑️ Логи очищены');
        }
        
        // Автоматическое обновление при загрузке
        window.addEventListener('load', function() {
            log('🚀 Инициализация AI Integration Test Center');
            updateStatus();
            updateMetrics();
            
            // Автообновление каждые 10 секунд
            setInterval(() => {
                updateStatus();
                updateMetrics();
            }, 10000);
        });
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def serve_api_status(self):
        """API статуса системы"""
        if not AI_AVAILABLE or not self.ai_coordinator:
            status = {
                'is_running': False,
                'error': 'AI components not available',
                'components': {
                    'ai_engine': 'unavailable',
                    'knowledge_base': 'unavailable',
                    'optimizer': 'unavailable'
                },
                'timestamp': datetime.now().isoformat()
            }
        else:
            status = self.ai_coordinator.get_status()
        
        self.send_json_response(status)
    
    def serve_api_metrics(self):
        """API метрик системы"""
        if not AI_AVAILABLE or not self.ai_coordinator:
            metrics = {
                'uptime_seconds': 0,
                'stats': {
                    'decisions_made': 0,
                    'predictions_generated': 0,
                    'knowledge_entries_added': 0
                },
                'timestamp': datetime.now().isoformat()
            }
        else:
            metrics = self.ai_coordinator.get_status()
        
        self.send_json_response(metrics)
    
    def serve_test_decision(self):
        """Тестирование принятия решений"""
        if not AI_AVAILABLE or not self.ai_coordinator:
            result = {
                'action': 'test_unavailable',
                'confidence': 0.0,
                'recommendations': ['AI components not available'],
                'timestamp': datetime.now().isoformat()
            }
        else:
            # Создаем тестовый контекст
            test_context = {
                'system_load': 0.7,
                'memory_usage': 0.6,
                'active_trades': 5,
                'test_mode': True
            }
            
            # Тестируем анализ контекста
            result = self.ai_coordinator.ai_engine.analyze_context(test_context)
            result['timestamp'] = datetime.now().isoformat()
        
        self.send_json_response(result)
    
    def serve_test_knowledge(self):
        """Тестирование базы знаний"""
        if not AI_AVAILABLE or not self.ai_coordinator:
            result = {
                'message': 'База знаний недоступна',
                'total_entries': 0,
                'success': False
            }
        else:
            try:
                # Получаем статистику базы знаний
                stats = self.ai_coordinator.knowledge_base.get_statistics()
                result = {
                    'message': 'База знаний работает корректно',
                    'total_entries': stats.get('total_entries', 0),
                    'categories': stats.get('categories', {}),
                    'success': True,
                    'timestamp': datetime.now().isoformat()
                }
            except Exception as e:
                result = {
                    'message': f'Ошибка базы знаний: {str(e)}',
                    'total_entries': 0,
                    'success': False
                }
        
        self.send_json_response(result)
    
    def serve_integration_test(self):
        """Полный интеграционный тест"""
        tests = []
        overall_success = True
        
        # Тест доступности компонентов
        tests.append({
            'name': 'Доступность ИИ компонентов',
            'success': AI_AVAILABLE,
            'result': 'Компоненты загружены' if AI_AVAILABLE else 'Компоненты недоступны'
        })
        
        if AI_AVAILABLE and self.ai_coordinator:
            # Тест координатора
            try:
                status = self.ai_coordinator.get_status()
                tests.append({
                    'name': 'ИИ Координатор',
                    'success': True,
                    'result': f'Статус получен, запущен: {status.get("is_running", False)}'
                })
            except Exception as e:
                tests.append({
                    'name': 'ИИ Координатор',
                    'success': False,
                    'result': f'Ошибка: {str(e)}'
                })
                overall_success = False
            
            # Тест ИИ движка
            try:
                test_context = {'test': True, 'timestamp': time.time()}
                decision = self.ai_coordinator.ai_engine.analyze_context(test_context)
                tests.append({
                    'name': 'ИИ Движок',
                    'success': True,
                    'result': f'Анализ выполнен, уверенность: {decision.get("confidence", 0):.2f}'
                })
            except Exception as e:
                tests.append({
                    'name': 'ИИ Движок',
                    'success': False,
                    'result': f'Ошибка: {str(e)}'
                })
                overall_success = False
            
            # Тест базы знаний
            try:
                stats = self.ai_coordinator.knowledge_base.get_statistics()
                tests.append({
                    'name': 'База знаний',
                    'success': True,
                    'result': f'Статистика получена, записей: {stats.get("total_entries", 0)}'
                })
            except Exception as e:
                tests.append({
                    'name': 'База знаний',
                    'success': False,
                    'result': f'Ошибка: {str(e)}'
                })
                overall_success = False
        
        result = {
            'tests': tests,
            'overall_success': overall_success,
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(tests),
            'passed_tests': sum(1 for t in tests if t['success'])
        }
        
        self.send_json_response(result)
    
    def send_json_response(self, data):
        """Отправка JSON ответа"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))
    
    def send_404(self):
        """Отправка 404 ошибки"""
        self.send_response(404)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'404 Not Found')

def create_handler_class(ai_coordinator):
    """Создание класса обработчика с ИИ координатором"""
    class Handler(AIIntegrationHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, ai_coordinator=ai_coordinator, **kwargs)
    
    return Handler

def run_ai_integration_server(port=8081):
    """Запуск сервера для тестирования ИИ интеграции"""
    print(f"🚀 Запуск AI Integration Test Server на порту {port}")
    
    # Инициализация ИИ координатора
    ai_coordinator = None
    if AI_AVAILABLE:
        try:
            ai_coordinator = MiraiAICoordinator()
            print("✅ ИИ координатор инициализирован")
        except Exception as e:
            print(f"⚠️ Ошибка инициализации ИИ координатора: {e}")
    
    # Создание HTTP сервера
    handler_class = create_handler_class(ai_coordinator)
    server = HTTPServer(('0.0.0.0', port), handler_class)
    
    print(f"🌐 Сервер доступен по адресу: http://localhost:{port}")
    print("📊 Открыть дашборд: http://localhost:{port}")
    print("🔧 API статуса: http://localhost:{port}/api/status")
    print("📈 API метрик: http://localhost:{port}/api/metrics")
    print("🧪 Полный тест: http://localhost:{port}/test")
    print("\nНажмите Ctrl+C для остановки сервера")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Остановка сервера...")
        server.shutdown()

if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Запуск сервера
    port = 8081
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("⚠️ Неверный номер порта, используется порт по умолчанию 8081")
    
    run_ai_integration_server(port)
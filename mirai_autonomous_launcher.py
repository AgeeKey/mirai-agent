#!/usr/bin/env python3
"""
Mirai Advanced Autonomous Launcher
Запуск всех автономных систем Mirai в едином оркестраторе
"""

import asyncio
import logging
import threading
import time
import signal
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import subprocess

# Добавляем пути для импорта ИИ модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from autonomous_content_engine import MiraiContentEngine
    from machine_learning_engine import MiraiLearningEngine
    from social_ecosystem import SocialEcosystemAPI
    # Убираем проблематичный импорт ai_test_server
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Модули недоступны: {e}")
    MODULES_AVAILABLE = False

class MiraiAutonomousOrchestrator:
    """Оркестратор автономных систем Mirai"""
    
    def __init__(self):
        self.logger = self.setup_logging()
        self.active_systems = {}
        self.system_stats = {}
        self.orchestrator_config = {
            'content_engine_enabled': True,
            'learning_engine_enabled': True,
            'social_ecosystem_enabled': True,
            'ai_test_server_enabled': True,
            'health_check_interval': 30,
            'auto_restart': True,
            'max_restart_attempts': 3
        }
        
        # Статистика работы
        self.orchestrator_stats = {
            'start_time': datetime.now(),
            'systems_launched': 0,
            'systems_restarted': 0,
            'total_uptime': 0,
            'health_checks_passed': 0,
            'health_checks_failed': 0
        }
        
        # Обработчики сигналов для graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.running = True
    
    def setup_logging(self):
        """Настройка логирования оркестратора"""
        log_dir = Path('/root/mirai-agent/logs')
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'orchestrator.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger('MiraiOrchestrator')
    
    def signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        self.logger.info(f"🛑 Получен сигнал {signum}, инициализация остановки...")
        self.running = False
    
    async def start_content_engine(self):
        """Запуск движка контента"""
        if not self.orchestrator_config['content_engine_enabled']:
            return
        
        try:
            self.logger.info("🎬 Запуск автономного контентного движка...")
            
            content_engine = MiraiContentEngine()
            self.active_systems['content_engine'] = {
                'instance': content_engine,
                'status': 'starting',
                'start_time': datetime.now(),
                'restart_count': 0,
                'health_status': 'unknown'
            }
            
            # Запуск в отдельной задаче
            task = asyncio.create_task(content_engine.start_content_engine())
            self.active_systems['content_engine']['task'] = task
            self.active_systems['content_engine']['status'] = 'running'
            
            self.orchestrator_stats['systems_launched'] += 1
            self.logger.info("✅ Контентный движок запущен")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка запуска контентного движка: {e}")
            if 'content_engine' in self.active_systems:
                self.active_systems['content_engine']['status'] = 'failed'
    
    async def start_learning_engine(self):
        """Запуск движка машинного обучения"""
        if not self.orchestrator_config['learning_engine_enabled']:
            return
        
        try:
            self.logger.info("🧠 Запуск движка машинного обучения...")
            
            learning_engine = MiraiLearningEngine()
            self.active_systems['learning_engine'] = {
                'instance': learning_engine,
                'status': 'starting',
                'start_time': datetime.now(),
                'restart_count': 0,
                'health_status': 'unknown'
            }
            
            # Запуск в отдельной задаче
            task = asyncio.create_task(learning_engine.start_learning_engine())
            self.active_systems['learning_engine']['task'] = task
            self.active_systems['learning_engine']['status'] = 'running'
            
            self.orchestrator_stats['systems_launched'] += 1
            self.logger.info("✅ Движок машинного обучения запущен")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка запуска движка обучения: {e}")
            if 'learning_engine' in self.active_systems:
                self.active_systems['learning_engine']['status'] = 'failed'
    
    def start_social_ecosystem(self):
        """Запуск социальной экосистемы"""
        if not self.orchestrator_config['social_ecosystem_enabled']:
            return
        
        try:
            self.logger.info("🌐 Запуск социальной экосистемы...")
            
            social_ecosystem = SocialEcosystemAPI()
            self.active_systems['social_ecosystem'] = {
                'instance': social_ecosystem,
                'status': 'starting',
                'start_time': datetime.now(),
                'restart_count': 0,
                'health_status': 'unknown'
            }
            
            # Запуск в отдельном потоке (так как использует Flask)
            def run_social_ecosystem():
                try:
                    social_ecosystem.start_social_ecosystem()
                except Exception as e:
                    self.logger.error(f"❌ Ошибка в социальной экосистеме: {e}")
                    self.active_systems['social_ecosystem']['status'] = 'failed'
            
            thread = threading.Thread(target=run_social_ecosystem, daemon=True)
            thread.start()
            
            self.active_systems['social_ecosystem']['thread'] = thread
            self.active_systems['social_ecosystem']['status'] = 'running'
            
            self.orchestrator_stats['systems_launched'] += 1
            self.logger.info("✅ Социальная экосистема запущена (порт 8082)")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка запуска социальной экосистемы: {e}")
            if 'social_ecosystem' in self.active_systems:
                self.active_systems['social_ecosystem']['status'] = 'failed'
    
    def start_ai_test_server(self):
        """Запуск ИИ тестового сервера"""
        if not self.orchestrator_config['ai_test_server_enabled']:
            return
        
        try:
            self.logger.info("🤖 Запуск ИИ тестового сервера...")
            
            self.active_systems['ai_test_server'] = {
                'status': 'starting',
                'start_time': datetime.now(),
                'restart_count': 0,
                'health_status': 'unknown'
            }
            
            # Запуск через subprocess для изоляции
            def run_ai_server():
                try:
                    process = subprocess.Popen([
                        sys.executable, 'ai_integration_test_server.py'
                    ], cwd='/root/mirai-agent', env={**os.environ, 'PYTHONPATH': '/root/mirai-agent'})
                    
                    self.active_systems['ai_test_server']['process'] = process
                    self.active_systems['ai_test_server']['status'] = 'running'
                    
                    # Ждем завершения процесса
                    process.wait()
                    
                except Exception as e:
                    self.logger.error(f"❌ Ошибка в ИИ тестовом сервере: {e}")
                    self.active_systems['ai_test_server']['status'] = 'failed'
            
            thread = threading.Thread(target=run_ai_server, daemon=True)
            thread.start()
            
            self.active_systems['ai_test_server']['thread'] = thread
            
            self.orchestrator_stats['systems_launched'] += 1
            self.logger.info("✅ ИИ тестовый сервер запущен (порт 8081)")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка запуска ИИ тестового сервера: {e}")
            if 'ai_test_server' in self.active_systems:
                self.active_systems['ai_test_server']['status'] = 'failed'
    
    async def health_check_system(self, system_name: str) -> bool:
        """Проверка здоровья системы"""
        if system_name not in self.active_systems:
            return False
        
        system = self.active_systems[system_name]
        
        try:
            # Проверяем статус
            if system['status'] != 'running':
                return False
            
            # Проверяем задачи/потоки
            if 'task' in system:
                task = system['task']
                if task.done() or task.cancelled():
                    return False
            
            if 'thread' in system:
                thread = system['thread']
                if not thread.is_alive():
                    return False
            
            if 'process' in system:
                process = system['process']
                if process.poll() is not None:  # Процесс завершился
                    return False
            
            # Дополнительные проверки для конкретных систем
            if system_name == 'social_ecosystem':
                # Можно добавить HTTP-проверку порта 8082
                pass
            elif system_name == 'ai_test_server':
                # Можно добавить HTTP-проверку порта 8081
                pass
            
            system['health_status'] = 'healthy'
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка проверки здоровья {system_name}: {e}")
            system['health_status'] = 'unhealthy'
            return False
    
    async def restart_system(self, system_name: str):
        """Перезапуск системы"""
        if system_name not in self.active_systems:
            return
        
        system = self.active_systems[system_name]
        restart_count = system.get('restart_count', 0)
        
        if restart_count >= self.orchestrator_config['max_restart_attempts']:
            self.logger.error(f"❌ Превышено максимальное количество перезапусков для {system_name}")
            system['status'] = 'failed_max_restarts'
            return
        
        self.logger.info(f"🔄 Перезапуск системы {system_name} (попытка {restart_count + 1})")
        
        try:
            # Останавливаем систему
            await self.stop_system(system_name)
            
            # Ждем немного
            await asyncio.sleep(5)
            
            # Запускаем заново
            if system_name == 'content_engine':
                await self.start_content_engine()
            elif system_name == 'learning_engine':
                await self.start_learning_engine()
            elif system_name == 'social_ecosystem':
                self.start_social_ecosystem()
            elif system_name == 'ai_test_server':
                self.start_ai_test_server()
            
            # Обновляем счетчик перезапусков
            if system_name in self.active_systems:
                self.active_systems[system_name]['restart_count'] = restart_count + 1
                self.orchestrator_stats['systems_restarted'] += 1
            
            self.logger.info(f"✅ Система {system_name} перезапущена")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка перезапуска {system_name}: {e}")
    
    async def stop_system(self, system_name: str):
        """Остановка системы"""
        if system_name not in self.active_systems:
            return
        
        system = self.active_systems[system_name]
        
        try:
            # Останавливаем задачи
            if 'task' in system:
                task = system['task']
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Останавливаем процессы
            if 'process' in system:
                process = system['process']
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
            
            system['status'] = 'stopped'
            self.logger.info(f"🛑 Система {system_name} остановлена")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка остановки {system_name}: {e}")
    
    async def health_monitoring_loop(self):
        """Цикл мониторинга здоровья систем"""
        self.logger.info("❤️ Запуск мониторинга здоровья систем")
        
        while self.running:
            try:
                healthy_systems = 0
                total_systems = len(self.active_systems)
                
                for system_name in list(self.active_systems.keys()):
                    is_healthy = await self.health_check_system(system_name)
                    
                    if is_healthy:
                        healthy_systems += 1
                        self.orchestrator_stats['health_checks_passed'] += 1
                    else:
                        self.orchestrator_stats['health_checks_failed'] += 1
                        self.logger.warning(f"⚠️ Система {system_name} нездорова")
                        
                        # Автоматический перезапуск при необходимости
                        if self.orchestrator_config['auto_restart']:
                            await self.restart_system(system_name)
                
                # Логируем общий статус
                if total_systems > 0:
                    health_percentage = (healthy_systems / total_systems) * 100
                    self.logger.info(f"💚 Здоровье экосистемы: {health_percentage:.1f}% ({healthy_systems}/{total_systems})")
                
                # Пауза между проверками
                await asyncio.sleep(self.orchestrator_config['health_check_interval'])
                
            except Exception as e:
                self.logger.error(f"❌ Ошибка в цикле мониторинга: {e}")
                await asyncio.sleep(30)  # Пауза при ошибке
    
    def generate_status_report(self) -> Dict[str, Any]:
        """Генерация отчета о статусе"""
        uptime = datetime.now() - self.orchestrator_stats['start_time']
        
        systems_status = {}
        for system_name, system in self.active_systems.items():
            system_uptime = datetime.now() - system['start_time']
            systems_status[system_name] = {
                'status': system['status'],
                'health_status': system.get('health_status', 'unknown'),
                'uptime_seconds': system_uptime.total_seconds(),
                'restart_count': system.get('restart_count', 0)
            }
        
        return {
            'orchestrator': {
                'uptime_seconds': uptime.total_seconds(),
                'systems_launched': self.orchestrator_stats['systems_launched'],
                'systems_restarted': self.orchestrator_stats['systems_restarted'],
                'health_checks_passed': self.orchestrator_stats['health_checks_passed'],
                'health_checks_failed': self.orchestrator_stats['health_checks_failed']
            },
            'systems': systems_status,
            'config': self.orchestrator_config,
            'timestamp': datetime.now().isoformat()
        }
    
    async def status_reporting_loop(self):
        """Цикл отчетов о статусе"""
        while self.running:
            try:
                # Генерируем отчет каждые 5 минут
                await asyncio.sleep(300)
                
                report = self.generate_status_report()
                
                # Сохраняем отчет
                report_path = '/root/mirai-agent/logs/orchestrator_status.json'
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                
                # Краткий лог
                running_systems = [name for name, sys in self.active_systems.items() if sys['status'] == 'running']
                self.logger.info(f"📊 Активные системы: {', '.join(running_systems)}")
                
            except Exception as e:
                self.logger.error(f"❌ Ошибка в отчетности: {e}")
                await asyncio.sleep(60)
    
    async def start_all_systems(self):
        """Запуск всех систем"""
        if not MODULES_AVAILABLE:
            self.logger.error("❌ Не удается загрузить модули, проверьте зависимости")
            return
        
        self.logger.info("🚀 Запуск всех автономных систем Mirai")
        
        # Запускаем системы параллельно где возможно
        async_tasks = []
        
        if self.orchestrator_config['content_engine_enabled']:
            async_tasks.append(self.start_content_engine())
        
        if self.orchestrator_config['learning_engine_enabled']:
            async_tasks.append(self.start_learning_engine())
        
        # Запускаем асинхронные системы
        if async_tasks:
            await asyncio.gather(*async_tasks, return_exceptions=True)
        
        # Запускаем синхронные системы
        if self.orchestrator_config['social_ecosystem_enabled']:
            self.start_social_ecosystem()
        
        if self.orchestrator_config['ai_test_server_enabled']:
            self.start_ai_test_server()
        
        # Даем системам время на инициализацию
        await asyncio.sleep(10)
        
        self.logger.info("✅ Все системы запущены, начинаем мониторинг")
    
    async def shutdown_all_systems(self):
        """Корректное завершение всех систем"""
        self.logger.info("🛑 Начинаем корректное завершение всех систем...")
        
        # Останавливаем системы
        for system_name in list(self.active_systems.keys()):
            await self.stop_system(system_name)
        
        self.logger.info("✅ Все системы корректно завершены")
    
    async def run(self):
        """Основной цикл оркестратора"""
        try:
            # Запускаем все системы
            await self.start_all_systems()
            
            # Запускаем мониторинг в фоне
            monitoring_task = asyncio.create_task(self.health_monitoring_loop())
            reporting_task = asyncio.create_task(self.status_reporting_loop())
            
            # Основной цикл
            while self.running:
                await asyncio.sleep(1)
            
            # Останавливаем мониторинг
            monitoring_task.cancel()
            reporting_task.cancel()
            
            # Завершаем системы
            await self.shutdown_all_systems()
            
        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка оркестратора: {e}")
        finally:
            self.logger.info("🏁 Оркестратор завершен")

def print_startup_banner():
    """Вывод стартового баннера"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                   🚀 MIRAI AUTONOMOUS SYSTEM 🚀                ║
    ║                        Advanced AI Ecosystem                  ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  🎬 Content Engine    - Автономная генерация контента        ║
    ║  🧠 Learning Engine   - Машинное обучение и адаптация        ║
    ║  🌐 Social Ecosystem  - Социальная платформа с ИИ            ║
    ║  🤖 AI Test Server    - Интерфейс тестирования ИИ            ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  Все системы работают автономно в режиме реального времени   ║
    ║  Веб-интерфейсы: http://localhost:8081 и http://localhost:8082║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

async def main():
    """Основная функция запуска"""
    print_startup_banner()
    
    orchestrator = MiraiAutonomousOrchestrator()
    
    try:
        await orchestrator.run()
    except KeyboardInterrupt:
        print("\n🛑 Получен сигнал прерывания, завершаем работу...")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    
    print("🏁 Mirai Autonomous System завершен")

if __name__ == "__main__":
    asyncio.run(main())
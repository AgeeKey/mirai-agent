#!/usr/bin/env python3
"""
Mirai Advanced Performance Analyzer
Продвинутый анализатор производительности экосистемы Mirai
"""

import asyncio
import json
import time
import requests
import psutil
import subprocess
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import logging

class MiraiPerformanceAnalyzer:
    """Анализатор производительности экосистемы Mirai"""
    
    def __init__(self):
        self.metrics = {}
        self.recommendations = []
        self.issues = []
        self.logger = self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger('MiraiAnalyzer')
    
    async def analyze_system_performance(self):
        """Анализ производительности системы"""
        self.logger.info("🔍 Анализ системной производительности...")
        
        # CPU анализ
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        self.metrics['cpu'] = {
            'usage_percent': cpu_percent,
            'cores': cpu_count,
            'frequency': cpu_freq.current if cpu_freq else 0,
            'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
        }
        
        # Память
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        self.metrics['memory'] = {
            'total_gb': memory.total / (1024**3),
            'used_gb': memory.used / (1024**3),
            'available_gb': memory.available / (1024**3),
            'percent': memory.percent,
            'swap_percent': swap.percent
        }
        
        # Диск
        disk = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        
        self.metrics['disk'] = {
            'total_gb': disk.total / (1024**3),
            'used_gb': disk.used / (1024**3),
            'free_gb': disk.free / (1024**3),
            'percent': (disk.used / disk.total) * 100,
            'read_mb': disk_io.read_bytes / (1024**2) if disk_io else 0,
            'write_mb': disk_io.write_bytes / (1024**2) if disk_io else 0
        }
        
        # Сеть
        net_io = psutil.net_io_counters()
        connections = len(psutil.net_connections())
        
        self.metrics['network'] = {
            'bytes_sent_mb': net_io.bytes_sent / (1024**2),
            'bytes_recv_mb': net_io.bytes_recv / (1024**2),
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv,
            'connections': connections
        }
        
        # Рекомендации по системе
        if cpu_percent > 80:
            self.issues.append("Высокая загрузка CPU")
            self.recommendations.append("Оптимизировать алгоритмы или добавить кэширование")
            
        if memory.percent > 85:
            self.issues.append("Высокое использование памяти")
            self.recommendations.append("Проверить утечки памяти в приложениях")
            
        if (disk.used / disk.total) * 100 > 90:
            self.issues.append("Мало места на диске")
            self.recommendations.append("Очистить логи и временные файлы")
    
    async def analyze_api_performance(self):
        """Анализ производительности API"""
        self.logger.info("🔗 Анализ производительности API...")
        
        apis = [
            {'name': 'Trading API', 'url': 'http://localhost:8001/health'},
            {'name': 'Services API', 'url': 'http://localhost:8002/health'},
            {'name': 'Web Interface', 'url': 'http://localhost:3001'}
        ]
        
        api_metrics = {}
        
        for api in apis:
            try:
                start_time = time.time()
                response = requests.get(api['url'], timeout=10)
                response_time = (time.time() - start_time) * 1000  # мс
                
                api_metrics[api['name']] = {
                    'status': 'online' if response.status_code == 200 else 'error',
                    'response_time_ms': response_time,
                    'status_code': response.status_code
                }
                
                if response_time > 1000:  # > 1 секунды
                    self.issues.append(f"{api['name']} медленно отвечает")
                    self.recommendations.append(f"Оптимизировать {api['name']} или добавить кэширование")
                    
            except Exception as e:
                api_metrics[api['name']] = {
                    'status': 'offline',
                    'error': str(e)
                }
                self.issues.append(f"{api['name']} недоступен")
                self.recommendations.append(f"Перезапустить {api['name']}")
        
        self.metrics['apis'] = api_metrics
    
    async def analyze_database_performance(self):
        """Анализ производительности базы данных"""
        self.logger.info("🗄️ Анализ баз данных...")
        
        db_metrics = {}
        
        # SQLite анализ
        sqlite_path = '/root/mirai-agent/state/mirai.db'
        if Path(sqlite_path).exists():
            try:
                stat = Path(sqlite_path).stat()
                db_metrics['sqlite'] = {
                    'size_mb': stat.st_size / (1024**2),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
                
                # Подключаемся и проверяем
                conn = sqlite3.connect(sqlite_path)
                cursor = conn.cursor()
                
                # Получаем список таблиц
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                table_info = {}
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    table_info[table_name] = count
                
                db_metrics['sqlite']['tables'] = table_info
                conn.close()
                
                if stat.st_size > 100 * 1024 * 1024:  # > 100MB
                    self.recommendations.append("Оптимизировать SQLite базу данных")
                    
            except Exception as e:
                db_metrics['sqlite'] = {'error': str(e)}
        
        self.metrics['databases'] = db_metrics
    
    async def analyze_docker_performance(self):
        """Анализ производительности Docker контейнеров"""
        self.logger.info("🐳 Анализ Docker контейнеров...")
        
        try:
            # Получаем статистику контейнеров
            result = subprocess.run(
                ['docker', 'stats', '--no-stream', '--format', 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}'],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Пропускаем заголовок
                containers = {}
                
                for line in lines:
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 5:
                            name = parts[0]
                            cpu = parts[1]
                            memory = parts[2]
                            network = parts[3]
                            block_io = parts[4]
                            
                            containers[name] = {
                                'cpu_percent': cpu,
                                'memory_usage': memory,
                                'network_io': network,
                                'block_io': block_io
                            }
                            
                            # Проверяем высокое потребление
                            cpu_val = float(cpu.replace('%', '')) if '%' in cpu else 0
                            if cpu_val > 50:
                                self.issues.append(f"Контейнер {name} потребляет много CPU")
                
                self.metrics['docker'] = containers
                
        except Exception as e:
            self.metrics['docker'] = {'error': str(e)}
    
    async def analyze_autonomous_system(self):
        """Анализ автономной системы"""
        self.logger.info("🤖 Анализ автономной системы...")
        
        autonomous_metrics = {}
        
        # Проверяем логи автономной системы
        log_path = '/root/mirai-agent/logs/autonomous.log'
        if Path(log_path).exists():
            try:
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                
                recent_lines = lines[-100:]  # Последние 100 строк
                
                error_count = sum(1 for line in recent_lines if 'ERROR' in line)
                warning_count = sum(1 for line in recent_lines if 'WARNING' in line)
                task_completed = sum(1 for line in recent_lines if 'Задача завершена' in line)
                task_failed = sum(1 for line in recent_lines if 'Задача провалена' in line)
                
                autonomous_metrics = {
                    'recent_errors': error_count,
                    'recent_warnings': warning_count,
                    'tasks_completed': task_completed,
                    'tasks_failed': task_failed,
                    'log_size_mb': Path(log_path).stat().st_size / (1024**2)
                }
                
                if error_count > 5:
                    self.issues.append("Много ошибок в автономной системе")
                    self.recommendations.append("Проверить и исправить ошибки в автономной системе")
                
            except Exception as e:
                autonomous_metrics = {'error': str(e)}
        
        self.metrics['autonomous_system'] = autonomous_metrics
    
    def calculate_performance_score(self):
        """Расчет общего балла производительности"""
        score = 100
        
        # Вычитаем баллы за проблемы
        if self.metrics.get('cpu', {}).get('usage_percent', 0) > 80:
            score -= 20
        elif self.metrics.get('cpu', {}).get('usage_percent', 0) > 60:
            score -= 10
            
        if self.metrics.get('memory', {}).get('percent', 0) > 85:
            score -= 20
        elif self.metrics.get('memory', {}).get('percent', 0) > 70:
            score -= 10
            
        if self.metrics.get('disk', {}).get('percent', 0) > 90:
            score -= 15
        elif self.metrics.get('disk', {}).get('percent', 0) > 80:
            score -= 5
            
        # За каждую проблему
        score -= len(self.issues) * 5
        
        return max(0, min(100, score))
    
    def generate_optimization_plan(self):
        """Генерация плана оптимизации"""
        plan = []
        
        # Приоритетные оптимизации
        if self.metrics.get('memory', {}).get('percent', 0) > 70:
            plan.append({
                'priority': 'high',
                'action': 'memory_optimization',
                'description': 'Оптимизация использования памяти',
                'commands': [
                    'docker system prune -f',
                    'sync && echo 3 > /proc/sys/vm/drop_caches'
                ]
            })
        
        if self.metrics.get('disk', {}).get('percent', 0) > 80:
            plan.append({
                'priority': 'high',
                'action': 'disk_cleanup',
                'description': 'Очистка диска',
                'commands': [
                    '/root/mirai-agent/scripts/cleanup-disk.sh'
                ]
            })
        
        # API оптимизации
        slow_apis = [name for name, data in self.metrics.get('apis', {}).items() 
                    if data.get('response_time_ms', 0) > 500]
        
        if slow_apis:
            plan.append({
                'priority': 'medium',
                'action': 'api_optimization',
                'description': f'Оптимизация медленных API: {", ".join(slow_apis)}',
                'commands': [
                    'systemctl reload nginx',
                    '/root/mirai-agent/scripts/optimize-performance.sh'
                ]
            })
        
        # Базы данных
        if self.metrics.get('databases', {}).get('sqlite', {}).get('size_mb', 0) > 100:
            plan.append({
                'priority': 'medium',
                'action': 'database_optimization',
                'description': 'Оптимизация базы данных',
                'commands': [
                    'sqlite3 /root/mirai-agent/state/mirai.db "VACUUM;"',
                    'sqlite3 /root/mirai-agent/state/mirai.db "REINDEX;"'
                ]
            })
        
        return plan
    
    async def create_report(self):
        """Создание подробного отчета"""
        await self.analyze_system_performance()
        await self.analyze_api_performance()
        await self.analyze_database_performance()
        await self.analyze_docker_performance()
        await self.analyze_autonomous_system()
        
        score = self.calculate_performance_score()
        optimization_plan = self.generate_optimization_plan()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'performance_score': score,
            'metrics': self.metrics,
            'issues': self.issues,
            'recommendations': self.recommendations,
            'optimization_plan': optimization_plan,
            'summary': {
                'total_issues': len(self.issues),
                'critical_issues': len([i for i in self.issues if 'высок' in i.lower() or 'мало' in i.lower()]),
                'apis_online': len([api for api in self.metrics.get('apis', {}).values() if api.get('status') == 'online']),
                'docker_containers': len(self.metrics.get('docker', {})),
                'system_load': self.metrics.get('cpu', {}).get('load_average', [0])[0]
            }
        }
        
        # Сохраняем отчет
        report_file = f'/root/mirai-agent/reports/performance_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        Path('/root/mirai-agent/reports').mkdir(exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"📊 Отчет сохранен: {report_file}")
        
        # Выводим краткую сводку
        print(f"\n🎯 ОЦЕНКА ПРОИЗВОДИТЕЛЬНОСТИ: {score}/100")
        print(f"📊 Выявлено проблем: {len(self.issues)}")
        print(f"🔧 Рекомендаций: {len(self.recommendations)}")
        print(f"⚡ План оптимизации: {len(optimization_plan)} действий")
        
        if self.issues:
            print("\n⚠️ ОСНОВНЫЕ ПРОБЛЕМЫ:")
            for issue in self.issues[:5]:
                print(f"  • {issue}")
        
        if optimization_plan:
            print("\n🚀 ПРИОРИТЕТНЫЕ ОПТИМИЗАЦИИ:")
            for action in optimization_plan[:3]:
                print(f"  • {action['description']} ({action['priority']})")
        
        return report

async def main():
    analyzer = MiraiPerformanceAnalyzer()
    await analyzer.create_report()

if __name__ == "__main__":
    asyncio.run(main())
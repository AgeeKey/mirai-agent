#!/usr/bin/env python3
"""
Mirai AI Integration Module
Интеграция ИИ-компонентов в автономную систему Mirai
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys
import os

# Добавляем текущую директорию в путь для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from ai_engine import MiraiAdvancedAI, DecisionContext, DecisionType
    from intelligent_algorithms import IntelligentAlgorithmManager
    from knowledge_base import MiraiKnowledgeBase
    from performance_optimizer import MiraiPerformanceOptimizer
    OPTIMIZER_AVAILABLE = True
except ImportError as e:
    print(f"Ошибка импорта модулей ИИ: {e}")
    sys.exit(1)

class MiraiAICoordinator:
    """Координатор ИИ-систем Mirai"""
    
    def __init__(self):
        self.ai_engine = MiraiAdvancedAI()
        self.algorithm_manager = IntelligentAlgorithmManager()
        self.knowledge_base = MiraiKnowledgeBase()
        
        # Инициализация оптимизатора производительности
        if OPTIMIZER_AVAILABLE:
            self.performance_optimizer = MiraiPerformanceOptimizer()
            self.optimization_enabled = True
        else:
            self.performance_optimizer = None
            self.optimization_enabled = False
        
        self.logger = self.setup_logging()
        self.is_running = False
        
        # Настройки интеграции
        self.decision_interval = 30  # секунды между принятием решений
        self.learning_interval = 60  # секунды между циклами обучения
        self.knowledge_update_interval = 120  # секунды между обновлениями знаний
        
        # Статистика работы
        self.stats = {
            'decisions_made': 0,
            'predictions_generated': 0,
            'knowledge_entries_added': 0,
            'start_time': None,
            'last_decision': None,
            'last_prediction': None
        }
    
    def setup_logging(self):
        """Настройка логирования"""
        logger = logging.getLogger('MiraiAICoordinator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Файловый хендлер
            log_dir = Path('/root/mirai-agent/logs')
            log_dir.mkdir(exist_ok=True)
            
            file_handler = logging.FileHandler(log_dir / 'ai_coordinator.log')
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            # Консольный хендлер
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter('%(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def get_status(self) -> Dict[str, Any]:
        """Получение статуса ИИ координатора"""
        uptime_seconds = 0
        if self.stats['start_time']:
            uptime_seconds = (datetime.now() - self.stats['start_time']).total_seconds()
        
        status = {
            'is_running': self.is_running,
            'uptime_seconds': uptime_seconds,
            'stats': self.stats.copy(),
            'optimization_enabled': self.optimization_enabled,
            'components': {
                'ai_engine': 'active' if self.ai_engine else 'inactive',
                'algorithms': 'active' if self.algorithm_manager else 'inactive', 
                'knowledge_base': 'active' if self.knowledge_base else 'inactive',
                'optimizer': 'active' if self.performance_optimizer else 'inactive'
            },
            'intervals': {
                'decision_interval': self.decision_interval,
                'learning_interval': self.learning_interval,
                'knowledge_update_interval': self.knowledge_update_interval
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return status
    
    async def start_ai_coordination(self):
        """Запуск координации ИИ-систем"""
        self.logger.info("🚀 Запуск ИИ-координатора Mirai")
        self.is_running = True
        self.stats['start_time'] = datetime.now()
        
        # Запуск оптимизатора производительности
        if self.performance_optimizer and self.optimization_enabled:
            self.performance_optimizer.start_optimization()
            self.logger.info("⚡ Оптимизатор производительности запущен")
        
        # Запуск задач в параллель
        tasks = [
            asyncio.create_task(self.decision_making_cycle()),
            asyncio.create_task(self.learning_cycle()),
            asyncio.create_task(self.knowledge_management_cycle())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"Ошибка в ИИ-координаторе: {e}")
        finally:
            self.is_running = False
            
            # Остановка оптимизатора
            if self.performance_optimizer and self.optimization_enabled:
                self.performance_optimizer.stop_optimization()
                self.logger.info("🛑 Оптимизатор производительности остановлен")
    
    async def decision_making_cycle(self):
        """Цикл принятия решений"""
        self.logger.info("🧠 Запуск цикла принятия решений")
        
        while self.is_running:
            try:
                # Анализ текущей ситуации
                system_state = await self.analyze_current_situation()
                
                # Определение необходимых решений
                required_decisions = await self.identify_required_decisions(system_state)
                
                # Принятие решений с оптимизацией
                for decision_context in required_decisions:
                    if self.performance_optimizer and self.optimization_enabled:
                        # Оптимизированное принятие решений
                        decision = await self.performance_optimizer.optimize_ai_decision_making(decision_context)
                        
                        # Преобразуем в объект Decision для совместимости
                        from ai_engine import Decision
                        optimized_decision = Decision(
                            action=decision.get('action', 'optimized_action'),
                            confidence=decision.get('confidence', 0.8),
                            reasoning="Оптимизированное решение",
                            parameters={},
                            expected_outcome="Результат оптимизированного решения",
                            risk_assessment={'optimization_risk': 0.1},
                            timestamp=datetime.now(),
                            context_hash=""
                        )
                        decision = optimized_decision
                    else:
                        # Обычное принятие решений
                        decision = await self.ai_engine.make_decision(decision_context)
                    
                    if decision:
                        # Выполнение решения
                        await self.execute_decision(decision, decision_context)
                        
                        # Сохранение в базу знаний
                        await self.save_decision_knowledge(decision, decision_context)
                        
                        self.stats['decisions_made'] += 1
                        self.stats['last_decision'] = decision.action
                
                await asyncio.sleep(self.decision_interval)
                
            except Exception as e:
                self.logger.error(f"Ошибка в цикле принятия решений: {e}")
                await asyncio.sleep(10)
    
    async def learning_cycle(self):
        """Цикл обучения алгоритмов"""
        self.logger.info("📚 Запуск цикла обучения")
        
        # Запуск менеджера алгоритмов
        learning_task = asyncio.create_task(self.algorithm_manager.start_learning_cycle())
        
        while self.is_running:
            try:
                # Получение прогнозов от алгоритмов
                market_data = await self.get_current_market_data()
                
                if market_data:
                    # Консенсус-прогноз
                    consensus = await self.algorithm_manager.get_consensus_prediction(market_data)
                    
                    if consensus:
                        # Сохранение прогноза в знания
                        await self.save_prediction_knowledge(consensus, market_data)
                        
                        self.stats['predictions_generated'] += 1
                        self.stats['last_prediction'] = consensus.prediction
                
                await asyncio.sleep(self.learning_interval)
                
            except Exception as e:
                self.logger.error(f"Ошибка в цикле обучения: {e}")
                await asyncio.sleep(30)
        
        # Остановка обучения при завершении
        self.algorithm_manager.stop_learning_cycle()
        learning_task.cancel()
    
    async def knowledge_management_cycle(self):
        """Цикл управления знаниями"""
        self.logger.info("🧩 Запуск цикла управления знаниями")
        
        while self.is_running:
            try:
                # Анализ системных метрик
                metrics = await self.collect_system_metrics()
                
                # Сохранение метрик в базу знаний
                await self.knowledge_base.add_knowledge(
                    topic=f"system_metrics_{datetime.now().strftime('%Y%m%d_%H%M')}",
                    content=metrics,
                    category="system",
                    source="ai_coordinator",
                    tags=["metrics", "system", "monitoring"]
                )
                
                # Обновление связей в графе знаний
                await self.update_knowledge_relationships()
                
                # Очистка устаревших данных
                await self.cleanup_old_knowledge()
                
                self.stats['knowledge_entries_added'] += 1
                
                await asyncio.sleep(self.knowledge_update_interval)
                
            except Exception as e:
                self.logger.error(f"Ошибка в цикле управления знаниями: {e}")
                await asyncio.sleep(60)
    
    async def analyze_current_situation(self) -> Dict[str, Any]:
        """Анализ текущей ситуации в системе"""
        try:
            # Получение состояния системы от ИИ-движка
            system_state = await self.ai_engine.analyze_system_state()
            
            # Дополнительные метрики
            additional_metrics = await self.collect_system_metrics()
            
            # Объединение данных
            situation = {
                **system_state,
                'additional_metrics': additional_metrics,
                'timestamp': datetime.now().isoformat()
            }
            
            return situation
            
        except Exception as e:
            self.logger.error(f"Ошибка анализа ситуации: {e}")
            return {}
    
    async def identify_required_decisions(self, system_state: Dict[str, Any]) -> List[DecisionContext]:
        """Определение необходимых решений"""
        decisions = []
        
        try:
            # Анализ производительности системы
            performance = system_state.get('performance', {})
            
            if performance.get('cpu_percent', 0) > 80:
                decisions.append(DecisionContext(
                    decision_type=DecisionType.SYSTEM_OPTIMIZATION,
                    input_data={'issue': 'high_cpu', 'current_usage': performance['cpu_percent']},
                    timestamp=datetime.now(),
                    priority=8
                ))
            
            if performance.get('memory_percent', 0) > 85:
                decisions.append(DecisionContext(
                    decision_type=DecisionType.SYSTEM_OPTIMIZATION,
                    input_data={'issue': 'high_memory', 'current_usage': performance['memory_percent']},
                    timestamp=datetime.now(),
                    priority=9
                ))
            
            # Анализ сервисов
            services = system_state.get('services', {})
            offline_services = [name for name, data in services.items() if data.get('status') == 'offline']
            
            if offline_services:
                decisions.append(DecisionContext(
                    decision_type=DecisionType.SYSTEM_OPTIMIZATION,
                    input_data={'issue': 'service_outage', 'offline_services': offline_services},
                    timestamp=datetime.now(),
                    priority=10
                ))
            
            # Решения по развитию
            current_hour = datetime.now().hour
            if current_hour % 4 == 0:  # Каждые 4 часа
                decisions.append(DecisionContext(
                    decision_type=DecisionType.DEVELOPMENT_TASK,
                    input_data={'task_type': 'improvement', 'trigger': 'scheduled_enhancement'},
                    timestamp=datetime.now(),
                    priority=5
                ))
            
            return decisions
            
        except Exception as e:
            self.logger.error(f"Ошибка определения решений: {e}")
            return []
    
    async def execute_decision(self, decision, context: DecisionContext):
        """Выполнение принятого решения"""
        try:
            self.logger.info(f"⚡ Выполнение решения: {decision.action}")
            
            # В зависимости от типа решения выполняем различные действия
            if decision.action == "optimize_memory_usage":
                await self.execute_memory_optimization(decision.parameters)
            elif decision.action == "optimize_cpu_usage":
                await self.execute_cpu_optimization(decision.parameters)
            elif decision.action == "restart_failed_services":
                await self.execute_service_restart(decision.parameters)
            elif decision.action == "plan_development_iteration":
                await self.execute_development_planning(decision.parameters)
            else:
                self.logger.info(f"Решение {decision.action} не требует немедленного выполнения")
            
        except Exception as e:
            self.logger.error(f"Ошибка выполнения решения: {e}")
    
    async def execute_memory_optimization(self, parameters: Dict[str, Any]):
        """Выполнение оптимизации памяти"""
        self.logger.info("🧹 Выполнение оптимизации памяти")
        
        # Очистка кешей
        if parameters.get('clear_cache'):
            self.knowledge_base.cache.clear()
            self.logger.info("Очищен кеш базы знаний")
        
        # Дополнительные оптимизации могут быть добавлены здесь
    
    async def execute_cpu_optimization(self, parameters: Dict[str, Any]):
        """Выполнение оптимизации CPU"""
        self.logger.info("⚡ Выполнение оптимизации CPU")
        
        # Увеличение интервалов между операциями
        if parameters.get('limit_background_tasks'):
            self.decision_interval = min(self.decision_interval * 1.2, 60)
            self.learning_interval = min(self.learning_interval * 1.2, 120)
            self.logger.info("Увеличены интервалы между задачами")
    
    async def execute_service_restart(self, parameters: Dict[str, Any]):
        """Перезапуск упавших сервисов"""
        offline_services = parameters.get('services', [])
        self.logger.info(f"🔄 Попытка восстановления сервисов: {offline_services}")
        
        # Здесь можно добавить логику перезапуска сервисов
        # Пока просто логируем
        for service in offline_services:
            self.logger.info(f"Восстановление сервиса: {service}")
    
    async def execute_development_planning(self, parameters: Dict[str, Any]):
        """Планирование задач разработки"""
        task_type = parameters.get('task_type')
        self.logger.info(f"📋 Планирование задачи разработки: {task_type}")
        
        # Сохранение плана в базу знаний
        await self.knowledge_base.add_knowledge(
            topic=f"development_plan_{datetime.now().strftime('%Y%m%d_%H%M')}",
            content=parameters,
            category="development",
            source="ai_coordinator",
            tags=["planning", "development", "automation"]
        )
    
    async def save_decision_knowledge(self, decision, context: DecisionContext):
        """Сохранение знаний о принятом решении"""
        try:
            knowledge_entry = {
                'decision_action': decision.action,
                'confidence': decision.confidence,
                'reasoning': decision.reasoning,
                'expected_outcome': decision.expected_outcome,
                'risk_assessment': decision.risk_assessment,
                'context_type': context.decision_type.value,
                'priority': context.priority,
                'execution_timestamp': datetime.now().isoformat()
            }
            
            await self.knowledge_base.add_knowledge(
                topic=f"decision_{decision.action}_{context.decision_type.value}",
                content=knowledge_entry,
                category="decisions",
                confidence=decision.confidence,
                source="ai_engine",
                tags=["decision", "ai", context.decision_type.value]
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения знаний о решении: {e}")
    
    async def save_prediction_knowledge(self, prediction, market_data: Dict[str, Any]):
        """Сохранение знаний о прогнозе"""
        try:
            knowledge_entry = {
                'prediction_value': prediction.prediction,
                'confidence': prediction.confidence,
                'model_name': prediction.model_name,
                'features_used': prediction.features_used,
                'market_data': market_data,
                'prediction_timestamp': prediction.timestamp.isoformat()
            }
            
            await self.knowledge_base.add_knowledge(
                topic=f"prediction_{prediction.model_name}_{datetime.now().strftime('%Y%m%d_%H%M')}",
                content=knowledge_entry,
                category="predictions",
                confidence=prediction.confidence,
                source="intelligent_algorithms",
                tags=["prediction", "ml", "trading"]
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения знаний о прогнозе: {e}")
    
    async def get_current_market_data(self) -> Dict[str, Any]:
        """Получение текущих рыночных данных"""
        try:
            # Используем сборщик данных из менеджера алгоритмов
            return await self.algorithm_manager.data_collector.collect_market_data()
        except Exception as e:
            self.logger.error(f"Ошибка получения рыночных данных: {e}")
            return {}
    
    async def collect_system_metrics(self) -> Dict[str, Any]:
        """Сбор системных метрик"""
        try:
            import psutil
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100,
                'process_count': len(psutil.pids()),
                'uptime': (datetime.now() - datetime.fromtimestamp(psutil.boot_time())).total_seconds(),
                'ai_coordinator_stats': self.stats.copy()
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Ошибка сбора метрик: {e}")
            return {}
    
    async def update_knowledge_relationships(self):
        """Обновление связей в графе знаний"""
        try:
            # Поиск новых связей между недавними знаниями
            recent_entries = await self.knowledge_base.search_knowledge(
                "", 
                max_results=20
            )
            
            # Создание связей между похожими записями
            for i, entry1 in enumerate(recent_entries):
                for entry2 in recent_entries[i+1:]:
                    if entry1.category == entry2.category:
                        # Создаем связь между записями одной категории
                        await self.knowledge_base.create_relation(
                            entry1.topic,
                            entry2.topic,
                            'category_similarity',
                            0.6
                        )
                        
        except Exception as e:
            self.logger.error(f"Ошибка обновления связей: {e}")
    
    async def cleanup_old_knowledge(self):
        """Очистка устаревших знаний"""
        try:
            # В реальной системе здесь была бы логика удаления старых записей
            # Пока просто логируем
            self.logger.debug("Выполнение очистки устаревших знаний")
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки знаний: {e}")
    
    def stop_ai_coordination(self):
        """Остановка координации ИИ-систем"""
        self.logger.info("🛑 Остановка ИИ-координатора")
        self.is_running = False
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Получение статуса интеграции"""
        uptime = None
        if self.stats['start_time']:
            uptime = (datetime.now() - self.stats['start_time']).total_seconds()
        
        status = {
            'is_running': self.is_running,
            'uptime_seconds': uptime,
            'stats': self.stats,
            'ai_engine_active': hasattr(self.ai_engine, 'knowledge_base'),
            'algorithm_manager_active': hasattr(self.algorithm_manager, 'trading_algorithms'),
            'knowledge_base_entries': len(self.knowledge_base.knowledge_graph.nodes),
            'optimization_enabled': self.optimization_enabled
        }
        
        # Добавляем статус оптимизации если доступен
        if self.performance_optimizer and self.optimization_enabled:
            status['optimization_status'] = self.performance_optimizer.get_optimization_status()
        
        return status

async def main():
    """Демонстрация интеграции ИИ-систем"""
    coordinator = MiraiAICoordinator()
    
    try:
        # Запуск на ограниченное время для демонстрации
        await asyncio.wait_for(coordinator.start_ai_coordination(), timeout=180)  # 3 минуты
    except asyncio.TimeoutError:
        coordinator.stop_ai_coordination()
        print("✅ Демонстрация интеграции ИИ завершена")
        
        # Показываем статистику
        status = coordinator.get_integration_status()
        print(f"📊 Статистика: {status['stats']['decisions_made']} решений, {status['stats']['predictions_generated']} прогнозов")

if __name__ == "__main__":
    asyncio.run(main())
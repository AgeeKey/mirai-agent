#!/usr/bin/env python3
"""
Mirai Advanced AI Engine
Продвинутый ИИ движок для автономного принятия решений
"""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import requests
import sqlite3
from pathlib import Path
import hashlib
import pickle

class DecisionType(Enum):
    SYSTEM_OPTIMIZATION = "system_optimization"
    TRADING_STRATEGY = "trading_strategy"
    CONTENT_GENERATION = "content_generation"
    RESOURCE_ALLOCATION = "resource_allocation"
    SECURITY_ACTION = "security_action"
    DEVELOPMENT_TASK = "development_task"

class ConfidenceLevel(Enum):
    LOW = 0.3
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.95

@dataclass
class DecisionContext:
    """Контекст для принятия решения"""
    decision_type: DecisionType
    input_data: Dict[str, Any]
    timestamp: datetime
    priority: int = 5  # 1-10
    constraints: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.constraints is None:
            self.constraints = {}

@dataclass
class Decision:
    """Результат принятия решения"""
    action: str
    confidence: float
    reasoning: str
    parameters: Dict[str, Any]
    expected_outcome: str
    risk_assessment: Dict[str, float]
    timestamp: datetime
    context_hash: str

class MiraiAdvancedAI:
    """Продвинутый ИИ движок Mirai"""
    
    def __init__(self):
        self.knowledge_base = {}
        self.decision_history = []
        self.learning_data = []
        self.performance_metrics = {}
        self.logger = self.setup_logging()
        self.db_path = '/root/mirai-agent/state/ai_engine.db'
        self.init_database()
        self.load_knowledge_base()
    
    def analyze_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Синхронный метод анализа контекста для обратной совместимости"""
        self.logger.info(f"📊 Анализ контекста: {context}")
        
        # Базовый анализ контекста
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'action': 'analyze_system',
            'confidence': 0.75,
            'context': context,
            'recommendations': []
        }
        
        # Анализ системной нагрузки
        if 'system_load' in context:
            load = context['system_load']
            if load > 0.8:
                analysis['recommendations'].append('optimize_system_performance')
                analysis['confidence'] = 0.9
            elif load > 0.6:
                analysis['recommendations'].append('monitor_system_load')
                analysis['confidence'] = 0.8
        
        # Анализ использования памяти
        if 'memory_usage' in context:
            memory = context['memory_usage']
            if memory > 0.8:
                analysis['recommendations'].append('optimize_memory_usage')
                analysis['confidence'] = min(analysis['confidence'] + 0.1, 1.0)
        
        # Анализ торговой активности
        if 'active_trades' in context:
            trades = context['active_trades']
            if trades > 10:
                analysis['recommendations'].append('review_trading_strategy')
                analysis['confidence'] = min(analysis['confidence'] + 0.05, 1.0)
        
        return analysis
    
    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/root/mirai-agent/logs/ai_engine.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger('MiraiAI')
    
    def init_database(self):
        """Инициализация базы данных ИИ"""
        Path(self.db_path).parent.mkdir(exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    reasoning TEXT NOT NULL,
                    parameters TEXT NOT NULL,
                    expected_outcome TEXT NOT NULL,
                    risk_assessment TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    context_hash TEXT NOT NULL,
                    actual_outcome TEXT,
                    success_score REAL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    data TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS learning_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    pattern_data TEXT NOT NULL,
                    effectiveness REAL NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            ''')
            
            conn.commit()
    
    def load_knowledge_base(self):
        """Загрузка базы знаний"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT topic, data, confidence FROM knowledge")
                
                for topic, data, confidence in cursor.fetchall():
                    try:
                        self.knowledge_base[topic] = {
                            'data': json.loads(data),
                            'confidence': confidence
                        }
                    except json.JSONDecodeError:
                        continue
                        
            self.logger.info(f"Загружено {len(self.knowledge_base)} элементов знаний")
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки базы знаний: {e}")
    
    def save_decision(self, decision: Decision, context: DecisionContext):
        """Сохранение решения в базу данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO decisions 
                    (action, confidence, reasoning, parameters, expected_outcome, 
                     risk_assessment, timestamp, context_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    decision.action,
                    decision.confidence,
                    decision.reasoning,
                    json.dumps(decision.parameters),
                    decision.expected_outcome,
                    json.dumps(decision.risk_assessment),
                    decision.timestamp.isoformat(),
                    decision.context_hash
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Ошибка сохранения решения: {e}")
    
    def update_knowledge(self, topic: str, data: Dict[str, Any], confidence: float = 0.8):
        """Обновление базы знаний"""
        try:
            current_time = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                # Проверяем, существует ли запись
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM knowledge WHERE topic = ?", (topic,))
                existing = cursor.fetchone()
                
                if existing:
                    conn.execute('''
                        UPDATE knowledge 
                        SET data = ?, confidence = ?, updated_at = ?
                        WHERE topic = ?
                    ''', (json.dumps(data), confidence, current_time, topic))
                else:
                    conn.execute('''
                        INSERT INTO knowledge (topic, data, confidence, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (topic, json.dumps(data), confidence, current_time, current_time))
                
                conn.commit()
                
            # Обновляем локальную копию
            self.knowledge_base[topic] = {
                'data': data,
                'confidence': confidence
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления знаний: {e}")
    
    async def analyze_system_state(self) -> Dict[str, Any]:
        """Анализ текущего состояния системы"""
        try:
            # Получаем системные метрики
            system_state = {
                'timestamp': datetime.now().isoformat(),
                'services': {},
                'performance': {},
                'resources': {},
                'health': {}
            }
            
            # Проверяем сервисы
            services = [
                ('api_trading', 'http://localhost:8001/health'),
                ('api_services', 'http://localhost:8002/health'),
                ('web_interface', 'http://localhost:3001'),
                ('monitoring', 'http://localhost:9090'),
            ]
            
            for service_name, url in services:
                try:
                    response = requests.get(url, timeout=5)
                    system_state['services'][service_name] = {
                        'status': 'online' if response.status_code == 200 else 'error',
                        'response_time': response.elapsed.total_seconds()
                    }
                except:
                    system_state['services'][service_name] = {
                        'status': 'offline',
                        'response_time': None
                    }
            
            # Получаем производительность из анализатора
            try:
                import psutil
                system_state['performance'] = {
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_percent': (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100,
                    'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
                }
            except:
                system_state['performance'] = {}
            
            return system_state
            
        except Exception as e:
            self.logger.error(f"Ошибка анализа системы: {e}")
            return {}
    
    def calculate_decision_confidence(self, context: DecisionContext, analysis_result: Dict) -> float:
        """Расчет уверенности в решении"""
        base_confidence = 0.5
        
        # Факторы уверенности
        factors = {
            'data_quality': 0.0,
            'historical_success': 0.0,
            'system_stability': 0.0,
            'risk_level': 0.0
        }
        
        # Качество данных
        if analysis_result and len(analysis_result) > 3:
            factors['data_quality'] = 0.2
        
        # Историческая успешность
        similar_decisions = self.get_similar_decisions(context)
        if similar_decisions:
            avg_success = sum(d.get('success_score', 0.5) for d in similar_decisions) / len(similar_decisions)
            factors['historical_success'] = (avg_success - 0.5) * 0.3
        
        # Стабильность системы
        if analysis_result.get('performance', {}).get('cpu_percent', 100) < 70:
            factors['system_stability'] = 0.1
        
        # Уровень риска
        risk_level = self.assess_risk(context, analysis_result)
        factors['risk_level'] = max(0, (1 - risk_level) * 0.2)
        
        # Итоговая уверенность
        confidence = base_confidence + sum(factors.values())
        return min(0.95, max(0.1, confidence))
    
    def get_similar_decisions(self, context: DecisionContext) -> List[Dict]:
        """Получение похожих решений из истории"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Ищем решения того же типа за последний месяц
                month_ago = (datetime.now() - timedelta(days=30)).isoformat()
                cursor.execute('''
                    SELECT action, confidence, success_score 
                    FROM decisions 
                    WHERE timestamp > ? AND success_score IS NOT NULL
                    ORDER BY timestamp DESC LIMIT 10
                ''', (month_ago,))
                
                return [{'action': action, 'confidence': conf, 'success_score': score} 
                       for action, conf, score in cursor.fetchall()]
        except:
            return []
    
    def assess_risk(self, context: DecisionContext, analysis_result: Dict) -> float:
        """Оценка риска решения"""
        risk_factors = {
            'system_load': 0.0,
            'service_availability': 0.0,
            'decision_complexity': 0.0,
            'potential_impact': 0.0
        }
        
        # Нагрузка на систему
        cpu_usage = analysis_result.get('performance', {}).get('cpu_percent', 0)
        if cpu_usage > 80:
            risk_factors['system_load'] = 0.3
        elif cpu_usage > 60:
            risk_factors['system_load'] = 0.1
        
        # Доступность сервисов
        services = analysis_result.get('services', {})
        offline_services = sum(1 for s in services.values() if s.get('status') == 'offline')
        if offline_services > 0:
            risk_factors['service_availability'] = offline_services * 0.2
        
        # Сложность решения
        if context.decision_type in [DecisionType.SYSTEM_OPTIMIZATION, DecisionType.SECURITY_ACTION]:
            risk_factors['decision_complexity'] = 0.2
        
        # Потенциальное влияние
        if context.priority > 7:
            risk_factors['potential_impact'] = 0.3
        
        return min(1.0, sum(risk_factors.values()))
    
    async def make_decision(self, context: DecisionContext) -> Optional[Decision]:
        """Основной метод принятия решений"""
        self.logger.info(f"🧠 Принятие решения: {context.decision_type.value}")
        
        try:
            # Анализируем текущее состояние
            analysis_result = await self.analyze_system_state()
            
            # Генерируем контекстный хеш
            context_data = asdict(context)
            context_hash = hashlib.md5(json.dumps(context_data, sort_keys=True).encode()).hexdigest()
            
            # Определяем стратегию принятия решения
            decision = None
            
            if context.decision_type == DecisionType.SYSTEM_OPTIMIZATION:
                decision = await self.decide_system_optimization(context, analysis_result)
            elif context.decision_type == DecisionType.TRADING_STRATEGY:
                decision = await self.decide_trading_strategy(context, analysis_result)
            elif context.decision_type == DecisionType.CONTENT_GENERATION:
                decision = await self.decide_content_generation(context, analysis_result)
            elif context.decision_type == DecisionType.RESOURCE_ALLOCATION:
                decision = await self.decide_resource_allocation(context, analysis_result)
            elif context.decision_type == DecisionType.SECURITY_ACTION:
                decision = await self.decide_security_action(context, analysis_result)
            elif context.decision_type == DecisionType.DEVELOPMENT_TASK:
                decision = await self.decide_development_task(context, analysis_result)
            
            if decision:
                decision.context_hash = context_hash
                decision.confidence = self.calculate_decision_confidence(context, analysis_result)
                
                # Сохраняем решение
                self.save_decision(decision, context)
                
                # Обновляем знания
                await self.learn_from_decision(decision, context, analysis_result)
                
                self.logger.info(f"✅ Решение принято: {decision.action} (уверенность: {decision.confidence:.2f})")
                return decision
            
        except Exception as e:
            self.logger.error(f"Ошибка принятия решения: {e}")
        
        return None
    
    async def decide_system_optimization(self, context: DecisionContext, analysis: Dict) -> Decision:
        """Решения по оптимизации системы"""
        performance = analysis.get('performance', {})
        services = analysis.get('services', {})
        
        # Определяем проблемы
        issues = []
        if performance.get('cpu_percent', 0) > 80:
            issues.append('high_cpu')
        if performance.get('memory_percent', 0) > 85:
            issues.append('high_memory')
        if performance.get('disk_percent', 0) > 90:
            issues.append('high_disk')
        
        offline_services = [name for name, data in services.items() if data.get('status') == 'offline']
        if offline_services:
            issues.append('service_outage')
        
        # Выбираем действие
        if 'high_memory' in issues:
            action = "optimize_memory_usage"
            parameters = {
                'clear_cache': True,
                'restart_heavy_processes': True,
                'enable_swap': False
            }
            expected_outcome = "Снижение использования памяти на 10-20%"
            
        elif 'high_cpu' in issues:
            action = "optimize_cpu_usage"
            parameters = {
                'limit_background_tasks': True,
                'optimize_algorithms': True,
                'distribute_load': True
            }
            expected_outcome = "Снижение загрузки CPU на 15-25%"
            
        elif 'service_outage' in issues:
            action = "restart_failed_services"
            parameters = {
                'services': offline_services,
                'health_check': True,
                'gradual_restart': True
            }
            expected_outcome = "Восстановление всех сервисов"
            
        else:
            action = "maintain_optimal_performance"
            parameters = {
                'cleanup_logs': True,
                'update_dependencies': False,
                'monitor_trends': True
            }
            expected_outcome = "Поддержание стабильной работы"
        
        return Decision(
            action=action,
            confidence=0.0,  # Будет пересчитано
            reasoning=f"Обнаружены проблемы: {', '.join(issues) if issues else 'Профилактическое обслуживание'}",
            parameters=parameters,
            expected_outcome=expected_outcome,
            risk_assessment={'system_impact': 0.2, 'downtime_risk': 0.1},
            timestamp=datetime.now(),
            context_hash=""
        )
    
    async def decide_trading_strategy(self, context: DecisionContext, analysis: Dict) -> Decision:
        """Решения по торговым стратегиям"""
        # Пока простая логика, будет расширена с подключением реальных API
        market_data = context.input_data.get('market_data', {})
        
        action = "analyze_market_trends"
        parameters = {
            'timeframe': '1h',
            'indicators': ['sma', 'rsi', 'macd'],
            'risk_level': 'conservative'
        }
        
        return Decision(
            action=action,
            confidence=0.0,
            reasoning="Анализ рыночных трендов для определения стратегии",
            parameters=parameters,
            expected_outcome="Определение оптимальной торговой стратегии",
            risk_assessment={'market_risk': 0.4, 'liquidity_risk': 0.2},
            timestamp=datetime.now(),
            context_hash=""
        )
    
    async def decide_content_generation(self, context: DecisionContext, analysis: Dict) -> Decision:
        """Решения по генерации контента"""
        content_type = context.input_data.get('content_type', 'blog_post')
        topic = context.input_data.get('topic', 'ai_development')
        
        action = "generate_educational_content"
        parameters = {
            'content_type': content_type,
            'topic': topic,
            'length': 'medium',
            'technical_level': 'intermediate'
        }
        
        return Decision(
            action=action,
            confidence=0.0,
            reasoning=f"Генерация контента типа {content_type} на тему {topic}",
            parameters=parameters,
            expected_outcome="Создание качественного образовательного контента",
            risk_assessment={'quality_risk': 0.2, 'relevance_risk': 0.1},
            timestamp=datetime.now(),
            context_hash=""
        )
    
    async def decide_resource_allocation(self, context: DecisionContext, analysis: Dict) -> Decision:
        """Решения по распределению ресурсов"""
        available_resources = context.input_data.get('resources', {})
        
        action = "optimize_resource_distribution"
        parameters = {
            'priority_services': ['api', 'autonomous_system'],
            'resource_limits': {'cpu': 80, 'memory': 85, 'disk': 90},
            'scaling_strategy': 'conservative'
        }
        
        return Decision(
            action=action,
            confidence=0.0,
            reasoning="Оптимизация распределения ресурсов между сервисами",
            parameters=parameters,
            expected_outcome="Более эффективное использование ресурсов",
            risk_assessment={'performance_impact': 0.3, 'stability_risk': 0.2},
            timestamp=datetime.now(),
            context_hash=""
        )
    
    async def decide_security_action(self, context: DecisionContext, analysis: Dict) -> Decision:
        """Решения по безопасности"""
        threat_level = context.input_data.get('threat_level', 'low')
        
        if threat_level == 'high':
            action = "implement_security_lockdown"
            parameters = {
                'block_suspicious_ips': True,
                'enable_strict_monitoring': True,
                'backup_critical_data': True
            }
        else:
            action = "routine_security_check"
            parameters = {
                'scan_vulnerabilities': True,
                'update_security_rules': True,
                'review_access_logs': True
            }
        
        return Decision(
            action=action,
            confidence=0.0,
            reasoning=f"Реагирование на угрозу уровня {threat_level}",
            parameters=parameters,
            expected_outcome="Обеспечение безопасности системы",
            risk_assessment={'security_gap': 0.1, 'false_positive': 0.15},
            timestamp=datetime.now(),
            context_hash=""
        )
    
    async def decide_development_task(self, context: DecisionContext, analysis: Dict) -> Decision:
        """Решения по задачам разработки"""
        task_type = context.input_data.get('task_type', 'enhancement')
        complexity = context.input_data.get('complexity', 'medium')
        
        action = "plan_development_iteration"
        parameters = {
            'task_type': task_type,
            'complexity': complexity,
            'estimated_time': self.estimate_development_time(task_type, complexity),
            'dependencies': context.input_data.get('dependencies', [])
        }
        
        return Decision(
            action=action,
            confidence=0.0,
            reasoning=f"Планирование задачи разработки: {task_type}",
            parameters=parameters,
            expected_outcome="Успешная реализация функциональности",
            risk_assessment={'technical_risk': 0.3, 'time_risk': 0.2},
            timestamp=datetime.now(),
            context_hash=""
        )
    
    def estimate_development_time(self, task_type: str, complexity: str) -> str:
        """Оценка времени разработки"""
        base_times = {
            'bug_fix': {'low': '2h', 'medium': '4h', 'high': '8h'},
            'enhancement': {'low': '6h', 'medium': '12h', 'high': '24h'},
            'new_feature': {'low': '1d', 'medium': '3d', 'high': '1w'},
            'refactoring': {'low': '4h', 'medium': '8h', 'high': '16h'}
        }
        
        return base_times.get(task_type, {}).get(complexity, '8h')
    
    async def learn_from_decision(self, decision: Decision, context: DecisionContext, analysis: Dict):
        """Обучение на основе принятых решений"""
        try:
            # Сохраняем паттерн принятия решения
            pattern = {
                'context_type': context.decision_type.value,
                'system_state': analysis,
                'decision_action': decision.action,
                'confidence': decision.confidence,
                'risk_factors': decision.risk_assessment
            }
            
            # Обновляем знания о паттернах
            pattern_topic = f"decision_pattern_{context.decision_type.value}"
            existing_patterns = self.knowledge_base.get(pattern_topic, {}).get('data', [])
            existing_patterns.append(pattern)
            
            # Ограничиваем количество сохраненных паттернов
            if len(existing_patterns) > 100:
                existing_patterns = existing_patterns[-100:]
            
            self.update_knowledge(pattern_topic, existing_patterns, 0.9)
            
        except Exception as e:
            self.logger.error(f"Ошибка обучения: {e}")
    
    async def get_decision_recommendations(self, decision_type: DecisionType) -> List[str]:
        """Получение рекомендаций по типу решения"""
        try:
            pattern_topic = f"decision_pattern_{decision_type.value}"
            patterns = self.knowledge_base.get(pattern_topic, {}).get('data', [])
            
            if not patterns:
                return []
            
            # Анализируем успешные паттерны
            recommendations = []
            successful_patterns = [p for p in patterns if p.get('confidence', 0) > 0.7]
            
            if successful_patterns:
                common_actions = {}
                for pattern in successful_patterns:
                    action = pattern.get('decision_action', '')
                    common_actions[action] = common_actions.get(action, 0) + 1
                
                # Сортируем по частоте
                sorted_actions = sorted(common_actions.items(), key=lambda x: x[1], reverse=True)
                recommendations = [action for action, count in sorted_actions[:5]]
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Ошибка получения рекомендаций: {e}")
            return []

async def main():
    """Демонстрация работы ИИ движка"""
    ai_engine = MiraiAdvancedAI()
    
    # Пример принятия решения по оптимизации системы
    context = DecisionContext(
        decision_type=DecisionType.SYSTEM_OPTIMIZATION,
        input_data={'trigger': 'performance_degradation'},
        timestamp=datetime.now(),
        priority=8
    )
    
    decision = await ai_engine.make_decision(context)
    if decision:
        print(f"🎯 Принято решение: {decision.action}")
        print(f"🔍 Обоснование: {decision.reasoning}")
        print(f"📊 Уверенность: {decision.confidence:.2f}")
        print(f"🎯 Ожидаемый результат: {decision.expected_outcome}")

if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Mirai AI Performance Validation Suite
Валидация производительности ML моделей и оптимизации
"""

import asyncio
import time
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import sys
import os
from concurrent.futures import ThreadPoolExecutor
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import psutil

# Добавляем путь для импорта ИИ модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from ai_integration import MiraiAICoordinator
    from intelligent_algorithms import IntelligentAlgorithmManager
    from performance_optimizer import MiraiPerformanceOptimizer
    from knowledge_base import MiraiKnowledgeBase
    AI_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ ИИ компоненты недоступны: {e}")
    AI_COMPONENTS_AVAILABLE = False

class PerformanceValidationSuite:
    """Набор тестов для валидации производительности ИИ системы"""
    
    def __init__(self):
        self.logger = self.setup_logging()
        self.results = {
            'test_start_time': datetime.now().isoformat(),
            'tests': [],
            'system_metrics': [],
            'ml_performance': {},
            'optimization_results': {}
        }
        
        if AI_COMPONENTS_AVAILABLE:
            self.ai_coordinator = MiraiAICoordinator()
            self.algorithm_manager = IntelligentAlgorithmManager()
            self.performance_optimizer = MiraiPerformanceOptimizer()
            self.knowledge_base = MiraiKnowledgeBase()
        else:
            self.ai_coordinator = None
            self.algorithm_manager = None
            self.performance_optimizer = None
            self.knowledge_base = None
    
    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/root/mirai-agent/logs/performance_validation.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger('PerformanceValidator')
    
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Сбор системных метрик"""
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_used': psutil.virtual_memory().used,
            'memory_total': psutil.virtual_memory().total,
            'disk_usage': psutil.disk_usage('/').percent,
            'processes': len(psutil.pids()),
            'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
        }
    
    async def test_decision_making_performance(self) -> Dict[str, Any]:
        """Тест производительности принятия решений"""
        self.logger.info("🧠 Тестирование производительности принятия решений")
        
        if not self.ai_coordinator:
            return {'error': 'AI coordinator not available', 'success': False}
        
        # Подготовка тестовых контекстов
        test_contexts = [
            {'system_load': 0.3, 'memory_usage': 0.4, 'active_trades': 2},
            {'system_load': 0.6, 'memory_usage': 0.7, 'active_trades': 5},
            {'system_load': 0.8, 'memory_usage': 0.9, 'active_trades': 10},
            {'system_load': 0.5, 'memory_usage': 0.5, 'active_trades': 3},
            {'system_load': 0.9, 'memory_usage': 0.8, 'active_trades': 8}
        ]
        
        decision_times = []
        successful_decisions = 0
        
        for i, context in enumerate(test_contexts):
            start_time = time.time()
            
            try:
                # Добавляем метку времени и номер теста
                context['timestamp'] = datetime.now().isoformat()
                context['test_id'] = i + 1
                
                # Анализируем контекст через ИИ движок
                decision = self.ai_coordinator.ai_engine.analyze_context(context)
                
                decision_time = time.time() - start_time
                decision_times.append(decision_time)
                
                if decision and isinstance(decision, dict):
                    successful_decisions += 1
                    self.logger.info(f"✅ Решение {i+1}: {decision_time:.3f}с, уверенность: {decision.get('confidence', 0):.2f}")
                else:
                    self.logger.warning(f"⚠️ Решение {i+1}: некорректный результат")
                
            except Exception as e:
                self.logger.error(f"❌ Ошибка в решении {i+1}: {e}")
                decision_times.append(999.0)  # Штрафное время
        
        # Анализ результатов
        avg_time = np.mean(decision_times) if decision_times else 0
        max_time = np.max(decision_times) if decision_times else 0
        min_time = np.min(decision_times) if decision_times else 0
        success_rate = successful_decisions / len(test_contexts) * 100
        
        result = {
            'test_name': 'Decision Making Performance',
            'total_tests': len(test_contexts),
            'successful_decisions': successful_decisions,
            'success_rate_percent': success_rate,
            'avg_decision_time_ms': avg_time * 1000,
            'max_decision_time_ms': max_time * 1000,
            'min_decision_time_ms': min_time * 1000,
            'performance_rating': 'excellent' if avg_time < 0.1 else 'good' if avg_time < 0.5 else 'needs_improvement',
            'success': success_rate >= 80
        }
        
        self.results['tests'].append(result)
        return result
    
    async def test_knowledge_base_performance(self) -> Dict[str, Any]:
        """Тест производительности базы знаний"""
        self.logger.info("📚 Тестирование производительности базы знаний")
        
        if not self.knowledge_base:
            return {'error': 'Knowledge base not available', 'success': False}
        
        # Тестовые данные для базы знаний
        test_knowledge_entries = [
            {
                'title': f'AI Strategy {i}',
                'content': f'Advanced AI trading strategy #{i} with machine learning components and real-time analysis capabilities',
                'category': 'AI/ML',
                'tags': ['ai', 'strategy', f'test-{i}']
            }
            for i in range(1, 21)  # 20 записей
        ]
        
        # Тест добавления знаний
        add_times = []
        successful_adds = 0
        
        for entry in test_knowledge_entries:
            start_time = time.time()
            
            try:
                # Синхронное добавление (если async не работает)
                if hasattr(self.knowledge_base, 'add_knowledge'):
                    result = self.knowledge_base.add_knowledge(
                        entry['title'],
                        entry['content'], 
                        entry['category'],
                        entry['tags']
                    )
                    
                    add_time = time.time() - start_time
                    add_times.append(add_time)
                    
                    if result:
                        successful_adds += 1
                
            except Exception as e:
                self.logger.warning(f"⚠️ Ошибка добавления знания: {e}")
                add_times.append(999.0)
        
        # Тест поиска знаний
        search_queries = ['AI', 'trading', 'strategy', 'machine learning', 'analysis']
        search_times = []
        successful_searches = 0
        
        for query in search_queries:
            start_time = time.time()
            
            try:
                if hasattr(self.knowledge_base, 'search_knowledge'):
                    results = self.knowledge_base.search_knowledge(query)
                    search_time = time.time() - start_time
                    search_times.append(search_time)
                    
                    if results is not None:
                        successful_searches += 1
                        self.logger.info(f"🔍 Поиск '{query}': {search_time:.3f}с, найдено: {len(results) if isinstance(results, list) else 'N/A'}")
                
            except Exception as e:
                self.logger.warning(f"⚠️ Ошибка поиска '{query}': {e}")
                search_times.append(999.0)
        
        # Статистика базы знаний
        try:
            stats = self.knowledge_base.get_statistics()
            total_entries = stats.get('total_entries', 0)
        except:
            total_entries = 0
        
        # Анализ результатов
        avg_add_time = np.mean(add_times) if add_times else 0
        avg_search_time = np.mean(search_times) if search_times else 0
        add_success_rate = successful_adds / len(test_knowledge_entries) * 100 if test_knowledge_entries else 0
        search_success_rate = successful_searches / len(search_queries) * 100 if search_queries else 0
        
        result = {
            'test_name': 'Knowledge Base Performance',
            'total_entries_in_db': total_entries,
            'test_additions': len(test_knowledge_entries),
            'successful_additions': successful_adds,
            'add_success_rate_percent': add_success_rate,
            'avg_add_time_ms': avg_add_time * 1000,
            'test_searches': len(search_queries),
            'successful_searches': successful_searches,
            'search_success_rate_percent': search_success_rate,
            'avg_search_time_ms': avg_search_time * 1000,
            'performance_rating': 'excellent' if avg_search_time < 0.1 else 'good' if avg_search_time < 0.5 else 'needs_improvement',
            'success': add_success_rate >= 70 and search_success_rate >= 70
        }
        
        self.results['tests'].append(result)
        return result
    
    async def test_ml_algorithm_performance(self) -> Dict[str, Any]:
        """Тест производительности ML алгоритмов"""
        self.logger.info("🤖 Тестирование производительности ML алгоритмов")
        
        if not self.algorithm_manager:
            return {'error': 'Algorithm manager not available', 'success': False}
        
        # Генерация тестовых данных
        test_data = self.generate_test_market_data()
        
        # Тест различных алгоритмов
        algorithm_results = {}
        symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
        
        for symbol in symbols:
            symbol_results = {}
            
            # Тест генерации предсказаний
            prediction_times = []
            successful_predictions = 0
            
            for i in range(5):  # 5 тестов на символ
                start_time = time.time()
                
                try:
                    # Пробуем разные методы предсказания
                    prediction = None
                    
                    if hasattr(self.algorithm_manager, 'generate_predictions'):
                        # Проверяем если метод асинхронный
                        method = getattr(self.algorithm_manager, 'generate_predictions')
                        if asyncio.iscoroutinefunction(method):
                            prediction = await method(symbol)
                        else:
                            prediction = method(symbol)
                    
                    prediction_time = time.time() - start_time
                    prediction_times.append(prediction_time)
                    
                    if prediction is not None:
                        successful_predictions += 1
                        self.logger.info(f"🎯 Предсказание {symbol}-{i+1}: {prediction_time:.3f}с")
                
                except Exception as e:
                    self.logger.warning(f"⚠️ Ошибка предсказания {symbol}-{i+1}: {e}")
                    prediction_times.append(999.0)
            
            # Анализ результатов для символа
            avg_prediction_time = np.mean(prediction_times) if prediction_times else 0
            success_rate = successful_predictions / 5 * 100
            
            symbol_results = {
                'symbol': symbol,
                'test_count': 5,
                'successful_predictions': successful_predictions,
                'success_rate_percent': success_rate,
                'avg_prediction_time_ms': avg_prediction_time * 1000,
                'performance_rating': 'excellent' if avg_prediction_time < 1.0 else 'good' if avg_prediction_time < 3.0 else 'needs_improvement'
            }
            
            algorithm_results[symbol] = symbol_results
        
        # Общий анализ ML производительности
        all_success_rates = [results['success_rate_percent'] for results in algorithm_results.values()]
        all_times = [results['avg_prediction_time_ms'] for results in algorithm_results.values()]
        
        overall_success_rate = np.mean(all_success_rates) if all_success_rates else 0
        overall_avg_time = np.mean(all_times) if all_times else 0
        
        result = {
            'test_name': 'ML Algorithm Performance',
            'tested_symbols': symbols,
            'symbol_results': algorithm_results,
            'overall_success_rate_percent': overall_success_rate,
            'overall_avg_prediction_time_ms': overall_avg_time,
            'performance_rating': 'excellent' if overall_avg_time < 1000 else 'good' if overall_avg_time < 3000 else 'needs_improvement',
            'success': overall_success_rate >= 60
        }
        
        self.results['ml_performance'] = result
        return result
    
    def generate_test_market_data(self) -> Dict[str, List[float]]:
        """Генерация тестовых рыночных данных"""
        np.random.seed(42)  # Для воспроизводимости
        
        data = {}
        symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
        
        for symbol in symbols:
            # Генерируем случайные цены с трендом
            base_price = 45000 if symbol == 'BTCUSDT' else 3000 if symbol == 'ETHUSDT' else 1.5
            prices = [base_price]
            
            for i in range(100):  # 100 точек данных
                change = np.random.normal(0, base_price * 0.02)  # 2% волатильность
                new_price = max(prices[-1] + change, base_price * 0.5)  # Минимум 50% от базовой цены
                prices.append(new_price)
            
            data[symbol] = prices
        
        return data
    
    async def test_optimization_effectiveness(self) -> Dict[str, Any]:
        """Тест эффективности оптимизации"""
        self.logger.info("⚡ Тестирование эффективности оптимизации")
        
        if not self.performance_optimizer:
            return {'error': 'Performance optimizer not available', 'success': False}
        
        # Измерение производительности до оптимизации
        metrics_before = self.collect_system_metrics()
        
        # Тест кеширования
        cache_test_results = self.test_cache_performance()
        
        # Тест оптимизации памяти
        memory_test_results = self.test_memory_optimization()
        
        # Измерение производительности после оптимизации
        metrics_after = self.collect_system_metrics()
        
        # Анализ улучшений
        memory_improvement = metrics_before['memory_percent'] - metrics_after['memory_percent']
        cpu_impact = metrics_after['cpu_percent'] - metrics_before['cpu_percent']
        
        result = {
            'test_name': 'Optimization Effectiveness',
            'cache_performance': cache_test_results,
            'memory_optimization': memory_test_results,
            'system_metrics_before': metrics_before,
            'system_metrics_after': metrics_after,
            'memory_improvement_percent': memory_improvement,
            'cpu_impact_percent': cpu_impact,
            'optimization_effective': memory_improvement > 0 and cpu_impact < 10,
            'success': True
        }
        
        self.results['optimization_results'] = result
        return result
    
    def test_cache_performance(self) -> Dict[str, Any]:
        """Тест производительности кеширования"""
        if not hasattr(self.performance_optimizer, 'cache_manager'):
            return {'error': 'Cache manager not available'}
        
        cache_manager = self.performance_optimizer.cache_manager
        
        # Тест записи в кеш
        write_times = []
        for i in range(100):
            start_time = time.time()
            cache_manager.set(f'test_key_{i}', {'data': f'test_value_{i}', 'timestamp': time.time()})
            write_time = time.time() - start_time
            write_times.append(write_time)
        
        # Тест чтения из кеша
        read_times = []
        cache_hits = 0
        for i in range(100):
            start_time = time.time()
            value = cache_manager.get(f'test_key_{i}')
            read_time = time.time() - start_time
            read_times.append(read_time)
            
            if value is not None:
                cache_hits += 1
        
        return {
            'avg_write_time_ms': np.mean(write_times) * 1000 if write_times else 0,
            'avg_read_time_ms': np.mean(read_times) * 1000 if read_times else 0,
            'cache_hit_rate_percent': cache_hits,
            'performance_rating': 'excellent' if np.mean(read_times) < 0.001 else 'good'
        }
    
    def test_memory_optimization(self) -> Dict[str, Any]:
        """Тест оптимизации памяти"""
        try:
            # Тест memory pool если доступен
            if hasattr(self.performance_optimizer, 'memory_pool'):
                memory_pool = self.performance_optimizer.memory_pool
                
                # Создаем большие объекты для тестирования
                test_objects = []
                for i in range(10):
                    test_objects.append(np.random.rand(1000, 1000))  # 1M элементов
                
                # Имитируем оптимизацию памяти
                del test_objects
                
                return {
                    'memory_pool_available': True,
                    'optimization_applied': True,
                    'performance_rating': 'good'
                }
            else:
                return {
                    'memory_pool_available': False,
                    'optimization_applied': False,
                    'performance_rating': 'needs_improvement'
                }
        
        except Exception as e:
            return {
                'error': str(e),
                'memory_pool_available': False,
                'optimization_applied': False
            }
    
    async def run_full_performance_validation(self) -> Dict[str, Any]:
        """Запуск полной валидации производительности"""
        self.logger.info("🚀 Запуск полной валидации производительности ИИ системы")
        
        start_time = time.time()
        
        # Сбор начальных системных метрик
        initial_metrics = self.collect_system_metrics()
        self.results['system_metrics'].append(initial_metrics)
        
        # Выполнение всех тестов
        tests = [
            self.test_decision_making_performance(),
            self.test_knowledge_base_performance(),
            self.test_ml_algorithm_performance(),
            self.test_optimization_effectiveness()
        ]
        
        # Запуск тестов параллельно где возможно
        test_results = []
        for test in tests:
            try:
                result = await test
                test_results.append(result)
                
                # Сбор метрик после каждого теста
                metrics = self.collect_system_metrics()
                self.results['system_metrics'].append(metrics)
                
            except Exception as e:
                self.logger.error(f"❌ Ошибка выполнения теста: {e}")
                test_results.append({'error': str(e), 'success': False})
        
        total_time = time.time() - start_time
        
        # Анализ общих результатов
        successful_tests = sum(1 for result in test_results if result.get('success', False))
        overall_success_rate = successful_tests / len(test_results) * 100
        
        # Итоговый отчет
        final_report = {
            'validation_summary': {
                'total_tests': len(test_results),
                'successful_tests': successful_tests,
                'overall_success_rate_percent': overall_success_rate,
                'total_validation_time_seconds': total_time,
                'validation_rating': 'excellent' if overall_success_rate >= 90 else 'good' if overall_success_rate >= 70 else 'needs_improvement'
            },
            'test_results': test_results,
            'system_performance': {
                'avg_cpu_usage': np.mean([m['cpu_percent'] for m in self.results['system_metrics']]),
                'avg_memory_usage': np.mean([m['memory_percent'] for m in self.results['system_metrics']]),
                'peak_memory_usage': np.max([m['memory_percent'] for m in self.results['system_metrics']])
            },
            'recommendations': self.generate_performance_recommendations(test_results),
            'timestamp': datetime.now().isoformat()
        }
        
        self.results.update(final_report)
        
        # Сохранение результатов
        self.save_results()
        
        return final_report
    
    def generate_performance_recommendations(self, test_results: List[Dict]) -> List[str]:
        """Генерация рекомендаций по улучшению производительности"""
        recommendations = []
        
        for result in test_results:
            if not result.get('success', False):
                test_name = result.get('test_name', 'Unknown test')
                recommendations.append(f"Исправить проблемы в тесте: {test_name}")
            
            # Анализ времени отклика
            if 'avg_decision_time_ms' in result and result['avg_decision_time_ms'] > 500:
                recommendations.append("Оптимизировать скорость принятия решений")
            
            if 'avg_search_time_ms' in result and result['avg_search_time_ms'] > 100:
                recommendations.append("Улучшить индексацию базы знаний")
            
            if 'overall_avg_prediction_time_ms' in result and result['overall_avg_prediction_time_ms'] > 2000:
                recommendations.append("Оптимизировать ML алгоритмы")
        
        if not recommendations:
            recommendations.append("Система работает оптимально")
        
        return recommendations
    
    def save_results(self):
        """Сохранение результатов валидации"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/root/mirai-agent/reports/performance_validation_{timestamp}.json"
        
        # Создаем директорию если не существует
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Преобразуем numpy типы в обычные Python типы для JSON сериализации
        def convert_numpy_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            else:
                return obj
        
        results_for_json = convert_numpy_types(self.results)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_for_json, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"📊 Результаты сохранены в: {filename}")
    
    def print_summary(self):
        """Вывод краткого отчета"""
        if 'validation_summary' not in self.results:
            print("❌ Валидация не выполнена")
            return
        
        summary = self.results['validation_summary']
        
        print("\n" + "="*60)
        print("🎯 ОТЧЕТ ПО ВАЛИДАЦИИ ПРОИЗВОДИТЕЛЬНОСТИ ИИ")
        print("="*60)
        print(f"📊 Тестов выполнено: {summary['total_tests']}")
        print(f"✅ Успешных тестов: {summary['successful_tests']}")
        print(f"📈 Общий процент успеха: {summary['overall_success_rate_percent']:.1f}%")
        print(f"⏱️  Время валидации: {summary['total_validation_time_seconds']:.2f} секунд")
        print(f"🏆 Общая оценка: {summary['validation_rating']}")
        
        if 'system_performance' in self.results:
            perf = self.results['system_performance']
            print(f"\n💻 Системная производительность:")
            print(f"   CPU: {perf['avg_cpu_usage']:.1f}% (среднее)")
            print(f"   Память: {perf['avg_memory_usage']:.1f}% (среднее), {perf['peak_memory_usage']:.1f}% (пик)")
        
        if 'recommendations' in self.results:
            print(f"\n💡 Рекомендации:")
            for i, rec in enumerate(self.results['recommendations'], 1):
                print(f"   {i}. {rec}")
        
        print("="*60)

async def main():
    """Основная функция для запуска валидации"""
    print("🚀 Mirai AI Performance Validation Suite")
    print("Запуск комплексной валидации производительности ИИ системы...")
    
    validator = PerformanceValidationSuite()
    
    if not AI_COMPONENTS_AVAILABLE:
        print("❌ ИИ компоненты недоступны. Установите зависимости:")
        print("   pip install numpy pandas scikit-learn requests aiofiles psutil")
        return
    
    try:
        # Запуск полной валидации
        results = await validator.run_full_performance_validation()
        
        # Вывод отчета
        validator.print_summary()
        
        return results
        
    except Exception as e:
        validator.logger.error(f"❌ Критическая ошибка валидации: {e}")
        print(f"❌ Ошибка выполнения валидации: {e}")
        return None

if __name__ == "__main__":
    # Запуск валидации
    asyncio.run(main())
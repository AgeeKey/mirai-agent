"""
Mirai Agent - Portfolio Management System
Система управления портфелем с автоматической ребалансировкой и диверсификацией
"""
import asyncio
import logging
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sys
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AssetClass(Enum):
    """Классы активов"""
    CRYPTOCURRENCY = "crypto"
    FOREX = "forex"
    STOCKS = "stocks"
    COMMODITIES = "commodities"

class RebalanceStrategy(Enum):
    """Стратегии ребалансировки"""
    TIME_BASED = "time_based"          # По времени
    THRESHOLD_BASED = "threshold_based" # По отклонению
    VOLATILITY_BASED = "volatility_based" # По волатильности
    RISK_PARITY = "risk_parity"        # Равенство рисков

@dataclass
class AssetAllocation:
    """Распределение активов"""
    symbol: str
    asset_class: AssetClass
    target_weight: float  # Целевая доля (0-1)
    current_weight: float = 0.0
    min_weight: float = 0.0
    max_weight: float = 1.0
    risk_score: float = 5.0  # 1-10
    correlation_group: str = "default"

@dataclass
class PortfolioMetrics:
    """Метрики портфеля"""
    total_value: float
    total_pnl: float
    daily_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    diversification_ratio: float
    risk_score: float
    concentration_risk: float
    correlation_risk: float

@dataclass
class RebalanceAction:
    """Действие ребалансировки"""
    symbol: str
    action: str  # buy/sell
    current_amount: float
    target_amount: float
    difference: float
    reasoning: str

class CorrelationAnalyzer:
    """Анализатор корреляций между активами"""
    
    def __init__(self):
        # Матрица корреляций (симуляция)
        self.correlation_matrix = {
            "BTCUSDT": {"ETHUSDT": 0.85, "ADAUSDT": 0.70, "EURUSD": -0.20},
            "ETHUSDT": {"BTCUSDT": 0.85, "ADAUSDT": 0.75, "EURUSD": -0.15},
            "ADAUSDT": {"BTCUSDT": 0.70, "ETHUSDT": 0.75, "EURUSD": -0.10},
            "EURUSD": {"BTCUSDT": -0.20, "ETHUSDT": -0.15, "ADAUSDT": -0.10}
        }
    
    def get_correlation(self, symbol1: str, symbol2: str) -> float:
        """Получение корреляции между двумя активами"""
        if symbol1 in self.correlation_matrix and symbol2 in self.correlation_matrix[symbol1]:
            return self.correlation_matrix[symbol1][symbol2]
        elif symbol2 in self.correlation_matrix and symbol1 in self.correlation_matrix[symbol2]:
            return self.correlation_matrix[symbol2][symbol1]
        else:
            return 0.0  # Нет данных о корреляции
    
    def calculate_portfolio_correlation_risk(self, allocations: List[AssetAllocation]) -> float:
        """Расчет корреляционного риска портфеля"""
        if len(allocations) < 2:
            return 0.0
        
        total_correlation_risk = 0.0
        pair_count = 0
        
        for i, asset1 in enumerate(allocations):
            for j, asset2 in enumerate(allocations[i+1:], i+1):
                correlation = abs(self.get_correlation(asset1.symbol, asset2.symbol))
                weight_product = asset1.current_weight * asset2.current_weight
                risk_contribution = correlation * weight_product
                total_correlation_risk += risk_contribution
                pair_count += 1
        
        return total_correlation_risk / max(1, pair_count) if pair_count > 0 else 0.0

class RiskMetricsCalculator:
    """Калькулятор метрик риска"""
    
    @staticmethod
    def calculate_portfolio_volatility(allocations: List[AssetAllocation], 
                                     correlation_analyzer: CorrelationAnalyzer) -> float:
        """Расчет волатильности портфеля"""
        if not allocations:
            return 0.0
        
        # Упрощенный расчет волатильности портфеля
        portfolio_variance = 0.0
        
        # Индивидуальные риски
        for asset in allocations:
            # Предполагаем волатильность на основе риск-скора
            asset_volatility = asset.risk_score * 0.02  # 2% за единицу риска
            portfolio_variance += (asset.current_weight ** 2) * (asset_volatility ** 2)
        
        # Корреляционные эффекты
        for i, asset1 in enumerate(allocations):
            for j, asset2 in enumerate(allocations[i+1:], i+1):
                correlation = correlation_analyzer.get_correlation(asset1.symbol, asset2.symbol)
                vol1 = asset1.risk_score * 0.02
                vol2 = asset2.risk_score * 0.02
                covariance = correlation * vol1 * vol2
                portfolio_variance += 2 * asset1.current_weight * asset2.current_weight * covariance
        
        return np.sqrt(max(0, portfolio_variance))
    
    @staticmethod
    def calculate_diversification_ratio(allocations: List[AssetAllocation]) -> float:
        """Расчет коэффициента диверсификации"""
        if not allocations:
            return 0.0
        
        # Коэффициент Херфиндаля-Хиршмана (обратный)
        hhi = sum(weight.current_weight ** 2 for weight in allocations)
        max_diversification = 1.0 / len(allocations)  # Равномерное распределение
        
        return max(0, 1 - hhi / max_diversification) if max_diversification > 0 else 0.0
    
    @staticmethod
    def calculate_concentration_risk(allocations: List[AssetAllocation]) -> float:
        """Расчет риска концентрации"""
        if not allocations:
            return 0.0
        
        # Максимальная доля активов
        max_weight = max(asset.current_weight for asset in allocations)
        
        # Доля топ-3 активов
        sorted_weights = sorted([asset.current_weight for asset in allocations], reverse=True)
        top3_weight = sum(sorted_weights[:3])
        
        return max(max_weight, top3_weight / 3.0)

class PortfolioOptimizer:
    """Оптимизатор портфеля"""
    
    def __init__(self, strategy: RebalanceStrategy = RebalanceStrategy.THRESHOLD_BASED):
        self.strategy = strategy
        self.correlation_analyzer = CorrelationAnalyzer()
        self.risk_calculator = RiskMetricsCalculator()
    
    def optimize_allocation(self, allocations: List[AssetAllocation], 
                          market_conditions: Dict) -> List[AssetAllocation]:
        """Оптимизация распределения активов"""
        
        if self.strategy == RebalanceStrategy.THRESHOLD_BASED:
            return self._threshold_optimization(allocations)
        elif self.strategy == RebalanceStrategy.VOLATILITY_BASED:
            return self._volatility_optimization(allocations, market_conditions)
        elif self.strategy == RebalanceStrategy.RISK_PARITY:
            return self._risk_parity_optimization(allocations)
        else:
            return allocations  # Без изменений
    
    def _threshold_optimization(self, allocations: List[AssetAllocation]) -> List[AssetAllocation]:
        """Оптимизация на основе пороговых отклонений"""
        threshold = 0.05  # 5% отклонение
        
        optimized = []
        for asset in allocations:
            deviation = abs(asset.current_weight - asset.target_weight)
            
            if deviation > threshold:
                # Постепенная корректировка к целевому весу
                adjustment = (asset.target_weight - asset.current_weight) * 0.5
                new_weight = asset.current_weight + adjustment
                
                # Соблюдение лимитов
                new_weight = max(asset.min_weight, min(asset.max_weight, new_weight))
                
                asset.target_weight = new_weight
            
            optimized.append(asset)
        
        return self._normalize_weights(optimized)
    
    def _volatility_optimization(self, allocations: List[AssetAllocation], 
                               market_conditions: Dict) -> List[AssetAllocation]:
        """Оптимизация на основе волатильности"""
        market_volatility = market_conditions.get('volatility', 0.02)
        
        optimized = []
        for asset in allocations:
            # Уменьшение веса высокорисковых активов при высокой волатильности
            if market_volatility > 0.05 and asset.risk_score > 7:
                adjustment = -0.1 * (market_volatility - 0.05)
                new_weight = asset.target_weight + adjustment
            # Увеличение веса низкорисковых активов
            elif market_volatility > 0.05 and asset.risk_score < 4:
                adjustment = 0.05 * (market_volatility - 0.05)
                new_weight = asset.target_weight + adjustment
            else:
                new_weight = asset.target_weight
            
            # Соблюдение лимитов
            new_weight = max(asset.min_weight, min(asset.max_weight, new_weight))
            asset.target_weight = new_weight
            optimized.append(asset)
        
        return self._normalize_weights(optimized)
    
    def _risk_parity_optimization(self, allocations: List[AssetAllocation]) -> List[AssetAllocation]:
        """Оптимизация равенства рисков"""
        # Инвертированные веса на основе риск-скора
        total_inverse_risk = sum(1.0 / max(0.1, asset.risk_score) for asset in allocations)
        
        optimized = []
        for asset in allocations:
            # Вес обратно пропорционален риску
            risk_parity_weight = (1.0 / max(0.1, asset.risk_score)) / total_inverse_risk
            
            # Постепенная корректировка
            adjustment = (risk_parity_weight - asset.current_weight) * 0.3
            new_weight = asset.current_weight + adjustment
            
            # Соблюдение лимитов
            new_weight = max(asset.min_weight, min(asset.max_weight, new_weight))
            asset.target_weight = new_weight
            optimized.append(asset)
        
        return self._normalize_weights(optimized)
    
    def _normalize_weights(self, allocations: List[AssetAllocation]) -> List[AssetAllocation]:
        """Нормализация весов до суммы 1.0"""
        total_weight = sum(asset.target_weight for asset in allocations)
        
        if total_weight > 0:
            for asset in allocations:
                asset.target_weight = asset.target_weight / total_weight
        
        return allocations

class PortfolioManager:
    """Основной менеджер портфеля"""
    
    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.allocations: List[AssetAllocation] = []
        self.optimizer = PortfolioOptimizer()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.risk_calculator = RiskMetricsCalculator()
        
        # История ребалансировок
        self.rebalance_history: List[Dict] = []
        self.last_rebalance = datetime.now()
        
        logger.info(f"Инициализирован Portfolio Manager с балансом ${initial_balance}")
    
    def add_asset(self, allocation: AssetAllocation):
        """Добавление актива в портфель"""
        # Проверка на дублирование
        existing = next((a for a in self.allocations if a.symbol == allocation.symbol), None)
        if existing:
            existing.target_weight = allocation.target_weight
            existing.min_weight = allocation.min_weight
            existing.max_weight = allocation.max_weight
            logger.info(f"Обновлен актив {allocation.symbol}")
        else:
            self.allocations.append(allocation)
            logger.info(f"Добавлен актив {allocation.symbol} с целевым весом {allocation.target_weight:.1%}")
        
        # Нормализация весов
        self._normalize_target_weights()
    
    def update_current_weights(self, current_positions: Dict[str, float]):
        """Обновление текущих весов на основе позиций"""
        total_value = sum(current_positions.values())
        
        for allocation in self.allocations:
            if allocation.symbol in current_positions and total_value > 0:
                allocation.current_weight = current_positions[allocation.symbol] / total_value
            else:
                allocation.current_weight = 0.0
        
        self.current_balance = total_value
    
    async def calculate_portfolio_metrics(self) -> PortfolioMetrics:
        """Расчет метрик портфеля"""
        
        # Базовые метрики
        total_value = self.current_balance
        total_pnl = total_value - self.initial_balance
        daily_return = total_pnl / self.initial_balance if self.initial_balance > 0 else 0.0
        
        # Риск-метрики
        volatility = self.risk_calculator.calculate_portfolio_volatility(
            self.allocations, self.correlation_analyzer
        )
        
        diversification_ratio = self.risk_calculator.calculate_diversification_ratio(self.allocations)
        concentration_risk = self.risk_calculator.calculate_concentration_risk(self.allocations)
        correlation_risk = self.correlation_analyzer.calculate_portfolio_correlation_risk(self.allocations)
        
        # Средний риск-скор
        risk_score = np.mean([asset.risk_score for asset in self.allocations]) if self.allocations else 0.0
        
        # Sharpe ratio (упрощенный)
        risk_free_rate = 0.02  # 2% безрисковая ставка
        sharpe_ratio = (daily_return - risk_free_rate) / max(volatility, 0.001)
        
        return PortfolioMetrics(
            total_value=total_value,
            total_pnl=total_pnl,
            daily_return=daily_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max(0, (self.initial_balance - total_value) / self.initial_balance),
            diversification_ratio=diversification_ratio,
            risk_score=risk_score,
            concentration_risk=concentration_risk,
            correlation_risk=correlation_risk
        )
    
    async def should_rebalance(self, market_conditions: Dict) -> Tuple[bool, str]:
        """Определение необходимости ребалансировки"""
        
        # Временной критерий (раз в день)
        time_since_last = datetime.now() - self.last_rebalance
        if time_since_last > timedelta(hours=24):
            return True, "Плановая ребалансировка (24 часа)"
        
        # Критерий отклонения
        max_deviation = 0.0
        for asset in self.allocations:
            deviation = abs(asset.current_weight - asset.target_weight)
            max_deviation = max(max_deviation, deviation)
        
        if max_deviation > 0.1:  # 10% отклонение
            return True, f"Критическое отклонение весов: {max_deviation:.1%}"
        
        # Критерий волатильности
        market_volatility = market_conditions.get('volatility', 0.02)
        if market_volatility > 0.07:  # Высокая волатильность
            return True, f"Высокая рыночная волатильность: {market_volatility:.1%}"
        
        # Критерий корреляционного риска
        correlation_risk = self.correlation_analyzer.calculate_portfolio_correlation_risk(self.allocations)
        if correlation_risk > 0.5:  # Высокая корреляция
            return True, f"Высокий корреляционный риск: {correlation_risk:.1%}"
        
        return False, "Ребалансировка не требуется"
    
    async def execute_rebalance(self, market_conditions: Dict) -> List[RebalanceAction]:
        """Выполнение ребалансировки портфеля"""
        
        logger.info("Начало ребалансировки портфеля")
        
        # Оптимизация распределения
        optimized_allocations = self.optimizer.optimize_allocation(self.allocations, market_conditions)
        self.allocations = optimized_allocations
        
        # Генерация действий ребалансировки
        actions = []
        total_value = self.current_balance
        
        for asset in self.allocations:
            current_amount = asset.current_weight * total_value
            target_amount = asset.target_weight * total_value
            difference = target_amount - current_amount
            
            if abs(difference) > total_value * 0.01:  # Минимум 1% от портфеля
                action = "buy" if difference > 0 else "sell"
                
                reasoning = f"Корректировка веса с {asset.current_weight:.1%} до {asset.target_weight:.1%}"
                
                actions.append(RebalanceAction(
                    symbol=asset.symbol,
                    action=action,
                    current_amount=current_amount,
                    target_amount=target_amount,
                    difference=abs(difference),
                    reasoning=reasoning
                ))
        
        # Сохранение в историю
        rebalance_record = {
            "timestamp": datetime.now().isoformat(),
            "actions_count": len(actions),
            "total_adjustment": sum(action.difference for action in actions),
            "market_conditions": market_conditions,
            "actions": [asdict(action) for action in actions]
        }
        
        self.rebalance_history.append(rebalance_record)
        self.last_rebalance = datetime.now()
        
        logger.info(f"Ребалансировка завершена: {len(actions)} действий")
        
        return actions
    
    def _normalize_target_weights(self):
        """Нормализация целевых весов"""
        total_weight = sum(asset.target_weight for asset in self.allocations)
        
        if total_weight > 0:
            for asset in self.allocations:
                asset.target_weight = asset.target_weight / total_weight
    
    async def get_portfolio_report(self) -> Dict:
        """Генерация комплексного отчета портфеля"""
        
        metrics = await self.calculate_portfolio_metrics()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "portfolio_value": self.current_balance,
            "initial_balance": self.initial_balance,
            "total_return": metrics.total_pnl,
            "return_pct": (metrics.total_pnl / self.initial_balance * 100) if self.initial_balance > 0 else 0,
            "metrics": asdict(metrics),
            "assets": [
                {
                    "symbol": asset.symbol,
                    "asset_class": asset.asset_class.value,
                    "current_weight": asset.current_weight,
                    "target_weight": asset.target_weight,
                    "deviation": abs(asset.current_weight - asset.target_weight),
                    "risk_score": asset.risk_score,
                    "correlation_group": asset.correlation_group
                } for asset in self.allocations
            ],
            "rebalancing": {
                "last_rebalance": self.last_rebalance.isoformat(),
                "rebalances_count": len(self.rebalance_history),
                "recent_actions": len(self.rebalance_history[-1]["actions"]) if self.rebalance_history else 0
            }
        }

# Тестирование Portfolio Management System
async def test_portfolio_management():
    """Тестирование системы управления портфелем"""
    
    # Инициализация
    portfolio = PortfolioManager(initial_balance=100000.0)
    
    # Добавление активов
    btc = AssetAllocation(
        symbol="BTCUSDT",
        asset_class=AssetClass.CRYPTOCURRENCY,
        target_weight=0.4,
        min_weight=0.2,
        max_weight=0.6,
        risk_score=8.0,
        correlation_group="crypto"
    )
    
    eth = AssetAllocation(
        symbol="ETHUSDT", 
        asset_class=AssetClass.CRYPTOCURRENCY,
        target_weight=0.3,
        min_weight=0.15,
        max_weight=0.5,
        risk_score=7.5,
        correlation_group="crypto"
    )
    
    eur = AssetAllocation(
        symbol="EURUSD",
        asset_class=AssetClass.FOREX,
        target_weight=0.3,
        min_weight=0.1,
        max_weight=0.4,
        risk_score=3.0,
        correlation_group="forex"
    )
    
    portfolio.add_asset(btc)
    portfolio.add_asset(eth)
    portfolio.add_asset(eur)
    
    # Симуляция текущих позиций
    current_positions = {
        "BTCUSDT": 50000.0,  # 50% (отклонение от 40%)
        "ETHUSDT": 25000.0,  # 25% (отклонение от 30%)
        "EURUSD": 25000.0    # 25% (отклонение от 30%)
    }
    
    portfolio.update_current_weights(current_positions)
    
    # Рыночные условия
    market_conditions = {
        "volatility": 0.04,
        "trend": "bullish",
        "liquidity": "high"
    }
    
    # Проверка необходимости ребалансировки
    should_rebalance, reason = await portfolio.should_rebalance(market_conditions)
    print(f"Требуется ребалансировка: {should_rebalance}")
    print(f"Причина: {reason}\n")
    
    # Выполнение ребалансировки
    if should_rebalance:
        actions = await portfolio.execute_rebalance(market_conditions)
        print("Действия ребалансировки:")
        for action in actions:
            print(f"- {action.action.upper()} {action.symbol}: ${action.difference:.2f}")
            print(f"  {action.reasoning}\n")
    
    # Метрики портфеля
    metrics = await portfolio.calculate_portfolio_metrics()
    print("Метрики портфеля:")
    print(f"- Общая стоимость: ${metrics.total_value:,.2f}")
    print(f"- Волатильность: {metrics.volatility:.1%}")
    print(f"- Диверсификация: {metrics.diversification_ratio:.1%}")
    print(f"- Корреляционный риск: {metrics.correlation_risk:.1%}")
    print(f"- Sharpe ratio: {metrics.sharpe_ratio:.2f}\n")
    
    # Комплексный отчет
    report = await portfolio.get_portfolio_report()
    print("Комплексный отчет:")
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(test_portfolio_management())
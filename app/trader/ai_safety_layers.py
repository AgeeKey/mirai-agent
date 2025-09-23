"""
Mirai Agent - AI Safety Layers
Дополнительные слои безопасности с использованием LLM для критического анализа
"""
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import sys
import os

# Опциональный импорт OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SafetyLevel(Enum):
    """Уровни безопасности"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SafetyAction(Enum):
    """Действия системы безопасности"""
    APPROVE = "approve"
    REVIEW = "review"
    REJECT = "reject"
    EMERGENCY_STOP = "emergency_stop"

@dataclass
class SafetyCheck:
    """Результат проверки безопасности"""
    check_type: str
    safety_level: SafetyLevel
    action: SafetyAction
    confidence: float
    reasoning: str
    recommendations: List[str]
    timestamp: datetime

@dataclass
class TradingContext:
    """Контекст для анализа торговой операции"""
    signal: Dict
    market_conditions: Dict
    account_status: Dict
    position_size_usd: float
    risk_metrics: Dict
    recent_performance: Dict

class MarketAnalysisAI:
    """AI анализатор рыночных условий"""
    
    def __init__(self):
        # Проверяем доступность OpenAI
        self.openai_available = OPENAI_AVAILABLE
        if not self.openai_available:
            logger.warning("OpenAI недоступен, используется эмуляция")
    
    async def analyze_market_regime(self, market_data: Dict) -> Dict:
        """Анализ рыночного режима с помощью AI"""
        
        if self.openai_available:
            # Реальный анализ через OpenAI
            return await self._openai_market_analysis(market_data)
        else:
            # Эмуляция анализа
            return await self._simulate_market_analysis(market_data)
    
    async def _openai_market_analysis(self, market_data: Dict) -> Dict:
        """Анализ через OpenAI API"""
        try:
            prompt = f"""
            Проанализируй текущие рыночные условия и дай рекомендации по торговле:
            
            Данные рынка: {json.dumps(market_data, indent=2)}
            
            Оцени:
            1. Текущий режим рынка (тренд/боковик/волатильность)
            2. Уровень риска (1-10)
            3. Рекомендации по позиционированию
            4. Предупреждения о возможных рисках
            
            Ответь в формате JSON с полями: regime, risk_level, recommendations, warnings
            """
            
            # В реальной реализации здесь будет вызов OpenAI API
            # response = await openai.ChatCompletion.acreate(...)
            
            # Пока возвращаем симуляцию
            return await self._simulate_market_analysis(market_data)
            
        except Exception as e:
            logger.error(f"Ошибка анализа OpenAI: {e}")
            return await self._simulate_market_analysis(market_data)
    
    async def _simulate_market_analysis(self, market_data: Dict) -> Dict:
        """Симуляция AI анализа"""
        
        # Простой анализ на основе данных
        volatility = market_data.get('volatility', 0.02)
        trend_strength = market_data.get('trend_strength', 0.5)
        volume_ratio = market_data.get('volume_ratio', 1.0)
        
        # Определение режима
        if volatility > 0.05:
            regime = "high_volatility"
            risk_level = 8
        elif trend_strength > 0.7:
            regime = "strong_trend"
            risk_level = 4
        elif trend_strength < 0.3:
            regime = "sideways"
            risk_level = 6
        else:
            regime = "moderate_trend"
            risk_level = 5
        
        recommendations = []
        warnings = []
        
        if risk_level >= 7:
            recommendations.append("Уменьшить размер позиций")
            recommendations.append("Увеличить частоту мониторинга")
            warnings.append("Высокий уровень рыночного риска")
        
        if volume_ratio < 0.5:
            warnings.append("Низкая ликвидность")
            recommendations.append("Быть осторожным с крупными ордерами")
        
        return {
            "regime": regime,
            "risk_level": risk_level,
            "recommendations": recommendations,
            "warnings": warnings,
            "confidence": 0.75,
            "analysis_timestamp": datetime.now().isoformat()
        }

class LLMSafetyValidator:
    """LLM валидатор для критических торговых решений"""
    
    def __init__(self):
        self.market_analyzer = MarketAnalysisAI()
        self.validation_history = []
    
    async def validate_trading_decision(self, context: TradingContext) -> SafetyCheck:
        """Валидация торгового решения через LLM"""
        
        # Определение уровня критичности
        safety_level = self._assess_safety_level(context)
        
        # Базовые проверки
        basic_checks = await self._basic_safety_checks(context)
        
        # Продвинутый анализ для критичных случаев
        if safety_level in [SafetyLevel.HIGH, SafetyLevel.CRITICAL]:
            advanced_analysis = await self._advanced_llm_analysis(context)
        else:
            advanced_analysis = {"passed": True, "reasoning": "Базовые проверки пройдены"}
        
        # Объединение результатов
        return await self._combine_safety_results(context, safety_level, basic_checks, advanced_analysis)
    
    def _assess_safety_level(self, context: TradingContext) -> SafetyLevel:
        """Оценка уровня критичности операции"""
        
        risk_factors = 0
        
        # Размер позиции
        if context.position_size_usd > 1000:
            risk_factors += 1
        if context.position_size_usd > 5000:
            risk_factors += 2
        
        # Текущие убытки
        daily_pnl = context.account_status.get('daily_pnl', 0)
        if daily_pnl < -500:
            risk_factors += 1
        if daily_pnl < -1000:
            risk_factors += 2
        
        # Открытые позиции
        open_positions = context.risk_metrics.get('open_positions_count', 0)
        if open_positions >= 2:
            risk_factors += 1
        if open_positions >= 3:
            risk_factors += 1
        
        # Уверенность стратегии
        confidence = context.signal.get('confidence', 100)
        if confidence < 70:
            risk_factors += 1
        if confidence < 60:
            risk_factors += 1
        
        # Маппинг в уровни безопасности
        if risk_factors >= 5:
            return SafetyLevel.CRITICAL
        elif risk_factors >= 3:
            return SafetyLevel.HIGH
        elif risk_factors >= 1:
            return SafetyLevel.MEDIUM
        else:
            return SafetyLevel.LOW
    
    async def _basic_safety_checks(self, context: TradingContext) -> Dict:
        """Базовые проверки безопасности"""
        
        checks = {
            "position_size_reasonable": True,
            "stop_loss_present": True,
            "account_balance_sufficient": True,
            "no_correlation_conflict": True,
            "passed": True,
            "issues": []
        }
        
        # Проверка размера позиции
        max_position = context.account_status.get('balance', 10000) * 0.1  # 10% от баланса
        if context.position_size_usd > max_position:
            checks["position_size_reasonable"] = False
            checks["issues"].append(f"Позиция {context.position_size_usd} превышает лимит {max_position}")
        
        # Проверка стоп-лосса
        if not context.signal.get('stop_loss'):
            checks["stop_loss_present"] = False
            checks["issues"].append("Отсутствует стоп-лосс")
        
        # Проверка баланса
        required_margin = context.position_size_usd * 0.1  # 10% маржи
        available_balance = context.account_status.get('balance', 0)
        if required_margin > available_balance:
            checks["account_balance_sufficient"] = False
            checks["issues"].append("Недостаточно средств для маржи")
        
        # Общий результат
        checks["passed"] = len(checks["issues"]) == 0
        
        return checks
    
    async def _advanced_llm_analysis(self, context: TradingContext) -> Dict:
        """Продвинутый анализ через LLM"""
        
        # Анализ рыночных условий
        market_analysis = await self.market_analyzer.analyze_market_regime(
            context.market_conditions
        )
        
        # Формирование контекста для LLM
        analysis_context = {
            "signal": context.signal,
            "position_size_usd": context.position_size_usd,
            "account_balance": context.account_status.get('balance', 0),
            "daily_pnl": context.account_status.get('daily_pnl', 0),
            "open_positions": context.risk_metrics.get('open_positions_count', 0),
            "market_analysis": market_analysis,
            "recent_performance": context.recent_performance
        }
        
        # Симуляция LLM анализа (в реальности - вызов OpenAI)
        llm_response = await self._simulate_llm_analysis(analysis_context)
        
        return llm_response
    
    async def _simulate_llm_analysis(self, analysis_context: Dict) -> Dict:
        """Симуляция анализа LLM"""
        
        # Анализ факторов риска
        risk_score = 0
        concerns = []
        recommendations = []
        
        # Анализ размера позиции
        position_ratio = analysis_context['position_size_usd'] / analysis_context['account_balance']
        if position_ratio > 0.05:  # 5% от баланса
            risk_score += 2
            concerns.append(f"Крупная позиция: {position_ratio*100:.1f}% от баланса")
        
        # Анализ текущего P&L
        daily_pnl = analysis_context['daily_pnl']
        if daily_pnl < -200:
            risk_score += 2
            concerns.append(f"Дневные убытки: ${daily_pnl}")
            recommendations.append("Рассмотреть прекращение торговли на сегодня")
        
        # Анализ рыночных условий
        market_risk = analysis_context['market_analysis']['risk_level']
        if market_risk >= 7:
            risk_score += 1
            concerns.append("Высокий рыночный риск")
            recommendations.append("Уменьшить размер позиции на 50%")
        
        # Анализ открытых позиций
        open_positions = analysis_context['open_positions']
        if open_positions >= 2:
            risk_score += 1
            concerns.append(f"Множественные позиции: {open_positions}")
        
        # Принятие решения
        if risk_score >= 5:
            decision = "reject"
            reasoning = "Слишком высокий совокупный риск"
        elif risk_score >= 3:
            decision = "review"
            reasoning = "Требуется дополнительная проверка"
        else:
            decision = "approve"
            reasoning = "Риски в пределах нормы"
        
        return {
            "decision": decision,
            "risk_score": risk_score,
            "reasoning": reasoning,
            "concerns": concerns,
            "recommendations": recommendations,
            "confidence": 0.85,
            "passed": decision == "approve"
        }
    
    async def _combine_safety_results(self, context: TradingContext, safety_level: SafetyLevel, 
                                    basic_checks: Dict, advanced_analysis: Dict) -> SafetyCheck:
        """Объединение результатов всех проверок"""
        
        # Определение итогового действия
        if not basic_checks["passed"]:
            action = SafetyAction.REJECT
            reasoning = f"Базовые проверки не пройдены: {'; '.join(basic_checks['issues'])}"
        elif not advanced_analysis["passed"]:
            if safety_level == SafetyLevel.CRITICAL:
                action = SafetyAction.EMERGENCY_STOP
            else:
                action = SafetyAction.REJECT
            reasoning = advanced_analysis["reasoning"]
        elif safety_level in [SafetyLevel.HIGH, SafetyLevel.CRITICAL]:
            action = SafetyAction.REVIEW
            reasoning = "Высокий уровень риска требует дополнительного контроля"
        else:
            action = SafetyAction.APPROVE
            reasoning = "Все проверки безопасности пройдены"
        
        # Сбор рекомендаций
        recommendations = []
        recommendations.extend(basic_checks.get("issues", []))
        recommendations.extend(advanced_analysis.get("recommendations", []))
        
        # Расчет уверенности
        confidence = min(basic_checks.get("confidence", 1.0), advanced_analysis.get("confidence", 1.0))
        
        safety_check = SafetyCheck(
            check_type="comprehensive_trading_validation",
            safety_level=safety_level,
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            recommendations=recommendations,
            timestamp=datetime.now()
        )
        
        # Сохранение в историю
        self.validation_history.append(safety_check)
        
        logger.info(f"Safety check: {action.value} - {reasoning}")
        
        return safety_check

class AISafetySystem:
    """Основная система AI безопасности"""
    
    def __init__(self):
        self.llm_validator = LLMSafetyValidator()
        self.enabled = True
        self.intervention_count = 0
    
    async def validate_trade_execution(self, signal: Dict, market_data: Dict, 
                                     account_status: Dict, risk_metrics: Dict) -> Tuple[bool, SafetyCheck]:
        """Валидация исполнения торговой операции"""
        
        if not self.enabled:
            return True, None
        
        # Подготовка контекста
        position_size_usd = signal.get('position_size', 0) * signal.get('entry_price', 0)
        
        context = TradingContext(
            signal=signal,
            market_conditions=market_data,
            account_status=account_status,
            position_size_usd=position_size_usd,
            risk_metrics=risk_metrics,
            recent_performance=await self._get_recent_performance(account_status)
        )
        
        # Валидация через LLM
        safety_check = await self.llm_validator.validate_trading_decision(context)
        
        # Обработка результата
        if safety_check.action == SafetyAction.EMERGENCY_STOP:
            self.intervention_count += 1
            logger.critical(f"AI Safety: EMERGENCY STOP - {safety_check.reasoning}")
            return False, safety_check
        elif safety_check.action == SafetyAction.REJECT:
            self.intervention_count += 1
            logger.warning(f"AI Safety: Trade REJECTED - {safety_check.reasoning}")
            return False, safety_check
        elif safety_check.action == SafetyAction.REVIEW:
            logger.info(f"AI Safety: Trade requires REVIEW - {safety_check.reasoning}")
            # В реальной системе здесь может быть человеческое вмешательство
            return True, safety_check  # Пока разрешаем с предупреждением
        else:
            logger.info(f"AI Safety: Trade APPROVED - {safety_check.reasoning}")
            return True, safety_check
    
    async def _get_recent_performance(self, account_status: Dict) -> Dict:
        """Получение данных о недавней производительности"""
        return {
            "last_24h_pnl": account_status.get('daily_pnl', 0),
            "win_rate_last_10": 0.6,  # В реальности из базы данных
            "avg_trade_pnl": 50,      # В реальности из базы данных
            "max_drawdown_24h": account_status.get('daily_pnl', 0) if account_status.get('daily_pnl', 0) < 0 else 0
        }
    
    def get_safety_report(self) -> Dict:
        """Отчет по работе системы безопасности"""
        
        recent_checks = self.llm_validator.validation_history[-10:]  # Последние 10 проверок
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system_enabled": self.enabled,
            "total_interventions": self.intervention_count,
            "recent_checks_count": len(recent_checks),
            "recent_actions": [check.action.value for check in recent_checks],
            "safety_levels": [check.safety_level.value for check in recent_checks],
            "avg_confidence": sum(check.confidence for check in recent_checks) / len(recent_checks) if recent_checks else 0
        }

# Пример использования и тестирования
async def test_ai_safety_system():
    """Тестирование системы AI безопасности"""
    
    safety_system = AISafetySystem()
    
    # Тестовый сигнал
    test_signal = {
        "strategy_name": "test_strategy",
        "symbol": "BTCUSDT",
        "signal_type": "buy",
        "confidence": 75.0,
        "entry_price": 50000.0,
        "stop_loss": 49000.0,
        "take_profit": 52000.0,
        "position_size": 0.02  # 0.02 BTC
    }
    
    # Тестовые рыночные данные
    test_market_data = {
        "volatility": 0.03,
        "trend_strength": 0.6,
        "volume_ratio": 1.2,
        "price": 50000.0
    }
    
    # Статус аккаунта
    test_account = {
        "balance": 10000.0,
        "daily_pnl": -100.0
    }
    
    # Метрики риска
    test_risk_metrics = {
        "open_positions_count": 1,
        "total_exposure_pct": 5.0,
        "current_drawdown_pct": 1.0
    }
    
    # Валидация
    approved, safety_check = await safety_system.validate_trade_execution(
        test_signal, test_market_data, test_account, test_risk_metrics
    )
    
    print(f"Торговля одобрена: {approved}")
    if safety_check:
        print(f"Уровень безопасности: {safety_check.safety_level.value}")
        print(f"Действие: {safety_check.action.value}")
        print(f"Обоснование: {safety_check.reasoning}")
        print(f"Рекомендации: {safety_check.recommendations}")
    
    # Отчет системы
    report = safety_system.get_safety_report()
    print(f"\nОтчет системы безопасности: {json.dumps(report, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_ai_safety_system())
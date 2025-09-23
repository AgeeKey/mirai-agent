"""
Система безопасности и ограничений для автономного AI-агента
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib

logger = logging.getLogger('MiraiAgent.Safety')

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class OperationType(Enum):
    MARKET_ANALYSIS = "market_analysis"
    PORTFOLIO_CHECK = "portfolio_check"
    SMALL_TRADE = "small_trade"
    LARGE_TRADE = "large_trade"
    REAL_MONEY = "real_money"
    POSITION_CLOSE = "position_close"
    SYSTEM_CONFIG = "system_config"

@dataclass
class SafetyRule:
    """Правило безопасности"""
    name: str
    description: str
    max_value: float
    current_value: float = 0.0
    enabled: bool = True
    violation_count: int = 0
    last_violation: Optional[str] = None

class AgentSafetySystem:
    """Система безопасности агента с песочницей и ограничениями"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.daily_limits = {}
        self.session_stats = {
            "start_time": datetime.now().isoformat(),
            "trades_executed": 0,
            "total_volume": 0.0,
            "risk_violations": 0,
            "manual_interventions": 0
        }
        
        # Инициализация правил безопасности
        self.safety_rules = self._init_safety_rules()
        self.pending_confirmations = {}
        self.sandboxed = True  # По умолчанию в sandbox режиме
        
        logger.info("Система безопасности инициализирована")
    
    def _init_safety_rules(self) -> Dict[str, SafetyRule]:
        """Инициализация правил безопасности"""
        return {
            "max_position_size": SafetyRule(
                name="Максимальный размер позиции",
                description="Максимальный размер одной позиции в USD",
                max_value=self.config.get("max_position_size", 1000.0)
            ),
            "max_daily_trades": SafetyRule(
                name="Максимум сделок в день",
                description="Максимальное количество сделок за день",
                max_value=self.config.get("max_daily_trades", 10)
            ),
            "max_daily_volume": SafetyRule(
                name="Максимальный дневной объем",
                description="Максимальный торговый объем за день в USD",
                max_value=self.config.get("max_daily_volume", 5000.0)
            ),
            "max_position_risk": SafetyRule(
                name="Максимальный риск позиции",
                description="Максимальный риск позиции в % от портфеля",
                max_value=self.config.get("max_position_risk", 5.0)
            ),
            "max_portfolio_risk": SafetyRule(
                name="Максимальный риск портфеля",
                description="Максимальный общий риск портфеля в %",
                max_value=self.config.get("max_portfolio_risk", 20.0)
            ),
            "min_confidence": SafetyRule(
                name="Минимальная уверенность",
                description="Минимальная уверенность для выполнения сделки",
                max_value=1.0 - self.config.get("min_confidence", 0.7)  # Инвертируем для проверки
            )
        }
    
    def check_operation_safety(self, 
                             operation_type: OperationType, 
                             operation_data: Dict[str, Any]) -> Tuple[bool, List[str], RiskLevel]:
        """Проверка безопасности операции"""
        violations = []
        risk_level = RiskLevel.LOW
        
        try:
            # Проверка по типу операции
            if operation_type in [OperationType.MARKET_ANALYSIS, OperationType.PORTFOLIO_CHECK]:
                # Аналитические операции безопасны
                return True, [], RiskLevel.LOW
            
            elif operation_type in [OperationType.SMALL_TRADE, OperationType.LARGE_TRADE]:
                violations, risk_level = self._check_trading_safety(operation_data)
            
            elif operation_type == OperationType.REAL_MONEY:
                violations, risk_level = self._check_real_money_safety(operation_data)
            
            elif operation_type == OperationType.SYSTEM_CONFIG:
                violations, risk_level = self._check_system_config_safety(operation_data)
            
            # Общие проверки
            general_violations = self._check_general_limits()
            violations.extend(general_violations)
            
            # Определяем итоговый уровень риска
            if violations:
                if any("критический" in v.lower() or "critical" in v.lower() for v in violations):
                    risk_level = RiskLevel.CRITICAL
                elif any("высокий" in v.lower() or "high" in v.lower() for v in violations):
                    risk_level = RiskLevel.HIGH
                elif risk_level == RiskLevel.LOW:
                    risk_level = RiskLevel.MEDIUM
            
            # Логируем проверку
            logger.info(f"Проверка безопасности {operation_type.value}: "
                       f"{'ПРОЙДЕНА' if not violations else 'НАРУШЕНИЯ'}, риск: {risk_level.value}")
            
            if violations:
                logger.warning(f"Нарушения безопасности: {violations}")
                self.session_stats["risk_violations"] += 1
            
            return len(violations) == 0, violations, risk_level
            
        except Exception as e:
            logger.error(f"Ошибка проверки безопасности: {e}")
            return False, [f"Ошибка системы безопасности: {e}"], RiskLevel.CRITICAL
    
    def _check_trading_safety(self, trade_data: Dict[str, Any]) -> Tuple[List[str], RiskLevel]:
        """Проверка безопасности торговых операций"""
        violations = []
        risk_level = RiskLevel.LOW
        
        # Размер позиции
        position_size = trade_data.get("quantity", 0) * trade_data.get("price", 0)
        if position_size > self.safety_rules["max_position_size"].max_value:
            violations.append(f"Размер позиции ${position_size:.2f} превышает лимит "
                            f"${self.safety_rules['max_position_size'].max_value:.2f}")
            risk_level = RiskLevel.HIGH
        
        # Уверенность в сигнале
        confidence = trade_data.get("confidence", 0)
        min_confidence = 1.0 - self.safety_rules["min_confidence"].max_value
        if confidence < min_confidence:
            violations.append(f"Уверенность {confidence:.1%} ниже минимальной {min_confidence:.1%}")
            risk_level = max(risk_level, RiskLevel.MEDIUM)
        
        # Проверяем дневные лимиты
        today = datetime.now().date().isoformat()
        daily_trades = self.daily_limits.get(f"trades_{today}", 0)
        daily_volume = self.daily_limits.get(f"volume_{today}", 0.0)
        
        if daily_trades >= self.safety_rules["max_daily_trades"].max_value:
            violations.append(f"Превышен дневной лимит сделок: {daily_trades}")
            risk_level = RiskLevel.HIGH
        
        if daily_volume + position_size > self.safety_rules["max_daily_volume"].max_value:
            violations.append(f"Превышен дневной лимит объема: "
                            f"${daily_volume + position_size:.2f}")
            risk_level = RiskLevel.HIGH
        
        # Проверка режима dry-run
        if not trade_data.get("dry_run", True):
            violations.append("КРИТИЧЕСКИЙ: Попытка реальной торговли без разрешения")
            risk_level = RiskLevel.CRITICAL
        
        return violations, risk_level
    
    def _check_real_money_safety(self, operation_data: Dict[str, Any]) -> Tuple[List[str], RiskLevel]:
        """Проверка операций с реальными деньгами"""
        violations = []
        
        # В демо-версии реальная торговля запрещена
        if not self.config.get("real_trading_enabled", False):
            violations.append("КРИТИЧЕСКИЙ: Реальная торговля отключена в конфигурации")
            return violations, RiskLevel.CRITICAL
        
        # Дополнительные проверки для реальных денег
        if not operation_data.get("user_confirmation", False):
            violations.append("КРИТИЧЕСКИЙ: Отсутствует подтверждение пользователя")
            return violations, RiskLevel.CRITICAL
        
        return violations, RiskLevel.HIGH  # Реальные деньги всегда высокий риск
    
    def _check_system_config_safety(self, config_data: Dict[str, Any]) -> Tuple[List[str], RiskLevel]:
        """Проверка изменений системных настроек"""
        violations = []
        risk_level = RiskLevel.MEDIUM
        
        # Критические параметры, которые нельзя менять
        protected_keys = [
            "openai_api_key",
            "binance_api_secret", 
            "database_url",
            "security_enabled"
        ]
        
        for key in config_data.keys():
            if key in protected_keys:
                violations.append(f"КРИТИЧЕСКИЙ: Попытка изменения защищенного параметра {key}")
                risk_level = RiskLevel.CRITICAL
        
        return violations, risk_level
    
    def _check_general_limits(self) -> List[str]:
        """Проверка общих ограничений"""
        violations = []
        
        # Проверка лимитов времени работы
        if hasattr(self, 'session_start_time'):
            session_duration = (datetime.now() - self.session_start_time).total_seconds() / 3600
            max_session_hours = self.config.get("max_session_hours", 24)
            
            if session_duration > max_session_hours:
                violations.append(f"Превышено время сессии: {session_duration:.1f}ч > {max_session_hours}ч")
        
        # Проверка общего количества нарушений
        if self.session_stats["risk_violations"] > 10:
            violations.append("Слишком много нарушений безопасности за сессию")
        
        return violations
    
    def request_confirmation(self, 
                           operation: str, 
                           details: Dict[str, Any], 
                           risk_level: RiskLevel) -> str:
        """Запрос подтверждения для опасных операций"""
        confirmation_id = hashlib.md5(
            f"{operation}_{time.time()}".encode()
        ).hexdigest()[:8]
        
        self.pending_confirmations[confirmation_id] = {
            "operation": operation,
            "details": details,
            "risk_level": risk_level.value,
            "requested_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(minutes=5)).isoformat()
        }
        
        logger.warning(f"ТРЕБУЕТСЯ ПОДТВЕРЖДЕНИЕ [{confirmation_id}]: {operation}")
        logger.warning(f"Детали: {details}")
        logger.warning(f"Уровень риска: {risk_level.value}")
        logger.warning("Для подтверждения выполните:")
        logger.warning(f"agent.approve_operation('{confirmation_id}')")
        
        return confirmation_id
    
    def approve_operation(self, confirmation_id: str, user_code: str = None) -> bool:
        """Подтверждение операции пользователем"""
        if confirmation_id not in self.pending_confirmations:
            logger.error(f"Неизвестный ID подтверждения: {confirmation_id}")
            return False
        
        confirmation = self.pending_confirmations[confirmation_id]
        
        # Проверка истечения времени
        expires_at = datetime.fromisoformat(confirmation["expires_at"])
        if datetime.now() > expires_at:
            logger.error("Время подтверждения истекло")
            del self.pending_confirmations[confirmation_id]
            return False
        
        # В продакшен версии здесь была бы проверка кода пользователя
        logger.info(f"Операция подтверждена: {confirmation['operation']}")
        del self.pending_confirmations[confirmation_id]
        self.session_stats["manual_interventions"] += 1
        
        return True
    
    def update_daily_limits(self, trade_data: Dict[str, Any]):
        """Обновление дневных лимитов после сделки"""
        today = datetime.now().date().isoformat()
        
        # Увеличиваем счетчики
        self.daily_limits[f"trades_{today}"] = self.daily_limits.get(f"trades_{today}", 0) + 1
        
        position_size = trade_data.get("quantity", 0) * trade_data.get("price", 0)
        self.daily_limits[f"volume_{today}"] = self.daily_limits.get(f"volume_{today}", 0.0) + position_size
        
        self.session_stats["trades_executed"] += 1
        self.session_stats["total_volume"] += position_size
    
    def get_safety_status(self) -> Dict[str, Any]:
        """Получение статуса системы безопасности"""
        today = datetime.now().date().isoformat()
        
        return {
            "sandboxed": self.sandboxed,
            "session_stats": self.session_stats,
            "daily_limits": {
                "trades_today": self.daily_limits.get(f"trades_{today}", 0),
                "volume_today": self.daily_limits.get(f"volume_{today}", 0.0),
                "max_trades": self.safety_rules["max_daily_trades"].max_value,
                "max_volume": self.safety_rules["max_daily_volume"].max_value
            },
            "safety_rules_status": {
                name: {
                    "enabled": rule.enabled,
                    "current": rule.current_value,
                    "max": rule.max_value,
                    "violations": rule.violation_count
                }
                for name, rule in self.safety_rules.items()
            },
            "pending_confirmations": len(self.pending_confirmations),
            "timestamp": datetime.now().isoformat()
        }
    
    def enable_sandbox_mode(self):
        """Включение режима песочницы"""
        self.sandboxed = True
        logger.info("🏖️  Режим песочницы ВКЛЮЧЕН - все операции безопасны")
    
    def disable_sandbox_mode(self, admin_key: str = None):
        """Отключение режима песочницы (только для админа)"""
        # В продакшен версии здесь должна быть проверка админ-ключа
        expected_key = self.config.get("admin_key", "")
        
        if not expected_key or admin_key != expected_key:
            logger.error("❌ Неверный админ-ключ для отключения песочницы")
            return False
        
        self.sandboxed = False
        logger.warning("⚠️  Режим песочницы ОТКЛЮЧЕН - возможны реальные операции!")
        return True
    
    def emergency_stop(self, reason: str = "Emergency stop"):
        """Экстренная остановка всех операций"""
        self.sandboxed = True
        
        # Очищаем все ожидающие подтверждения
        self.pending_confirmations.clear()
        
        # Блокируем все правила
        for rule in self.safety_rules.values():
            rule.enabled = False
        
        logger.critical(f"🚨 ЭКСТРЕННАЯ ОСТАНОВКА: {reason}")
        logger.critical("Все операции заблокированы")
        
        return {
            "status": "emergency_stopped",
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
    
    def reset_daily_limits(self):
        """Сброс дневных лимитов (выполняется автоматически в полночь)"""
        today = datetime.now().date().isoformat()
        yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
        
        # Удаляем вчерашние лимиты
        keys_to_remove = [k for k in self.daily_limits.keys() if yesterday in k]
        for key in keys_to_remove:
            del self.daily_limits[key]
        
        logger.info("Дневные лимиты сброшены")

class AgentSandbox:
    """Песочница для безопасного выполнения операций агента"""
    
    def __init__(self, safety_system: AgentSafetySystem):
        self.safety_system = safety_system
        self.allowed_operations = [
            "market_analysis",
            "portfolio_check", 
            "risk_assessment",
            "news_analysis",
            "technical_analysis",
            "generate_signals"
        ]
        self.blocked_operations = [
            "real_trade",
            "withdraw_funds",
            "change_api_keys",
            "modify_safety_rules"
        ]
    
    def execute_in_sandbox(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение операции в песочнице"""
        if not self.safety_system.sandboxed:
            return {
                "error": "Операция не в песочнице - требуется дополнительная проверка",
                "requires_confirmation": True
            }
        
        if operation in self.blocked_operations:
            return {
                "error": f"Операция '{operation}' заблокирована в песочнице",
                "blocked": True
            }
        
        if operation not in self.allowed_operations:
            return {
                "error": f"Операция '{operation}' не разрешена в песочнице",
                "allowed_operations": self.allowed_operations
            }
        
        # Выполняем операцию безопасно
        try:
            result = self._execute_safe_operation(operation, params)
            result["sandbox_mode"] = True
            result["timestamp"] = datetime.now().isoformat()
            return result
        except Exception as e:
            logger.error(f"Ошибка в песочнице при выполнении {operation}: {e}")
            return {
                "error": f"Ошибка выполнения: {e}",
                "sandbox_mode": True,
                "timestamp": datetime.now().isoformat()
            }
    
    def _execute_safe_operation(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Безопасное выполнение операции"""
        # Здесь можно добавить специфичную логику для каждой операции
        
        if operation == "market_analysis":
            return {
                "operation": operation,
                "status": "completed",
                "result": "Анализ рынка выполнен в безопасном режиме",
                "data_source": "sandbox_simulation"
            }
        
        elif operation == "portfolio_check":
            return {
                "operation": operation,
                "status": "completed", 
                "portfolio": {
                    "total_value": 10000.0,
                    "positions": [],
                    "cash": 10000.0
                },
                "note": "Демо-портфель в песочнице"
            }
        
        else:
            return {
                "operation": operation,
                "status": "completed",
                "result": f"Операция {operation} выполнена в песочнице",
                "parameters": params
            }

# Функции для быстрого создания системы безопасности
def create_safety_system(config: Dict[str, Any] = None) -> AgentSafetySystem:
    """Создание системы безопасности с настройками по умолчанию"""
    default_config = {
        "max_position_size": 1000.0,
        "max_daily_trades": 10,
        "max_daily_volume": 5000.0,
        "max_position_risk": 5.0,
        "max_portfolio_risk": 20.0,
        "min_confidence": 0.7,
        "real_trading_enabled": False,
        "max_session_hours": 24,
        "admin_key": "mirai_admin_2024"
    }
    
    if config:
        default_config.update(config)
    
    return AgentSafetySystem(default_config)

def create_sandbox(safety_system: AgentSafetySystem = None) -> AgentSandbox:
    """Создание песочницы"""
    if safety_system is None:
        safety_system = create_safety_system()
    
    return AgentSandbox(safety_system)
"""
Mirai Agent - AI Safety System Test
Тестирование системы AI безопасности с различными сценариями
"""
import asyncio
import json
from ai_safety_layers import AISafetySystem

async def test_risky_scenarios():
    """Тестирование рискованных сценариев"""
    
    safety_system = AISafetySystem()
    
    print("=== Тестирование AI Safety System ===\n")
    
    # Сценарий 1: Нормальная торговля
    print("1. Нормальная торговля (малый риск)")
    normal_signal = {
        "strategy_name": "conservative_strategy",
        "symbol": "BTCUSDT",
        "signal_type": "buy",
        "confidence": 80.0,
        "entry_price": 50000.0,
        "stop_loss": 49500.0,
        "take_profit": 51000.0,
        "position_size": 0.01  # Малая позиция
    }
    
    normal_market = {
        "volatility": 0.02,
        "trend_strength": 0.6,
        "volume_ratio": 1.0
    }
    
    normal_account = {
        "balance": 10000.0,
        "daily_pnl": 50.0  # Небольшая прибыль
    }
    
    normal_risk = {
        "open_positions_count": 0,
        "total_exposure_pct": 2.0
    }
    
    approved, check = await safety_system.validate_trade_execution(
        normal_signal, normal_market, normal_account, normal_risk
    )
    print(f"Результат: {'✅ ОДОБРЕНО' if approved else '❌ ОТКЛОНЕНО'}")
    print(f"Уровень риска: {check.safety_level.value}")
    print(f"Обоснование: {check.reasoning}\n")
    
    # Сценарий 2: Крупная позиция
    print("2. Крупная позиция (высокий риск)")
    large_signal = {
        "strategy_name": "aggressive_strategy",
        "symbol": "BTCUSDT", 
        "signal_type": "buy",
        "confidence": 70.0,
        "entry_price": 50000.0,
        "stop_loss": 48000.0,
        "take_profit": 55000.0,
        "position_size": 0.2  # Крупная позиция
    }
    
    approved, check = await safety_system.validate_trade_execution(
        large_signal, normal_market, normal_account, normal_risk
    )
    print(f"Результат: {'✅ ОДОБРЕНО' if approved else '❌ ОТКЛОНЕНО'}")
    print(f"Уровень риска: {check.safety_level.value}")
    print(f"Обоснование: {check.reasoning}")
    if check.recommendations:
        print(f"Рекомендации: {'; '.join(check.recommendations)}\n")
    else:
        print()
    
    # Сценарий 3: Убыточный день
    print("3. Торговля после крупных убытков")
    loss_account = {
        "balance": 10000.0,
        "daily_pnl": -800.0  # Крупные убытки
    }
    
    loss_risk = {
        "open_positions_count": 2,  # Уже есть позиции
        "total_exposure_pct": 15.0
    }
    
    approved, check = await safety_system.validate_trade_execution(
        normal_signal, normal_market, loss_account, loss_risk
    )
    print(f"Результат: {'✅ ОДОБРЕНО' if approved else '❌ ОТКЛОНЕНО'}")
    print(f"Уровень риска: {check.safety_level.value}")
    print(f"Обоснование: {check.reasoning}")
    if check.recommendations:
        print(f"Рекомендации: {'; '.join(check.recommendations)}\n")
    else:
        print()
    
    # Сценарий 4: Высокая волатильность
    print("4. Высокая рыночная волатильность")
    volatile_market = {
        "volatility": 0.08,  # Очень высокая волатильность
        "trend_strength": 0.3,
        "volume_ratio": 0.5  # Низкая ликвидность
    }
    
    approved, check = await safety_system.validate_trade_execution(
        normal_signal, volatile_market, normal_account, normal_risk
    )
    print(f"Результат: {'✅ ОДОБРЕНО' if approved else '❌ ОТКЛОНЕНО'}")
    print(f"Уровень риска: {check.safety_level.value}")
    print(f"Обоснование: {check.reasoning}")
    if check.recommendations:
        print(f"Рекомендации: {'; '.join(check.recommendations)}\n")
    else:
        print()
    
    # Сценарий 5: Критическая ситуация
    print("5. Критическая ситуация (все факторы риска)")
    critical_signal = {
        "strategy_name": "high_risk_strategy",
        "symbol": "BTCUSDT",
        "signal_type": "buy",
        "confidence": 55.0,  # Низкая уверенность
        "entry_price": 50000.0,
        "stop_loss": 47000.0,
        "take_profit": 56000.0,
        "position_size": 0.25  # Очень крупная позиция
    }
    
    critical_account = {
        "balance": 8000.0,  # Уменьшенный баланс
        "daily_pnl": -1500.0  # Критические убытки
    }
    
    critical_risk = {
        "open_positions_count": 3,  # Максимум позиций
        "total_exposure_pct": 25.0  # Высокая экспозиция
    }
    
    approved, check = await safety_system.validate_trade_execution(
        critical_signal, volatile_market, critical_account, critical_risk
    )
    print(f"Результат: {'✅ ОДОБРЕНО' if approved else '❌ ОТКЛОНЕНО'}")
    print(f"Уровень риска: {check.safety_level.value}")
    print(f"Действие: {check.action.value}")
    print(f"Обоснование: {check.reasoning}")
    if check.recommendations:
        print(f"Рекомендации: {'; '.join(check.recommendations)}\n")
    else:
        print()
    
    # Итоговый отчет
    print("=== Итоговый отчет системы безопасности ===")
    report = safety_system.get_safety_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(test_risky_scenarios())
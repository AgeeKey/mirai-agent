def signal_score(ema_fast: float, ema_slow: float, rsi: float) -> float:
    if ema_fast > ema_slow and 45 <= rsi <= 60:
        return 0.8
    return 0.4
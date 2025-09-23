"""
Расширенные торговые инструменты для автономного AI-агента
"""

import os
import sys
import json
import time
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import random
import hashlib

# Добавляем путь для импорта модулей Mirai
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger('MiraiAgent.Tools')

class AdvancedTradingTools:
    """Расширенные инструменты для торговой деятельности агента"""
    
    def __init__(self, config=None):
        self.config = config
        self.binance_api = "https://api.binance.com"
        self.news_sources = [
            "https://api.coingecko.com/api/v3/news",
            "https://min-api.cryptocompare.com/data/v2/news/"
        ]
        
    def get_real_market_data(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """Получение реальных рыночных данных через Binance API"""
        try:
            # Получаем текущую цену
            price_url = f"{self.binance_api}/api/v3/ticker/price"
            price_response = requests.get(price_url, params={"symbol": symbol}, timeout=10)
            
            if price_response.status_code != 200:
                logger.warning(f"Не удалось получить цену для {symbol}, используем мок данные")
                return self._get_mock_market_data(symbol)
            
            price_data = price_response.json()
            current_price = float(price_data["price"])
            
            # Получаем 24h статистику
            stats_url = f"{self.binance_api}/api/v3/ticker/24hr"
            stats_response = requests.get(stats_url, params={"symbol": symbol}, timeout=10)
            
            if stats_response.status_code != 200:
                stats_data = {}
            else:
                stats_data = stats_response.json()
            
            # Получаем свечи для анализа тренда
            klines_url = f"{self.binance_api}/api/v3/klines"
            klines_params = {
                "symbol": symbol,
                "interval": "1h",
                "limit": 24
            }
            klines_response = requests.get(klines_url, params=klines_params, timeout=10)
            
            trend_analysis = "neutral"
            volatility = 0.0
            
            if klines_response.status_code == 200:
                klines = klines_response.json()
                if klines:
                    # Простой анализ тренда
                    open_price = float(klines[0][1])
                    close_price = float(klines[-1][4])
                    trend_analysis = "bullish" if close_price > open_price else "bearish"
                    
                    # Расчет волатильности
                    prices = [float(k[4]) for k in klines]
                    if len(prices) > 1:
                        price_changes = [abs(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
                        volatility = sum(price_changes) / len(price_changes) * 100
            
            result = {
                "symbol": symbol,
                "price": current_price,
                "change_24h": float(stats_data.get("priceChangePercent", 0)),
                "volume": float(stats_data.get("volume", 0)),
                "high_24h": float(stats_data.get("highPrice", current_price)),
                "low_24h": float(stats_data.get("lowPrice", current_price)),
                "trend": trend_analysis,
                "volatility": volatility,
                "timestamp": datetime.now().isoformat(),
                "data_source": "binance_api"
            }
            
            logger.info(f"Получены реальные данные для {symbol}: цена ${current_price:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка получения рыночных данных для {symbol}: {e}")
            return self._get_mock_market_data(symbol)
    
    def _get_mock_market_data(self, symbol: str) -> Dict[str, Any]:
        """Генерация мок данных если API недоступен"""
        # Базовые цены для разных символов
        base_prices = {
            "BTCUSDT": 45000,
            "ETHUSDT": 3000,
            "ADAUSDT": 0.5,
            "SOLUSDT": 100,
            "DOTUSDT": 8
        }
        
        base_price = base_prices.get(symbol, 1000)
        
        # Добавляем случайные колебания
        price_variation = random.uniform(-0.05, 0.05)  # ±5%
        current_price = base_price * (1 + price_variation)
        
        change_24h = random.uniform(-8, 8)
        volume = random.uniform(100000, 1000000)
        
        return {
            "symbol": symbol,
            "price": current_price,
            "change_24h": change_24h,
            "volume": volume,
            "high_24h": current_price * 1.03,
            "low_24h": current_price * 0.97,
            "trend": "bullish" if change_24h > 0 else "bearish",
            "volatility": abs(change_24h),
            "timestamp": datetime.now().isoformat(),
            "data_source": "mock_data"
        }
    
    def technical_analysis(self, symbol: str, timeframe: str = "1h") -> Dict[str, Any]:
        """Технический анализ инструмента"""
        try:
            # Получаем исторические данные
            klines_url = f"{self.binance_api}/api/v3/klines"
            params = {
                "symbol": symbol,
                "interval": timeframe,
                "limit": 100
            }
            
            response = requests.get(klines_url, params=params, timeout=10)
            
            if response.status_code != 200:
                return self._mock_technical_analysis(symbol)
            
            klines = response.json()
            
            if not klines:
                return self._mock_technical_analysis(symbol)
            
            # Извлекаем цены закрытия
            closes = [float(k[4]) for k in klines]
            highs = [float(k[2]) for k in klines]
            lows = [float(k[3]) for k in klines]
            
            # Простые технические индикаторы
            sma_20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else closes[-1]
            sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else closes[-1]
            
            current_price = closes[-1]
            
            # RSI упрощенный
            rsi = self._calculate_simple_rsi(closes)
            
            # Поддержка и сопротивление
            support = min(lows[-20:]) if len(lows) >= 20 else min(lows)
            resistance = max(highs[-20:]) if len(highs) >= 20 else max(highs)
            
            # Сигналы
            signals = []
            if current_price > sma_20 > sma_50:
                signals.append("bullish_trend")
            elif current_price < sma_20 < sma_50:
                signals.append("bearish_trend")
            
            if rsi > 70:
                signals.append("overbought")
            elif rsi < 30:
                signals.append("oversold")
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "current_price": current_price,
                "sma_20": sma_20,
                "sma_50": sma_50,
                "rsi": rsi,
                "support": support,
                "resistance": resistance,
                "signals": signals,
                "trend_strength": abs(current_price - sma_20) / sma_20 * 100,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка технического анализа для {symbol}: {e}")
            return self._mock_technical_analysis(symbol)
    
    def _calculate_simple_rsi(self, prices: List[float], period: int = 14) -> float:
        """Упрощенный расчет RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _mock_technical_analysis(self, symbol: str) -> Dict[str, Any]:
        """Мок технический анализ"""
        current_price = random.uniform(40000, 60000) if symbol == "BTCUSDT" else random.uniform(1000, 5000)
        sma_20 = current_price * random.uniform(0.98, 1.02)
        sma_50 = current_price * random.uniform(0.95, 1.05)
        rsi = random.uniform(30, 70)
        
        signals = []
        if rsi > 70:
            signals.append("overbought")
        elif rsi < 30:
            signals.append("oversold")
        
        return {
            "symbol": symbol,
            "timeframe": "1h",
            "current_price": current_price,
            "sma_20": sma_20,
            "sma_50": sma_50,
            "rsi": rsi,
            "support": current_price * 0.95,
            "resistance": current_price * 1.05,
            "signals": signals,
            "trend_strength": random.uniform(0, 5),
            "timestamp": datetime.now().isoformat(),
            "data_source": "mock"
        }
    
    def news_sentiment_analysis(self, keywords: List[str] = None) -> Dict[str, Any]:
        """Анализ новостей и настроений рынка"""
        try:
            if keywords is None:
                keywords = ["bitcoin", "ethereum", "cryptocurrency"]
            
            # Пытаемся получить реальные новости
            news_items = []
            
            try:
                # CoinGecko news API (бесплатный)
                response = requests.get(
                    "https://api.coingecko.com/api/v3/news",
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("data", [])[:5]:
                        news_items.append({
                            "title": item.get("title", ""),
                            "description": item.get("description", ""),
                            "url": item.get("url", ""),
                            "published_at": item.get("published_at", "")
                        })
            except:
                pass
            
            # Если не получили новости, создаем мок данные
            if not news_items:
                news_items = self._generate_mock_news()
            
            # Простой анализ настроений
            sentiment_score = self._analyze_sentiment(news_items)
            
            return {
                "news_count": len(news_items),
                "sentiment_score": sentiment_score,  # -1 (негативно) до 1 (позитивно)
                "sentiment_label": self._get_sentiment_label(sentiment_score),
                "key_topics": self._extract_key_topics(news_items),
                "news_items": news_items[:3],  # Первые 3 новости
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа новостей: {e}")
            return {
                "news_count": 0,
                "sentiment_score": 0.0,
                "sentiment_label": "neutral",
                "key_topics": [],
                "news_items": [],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_mock_news(self) -> List[Dict[str, str]]:
        """Генерация мок новостей"""
        mock_news = [
            {
                "title": "Bitcoin показывает признаки восстановления после недавнего падения",
                "description": "Аналитики отмечают положительные технические сигналы на графиках BTC",
                "url": "https://example.com/news1",
                "published_at": datetime.now().isoformat()
            },
            {
                "title": "Ethereum обновляет максимумы на фоне роста DeFi активности",
                "description": "Рост использования децентрализованных финансов поддерживает цену ETH",
                "url": "https://example.com/news2",
                "published_at": (datetime.now() - timedelta(hours=2)).isoformat()
            },
            {
                "title": "Регуляторы обсуждают новые правила для криптовалют",
                "description": "Возможны изменения в законодательстве касающемся цифровых активов",
                "url": "https://example.com/news3",
                "published_at": (datetime.now() - timedelta(hours=4)).isoformat()
            }
        ]
        return mock_news
    
    def _analyze_sentiment(self, news_items: List[Dict]) -> float:
        """Простой анализ настроений новостей"""
        positive_words = ["рост", "восстановление", "максимум", "позитивный", "прибыль", "успех"]
        negative_words = ["падение", "снижение", "потери", "негативный", "кризис", "проблемы"]
        
        total_score = 0
        total_items = 0
        
        for item in news_items:
            text = (item.get("title", "") + " " + item.get("description", "")).lower()
            
            positive_count = sum(1 for word in positive_words if word in text)
            negative_count = sum(1 for word in negative_words if word in text)
            
            if positive_count > 0 or negative_count > 0:
                score = (positive_count - negative_count) / (positive_count + negative_count)
                total_score += score
                total_items += 1
        
        return total_score / total_items if total_items > 0 else 0.0
    
    def _get_sentiment_label(self, score: float) -> str:
        """Получение текстовой метки настроения"""
        if score > 0.3:
            return "positive"
        elif score < -0.3:
            return "negative"
        else:
            return "neutral"
    
    def _extract_key_topics(self, news_items: List[Dict]) -> List[str]:
        """Извлечение ключевых тем из новостей"""
        # Простое извлечение ключевых слов
        key_words = ["bitcoin", "ethereum", "regulation", "defi", "nft", "mining"]
        topics = []
        
        for item in news_items:
            text = (item.get("title", "") + " " + item.get("description", "")).lower()
            for word in key_words:
                if word in text and word not in topics:
                    topics.append(word)
        
        return topics[:5]  # Максимум 5 тем
    
    def advanced_risk_assessment(self, 
                                portfolio: Dict[str, Any], 
                                proposed_trade: Dict[str, Any]) -> Dict[str, Any]:
        """Продвинутая оценка рисков"""
        try:
            total_portfolio_value = portfolio.get("total_value", 10000)
            trade_size = proposed_trade.get("quantity", 0) * proposed_trade.get("price", 0)
            
            # Базовый риск позиции
            position_risk = (trade_size / total_portfolio_value) * 100
            
            # Риск концентрации
            symbol = proposed_trade.get("symbol", "")
            current_exposure = 0
            for position in portfolio.get("positions", []):
                if position.get("symbol") == symbol:
                    current_exposure += position.get("value", 0)
            
            total_exposure = (current_exposure + trade_size) / total_portfolio_value * 100
            
            # Волатильность символа
            market_data = self.get_real_market_data(symbol)
            volatility = market_data.get("volatility", 5.0)
            
            # VaR (Value at Risk) упрощенный
            var_95 = trade_size * 0.02 * (volatility / 100) * 1.65  # 95% VaR
            
            # Корреляционный риск (упрощенный)
            correlation_risk = self._assess_correlation_risk(portfolio, symbol)
            
            # Общая оценка риска
            risk_factors = {
                "position_size": min(position_risk / 5, 1.0),  # Нормализуем к 0-1
                "concentration": min(total_exposure / 20, 1.0),
                "volatility": min(volatility / 10, 1.0),
                "correlation": correlation_risk
            }
            
            # Взвешенный риск-скор
            risk_score = sum(risk_factors.values()) / len(risk_factors)
            
            # Рекомендации
            recommendations = []
            if position_risk > 5:
                recommendations.append("Уменьшить размер позиции")
            if total_exposure > 25:
                recommendations.append("Слишком высокая концентрация в одном активе")
            if volatility > 8:
                recommendations.append("Высокая волатильность, рассмотреть стоп-лосс")
            if risk_score > 0.7:
                recommendations.append("Общий риск слишком высок")
            
            return {
                "risk_score": risk_score,
                "risk_level": "low" if risk_score < 0.3 else "medium" if risk_score < 0.7 else "high",
                "position_risk_percent": position_risk,
                "total_exposure_percent": total_exposure,
                "value_at_risk_95": var_95,
                "volatility": volatility,
                "risk_factors": risk_factors,
                "recommendations": recommendations,
                "approved": risk_score < 0.6,  # Автоматическое одобрение для низкого риска
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка оценки рисков: {e}")
            return {
                "error": str(e),
                "risk_score": 1.0,
                "risk_level": "high",
                "approved": False,
                "timestamp": datetime.now().isoformat()
            }
    
    def _assess_correlation_risk(self, portfolio: Dict, new_symbol: str) -> float:
        """Оценка корреляционного риска"""
        # Упрощенная матрица корреляций
        crypto_correlations = {
            ("BTCUSDT", "ETHUSDT"): 0.8,
            ("BTCUSDT", "ADAUSDT"): 0.7,
            ("ETHUSDT", "ADAUSDT"): 0.75,
            ("BTCUSDT", "SOLUSDT"): 0.6,
            ("ETHUSDT", "SOLUSDT"): 0.7
        }
        
        total_correlation = 0
        count = 0
        
        for position in portfolio.get("positions", []):
            existing_symbol = position.get("symbol", "")
            pair1 = (min(existing_symbol, new_symbol), max(existing_symbol, new_symbol))
            pair2 = (max(existing_symbol, new_symbol), min(existing_symbol, new_symbol))
            
            correlation = crypto_correlations.get(pair1, crypto_correlations.get(pair2, 0.5))
            
            # Взвешиваем по размеру позиции
            weight = position.get("value", 0) / portfolio.get("total_value", 1)
            total_correlation += correlation * weight
            count += weight
        
        return total_correlation / count if count > 0 else 0.0
    
    def portfolio_optimization_suggestions(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """Предложения по оптимизации портфеля"""
        try:
            positions = portfolio.get("positions", [])
            total_value = portfolio.get("total_value", 0)
            
            if not positions or total_value == 0:
                return {
                    "suggestions": ["Портфель пуст или нет данных"],
                    "rebalancing_needed": False,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Анализ распределения
            allocations = {}
            for position in positions:
                symbol = position.get("symbol", "")
                value = position.get("value", 0)
                allocations[symbol] = (value / total_value) * 100
            
            # Целевые аллокации (например)
            target_allocations = {
                "BTCUSDT": 40,  # 40% BTC
                "ETHUSDT": 30,  # 30% ETH
                "ADAUSDT": 15,  # 15% ADA
                "SOLUSDT": 10,  # 10% SOL
                "CASH": 5       # 5% кеш
            }
            
            suggestions = []
            rebalancing_actions = []
            
            # Сравниваем текущие и целевые аллокации
            for symbol, target in target_allocations.items():
                current = allocations.get(symbol, 0)
                difference = abs(current - target)
                
                if difference > 5:  # Если отклонение больше 5%
                    if current > target:
                        action = f"Уменьшить {symbol} на {difference:.1f}%"
                        rebalancing_actions.append({
                            "symbol": symbol,
                            "action": "reduce",
                            "current_percent": current,
                            "target_percent": target,
                            "difference": difference
                        })
                    else:
                        action = f"Увеличить {symbol} на {difference:.1f}%"
                        rebalancing_actions.append({
                            "symbol": symbol,
                            "action": "increase",
                            "current_percent": current,
                            "target_percent": target,
                            "difference": difference
                        })
                    suggestions.append(action)
            
            # Проверка диверсификации
            max_allocation = max(allocations.values()) if allocations else 0
            if max_allocation > 50:
                suggestions.append("Портфель слишком концентрирован в одном активе")
            
            # Проверка количества позиций
            if len(positions) < 3:
                suggestions.append("Рассмотреть добавление большей диверсификации")
            elif len(positions) > 10:
                suggestions.append("Возможно, слишком много позиций для эффективного управления")
            
            return {
                "current_allocations": allocations,
                "target_allocations": target_allocations,
                "suggestions": suggestions if suggestions else ["Портфель хорошо сбалансирован"],
                "rebalancing_actions": rebalancing_actions,
                "rebalancing_needed": len(rebalancing_actions) > 0,
                "diversification_score": self._calculate_diversification_score(allocations),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа портфеля: {e}")
            return {
                "error": str(e),
                "suggestions": ["Ошибка анализа портфеля"],
                "rebalancing_needed": False,
                "timestamp": datetime.now().isoformat()
            }
    
    def _calculate_diversification_score(self, allocations: Dict[str, float]) -> float:
        """Расчет индекса диверсификации (от 0 до 1)"""
        if not allocations:
            return 0.0
        
        # Используем индекс Херфиндаля-Хиршмана (HHI) инвертированный
        hhi = sum((allocation / 100) ** 2 for allocation in allocations.values())
        
        # Нормализуем к шкале 0-1 (1 = максимальная диверсификация)
        n = len(allocations)
        if n <= 1:
            return 0.0
        
        max_hhi = 1.0  # Максимальная концентрация
        min_hhi = 1.0 / n  # Максимальная диверсификация
        
        # Инвертируем и нормализуем
        diversification_score = (max_hhi - hhi) / (max_hhi - min_hhi)
        
        return max(0.0, min(1.0, diversification_score))
    
    def generate_trading_signals(self, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """Генерация торговых сигналов на основе анализа"""
        if symbols is None:
            symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
        
        signals = []
        
        for symbol in symbols:
            try:
                # Получаем рыночные данные
                market_data = self.get_real_market_data(symbol)
                
                # Технический анализ
                tech_analysis = self.technical_analysis(symbol)
                
                # Анализ новостей
                news_analysis = self.news_sentiment_analysis()
                
                # Генерируем сигнал
                signal = self._generate_signal_for_symbol(
                    symbol, market_data, tech_analysis, news_analysis
                )
                
                signals.append(signal)
                
            except Exception as e:
                logger.error(f"Ошибка генерации сигнала для {symbol}: {e}")
                signals.append({
                    "symbol": symbol,
                    "signal": "hold",
                    "confidence": 0.0,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        return signals
    
    def _generate_signal_for_symbol(self, 
                                   symbol: str,
                                   market_data: Dict,
                                   tech_analysis: Dict,
                                   news_analysis: Dict) -> Dict[str, Any]:
        """Генерация сигнала для конкретного символа"""
        
        score = 0.0
        confidence_factors = []
        
        # Технический анализ
        tech_signals = tech_analysis.get("signals", [])
        rsi = tech_analysis.get("rsi", 50)
        current_price = tech_analysis.get("current_price", 0)
        sma_20 = tech_analysis.get("sma_20", current_price)
        
        # RSI сигналы
        if rsi < 30:
            score += 0.3
            confidence_factors.append("RSI oversold")
        elif rsi > 70:
            score -= 0.3
            confidence_factors.append("RSI overbought")
        
        # Тренд
        if "bullish_trend" in tech_signals:
            score += 0.2
            confidence_factors.append("Bullish trend")
        elif "bearish_trend" in tech_signals:
            score -= 0.2
            confidence_factors.append("Bearish trend")
        
        # Позиция относительно скользящих средних
        if current_price > sma_20:
            score += 0.1
            confidence_factors.append("Above SMA20")
        else:
            score -= 0.1
            confidence_factors.append("Below SMA20")
        
        # Настроения новостей
        sentiment_score = news_analysis.get("sentiment_score", 0)
        if sentiment_score > 0.3:
            score += 0.2
            confidence_factors.append("Positive news sentiment")
        elif sentiment_score < -0.3:
            score -= 0.2
            confidence_factors.append("Negative news sentiment")
        
        # Волатильность
        volatility = market_data.get("volatility", 0)
        if volatility > 5:
            confidence_factors.append("High volatility - caution advised")
        
        # Определяем сигнал
        if score > 0.3:
            signal = "buy"
        elif score < -0.3:
            signal = "sell"
        else:
            signal = "hold"
        
        # Уверенность (0-1)
        confidence = min(abs(score), 1.0)
        
        return {
            "symbol": symbol,
            "signal": signal,
            "confidence": confidence,
            "score": score,
            "factors": confidence_factors,
            "recommended_position_size": self._calculate_position_size(confidence, volatility),
            "stop_loss_percent": max(2.0, volatility * 0.5),
            "take_profit_percent": max(4.0, volatility * 1.0),
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_position_size(self, confidence: float, volatility: float) -> float:
        """Расчет рекомендуемого размера позиции"""
        base_size = 0.02  # 2% от портфеля
        
        # Корректируем на уверенность
        confidence_multiplier = confidence
        
        # Корректируем на волатильность
        volatility_divisor = max(1.0, volatility / 5.0)
        
        position_size = (base_size * confidence_multiplier) / volatility_divisor
        
        # Ограничиваем размер
        return max(0.005, min(0.05, position_size))  # От 0.5% до 5%
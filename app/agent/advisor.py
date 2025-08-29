"""
AI Advisor module for trading signal analysis and recommendation

This module provides intelligent trading signal scoring using either OpenAI GPT models
or a deterministic mock for testing/fallback scenarios.
"""
import os
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


class SignalAdvisor:
    """AI-powered trading signal advisor"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the advisor with optional OpenAI API key
        
        Args:
            api_key: OpenAI API key, if None will try to get from environment
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.use_openai = OPENAI_AVAILABLE and bool(self.api_key)
        
        if self.use_openai:
            openai.api_key = self.api_key
            logger.info("SignalAdvisor initialized with OpenAI integration")
        else:
            logger.info("SignalAdvisor initialized with deterministic mock (no OpenAI key)")
    
    def get_signal_score(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market features and return trading signal score
        
        Args:
            features: Dictionary containing market data and technical indicators
                     Expected keys: price, ema, rsi, atr, adx, volume_trend, etc.
        
        Returns:
            Dictionary with keys:
            - score: float (0.0 to 1.0) - confidence score
            - rationale: str - reasoning behind the decision
            - strategy: str - trading strategy description  
            - action: str - "BUY", "SELL", or "HOLD"
        """
        if self.use_openai:
            return self._get_openai_signal_score(features)
        else:
            return self._get_mock_signal_score(features)
    
    def _get_openai_signal_score(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Get signal score using OpenAI GPT"""
        try:
            # Prepare the prompt with market features
            prompt = self._build_analysis_prompt(features)
            
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert trading advisor. Analyze the provided market data and return a JSON response with trading recommendations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                result = json.loads(content)
                return self._validate_and_normalize_response(result)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse OpenAI JSON response: {content}")
                return self._get_fallback_response("OpenAI returned invalid JSON")
                
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._get_fallback_response(f"OpenAI API error: {str(e)}")
    
    def _get_mock_signal_score(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministic mock for testing and fallback"""
        # Extract key indicators with safe defaults
        price = features.get('price', 50000.0)
        ema = features.get('ema', price)
        rsi = features.get('rsi', 50.0)
        atr = features.get('atr', price * 0.02)
        adx = features.get('adx', 25.0)
        
        # Simple deterministic scoring logic
        score = 0.5  # Base score
        rationale_parts = []
        
        # Price vs EMA trend analysis
        price_ema_ratio = (price - ema) / ema if ema > 0 else 0
        if price_ema_ratio > 0.02:  # Price 2% above EMA
            score += 0.15
            rationale_parts.append("bullish trend (price above EMA)")
        elif price_ema_ratio < -0.02:  # Price 2% below EMA
            score -= 0.15
            rationale_parts.append("bearish trend (price below EMA)")
        else:
            rationale_parts.append("neutral trend")
        
        # RSI analysis
        if rsi < 30:  # Oversold
            score += 0.2
            rationale_parts.append("oversold conditions (RSI < 30)")
        elif rsi > 70:  # Overbought  
            score -= 0.2
            rationale_parts.append("overbought conditions (RSI > 70)")
        elif 40 <= rsi <= 60:  # Neutral
            score += 0.05
            rationale_parts.append("neutral RSI")
        
        # ADX trend strength
        if adx > 25:
            score += 0.1
            rationale_parts.append(f"strong trend (ADX {adx:.1f})")
        else:
            score -= 0.05
            rationale_parts.append(f"weak trend (ADX {adx:.1f})")
        
        # Volatility check (ATR)
        atr_ratio = atr / price if price > 0 else 0
        if atr_ratio > 0.05:  # High volatility
            score -= 0.1
            rationale_parts.append("high volatility")
        elif atr_ratio < 0.01:  # Very low volatility
            score -= 0.05
            rationale_parts.append("very low volatility")
        
        # Clamp score between 0 and 1
        score = max(0.0, min(1.0, score))
        
        # Determine action based on score and additional logic
        if score >= 0.7:
            action = "BUY"
            strategy = "momentum_breakout"
        elif score <= 0.3:
            action = "SELL"
            strategy = "mean_reversion"
        else:
            action = "HOLD"
            strategy = "wait_and_see"
        
        rationale = f"Score {score:.2f}: " + ", ".join(rationale_parts)
        
        return {
            "score": round(score, 3),
            "rationale": rationale,
            "strategy": strategy,
            "action": action
        }
    
    def _build_analysis_prompt(self, features: Dict[str, Any]) -> str:
        """Build analysis prompt for OpenAI"""
        return f"""
        Analyze the following market data and provide a trading recommendation:
        
        Market Features:
        - Current Price: {features.get('price', 'N/A')}
        - EMA: {features.get('ema', 'N/A')}
        - RSI: {features.get('rsi', 'N/A')}
        - ATR: {features.get('atr', 'N/A')}
        - ADX: {features.get('adx', 'N/A')}
        - Volume Trend: {features.get('volume_trend', 'N/A')}
        
        Please return a JSON response with the following structure:
        {{
            "score": <float between 0.0 and 1.0>,
            "rationale": "<brief explanation of your analysis>",
            "strategy": "<trading strategy name>",
            "action": "<BUY, SELL, or HOLD>"
        }}
        
        Guidelines:
        - Score should reflect confidence in the trading signal (0.0 = very bearish, 1.0 = very bullish)
        - Rationale should be concise but informative
        - Consider trend, momentum, volatility, and risk factors
        - Be conservative in uncertain conditions
        """
    
    def _validate_and_normalize_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize API response"""
        # Ensure all required fields exist
        score = float(response.get('score', 0.5))
        rationale = str(response.get('rationale', 'No rationale provided'))
        strategy = str(response.get('strategy', 'unknown'))
        action = str(response.get('action', 'HOLD')).upper()
        
        # Validate score range
        score = max(0.0, min(1.0, score))
        
        # Validate action
        if action not in ['BUY', 'SELL', 'HOLD']:
            action = 'HOLD'
        
        return {
            "score": round(score, 3),
            "rationale": rationale[:200],  # Limit rationale length
            "strategy": strategy[:50],     # Limit strategy length
            "action": action
        }
    
    def _get_fallback_response(self, error_reason: str) -> Dict[str, Any]:
        """Return safe fallback response on error"""
        return {
            "score": 0.5,
            "rationale": f"Fallback response due to error: {error_reason}",
            "strategy": "fallback",
            "action": "HOLD"
        }


# Global advisor instance
_advisor_instance = None

def get_signal_score(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Global function to get signal score - maintains singleton advisor instance
    
    Args:
        features: Market features dictionary
        
    Returns:
        Signal score response dictionary
    """
    global _advisor_instance
    
    if _advisor_instance is None:
        _advisor_instance = SignalAdvisor()
    
    return _advisor_instance.get_signal_score(features)


def reset_advisor():
    """Reset the global advisor instance (useful for testing)"""
    global _advisor_instance
    _advisor_instance = None
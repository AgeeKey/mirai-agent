"""
Policy module for trading decisions with AI integration
"""

import asyncio
import aiohttp
import json
import random
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .schema import AgentDecision, MarketData, RiskParameters


class AIEnhancedPolicy:
    """
    AI-enhanced policy that integrates with Orchestrator for trading decisions
    Combines traditional rule-based decisions with AI recommendations
    """

    def __init__(self, risk_params: RiskParameters = None, ai_config: Dict[str, Any] = None):
        self.risk_params = risk_params or RiskParameters()
        self.ai_config = ai_config or {}
        self.logger = logging.getLogger(__name__)
        
        # AI configuration
        self.ai_enabled = self.ai_config.get('enabled', False)
        self.orchestrator_url = self.ai_config.get('orchestrator_url', 'http://localhost:8080')
        self.ai_weight = self.ai_config.get('decision_weight', 0.6)  # Weight of AI vs rules
        self.ai_timeout = self.ai_config.get('timeout', 8.0)
        
        # Traditional decision templates (fallback)
        self.decision_templates = [
            {
                "rationale": "Strong bullish momentum with RSI oversold conditions and positive volume divergence",
                "intent": "BUY",
                "action": "MARKET_BUY",
            },
            {
                "rationale": "Bearish divergence detected with overbought RSI and declining volume",
                "intent": "SELL",
                "action": "MARKET_SELL",
            },
            {
                "rationale": "Market showing sideways consolidation with low volatility, waiting for clear direction",
                "intent": "HOLD",
                "action": "HOLD",
            },
            {
                "rationale": "Price approaching key resistance level with decreasing momentum",
                "intent": "SELL",
                "action": "LIMIT_SELL",
            },
            {
                "rationale": "Support level holding strong with increasing buying pressure",
                "intent": "BUY",
                "action": "LIMIT_BUY",
            },
        ]
    
    async def analyze_market_with_ai(self, market_data: MarketData) -> AgentDecision:
        """
        Enhanced market analysis using AI orchestrator
        """
        try:
            # Get AI recommendation
            ai_recommendation = None
            if self.ai_enabled:
                ai_recommendation = await self._get_ai_market_analysis(market_data)
            
            # Get traditional analysis
            traditional_decision = self._traditional_market_analysis(market_data)
            
            # Combine AI and traditional analysis
            final_decision = await self._combine_analyses(
                traditional_decision, ai_recommendation, market_data
            )
            
            return final_decision
        
        except Exception as e:
            self.logger.error(f"Market analysis error: {e}")
            # Fallback to traditional analysis
            return self._traditional_market_analysis(market_data)
    
    async def _get_ai_market_analysis(self, market_data: MarketData) -> Optional[Dict[str, Any]]:
        """Get AI-powered market analysis from orchestrator"""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.ai_timeout)
            ) as session:
                
                # Prepare market data for AI
                ai_task_data = {
                    "type": "market_analysis",
                    "symbol": market_data.symbol,
                    "market_data": {
                        "price": float(market_data.price),
                        "volume": float(market_data.volume),
                        "timestamp": market_data.timestamp.isoformat(),
                        "rsi": getattr(market_data, 'rsi', None),
                        "macd": getattr(market_data, 'macd', None),
                        "bb_position": getattr(market_data, 'bb_position', None)
                    },
                    "goal": f"Analyze market conditions for {market_data.symbol} and provide trading recommendation",
                    "timestamp": datetime.now().isoformat()
                }
                
                # Submit task to orchestrator
                async with session.post(
                    f"{self.orchestrator_url}/task/submit",
                    json=ai_task_data
                ) as response:
                    if response.status == 200:
                        task_result = await response.json()
                        task_id = task_result.get('task_id')
                        
                        if task_id:
                            # Poll for result (with timeout)
                            return await self._poll_ai_result(session, task_id)
                    else:
                        self.logger.warning(f"AI task submission failed: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"AI market analysis error: {e}")
        
        return None
    
    async def _poll_ai_result(self, session: aiohttp.ClientSession, task_id: str, 
                             max_attempts: int = 10) -> Optional[Dict[str, Any]]:
        """Poll AI orchestrator for task result"""
        for attempt in range(max_attempts):
            try:
                async with session.get(
                    f"{self.orchestrator_url}/task/{task_id}/result"
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if result.get('status') == 'completed':
                            return result.get('recommendation', {})
                        elif result.get('status') == 'failed':
                            self.logger.error(f"AI task failed: {result.get('error')}")
                            return None
                        # Still processing, continue polling
                    
                    await asyncio.sleep(0.5)
            
            except Exception as e:
                self.logger.error(f"AI result polling error: {e}")
                break
        
        return None
    
    def _traditional_market_analysis(self, market_data: MarketData) -> AgentDecision:
        """Traditional rule-based market analysis"""
        # Simulate traditional analysis logic
        price_score = self._calculate_price_score(market_data)
        volume_score = self._calculate_volume_score(market_data)
        technical_score = self._calculate_technical_score(market_data)
        
        overall_score = (price_score + volume_score + technical_score) / 3
        
        # Select appropriate template
        if overall_score > 0.7:
            template = self.decision_templates[0]  # Bullish
            score = overall_score
        elif overall_score < 0.3:
            template = self.decision_templates[1]  # Bearish
            score = 1.0 - overall_score
        else:
            template = self.decision_templates[2]  # Hold
            score = 0.5
        
        return AgentDecision(
            symbol=market_data.symbol,
            score=score,
            rationale=f"Traditional analysis: {template['rationale']}",
            intent=template["intent"],
            action=template["action"],
            metadata={
                "analysis_type": "traditional",
                "price_score": price_score,
                "volume_score": volume_score,
                "technical_score": technical_score
            }
        )
    
    async def _combine_analyses(self, traditional_decision: AgentDecision, 
                              ai_recommendation: Optional[Dict[str, Any]], 
                              market_data: MarketData) -> AgentDecision:
        """Combine traditional and AI analyses into final decision"""
        
        if not ai_recommendation:
            # No AI recommendation, use traditional with slight penalty
            traditional_decision.score *= 0.9
            traditional_decision.metadata["ai_available"] = False
            return traditional_decision
        
        try:
            # Extract AI recommendation data
            ai_action = ai_recommendation.get('action', 'HOLD')
            ai_confidence = float(ai_recommendation.get('confidence', 0.5))
            ai_reasoning = ai_recommendation.get('reasoning', '')
            ai_risk_score = float(ai_recommendation.get('risk_score', 0.5))
            
            # Convert actions to common format
            traditional_score = self._action_to_score(traditional_decision.intent)
            ai_score = self._action_to_score(ai_action)
            
            # Weighted combination
            combined_score = (
                traditional_score * (1 - self.ai_weight) + 
                ai_score * ai_confidence * self.ai_weight
            )
            
            # Determine final action
            final_action, final_intent = self._score_to_action(combined_score)
            
            # Calculate final confidence
            final_confidence = (
                traditional_decision.score * (1 - self.ai_weight) + 
                ai_confidence * self.ai_weight
            )
            
            # Create combined rationale
            combined_rationale = f"""
            Combined Analysis:
            Traditional: {traditional_decision.rationale}
            AI: {ai_reasoning}
            Risk Assessment: {ai_risk_score:.2f}
            Confidence: {final_confidence:.2f}
            """
            
            return AgentDecision(
                symbol=market_data.symbol,
                score=final_confidence,
                rationale=combined_rationale.strip(),
                intent=final_intent,
                action=final_action,
                metadata={
                    "analysis_type": "ai_enhanced",
                    "traditional_score": traditional_decision.score,
                    "ai_confidence": ai_confidence,
                    "ai_risk_score": ai_risk_score,
                    "ai_weight": self.ai_weight,
                    "ai_available": True
                }
            )
        
        except Exception as e:
            self.logger.error(f"Analysis combination error: {e}")
            # Fallback to traditional
            traditional_decision.metadata["ai_error"] = str(e)
            return traditional_decision
    
    def _action_to_score(self, action: str) -> float:
        """Convert action to numeric score (-1 to 1)"""
        action = action.upper()
        if action in ['BUY', 'MARKET_BUY', 'LIMIT_BUY']:
            return 1.0
        elif action in ['SELL', 'MARKET_SELL', 'LIMIT_SELL']:
            return -1.0
        else:
            return 0.0
    
    def _score_to_action(self, score: float) -> tuple[str, str]:
        """Convert numeric score to action and intent"""
        if score > 0.3:
            return "MARKET_BUY", "BUY"
        elif score < -0.3:
            return "MARKET_SELL", "SELL"
        else:
            return "HOLD", "HOLD"
    
    def _calculate_price_score(self, market_data: MarketData) -> float:
        """Calculate price-based score (0.0 to 1.0)"""
        # Simple momentum based on price changes
        return random.uniform(0.2, 0.8)
    
    def _calculate_volume_score(self, market_data: MarketData) -> float:
        """Calculate volume-based score (0.0 to 1.0)"""
        # Volume analysis
        return random.uniform(0.3, 0.7)
    
    def _calculate_technical_score(self, market_data: MarketData) -> float:
        """Calculate technical indicator score (0.0 to 1.0)"""
        # Technical indicators like RSI, MACD, etc.
        return random.uniform(0.4, 0.9)


# Legacy support - keeping original class for compatibility
class MockLLMPolicy(AIEnhancedPolicy):
    """
    Legacy Mock LLM policy with AI enhancement
    Maintains backward compatibility while adding AI capabilities
    """
    
    def __init__(self, risk_params: RiskParameters = None, ai_config: Dict[str, Any] = None):
        super().__init__(risk_params, ai_config)
    
    def analyze_market(self, market_data: MarketData) -> AgentDecision:
        """
        Synchronous market analysis for backward compatibility
        Falls back to traditional analysis if AI is not available
        """
        try:
            # Try to run async AI analysis in sync context
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in async context, use traditional analysis
                return self._traditional_market_analysis(market_data)
            else:
                # Run async analysis
                return loop.run_until_complete(self.analyze_market_with_ai(market_data))
        except Exception as e:
            self.logger.warning(f"AI analysis failed, using traditional: {e}")
            return self._traditional_market_analysis(market_data)


class PolicyEngine:
    """
    Main policy engine that manages different trading policies
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # AI configuration
        ai_config = {
            'enabled': config.get('ai_enabled', False),
            'orchestrator_url': config.get('orchestrator_url', 'http://localhost:8080'),
            'decision_weight': config.get('ai_decision_weight', 0.6),
            'timeout': config.get('ai_timeout', 8.0)
        }
        
        # Initialize policy
        risk_params = RiskParameters(
            max_position_size=config.get('max_position_size', 0.1),
            stop_loss_pct=config.get('stop_loss_pct', 0.02),
            take_profit_pct=config.get('take_profit_pct', 0.06)
        )
        
        self.policy = AIEnhancedPolicy(risk_params, ai_config)
        self.logger.info(f"PolicyEngine initialized with AI: {'ENABLED' if ai_config['enabled'] else 'DISABLED'}")
    
    async def get_trading_decision(self, market_data: MarketData) -> AgentDecision:
        """Get trading decision from the policy engine"""
        try:
            return await self.policy.analyze_market_with_ai(market_data)
        except Exception as e:
            self.logger.error(f"Policy engine error: {e}")
            # Fallback to traditional analysis
            return self.policy._traditional_market_analysis(market_data)
    
    def get_trading_decision_sync(self, market_data: MarketData) -> AgentDecision:
        """Synchronous version for backward compatibility"""
        return self.policy.analyze_market(market_data)
    
    def update_ai_config(self, ai_config: Dict[str, Any]):
        """Update AI configuration on the fly"""
        self.policy.ai_config.update(ai_config)
        self.policy.ai_enabled = ai_config.get('enabled', self.policy.ai_enabled)
        self.policy.orchestrator_url = ai_config.get('orchestrator_url', self.policy.orchestrator_url)
        self.policy.ai_weight = ai_config.get('decision_weight', self.policy.ai_weight)
        self.policy.ai_timeout = ai_config.get('timeout', self.policy.ai_timeout)
        
        self.logger.info(f"AI config updated: AI {'ENABLED' if self.policy.ai_enabled else 'DISABLED'}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get policy engine status"""
        return {
            'ai_enabled': self.policy.ai_enabled,
            'orchestrator_url': self.policy.orchestrator_url,
            'ai_weight': self.policy.ai_weight,
            'ai_timeout': self.policy.ai_timeout,
            'risk_params': {
                'max_position_size': self.policy.risk_params.max_position_size,
                'stop_loss_pct': self.policy.risk_params.stop_loss_pct,
                'take_profit_pct': self.policy.risk_params.take_profit_pct
            }
        }
        """
        Simulate LLM analysis of market conditions
        Returns a realistic trading decision
        """
        # Simulate market analysis with some randomness but logical patterns
        price_change = market_data.change_24h

        # Base decision logic on price movement and some randomness
        if price_change > 0.05:  # Strong positive movement
            template_idx = random.choice([0, 4])  # Favor buy decisions
            base_score = 0.7 + random.uniform(0, 0.2)
        elif price_change < -0.05:  # Strong negative movement
            template_idx = random.choice([1, 3])  # Favor sell decisions
            base_score = 0.6 + random.uniform(0, 0.3)
        else:  # Sideways movement
            template_idx = random.choice([2, 2, 0, 1])  # Favor hold
            base_score = 0.4 + random.uniform(0, 0.4)

        template = self.decision_templates[template_idx]

        # Calculate target prices based on risk parameters
        target_price = None
        stop_loss = None
        take_profit = None
        quantity = random.uniform(0.1, 0.5)  # Random quantity for simulation

        if template["action"] in ["MARKET_BUY", "LIMIT_BUY"]:
            stop_loss = market_data.price * (1 - self.risk_params.stop_loss_percent)
            take_profit = market_data.price * (1 + self.risk_params.take_profit_percent)
            if template["action"] == "LIMIT_BUY":
                target_price = market_data.price * 0.995  # Slightly below current price
        elif template["action"] in ["MARKET_SELL", "LIMIT_SELL"]:
            stop_loss = market_data.price * (1 + self.risk_params.stop_loss_percent)
            take_profit = market_data.price * (1 - self.risk_params.take_profit_percent)
            if template["action"] == "LIMIT_SELL":
                target_price = market_data.price * 1.005  # Slightly above current price

        return AgentDecision(
            score=min(1.0, base_score),
            rationale=template["rationale"],
            intent=template["intent"],  # type: ignore
            action=template["action"],  # type: ignore
            target_price=target_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            quantity=quantity,
        )

    def evaluate_risk(self, decision: AgentDecision, current_positions: list = None) -> bool:
        """
        Evaluate if the decision meets risk management criteria
        """
        current_positions = current_positions or []

        # Check position size limits
        if decision.quantity and decision.quantity > self.risk_params.max_position_size:
            return False

        # Check if we're not exceeding maximum number of positions
        if len(current_positions) > 3 and decision.action != "HOLD":
            return False

        return True

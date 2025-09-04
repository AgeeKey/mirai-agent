"""
Policy module for trading decisions
"""

import random

from .schema import AgentDecision, MarketData, RiskParameters


class MockLLMPolicy:
    """
    Mock LLM policy that simulates intelligent trading decisions
    Returns realistic JSON plan with score, rationale, intent, and action
    """

    def __init__(self, risk_params: RiskParameters = None):
        self.risk_params = risk_params or RiskParameters()
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

    def analyze_market(self, market_data: MarketData) -> AgentDecision:
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
            intent=template["intent"],
            action=template["action"],
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

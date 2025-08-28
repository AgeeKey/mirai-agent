"""
Main agent loop for trading decisions
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from .schema import AgentDecision, MarketData, RiskParameters
from .policy import MockLLMPolicy


logger = logging.getLogger(__name__)


class AgentLoop:
    """
    Main trading agent that orchestrates decision making and execution
    """
    
    def __init__(self, trading_client, risk_params: RiskParameters = None):
        self.trading_client = trading_client
        self.risk_params = risk_params or RiskParameters()
        self.policy = MockLLMPolicy(self.risk_params)
        self.positions = []
        self.decision_history = []
    
    def make_decision(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """
        Make a trading decision for the given symbol
        """
        logger.info(f"Making decision for {symbol}")
        
        try:
            # Get market data
            market_data_dict = self.trading_client.get_market_data(symbol)
            market_data = MarketData(
                symbol=symbol,
                price=float(market_data_dict.get('price', 0)),
                volume=float(market_data_dict.get('volume', 0)),
                change_24h=float(market_data_dict.get('change_24h', 0)),
                timestamp=datetime.utcnow()
            )
            
            # Get agent decision
            decision = self.policy.analyze_market(market_data)
            
            # Evaluate risk
            if not self.policy.evaluate_risk(decision, self.positions):
                logger.warning("Decision rejected due to risk constraints")
                decision = AgentDecision(
                    score=0.0,
                    rationale="Decision rejected due to risk management constraints",
                    intent="HOLD",
                    action="HOLD"
                )
            
            # Store decision in history
            decision_dict = decision.dict()
            decision_dict['timestamp'] = datetime.utcnow().isoformat()
            decision_dict['symbol'] = symbol
            self.decision_history.append(decision_dict)
            
            logger.info(f"Decision made: {decision.intent} - {decision.rationale}")
            return decision_dict
            
        except Exception as e:
            logger.error(f"Error making decision: {str(e)}")
            # Return safe default decision
            return {
                'score': 0.0,
                'rationale': f"Error in decision making: {str(e)}",
                'intent': 'HOLD',
                'action': 'HOLD',
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': symbol
            }
    
    def execute_action(self, decision: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        Execute the trading action based on the decision
        """
        logger.info(f"Executing action: {decision['action']} for {symbol}")
        
        try:
            action = decision['action']
            
            if action == 'HOLD':
                return {'status': 'success', 'message': 'No action taken - HOLD decision'}
            
            # Prepare order parameters
            order_params = {
                'symbol': symbol,
                'quantity': decision.get('quantity', 0.1),
                'side': 'BUY' if 'BUY' in action else 'SELL',
                'type': 'MARKET' if 'MARKET' in action else 'LIMIT'
            }
            
            if order_params['type'] == 'LIMIT':
                order_params['price'] = decision.get('target_price')
            
            # Add stop loss and take profit if available
            if decision.get('stop_loss'):
                order_params['stop_loss'] = decision['stop_loss']
            if decision.get('take_profit'):
                order_params['take_profit'] = decision['take_profit']
            
            # Execute the order
            result = self.trading_client.place_order(**order_params)
            
            logger.info(f"Order executed successfully: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing action: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Calculate performance metrics
        """
        if not self.decision_history:
            return {'total_decisions': 0, 'avg_score': 0.0}
        
        total_decisions = len(self.decision_history)
        avg_score = sum(d['score'] for d in self.decision_history) / total_decisions
        
        action_counts = {}
        for decision in self.decision_history:
            action = decision['action']
            action_counts[action] = action_counts.get(action, 0) + 1
        
        return {
            'total_decisions': total_decisions,
            'avg_score': avg_score,
            'action_distribution': action_counts,
            'latest_decision': self.decision_history[-1] if self.decision_history else None
        }
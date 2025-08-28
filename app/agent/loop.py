"""
Main agent loop for trading decisions
"""
import logging
import sys
import os
from typing import Optional, Dict, Any
from datetime import datetime, timezone

# Add the app directory to the Python path for CLI usage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from .schema import AgentDecision, MarketData, RiskParameters
from .policy import MockLLMPolicy

# Import risk engine with proper path handling
try:
    from ..trader.risk_engine import get_risk_engine
except ImportError:
    # Fallback for CLI usage
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    from trader.risk_engine import get_risk_engine


logger = logging.getLogger(__name__)


class AgentLoop:
    """
    Main trading agent that orchestrates decision making and execution
    """
    
    def __init__(self, trading_client, risk_params: RiskParameters = None, notifier=None):
        self.trading_client = trading_client
        self.risk_params = risk_params or RiskParameters()
        self.policy = MockLLMPolicy(self.risk_params)
        self.positions = []
        self.decision_history = []
        self.paused = False  # Pause/resume functionality
        self.notifier = notifier  # Optional Telegram notifier
    
    def make_decision(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """
        Make a trading decision for the given symbol
        """
        logger.info(f"Making decision for {symbol}")
        
        # Check if agent is paused
        if self.paused:
            logger.info("Agent is paused, returning HOLD decision")
            return {
                'score': 0.0,
                'rationale': 'Agent is paused',
                'intent': 'HOLD',
                'action': 'HOLD',
                'timestamp': datetime.utcnow().isoformat(),
                'symbol': symbol
            }
        
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
            
            # Check Risk Engine gates before proposing order
            if decision.action != "HOLD":
                risk_engine = get_risk_engine()
                now_utc = datetime.now(timezone.utc)
                
                # Get account state for position checking
                try:
                    account_info = self.trading_client.get_account_info()
                except Exception as e:
                    logger.warning(f"Could not get account info for risk check: {e}")
                    account_info = {}
                
                allowed, reason = risk_engine.allow_entry(now_utc, symbol, account_info)
                
                if not allowed:
                    logger.warning(f"Risk Engine rejected entry: {reason}")
                    # Notify about risk block
                    if self.notifier:
                        self.notifier.notify_risk_block(symbol, reason)
                    
                    decision = AgentDecision(
                        score=0.0,
                        rationale=f"Risk Engine rejection: {reason}",
                        intent="HOLD",
                        action="HOLD"
                    )
            
            # Evaluate risk (existing policy risk check)
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
            
            # Notify about new entry
            if self.notifier and action != 'HOLD':
                self.notifier.notify_entry(
                    symbol=symbol,
                    side=order_params['side'],
                    qty=order_params['quantity'],
                    sl=decision.get('stop_loss'),
                    tp=decision.get('take_profit'),
                    rationale=decision.get('rationale', 'No rationale provided')
                )
            
            # Record simulated fill in DRY_RUN mode for Risk Engine
            if hasattr(self.trading_client, 'dry_run') and self.trading_client.dry_run:
                risk_engine = get_risk_engine()
                now_utc = datetime.now(timezone.utc)
                
                # Mock PnL calculation for simulation
                mock_pnl = 0.0  # Default to breakeven
                if order_params['side'] == 'BUY':
                    # Simulate a small profit/loss randomly
                    import random
                    mock_pnl = random.uniform(-5.0, 10.0)  # -5 to +10 USDT
                else:
                    import random
                    mock_pnl = random.uniform(-5.0, 10.0)  # -5 to +10 USDT
                
                # Record the simulated fill
                risk_engine.record_fill(
                    ts=now_utc.isoformat(),
                    symbol=symbol,
                    side=order_params['side'],
                    qty=order_params['quantity'],
                    price=decision.get('target_price', 50000.0),  # Mock price
                    pnl=mock_pnl
                )
                
                logger.info(f"Recorded simulated fill: {symbol} {order_params['side']} {order_params['quantity']} PnL: {mock_pnl}")
                
                # Simulate SL/TP triggers for notification testing
                if self.notifier and (decision.get('stop_loss') or decision.get('take_profit')):
                    import random
                    if random.random() < 0.3:  # 30% chance to simulate trigger
                        trigger_type = "Stop Loss" if mock_pnl < 0 else "Take Profit"
                        trigger_price = decision.get('stop_loss', decision.get('take_profit', 50000.0))
                        self.notifier.notify_sl_tp_trigger(
                            symbol=symbol,
                            trigger_type=trigger_type,
                            price=trigger_price,
                            pnl=mock_pnl
                        )
            
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
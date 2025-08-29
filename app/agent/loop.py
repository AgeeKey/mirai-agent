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
from .advisor import get_signal_score
from .explain_logger import log_decision
from .config import load_advisor_config

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
        
        # Advisor state
        self.advisor_config = load_advisor_config()
        self.latest_advisor_result = None
        self.recovery_tries = 0  # Track recovery attempts after losses
        
        logger.info(f"AgentLoop initialized with advisor config: {self.advisor_config}")
    
    def _build_market_features(self, market_data: MarketData) -> Dict[str, Any]:
        """
        Build market features for advisor analysis
        
        Args:
            market_data: Current market data
            
        Returns:
            Dictionary of features for advisor
        """
        # Basic price and volume features
        features = {
            'price': market_data.price,
            'volume': market_data.volume,
            'change_24h': market_data.change_24h,
            'timestamp': market_data.timestamp.isoformat()
        }
        
        # Mock technical indicators (in real implementation, these would be calculated)
        # For now, we'll use safe mock values based on price and volume
        try:
            # Simple EMA approximation (use price + small random variation)
            import random
            features['ema'] = market_data.price * (1 + random.uniform(-0.01, 0.01))
            
            # Mock RSI (random but somewhat correlated with price change)
            if market_data.change_24h > 0.02:
                features['rsi'] = random.uniform(55, 75)  # Tend toward overbought
            elif market_data.change_24h < -0.02:
                features['rsi'] = random.uniform(25, 45)  # Tend toward oversold
            else:
                features['rsi'] = random.uniform(40, 60)  # Neutral
            
            # Mock ATR (percentage of price)
            features['atr'] = market_data.price * random.uniform(0.01, 0.04)
            
            # Mock ADX (trend strength)
            features['adx'] = random.uniform(15, 40)
            
            # Volume trend (simple comparison)
            features['volume_trend'] = 'increasing' if market_data.volume > 1000000 else 'decreasing'
            
        except Exception as e:
            logger.warning(f"Error building technical indicators: {e}")
            # Use safe defaults
            features.update({
                'ema': market_data.price,
                'rsi': 50.0,
                'atr': market_data.price * 0.02,
                'adx': 25.0,
                'volume_trend': 'neutral'
            })
        
        return features
    
    def _check_recovery_logic(self, advisor_score: float) -> tuple[bool, str]:
        """
        Check if recovery logic allows trade after consecutive losses
        
        Args:
            advisor_score: Current advisor score
            
        Returns:
            Tuple of (allowed, reason)
        """
        # Check if we have consecutive losses from risk engine
        try:
            risk_engine = get_risk_engine()
            now_utc = datetime.now(timezone.utc)
            day_state = risk_engine.get_day_state(now_utc)
            
            # If no consecutive losses, reset recovery tries and allow
            if day_state.consecutive_losses == 0:
                self.recovery_tries = 0
                return True, "no_consecutive_losses"
            
            # If we have consecutive losses, check recovery conditions
            if day_state.consecutive_losses > 0:
                # Check if we've exceeded max recovery tries
                if self.recovery_tries >= self.advisor_config['RECOVERY_MAX_TRIES']:
                    return False, f"recovery_max_tries_exceeded ({self.recovery_tries}/{self.advisor_config['RECOVERY_MAX_TRIES']})"
                
                # Check if score meets recovery threshold
                if advisor_score < self.advisor_config['RECOVERY_THRESHOLD']:
                    return False, f"recovery_score_too_low ({advisor_score:.3f} < {self.advisor_config['RECOVERY_THRESHOLD']})"
                
                # Recovery conditions met
                self.recovery_tries += 1
                return True, f"recovery_allowed ({self.recovery_tries}/{self.advisor_config['RECOVERY_MAX_TRIES']})"
            
        except Exception as e:
            logger.error(f"Error in recovery logic check: {e}")
            return True, "recovery_check_error"
        
        return True, "recovery_check_default"
    
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
            
            # Build features for advisor
            features = self._build_market_features(market_data)
            
            # Get advisor signal score
            advisor_result = get_signal_score(features)
            self.latest_advisor_result = advisor_result
            logger.info(f"Advisor result: score={advisor_result['score']}, action={advisor_result['action']}, strategy={advisor_result['strategy']}")
            
            # Get base agent decision from policy
            base_decision = self.policy.analyze_market(market_data)
            
            # Apply advisor gating logic
            decision_accepted = True
            deny_reason = None
            
            # Check if action is not HOLD (i.e., wants to trade)
            if base_decision.action != "HOLD":
                # Check advisor threshold
                if advisor_result['score'] < self.advisor_config['ADVISOR_THRESHOLD']:
                    decision_accepted = False
                    deny_reason = f"advisor_low_score ({advisor_result['score']:.3f} < {self.advisor_config['ADVISOR_THRESHOLD']})"
                else:
                    # Check recovery logic if we have consecutive losses
                    recovery_allowed, recovery_reason = self._check_recovery_logic(advisor_result['score'])
                    if not recovery_allowed:
                        decision_accepted = False
                        deny_reason = recovery_reason
            
            # Create final decision based on advisor gating
            if decision_accepted:
                # Use the base decision but incorporate advisor info
                final_decision = base_decision
                final_rationale = f"Advisor approved (score: {advisor_result['score']:.3f}): {advisor_result['rationale']}"
            else:
                # Override to HOLD due to advisor
                final_decision = AgentDecision(
                    score=advisor_result['score'],
                    rationale=f"Advisor denied: {deny_reason}. {advisor_result['rationale']}",
                    intent="HOLD",
                    action="HOLD"
                )
                final_rationale = final_decision.rationale
            
            # Log the decision for explainability
            log_decision(
                symbol=symbol,
                score=advisor_result['score'],
                action=advisor_result['action'],
                strategy=advisor_result['strategy'],
                rationale=advisor_result['rationale'],
                accepted=decision_accepted,
                deny_reason=deny_reason,
                final_action=final_decision.action,
                market_price=market_data.price
            )
            
            # Check Risk Engine gates before proposing order (only if advisor approved)
            if final_decision.action != "HOLD":
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
                    
                    final_decision = AgentDecision(
                        score=0.0,
                        rationale=f"Risk Engine rejection: {reason}",
                        intent="HOLD",
                        action="HOLD"
                    )
                    final_rationale = final_decision.rationale
            
            # Evaluate risk (existing policy risk check)
            if not self.policy.evaluate_risk(final_decision, self.positions):
                logger.warning("Decision rejected due to risk constraints")
                final_decision = AgentDecision(
                    score=0.0,
                    rationale="Decision rejected due to risk management constraints",
                    intent="HOLD",
                    action="HOLD"
                )
                final_rationale = final_decision.rationale
            
            # Store decision in history with advisor info
            decision_dict = final_decision.dict()
            decision_dict['timestamp'] = datetime.utcnow().isoformat()
            decision_dict['symbol'] = symbol
            decision_dict['advisor_score'] = advisor_result['score']
            decision_dict['advisor_rationale'] = advisor_result['rationale']
            decision_dict['advisor_strategy'] = advisor_result['strategy']
            decision_dict['advisor_action'] = advisor_result['action']
            self.decision_history.append(decision_dict)
            
            logger.info(f"Decision made: {final_decision.intent} - {final_rationale}")
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
                'symbol': symbol,
                'advisor_score': 0.0,
                'advisor_rationale': 'Error occurred',
                'advisor_strategy': 'error',
                'advisor_action': 'HOLD'
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
                'order_type': 'MARKET' if 'MARKET' in action else 'LIMIT'
            }
            
            if order_params['order_type'] == 'LIMIT':
                order_params['price'] = decision.get('target_price')
            
            # Add stop loss and take profit if available
            if decision.get('stop_loss'):
                order_params['stop_loss'] = decision['stop_loss']
            if decision.get('take_profit'):
                order_params['take_profit'] = decision['take_profit']
            
            # Execute the order
            result = self.trading_client.place_order(**order_params)
            
            # Notify about new entry with advisor info
            if self.notifier and action != 'HOLD':
                # Include advisor rationale in notification
                advisor_info = ""
                if 'advisor_score' in decision:
                    advisor_info = f" (Advisor: {decision['advisor_score']:.2f} - {decision.get('advisor_rationale', '')[:50]})"
                
                enhanced_rationale = decision.get('rationale', 'No rationale provided') + advisor_info
                
                self.notifier.notify_entry(
                    symbol=symbol,
                    side=order_params['side'],
                    qty=order_params['quantity'],
                    sl=decision.get('stop_loss'),
                    tp=decision.get('take_profit'),
                    rationale=enhanced_rationale
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
            return {
                'total_decisions': 0, 
                'avg_score': 0.0,
                'advisor_score': 0.0,
                'advisor_rationale': 'No decisions yet',
                'advisor_strategy': 'none',
                'advisor_action': 'HOLD'
            }
        
        total_decisions = len(self.decision_history)
        avg_score = sum(d['score'] for d in self.decision_history) / total_decisions
        
        action_counts = {}
        for decision in self.decision_history:
            action = decision['action']
            action_counts[action] = action_counts.get(action, 0) + 1
        
        # Get latest advisor info
        latest_decision = self.decision_history[-1]
        
        return {
            'total_decisions': total_decisions,
            'avg_score': avg_score,
            'action_distribution': action_counts,
            'latest_decision': latest_decision,
            'advisor_score': latest_decision.get('advisor_score', 0.0),
            'advisor_rationale': latest_decision.get('advisor_rationale', 'No advisor data'),
            'advisor_strategy': latest_decision.get('advisor_strategy', 'none'),
            'advisor_action': latest_decision.get('advisor_action', 'HOLD'),
            'recovery_tries': self.recovery_tries
        }
    
    def get_advisor_state(self) -> Dict[str, Any]:
        """
        Get current advisor state for status endpoints
        
        Returns:
            Dictionary with current advisor state
        """
        if self.latest_advisor_result:
            return {
                'score': self.latest_advisor_result['score'],
                'rationale': self.latest_advisor_result['rationale'],
                'strategy': self.latest_advisor_result['strategy'],
                'action': self.latest_advisor_result['action'],
                'recovery_tries': self.recovery_tries,
                'recovery_max_tries': self.advisor_config['RECOVERY_MAX_TRIES'],
                'advisor_threshold': self.advisor_config['ADVISOR_THRESHOLD'],
                'recovery_threshold': self.advisor_config['RECOVERY_THRESHOLD']
            }
        else:
            return {
                'score': 0.0,
                'rationale': 'No advisor analysis yet',
                'strategy': 'none',
                'action': 'HOLD',
                'recovery_tries': self.recovery_tries,
                'recovery_max_tries': self.advisor_config['RECOVERY_MAX_TRIES'],
                'advisor_threshold': self.advisor_config['ADVISOR_THRESHOLD'],
                'recovery_threshold': self.advisor_config['RECOVERY_THRESHOLD']
            }
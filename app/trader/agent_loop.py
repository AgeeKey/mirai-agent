"""
Enhanced Agent Loop with AI Integration
Autonomous trading with SuperAGI and AutoGPT integration for intelligent decision making
"""

import asyncio
import os
import sys
import time
import logging
import json
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from decimal import Decimal

# Path resolution for CLI/package compatibility
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import trading components
try:
    from .async_loop import AsyncTradingLoop, TradingSignal, TradingState, LoopMetrics
    from .risk_engine import RiskEngine
    from .binance_client import BinanceClient
    from ..agent.advisor import TradingAdvisor
    from ..agent.policy import PolicyEngine
except ImportError:
    from async_loop import AsyncTradingLoop, TradingSignal, TradingState, LoopMetrics
    from risk_engine import RiskEngine
    from binance_client import BinanceClient
    try:
        from agent.advisor import TradingAdvisor
        from agent.policy import PolicyEngine
    except ImportError:
        # Mock for development
        class TradingAdvisor:
            pass
        class PolicyEngine:
            pass


class AITaskType(Enum):
    """AI task types for the orchestrator"""
    MARKET_ANALYSIS = "market_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    TREND_PREDICTION = "trend_prediction"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    SIGNAL_VALIDATION = "signal_validation"


@dataclass
class AIRecommendation:
    """AI recommendation from the orchestrator"""
    task_id: str
    task_type: AITaskType
    symbol: str
    action: str  # 'buy', 'sell', 'hold'
    confidence: float
    reasoning: str
    risk_score: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    position_size: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AIIntegratedTradingLoop(AsyncTradingLoop):
    """
    Enhanced trading loop with AI integration through Orchestrator service
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # AI configuration
        self.ai_enabled = config.get('ai_enabled', os.getenv('AI_ENABLED', 'false').lower() == 'true')
        self.orchestrator_url = config.get('orchestrator_url', 'http://localhost:8080')
        self.ai_decision_weight = config.get('ai_decision_weight', 0.7)  # Weight of AI vs traditional signals
        self.ai_timeout = config.get('ai_timeout', 10.0)  # Timeout for AI requests
        
        # AI session management
        self.ai_session: Optional[aiohttp.ClientSession] = None
        self.ai_health_check_interval = config.get('ai_health_check_interval', 30.0)
        self.last_ai_health_check = datetime.min
        
        # AI recommendations tracking
        self.ai_recommendations: List[AIRecommendation] = []
        self.ai_recommendation_queue: asyncio.Queue = asyncio.Queue(maxsize=50)
        
        # Traditional components
        self.trading_advisor: Optional[TradingAdvisor] = None
        self.policy_engine: Optional[PolicyEngine] = None
        
        self.logger.info(f"AI Integration: {'ENABLED' if self.ai_enabled else 'DISABLED'}")
    
    async def initialize(self):
        """Initialize enhanced components including AI"""
        await super().initialize()
        
        # Initialize AI session
        if self.ai_enabled:
            await self._initialize_ai_session()
            await self._verify_ai_connectivity()
        
        # Initialize traditional components
        await self._initialize_traditional_components()
        
        # Start AI background tasks
        if self.ai_enabled:
            await self._start_ai_background_tasks()
    
    async def _initialize_ai_session(self):
        """Initialize AI orchestrator connection"""
        try:
            self.ai_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.ai_timeout),
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mirai-Agent-AI/1.0'
                }
            )
            
            self.logger.info("AI session initialized")
        
        except Exception as e:
            self.logger.error(f"AI session initialization failed: {e}")
            self.ai_enabled = False
    
    async def _verify_ai_connectivity(self) -> bool:
        """Verify AI orchestrator is available"""
        try:
            if not self.ai_session:
                return False
            
            async with self.ai_session.get(f"{self.orchestrator_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    self.logger.info(f"AI Orchestrator health: {health_data}")
                    return True
                else:
                    self.logger.warning(f"AI health check failed: {response.status}")
                    return False
        
        except Exception as e:
            self.logger.error(f"AI connectivity check failed: {e}")
            return False
    
    async def _initialize_traditional_components(self):
        """Initialize traditional trading components"""
        try:
            # Initialize advisor
            self.trading_advisor = TradingAdvisor(self.config)
            
            # Initialize policy engine
            self.policy_engine = PolicyEngine(self.config)
            
            self.logger.info("Traditional trading components initialized")
        
        except Exception as e:
            self.logger.warning(f"Traditional components initialization failed: {e}")
    
    async def _start_ai_background_tasks(self):
        """Start AI-specific background tasks"""
        if not self.ai_enabled:
            return
        
        # AI recommendation processing task
        ai_task = asyncio.create_task(self._process_ai_recommendations_continuously())
        self.background_tasks.append(ai_task)
        
        # AI health monitoring task
        health_task = asyncio.create_task(self._monitor_ai_health_continuously())
        self.background_tasks.append(health_task)
        
        self.logger.info("AI background tasks started")
    
    async def _submit_ai_task(self, task_type: AITaskType, symbol: str, 
                             market_data: Dict[str, Any]) -> Optional[str]:
        """Submit task to AI orchestrator"""
        if not self.ai_enabled or not self.ai_session:
            return None
        
        try:
            task_data = {
                "type": task_type.value,
                "symbol": symbol,
                "market_data": market_data,
                "goal": f"Provide {task_type.value} for {symbol}",
                "dry_run": self.dry_run,
                "timestamp": datetime.now().isoformat()
            }
            
            async with self.ai_session.post(
                f"{self.orchestrator_url}/task/submit",
                json=task_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    task_id = result.get('task_id')
                    self.logger.debug(f"AI task submitted: {task_id} for {symbol}")
                    return task_id
                else:
                    self.logger.warning(f"AI task submission failed: {response.status}")
                    return None
        
        except Exception as e:
            self.logger.error(f"AI task submission error: {e}")
            return None
    
    async def _get_ai_task_result(self, task_id: str) -> Optional[AIRecommendation]:
        """Get AI task result from orchestrator"""
        if not self.ai_enabled or not self.ai_session:
            return None
        
        try:
            async with self.ai_session.get(
                f"{self.orchestrator_url}/task/{task_id}/result"
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Parse AI recommendation
                    if result.get('status') == 'completed' and 'recommendation' in result:
                        rec_data = result['recommendation']
                        
                        recommendation = AIRecommendation(
                            task_id=task_id,
                            task_type=AITaskType(result.get('task_type', 'market_analysis')),
                            symbol=rec_data.get('symbol', ''),
                            action=rec_data.get('action', 'hold'),
                            confidence=float(rec_data.get('confidence', 0.0)),
                            reasoning=rec_data.get('reasoning', ''),
                            risk_score=float(rec_data.get('risk_score', 0.5)),
                            target_price=rec_data.get('target_price'),
                            stop_loss=rec_data.get('stop_loss'),
                            position_size=rec_data.get('position_size')
                        )
                        
                        return recommendation
                
                elif response.status == 202:
                    # Task still processing
                    return None
                else:
                    self.logger.warning(f"AI task result fetch failed: {response.status}")
                    return None
        
        except Exception as e:
            self.logger.error(f"AI task result error: {e}")
            return None
    
    async def _process_ai_recommendations_continuously(self):
        """Background task to process AI recommendations"""
        pending_tasks = {}  # task_id -> (symbol, submission_time)
        
        while self.state != TradingState.STOPPED:
            try:
                # Check pending tasks for results
                completed_tasks = []
                
                for task_id, (symbol, submission_time) in pending_tasks.items():
                    # Timeout check
                    if datetime.now() - submission_time > timedelta(seconds=self.ai_timeout):
                        self.logger.warning(f"AI task {task_id} timed out")
                        completed_tasks.append(task_id)
                        continue
                    
                    # Check for completion
                    recommendation = await self._get_ai_task_result(task_id)
                    if recommendation:
                        # Add to processing queue
                        try:
                            await self.ai_recommendation_queue.put_nowait(recommendation)
                            self.logger.info(f"AI recommendation received: {recommendation.action} for {recommendation.symbol}")
                        except asyncio.QueueFull:
                            self.logger.warning("AI recommendation queue full")
                        
                        completed_tasks.append(task_id)
                
                # Remove completed tasks
                for task_id in completed_tasks:
                    del pending_tasks[task_id]
                
                await asyncio.sleep(1.0)
            
            except Exception as e:
                self.logger.error(f"AI recommendation processing error: {e}")
                await asyncio.sleep(5.0)
    
    async def _monitor_ai_health_continuously(self):
        """Background task to monitor AI system health"""
        while self.state != TradingState.STOPPED:
            try:
                current_time = datetime.now()
                
                if (current_time - self.last_ai_health_check).total_seconds() >= self.ai_health_check_interval:
                    ai_healthy = await self._verify_ai_connectivity()
                    
                    if not ai_healthy and self.ai_enabled:
                        self.logger.warning("AI system unhealthy - disabling AI mode temporarily")
                        # Don't permanently disable, just skip AI for this cycle
                    
                    self.last_ai_health_check = current_time
                
                await asyncio.sleep(self.ai_health_check_interval / 2)
            
            except Exception as e:
                self.logger.error(f"AI health monitoring error: {e}")
                await asyncio.sleep(10.0)
    
    async def _enhanced_main_loop_iteration(self) -> Dict[str, Any]:
        """Enhanced main loop iteration with AI integration"""
        iteration_start = time.time()
        results = {
            "ai_enabled": self.ai_enabled,
            "signals_generated": 0,
            "ai_recommendations": 0,
            "decisions_made": 0,
            "errors": []
        }
        
        try:
            symbols = self.config.get('symbols', ['BTCUSDT', 'ETHUSDT'])
            
            for symbol in symbols:
                try:
                    # Step 1: Collect market data
                    market_data = await self._collect_market_data(symbol)
                    
                    # Step 2: Generate traditional signals
                    traditional_signals = await self._generate_traditional_signals(symbol, market_data)
                    
                    # Step 3: Get AI recommendations (if enabled)
                    ai_recommendations = []
                    if self.ai_enabled:
                        ai_recommendations = await self._get_ai_recommendations_for_symbol(symbol, market_data)
                    
                    # Step 4: Combine signals and make trading decision
                    final_decision = await self._make_enhanced_trading_decision(
                        symbol, traditional_signals, ai_recommendations, market_data
                    )
                    
                    # Step 5: Execute decision
                    if final_decision and final_decision.action != 'hold':
                        await self._execute_enhanced_trading_decision(final_decision)
                        results["decisions_made"] += 1
                    
                    results["signals_generated"] += len(traditional_signals)
                    results["ai_recommendations"] += len(ai_recommendations)
                
                except Exception as e:
                    error_msg = f"Error processing {symbol}: {e}"
                    self.logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            # Update metrics
            self.metrics.loop_count += 1
            loop_time = time.time() - iteration_start
            self.metrics.last_loop_time = loop_time
            
            # Update average
            if self.metrics.loop_count > 1:
                self.metrics.avg_loop_time = (
                    (self.metrics.avg_loop_time * (self.metrics.loop_count - 1) + loop_time) / 
                    self.metrics.loop_count
                )
            else:
                self.metrics.avg_loop_time = loop_time
            
            results["loop_time"] = loop_time
            results["loop_count"] = self.metrics.loop_count
            
        except Exception as e:
            error_msg = f"Main loop iteration error: {e}"
            self.logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    async def _generate_traditional_signals(self, symbol: str, market_data: Dict[str, Any]) -> List[TradingSignal]:
        """Generate traditional trading signals"""
        signals = []
        
        try:
            # Use traditional advisor if available
            if self.trading_advisor:
                advisor_signals = await self._get_advisor_signals(symbol, market_data)
                signals.extend(advisor_signals)
            
            # Simple momentum signal as fallback
            if not signals:
                price_data = market_data.get('price_data', {})
                current_price = price_data.get('close')
                
                if current_price:
                    signal = TradingSignal(
                        symbol=symbol,
                        action='hold',  # Default conservative action
                        strength=0.5,
                        price=Decimal(str(current_price)),
                        strategy='momentum_fallback',
                        confidence=0.3
                    )
                    signals.append(signal)
        
        except Exception as e:
            self.logger.error(f"Traditional signal generation error for {symbol}: {e}")
        
        return signals
    
    async def _get_ai_recommendations_for_symbol(self, symbol: str, market_data: Dict[str, Any]) -> List[AIRecommendation]:
        """Get AI recommendations for a specific symbol"""
        recommendations = []
        
        if not self.ai_enabled:
            return recommendations
        
        try:
            # Check for pending recommendations in queue
            while not self.ai_recommendation_queue.empty():
                try:
                    rec = self.ai_recommendation_queue.get_nowait()
                    if rec.symbol == symbol:
                        recommendations.append(rec)
                    else:
                        # Put back if different symbol
                        await self.ai_recommendation_queue.put_nowait(rec)
                except asyncio.QueueEmpty:
                    break
            
            # Submit new AI analysis task (non-blocking)
            await self._submit_ai_task(AITaskType.MARKET_ANALYSIS, symbol, market_data)
        
        except Exception as e:
            self.logger.error(f"AI recommendation error for {symbol}: {e}")
        
        return recommendations
    
    async def _make_enhanced_trading_decision(self, symbol: str, traditional_signals: List[TradingSignal], 
                                           ai_recommendations: List[AIRecommendation], 
                                           market_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """Make enhanced trading decision combining traditional and AI signals"""
        
        try:
            # If no signals, return hold
            if not traditional_signals and not ai_recommendations:
                return TradingSignal(
                    symbol=symbol,
                    action='hold',
                    strength=0.0,
                    strategy='no_signals'
                )
            
            # Calculate weighted decision
            traditional_weight = 1.0 - self.ai_decision_weight if self.ai_enabled else 1.0
            ai_weight = self.ai_decision_weight if self.ai_enabled else 0.0
            
            # Aggregate traditional signals
            traditional_score = 0.0
            traditional_action = 'hold'
            
            if traditional_signals:
                buy_strength = sum(s.strength for s in traditional_signals if s.action == 'buy')
                sell_strength = sum(s.strength for s in traditional_signals if s.action == 'sell')
                
                if buy_strength > sell_strength:
                    traditional_action = 'buy'
                    traditional_score = buy_strength / len(traditional_signals)
                elif sell_strength > buy_strength:
                    traditional_action = 'sell'
                    traditional_score = sell_strength / len(traditional_signals)
            
            # Aggregate AI recommendations
            ai_score = 0.0
            ai_action = 'hold'
            
            if ai_recommendations:
                # Use highest confidence recommendation
                best_rec = max(ai_recommendations, key=lambda r: r.confidence)
                ai_action = best_rec.action
                ai_score = best_rec.confidence
            
            # Combine decisions
            final_action = 'hold'
            final_strength = 0.0
            final_confidence = 0.0
            
            if ai_recommendations and traditional_signals:
                # Both available - use weighted combination
                traditional_numeric = 1 if traditional_action == 'buy' else (-1 if traditional_action == 'sell' else 0)
                ai_numeric = 1 if ai_action == 'buy' else (-1 if ai_action == 'sell' else 0)
                
                combined_score = (traditional_numeric * traditional_score * traditional_weight + 
                                 ai_numeric * ai_score * ai_weight)
                
                if combined_score > 0.3:
                    final_action = 'buy'
                    final_strength = min(combined_score, 1.0)
                elif combined_score < -0.3:
                    final_action = 'sell'
                    final_strength = min(abs(combined_score), 1.0)
                
                final_confidence = (traditional_score * traditional_weight + ai_score * ai_weight)
            
            elif ai_recommendations:
                # AI only
                final_action = ai_action
                final_strength = ai_score
                final_confidence = ai_score
            
            elif traditional_signals:
                # Traditional only
                final_action = traditional_action
                final_strength = traditional_score
                final_confidence = traditional_score * 0.8  # Slightly lower confidence without AI
            
            # Create final decision
            final_signal = TradingSignal(
                symbol=symbol,
                action=final_action,
                strength=final_strength,
                strategy='ai_enhanced' if ai_recommendations else 'traditional',
                confidence=final_confidence,
                metadata={
                    'traditional_signals': len(traditional_signals),
                    'ai_recommendations': len(ai_recommendations),
                    'ai_enabled': self.ai_enabled
                }
            )
            
            self.logger.debug(f"Enhanced decision for {symbol}: {final_action} (strength={final_strength:.3f}, confidence={final_confidence:.3f})")
            
            return final_signal
        
        except Exception as e:
            self.logger.error(f"Enhanced decision making error for {symbol}: {e}")
            return None
    
    async def _execute_enhanced_trading_decision(self, decision: TradingSignal):
        """Execute enhanced trading decision with risk management"""
        try:
            # Apply risk management
            if hasattr(self, 'risk_manager') and self.risk_manager:
                risk_check = await self._apply_risk_management(decision)
                if not risk_check:
                    self.logger.info(f"Trade blocked by risk management: {decision.symbol} {decision.action}")
                    return
            
            # Execute trade
            if self.dry_run:
                self.logger.info(f"DRY RUN: Would execute {decision.action} for {decision.symbol} (strength={decision.strength:.3f})")
                self.metrics.orders_placed += 1
            else:
                # Real execution would go here
                self.logger.info(f"LIVE: Executing {decision.action} for {decision.symbol}")
                self.metrics.orders_placed += 1
        
        except Exception as e:
            self.logger.error(f"Trade execution error: {e}")
            self.metrics.errors_count += 1
    
    async def _apply_risk_management(self, decision: TradingSignal) -> bool:
        """Apply risk management rules"""
        try:
            # Basic risk checks
            if decision.confidence < 0.5:
                self.logger.debug(f"Low confidence trade rejected: {decision.confidence}")
                return False
            
            # Add more risk management logic here
            return True
        
        except Exception as e:
            self.logger.error(f"Risk management error: {e}")
            return False
    
    async def _collect_market_data(self, symbol: str) -> Dict[str, Any]:
        """Collect market data for symbol"""
        # Mock implementation - replace with real data collection
        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'price_data': {
                'close': 50000.0,  # Mock price
                'volume': 1000000
            }
        }
    
    async def _get_advisor_signals(self, symbol: str, market_data: Dict[str, Any]) -> List[TradingSignal]:
        """Get signals from traditional advisor"""
        # Mock implementation
        return []
    
    async def start(self):
        """Start the enhanced trading loop"""
        if self.state != TradingState.STOPPED:
            self.logger.warning("Trading loop is already running or starting")
            return
        
        self.state = TradingState.STARTING
        self.logger.info("Starting enhanced AI trading loop...")
        
        try:
            # Initialize components
            await self.initialize()
            
            # Start main loop
            self.state = TradingState.RUNNING
            
            while self.state == TradingState.RUNNING:
                try:
                    # Check for pause
                    if self.state == TradingState.PAUSING:
                        self.state = TradingState.PAUSED
                        await self.pause_event.wait()
                        self.state = TradingState.RUNNING
                        continue
                    
                    # Execute main loop iteration
                    results = await self._enhanced_main_loop_iteration()
                    
                    # Log iteration results
                    self.logger.debug(f"Loop iteration completed: {results}")
                    
                    # Wait for next iteration
                    await asyncio.sleep(self.loop_interval)
                
                except Exception as e:
                    self.logger.error(f"Loop iteration error: {e}")
                    self.metrics.errors_count += 1
                    await asyncio.sleep(5.0)  # Error recovery delay
        
        except Exception as e:
            self.logger.error(f"Trading loop failed: {e}")
            self.state = TradingState.ERROR
            raise
        
        finally:
            await self.cleanup()
    
    async def stop(self):
        """Stop the enhanced trading loop"""
        self.logger.info("Stopping enhanced trading loop...")
        self.state = TradingState.STOPPING
        
        # Cancel background tasks
        for task in self.background_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        self.state = TradingState.STOPPED
        self.logger.info("Enhanced trading loop stopped")
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Close AI session
            if self.ai_session:
                await self.ai_session.close()
                self.ai_session = None
            
            # Cleanup parent resources
            await super().cleanup() if hasattr(super(), 'cleanup') else None
            
            self.logger.info("Enhanced trading loop cleanup completed")
        
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get enhanced status information"""
        status = {
            'state': self.state.value,
            'ai_enabled': self.ai_enabled,
            'orchestrator_url': self.orchestrator_url if self.ai_enabled else None,
            'metrics': asdict(self.metrics),
            'ai_recommendations_pending': self.ai_recommendation_queue.qsize(),
            'last_ai_health_check': self.last_ai_health_check.isoformat() if self.last_ai_health_check != datetime.min else None,
            'background_tasks': len(self.background_tasks),
            'dry_run': self.dry_run
        }
        
        return status


# Factory function
def create_enhanced_trading_loop(config: Dict[str, Any]) -> AIIntegratedTradingLoop:
    """Create and return enhanced trading loop instance"""
    return AIIntegratedTradingLoop(config)


# CLI entry point for testing
async def main():
    """Test the enhanced trading loop"""
    config = {
        'dry_run': True,
        'ai_enabled': True,
        'orchestrator_url': 'http://localhost:8080',
        'symbols': ['BTCUSDT', 'ETHUSDT'],
        'loop_interval': 5.0
    }
    
    loop = create_enhanced_trading_loop(config)
    
    try:
        await loop.start()
    except KeyboardInterrupt:
        print("Stopping trading loop...")
        await loop.stop()


if __name__ == "__main__":
    asyncio.run(main())
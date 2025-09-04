"""
Pydantic schemas for the trading agent
"""

from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class MarketData(BaseModel):
    """Market data structure"""

    symbol: str
    price: float
    volume: float
    change_24h: float
    timestamp: datetime


class AgentDecision(BaseModel):
    """Agent decision output schema"""

    score: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")
    rationale: str = Field(..., description="Reasoning behind the decision")
    intent: Literal["BUY", "SELL", "HOLD"] = Field(..., description="Trading intent")
    action: Literal["MARKET_BUY", "MARKET_SELL", "LIMIT_BUY", "LIMIT_SELL", "HOLD"] = Field(
        ..., description="Specific action to take"
    )
    target_price: float | None = Field(None, description="Target price for limit orders")
    stop_loss: float | None = Field(None, description="Stop loss price")
    take_profit: float | None = Field(None, description="Take profit price")
    quantity: float | None = Field(None, description="Trade quantity")

    model_config = ConfigDict(extra="forbid")


class RiskParameters(BaseModel):
    """Risk management parameters"""

    max_position_size: float = Field(default=1000.0, gt=0)
    max_drawdown: float = Field(default=0.05, gt=0, le=1)
    stop_loss_percent: float = Field(default=0.02, gt=0, le=1)
    take_profit_percent: float = Field(default=0.04, gt=0, le=1)

    model_config = ConfigDict(extra="forbid")


class TradingSignal(BaseModel):
    """Trading signal from technical analysis"""

    signal_type: Literal["BUY", "SELL", "HOLD"]
    strength: float = Field(..., ge=0, le=1)
    indicators: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Position(BaseModel):
    """Trading position"""

    symbol: str
    side: Literal["LONG", "SHORT"]
    size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @property
    def pnl_percent(self) -> float:
        """Calculate PnL percentage"""
        if self.side == "LONG":
            return (self.current_price - self.entry_price) / self.entry_price
        else:
            return (self.entry_price - self.current_price) / self.entry_price

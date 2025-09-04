"""
Risk Engine for trading risk management and position sizing validation
"""

import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class DayState:
    """Daily trading state"""

    date_utc: str
    day_pnl: float
    max_day_pnl: float
    trades_today: int
    consecutive_losses: int
    cooldown_until: str | None = None


class RiskEngine:
    """
    Risk Engine for managing trading risk and enforcing gates
    """

    def __init__(self, config_path: str = "configs/risk.yaml", db_path: str = "state/mirai.db"):
        self.config_path = Path(config_path)
        self.db_path = Path(db_path)
        self.config = self._load_config()
        self._init_database()

    def _load_config(self) -> dict[str, Any]:
        """Load risk configuration from YAML file"""
        try:
            with open(self.config_path) as f:
                config = yaml.safe_load(f)
                return config.get("risk_engine", {})
        except Exception as e:
            logger.warning(f"Failed to load risk config: {e}. Using defaults.")
            return {
                "DAILY_MAX_LOSS": -30,
                "DAILY_TRAIL_DRAWDOWN": 20,
                "MAX_TRADES_PER_DAY": 6,
                "MAX_CONSECUTIVE_LOSSES": 3,
                "COOLDOWN_MINUTES": 15,
                "ONE_POSITION_PER_SYMBOL": True,
            }

    def _init_database(self):
        """Initialize SQLite database with required tables"""
        # Ensure state directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create day_state table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS day_state (
                    date_utc TEXT PRIMARY KEY,
                    day_pnl REAL NOT NULL DEFAULT 0.0,
                    max_day_pnl REAL NOT NULL DEFAULT 0.0,
                    trades_today INTEGER NOT NULL DEFAULT 0,
                    consecutive_losses INTEGER NOT NULL DEFAULT 0,
                    cooldown_until TEXT NULL
                )
            """
            )

            # Create fills table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS fills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    qty REAL NOT NULL,
                    price REAL NOT NULL,
                    pnl REAL NOT NULL
                )
            """
            )

            conn.commit()

    def get_day_state(self, now_utc: datetime) -> DayState:
        """
        Get daily state, rolling over to new day if needed
        """
        date_str = now_utc.strftime("%Y-%m-%d")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Try to get existing day state
            cursor.execute(
                (
                    "SELECT date_utc, day_pnl, max_day_pnl, trades_today, "
                    "consecutive_losses, cooldown_until "
                    "FROM day_state WHERE date_utc = ?"
                ),
                (date_str,),
            )
            row = cursor.fetchone()

            if row:
                return DayState(*row)
            else:
                # Create new day state
                new_state = DayState(
                    date_utc=date_str,
                    day_pnl=0.0,
                    max_day_pnl=0.0,
                    trades_today=0,
                    consecutive_losses=0,
                    cooldown_until=None,
                )

                cursor.execute(
                    (
                        "INSERT INTO day_state "
                        "(date_utc, day_pnl, max_day_pnl, trades_today, "
                        "consecutive_losses, cooldown_until) "
                        "VALUES (?, ?, ?, ?, ?, ?)"
                    ),
                    (
                        new_state.date_utc,
                        new_state.day_pnl,
                        new_state.max_day_pnl,
                        new_state.trades_today,
                        new_state.consecutive_losses,
                        new_state.cooldown_until,
                    ),
                )
                conn.commit()

                return new_state

    def allow_entry(self, now_utc: datetime, symbol: str, account_state: dict[str, Any] = None) -> tuple[bool, str]:
        """
        Check if entry is allowed based on risk gates
        Returns (allowed, reason)
        """
        day_state = self.get_day_state(now_utc)
        account_state = account_state or {}

        # Gate a) Stop-day by DAILY_MAX_LOSS
        if day_state.day_pnl <= self.config["DAILY_MAX_LOSS"]:
            return (
                False,
                f"Daily max loss reached: {day_state.day_pnl} <= {self.config['DAILY_MAX_LOSS']}",
            )

        # Gate b) Daily trail drawdown
        if day_state.max_day_pnl - day_state.day_pnl >= self.config["DAILY_TRAIL_DRAWDOWN"]:
            return (
                False,
                (
                    "Daily trail drawdown exceeded: "
                    f"{day_state.max_day_pnl - day_state.day_pnl} >= {self.config['DAILY_TRAIL_DRAWDOWN']}"
                ),
            )

        # Gate c) Trade limit
        if day_state.trades_today >= self.config["MAX_TRADES_PER_DAY"]:
            return (
                False,
                ("Max trades per day reached: " f"{day_state.trades_today} >= {self.config['MAX_TRADES_PER_DAY']}"),
            )

        # Gate d) Consecutive losses + cooldown
        if day_state.consecutive_losses >= self.config["MAX_CONSECUTIVE_LOSSES"]:
            if day_state.cooldown_until:
                cooldown_time = datetime.fromisoformat(day_state.cooldown_until)
                if now_utc < cooldown_time:
                    return (
                        False,
                        (
                            "In cooldown until "
                            f"{day_state.cooldown_until} after {day_state.consecutive_losses} consecutive losses"
                        ),
                    )

        # Gate e) One position per symbol
        if self.config["ONE_POSITION_PER_SYMBOL"]:
            if self._has_open_position(symbol, account_state):
                return False, f"Position already open for symbol {symbol}"

        return True, "Entry allowed"

    def _has_open_position(self, symbol: str, account_state: dict[str, Any]) -> bool:
        """Check if there's already an open position for the symbol"""
        # Check account state for open positions
        positions = account_state.get("positions", [])
        for position in positions:
            if position.get("symbol") == symbol and float(position.get("size", 0)) != 0:
                return True
        return False

    def record_fill(self, ts: str, symbol: str, side: str, qty: float, price: float, pnl: float):
        """
        Record a fill and update day state accordingly
        """
        # Parse timestamp
        if isinstance(ts, str):
            fill_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        else:
            fill_time = ts

        date_str = fill_time.strftime("%Y-%m-%d")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Insert fill record
            cursor.execute(
                """
                INSERT INTO fills (ts, symbol, side, qty, price, pnl)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (ts, symbol, side, qty, price, pnl),
            )

            # Get or create day state within same transaction
            cursor.execute(
                "SELECT date_utc, day_pnl, max_day_pnl, trades_today, consecutive_losses, cooldown_until "
                "FROM day_state WHERE date_utc = ?",
                (date_str,),
            )
            row = cursor.fetchone()

            if row:
                day_state = DayState(*row)
            else:
                # Create new day state
                day_state = DayState(
                    date_utc=date_str,
                    day_pnl=0.0,
                    max_day_pnl=0.0,
                    trades_today=0,
                    consecutive_losses=0,
                    cooldown_until=None,
                )

                cursor.execute(
                    (
                        "INSERT INTO day_state "
                        "(date_utc, day_pnl, max_day_pnl, trades_today, "
                        "consecutive_losses, cooldown_until) "
                        "VALUES (?, ?, ?, ?, ?, ?)"
                    ),
                    (
                        day_state.date_utc,
                        day_state.day_pnl,
                        day_state.max_day_pnl,
                        day_state.trades_today,
                        day_state.consecutive_losses,
                        day_state.cooldown_until,
                    ),
                )

            # Update day PnL
            new_day_pnl = day_state.day_pnl + pnl

            # Update max day PnL if it increased
            new_max_day_pnl = max(day_state.max_day_pnl, new_day_pnl)

            # Update trades count
            new_trades_today = day_state.trades_today + 1

            # Update consecutive losses
            new_consecutive_losses = day_state.consecutive_losses
            cooldown_until = day_state.cooldown_until

            if pnl < 0:  # Loss
                new_consecutive_losses += 1
                # Set cooldown if we hit max consecutive losses
                if new_consecutive_losses >= self.config["MAX_CONSECUTIVE_LOSSES"]:
                    cooldown_time = fill_time + timedelta(minutes=self.config["COOLDOWN_MINUTES"])
                    cooldown_until = cooldown_time.isoformat()
            else:  # Profit or breakeven
                new_consecutive_losses = 0
                cooldown_until = None

            # Update day state in database
            cursor.execute(
                (
                    "UPDATE day_state "
                    "SET day_pnl = ?, max_day_pnl = ?, trades_today = ?, consecutive_losses = ?, cooldown_until = ? "
                    "WHERE date_utc = ?"
                ),
                (
                    new_day_pnl,
                    new_max_day_pnl,
                    new_trades_today,
                    new_consecutive_losses,
                    cooldown_until,
                    day_state.date_utc,
                ),
            )

            conn.commit()

            logger.info(f"Recorded fill: {symbol} {side} {qty}@{price} PnL:{pnl}")

    def reset_day_state(self, date_utc: str = None):
        """Reset day state for testing purposes"""
        if date_utc is None:
            date_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                (
                    "UPDATE day_state "
                    "SET day_pnl = 0.0, max_day_pnl = 0.0, trades_today = 0, "
                    "consecutive_losses = 0, cooldown_until = NULL "
                    "WHERE date_utc = ?"
                ),
                (date_utc,),
            )

            # If no row was updated, insert a new one
            if cursor.rowcount == 0:
                cursor.execute(
                    (
                        "INSERT INTO day_state "
                        "(date_utc, day_pnl, max_day_pnl, trades_today, consecutive_losses, cooldown_until) "
                        "VALUES (?, 0.0, 0.0, 0, 0, NULL)"
                    ),
                    (date_utc,),
                )

            conn.commit()
            logger.info(f"Reset day state for {date_utc}")


# Global risk engine instance
_risk_engine = None


def get_risk_engine() -> RiskEngine:
    """Get global risk engine instance"""
    global _risk_engine
    if _risk_engine is None:
        _risk_engine = RiskEngine()
    return _risk_engine

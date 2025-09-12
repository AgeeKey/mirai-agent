"""
Explainability logging module for trading decisions

This module provides structured logging of trading decisions with all relevant
context for auditing and analysis.
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ExplainabilityLogger:
    """Logger for trading decision explanations and audit trail"""

    def __init__(self, log_path: str = "logs/explain.log"):
        """
        Initialize explainability logger

        Args:
            log_path: Path to the explain log file
        """
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure log file exists
        if not self.log_path.exists():
            self.log_path.touch()

    def log_decision(
        self,
        symbol: str,
        score: float,
        action: str,
        strategy: str,
        rationale: str,
        accepted: bool,
        deny_reason: str | None = None,
        additional_context: dict[str, Any] | None = None,
    ):
        """
        Log a trading decision with full context

        Args:
            symbol: Trading symbol (e.g., BTCUSDT)
            score: Advisor confidence score (0.0-1.0)
            action: Recommended action (BUY/SELL/HOLD)
            strategy: Strategy name
            rationale: Decision rationale
            accepted: Whether the decision was accepted
            deny_reason: Reason for denial if not accepted
            additional_context: Extra context data
        """
        timestamp = datetime.now(UTC).isoformat()

        # Build log entry
        log_entry = {
            "ts": timestamp,
            "symbol": symbol,
            "score": round(float(score), 3),
            "action": action,
            "strategy": strategy,
            "rationale": rationale,
            "accepted": bool(accepted),
            "deny_reason": deny_reason,
        }

        # Add additional context if provided
        if additional_context:
            log_entry.update(additional_context)

        # Write to log file
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write to explain log: {e}")

    def get_recent_decisions(self, limit: int = 100) -> list:
        """
        Get recent decisions from the log

        Args:
            limit: Maximum number of recent decisions to return

        Returns:
            List of decision dictionaries
        """
        decisions = []

        try:
            if not self.log_path.exists():
                return decisions

            with open(self.log_path, encoding="utf-8") as f:
                lines = f.readlines()

            # Get the last N lines
            recent_lines = lines[-limit:] if len(lines) > limit else lines

            for line in recent_lines:
                line = line.strip()
                if line:
                    try:
                        decision = json.loads(line)
                        decisions.append(decision)
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error(f"Failed to read explain log: {e}")

        return decisions

    def get_daily_stats(self, date_str: str | None = None) -> dict[str, Any]:
        """
        Get daily statistics from the explain log

        Args:
            date_str: Date in YYYY-MM-DD format, defaults to today

        Returns:
            Dictionary with daily statistics
        """
        if date_str is None:
            date_str = datetime.now(UTC).strftime("%Y-%m-%d")

        stats = {
            "date": date_str,
            "total_decisions": 0,
            "accepted_decisions": 0,
            "denied_decisions": 0,
            "avg_score": 0.0,
            "action_breakdown": {"BUY": 0, "SELL": 0, "HOLD": 0},
            "top_rationales": [],
            "filtered_by_advisor": 0,
        }

        try:
            decisions = self.get_recent_decisions(limit=1000)  # Get more for daily analysis
            daily_decisions = [d for d in decisions if d.get("ts", "").startswith(date_str)]

            if not daily_decisions:
                return stats

            stats["total_decisions"] = len(daily_decisions)
            stats["accepted_decisions"] = sum(1 for d in daily_decisions if d.get("accepted"))
            stats["denied_decisions"] = stats["total_decisions"] - stats["accepted_decisions"]

            # Calculate average score
            scores = [d.get("score", 0.0) for d in daily_decisions]
            stats["avg_score"] = round(sum(scores) / len(scores), 3) if scores else 0.0

            # Action breakdown
            for decision in daily_decisions:
                action = decision.get("action", "HOLD")
                if action in stats["action_breakdown"]:
                    stats["action_breakdown"][action] += 1

            # Count advisor-filtered decisions
            stats["filtered_by_advisor"] = sum(
                1 for d in daily_decisions if not d.get("accepted") and "advisor" in d.get("deny_reason", "").lower()
            )

            # Top rationales (by frequency)
            rationale_counts = {}
            for decision in daily_decisions:
                rationale = decision.get("rationale", "")[:50]  # First 50 chars
                if rationale:
                    rationale_counts[rationale] = rationale_counts.get(rationale, 0) + 1

            # Sort by frequency and get top 3
            sorted_rationales = sorted(rationale_counts.items(), key=lambda x: x[1], reverse=True)
            stats["top_rationales"] = [{"rationale": r[0], "count": r[1]} for r in sorted_rationales[:3]]

        except Exception as e:
            logger.error(f"Failed to calculate daily stats: {e}")

        return stats


# Global explainability logger instance
_explain_logger = None


def get_explain_logger() -> ExplainabilityLogger:
    """Get global explainability logger instance"""
    global _explain_logger

    if _explain_logger is None:
        _explain_logger = ExplainabilityLogger()

    return _explain_logger


def log_decision(
    symbol: str,
    score: float,
    action: str,
    strategy: str,
    rationale: str,
    accepted: bool,
    deny_reason: str | None = None,
    **kwargs,
):
    """
    Convenience function to log a trading decision

    Args:
        symbol: Trading symbol
        score: Advisor score
        action: Recommended action
        strategy: Strategy name
        rationale: Decision rationale
        accepted: Whether decision was accepted
        deny_reason: Reason for denial if not accepted
        **kwargs: Additional context
    """
    logger_instance = get_explain_logger()
    logger_instance.log_decision(
        symbol=symbol,
        score=score,
        action=action,
        strategy=strategy,
        rationale=rationale,
        accepted=accepted,
        deny_reason=deny_reason,
        additional_context=kwargs,
    )

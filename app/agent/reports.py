"""
Basic reporting functionality for AI Advisor analytics

This module provides daily reporting capabilities for advisor performance
and decision analysis.
"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from pathlib import Path

from .explain_logger import get_explain_logger

logger = logging.getLogger(__name__)


class AdvisorReports:
    """Generate reports on advisor performance and decisions"""
    
    def __init__(self, reports_dir: str = "reports"):
        """
        Initialize the reports generator
        
        Args:
            reports_dir: Directory to save reports
        """
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.explain_logger = get_explain_logger()
    
    def generate_daily_report(self, date_str: str = None) -> Dict[str, Any]:
        """
        Generate daily advisor report
        
        Args:
            date_str: Date in YYYY-MM-DD format, defaults to today
            
        Returns:
            Dictionary with daily report data
        """
        if date_str is None:
            date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        
        logger.info(f"Generating daily advisor report for {date_str}")
        
        # Get daily stats from explain logger
        daily_stats = self.explain_logger.get_daily_stats(date_str)
        
        # Enhanced report with additional calculations
        report = {
            "report_date": date_str,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_decisions": daily_stats["total_decisions"],
                "accepted_decisions": daily_stats["accepted_decisions"],
                "denied_decisions": daily_stats["denied_decisions"],
                "avg_advisor_score": daily_stats["avg_score"],
                "filtered_by_advisor_count": daily_stats["filtered_by_advisor"],
                "filtered_by_advisor_percent": self._calculate_percentage(
                    daily_stats["filtered_by_advisor"], 
                    daily_stats["total_decisions"]
                )
            },
            "action_breakdown": daily_stats["action_breakdown"],
            "top_rationales": daily_stats["top_rationales"],
            "advisor_effectiveness": self._analyze_advisor_effectiveness(daily_stats)
        }
        
        return report
    
    def save_daily_report(self, date_str: str = None) -> Path:
        """
        Generate and save daily report to file
        
        Args:
            date_str: Date in YYYY-MM-DD format, defaults to today
            
        Returns:
            Path to saved report file
        """
        if date_str is None:
            date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        
        report = self.generate_daily_report(date_str)
        
        # Save to JSON file
        report_file = self.reports_dir / f"advisor_daily_{date_str}.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Daily report saved to {report_file}")
            
            # Also create a human-readable summary
            self._save_human_readable_summary(report, date_str)
            
        except Exception as e:
            logger.error(f"Failed to save daily report: {e}")
            raise
        
        return report_file
    
    def _save_human_readable_summary(self, report: Dict[str, Any], date_str: str):
        """Save a human-readable summary of the report"""
        summary_file = self.reports_dir / f"advisor_summary_{date_str}.txt"
        
        summary = self._format_human_readable_summary(report)
        
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            logger.info(f"Human-readable summary saved to {summary_file}")
        except Exception as e:
            logger.warning(f"Failed to save human-readable summary: {e}")
    
    def _format_human_readable_summary(self, report: Dict[str, Any]) -> str:
        """Format report as human-readable text"""
        summary = report["summary"]
        
        text = f"""
AI ADVISOR DAILY REPORT
=======================
Date: {report["report_date"]}
Generated: {report["generated_at"]}

SUMMARY
-------
Total Decisions: {summary["total_decisions"]}
Accepted: {summary["accepted_decisions"]}
Denied: {summary["denied_decisions"]}
Average Advisor Score: {summary["avg_advisor_score"]:.3f}

ADVISOR FILTERING
-----------------
Filtered by Advisor: {summary["filtered_by_advisor_count"]} ({summary["filtered_by_advisor_percent"]:.1f}%)

ACTION BREAKDOWN
----------------
"""
        
        for action, count in report["action_breakdown"].items():
            text += f"{action}: {count}\n"
        
        text += "\nTOP RATIONALES\n--------------\n"
        for i, rationale_data in enumerate(report["top_rationales"], 1):
            text += f"{i}. {rationale_data['rationale']} (Count: {rationale_data['count']})\n"
        
        text += f"\nADVISOR EFFECTIVENESS\n--------------------\n"
        effectiveness = report["advisor_effectiveness"]
        text += f"Gating Rate: {effectiveness['gating_rate']:.1f}%\n"
        text += f"Decision Quality: {effectiveness['decision_quality']}\n"
        text += f"Avg Score (Accepted): {effectiveness['avg_score_accepted']:.3f}\n"
        text += f"Avg Score (Denied): {effectiveness['avg_score_denied']:.3f}\n"
        
        return text
    
    def _analyze_advisor_effectiveness(self, daily_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze advisor effectiveness metrics"""
        total = daily_stats["total_decisions"]
        filtered = daily_stats["filtered_by_advisor"]
        
        # Get recent decisions for more detailed analysis
        recent_decisions = self.explain_logger.get_recent_decisions(limit=1000)
        
        # Filter decisions for the current day
        date_str = daily_stats["date"]
        daily_decisions = [
            d for d in recent_decisions 
            if d.get("ts", "").startswith(date_str)
        ]
        
        # Calculate metrics
        accepted_scores = [
            d.get("score", 0.0) for d in daily_decisions 
            if d.get("accepted", False)
        ]
        denied_scores = [
            d.get("score", 0.0) for d in daily_decisions 
            if not d.get("accepted", True)
        ]
        
        return {
            "gating_rate": self._calculate_percentage(filtered, total),
            "decision_quality": self._assess_decision_quality(daily_stats),
            "avg_score_accepted": sum(accepted_scores) / len(accepted_scores) if accepted_scores else 0.0,
            "avg_score_denied": sum(denied_scores) / len(denied_scores) if denied_scores else 0.0,
            "score_separation": abs(
                (sum(accepted_scores) / len(accepted_scores) if accepted_scores else 0.0) -
                (sum(denied_scores) / len(denied_scores) if denied_scores else 0.0)
            )
        }
    
    def _assess_decision_quality(self, daily_stats: Dict[str, Any]) -> str:
        """Assess the quality of advisor decisions"""
        avg_score = daily_stats["avg_score"]
        filtered_percent = self._calculate_percentage(
            daily_stats["filtered_by_advisor"], 
            daily_stats["total_decisions"]
        )
        
        if avg_score >= 0.75 and filtered_percent < 30:
            return "Excellent"
        elif avg_score >= 0.65 and filtered_percent < 50:
            return "Good"
        elif avg_score >= 0.55:
            return "Fair"
        else:
            return "Poor"
    
    def _calculate_percentage(self, part: int, total: int) -> float:
        """Calculate percentage with safe division"""
        return (part / total * 100) if total > 0 else 0.0
    
    def get_weekly_summary(self, end_date: str = None) -> Dict[str, Any]:
        """
        Get weekly summary of advisor performance
        
        Args:
            end_date: End date in YYYY-MM-DD format, defaults to today
            
        Returns:
            Weekly summary dictionary
        """
        if end_date is None:
            end_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        
        # This is a simplified weekly summary
        # In a full implementation, you'd aggregate multiple daily reports
        daily_report = self.generate_daily_report(end_date)
        
        return {
            "week_ending": end_date,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "daily_snapshot": daily_report,
            "note": "Weekly aggregation not yet implemented - showing daily snapshot"
        }


# Global reports instance
_reports_instance = None

def get_reports_generator() -> AdvisorReports:
    """Get global reports generator instance"""
    global _reports_instance
    
    if _reports_instance is None:
        _reports_instance = AdvisorReports()
    
    return _reports_instance


def generate_daily_report(date_str: str = None) -> Dict[str, Any]:
    """
    Convenience function to generate daily report
    
    Args:
        date_str: Date in YYYY-MM-DD format, defaults to today
        
    Returns:
        Daily report dictionary
    """
    reports_gen = get_reports_generator()
    return reports_gen.generate_daily_report(date_str)


def save_daily_report(date_str: str = None) -> Path:
    """
    Convenience function to save daily report
    
    Args:
        date_str: Date in YYYY-MM-DD format, defaults to today
        
    Returns:
        Path to saved report file
    """
    reports_gen = get_reports_generator()
    return reports_gen.save_daily_report(date_str)
"""
Advanced Trading Alerts and Notifications
Enterprise-level alerting system
"""

import asyncio
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    PORTFOLIO_RISK = "portfolio_risk"
    POSITION_RISK = "position_risk"
    SYSTEM_ERROR = "system_error"
    PERFORMANCE = "performance"
    MARKET_ANOMALY = "market_anomaly"
    AI_MODEL = "ai_model"


@dataclass
class Alert:
    type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    symbol: Optional[str] = None
    value: Optional[float] = None
    threshold: Optional[float] = None
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class AlertManager:
    """
    Advanced alert management system for trading operations
    """
    
    def __init__(self, telegram_notifier=None, email_config: Dict = None):
        self.telegram_notifier = telegram_notifier
        self.email_config = email_config or {}
        self.active_alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        self.suppression_rules: Dict[str, datetime] = {}
        self.thresholds = self._load_alert_thresholds()
        
    def _load_alert_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Load alert thresholds from configuration"""
        return {
            "portfolio": {
                "max_drawdown": 0.15,  # 15%
                "daily_loss_limit": 0.05,  # 5%
                "risk_exposure": 0.8,  # 80%
                "margin_ratio_warning": 0.8,  # 80%
                "margin_ratio_critical": 0.9  # 90%
            },
            "position": {
                "single_position_risk": 0.1,  # 10%
                "stop_loss_breach": 1.0,  # Any stop loss breach
                "large_slippage": 50.0,  # 50 bps
            },
            "performance": {
                "win_rate_low": 0.3,  # 30%
                "sharpe_ratio_low": 0.5,
                "daily_trades_high": 50,
                "order_latency_high": 5.0  # 5 seconds
            },
            "system": {
                "api_error_rate": 0.05,  # 5%
                "websocket_disconnects": 5,  # per hour
                "ai_decision_latency": 10.0  # 10 seconds
            }
        }
    
    async def check_portfolio_risk(self, portfolio_data: Dict[str, Any]):
        """Check portfolio-level risk alerts"""
        portfolio_value = portfolio_data.get('total_value', 0)
        unrealized_pnl = portfolio_data.get('unrealized_pnl', 0)
        daily_pnl = portfolio_data.get('daily_pnl', 0)
        max_drawdown = portfolio_data.get('max_drawdown', 0)
        
        # Max drawdown alert
        if max_drawdown > self.thresholds["portfolio"]["max_drawdown"]:
            await self._trigger_alert(Alert(
                type=AlertType.PORTFOLIO_RISK,
                severity=AlertSeverity.CRITICAL,
                title="Maximum Drawdown Exceeded",
                message=f"Portfolio drawdown {max_drawdown:.2%} exceeds limit {self.thresholds['portfolio']['max_drawdown']:.2%}",
                value=max_drawdown,
                threshold=self.thresholds["portfolio"]["max_drawdown"]
            ))
        
        # Daily loss limit
        daily_loss_ratio = abs(daily_pnl) / portfolio_value if portfolio_value > 0 else 0
        if daily_pnl < 0 and daily_loss_ratio > self.thresholds["portfolio"]["daily_loss_limit"]:
            await self._trigger_alert(Alert(
                type=AlertType.PORTFOLIO_RISK,
                severity=AlertSeverity.HIGH,
                title="Daily Loss Limit Exceeded",
                message=f"Daily loss {daily_loss_ratio:.2%} exceeds limit {self.thresholds['portfolio']['daily_loss_limit']:.2%}",
                value=daily_loss_ratio,
                threshold=self.thresholds["portfolio"]["daily_loss_limit"]
            ))
    
    async def check_position_risk(self, symbol: str, position_data: Dict[str, Any]):
        """Check individual position risk alerts"""
        size = abs(position_data.get('size', 0))
        unrealized_pnl = position_data.get('unrealized_pnl', 0)
        entry_price = position_data.get('entry_price', 0)
        current_price = position_data.get('current_price', 0)
        
        # Large position alert
        portfolio_value = position_data.get('portfolio_value', 1)
        position_ratio = abs(position_data.get('notional', 0)) / portfolio_value
        
        if position_ratio > self.thresholds["position"]["single_position_risk"]:
            await self._trigger_alert(Alert(
                type=AlertType.POSITION_RISK,
                severity=AlertSeverity.MEDIUM,
                title="Large Position Warning",
                message=f"{symbol} position size {position_ratio:.2%} exceeds recommended limit",
                symbol=symbol,
                value=position_ratio,
                threshold=self.thresholds["position"]["single_position_risk"]
            ))
    
    async def check_performance_metrics(self, performance_data: Dict[str, Any]):
        """Check performance-related alerts"""
        win_rate = performance_data.get('win_rate', 0)
        sharpe_ratio = performance_data.get('sharpe_ratio', 0)
        daily_trades = performance_data.get('daily_trades', 0)
        avg_order_latency = performance_data.get('avg_order_latency', 0)
        
        # Low win rate
        if win_rate < self.thresholds["performance"]["win_rate_low"]:
            await self._trigger_alert(Alert(
                type=AlertType.PERFORMANCE,
                severity=AlertSeverity.MEDIUM,
                title="Low Win Rate Alert",
                message=f"Win rate {win_rate:.2%} below threshold {self.thresholds['performance']['win_rate_low']:.2%}",
                value=win_rate,
                threshold=self.thresholds["performance"]["win_rate_low"]
            ))
        
        # High order latency
        if avg_order_latency > self.thresholds["performance"]["order_latency_high"]:
            await self._trigger_alert(Alert(
                type=AlertType.PERFORMANCE,
                severity=AlertSeverity.HIGH,
                title="High Order Latency",
                message=f"Average order latency {avg_order_latency:.2f}s exceeds threshold",
                value=avg_order_latency,
                threshold=self.thresholds["performance"]["order_latency_high"]
            ))
    
    async def check_ai_model_performance(self, model_data: Dict[str, Any]):
        """Check AI model performance alerts"""
        model_name = model_data.get('model_name', 'unknown')
        accuracy = model_data.get('accuracy', 0)
        decision_latency = model_data.get('decision_latency', 0)
        last_update = model_data.get('last_update')
        
        # Model accuracy degradation
        if accuracy < 0.6:  # 60% minimum accuracy
            await self._trigger_alert(Alert(
                type=AlertType.AI_MODEL,
                severity=AlertSeverity.HIGH,
                title="AI Model Accuracy Drop",
                message=f"Model '{model_name}' accuracy {accuracy:.2%} below acceptable threshold",
                value=accuracy,
                threshold=0.6,
                metadata={'model_name': model_name}
            ))
        
        # High decision latency
        if decision_latency > self.thresholds["system"]["ai_decision_latency"]:
            await self._trigger_alert(Alert(
                type=AlertType.AI_MODEL,
                severity=AlertSeverity.MEDIUM,
                title="AI Decision Latency High",
                message=f"Model '{model_name}' decision latency {decision_latency:.2f}s is high",
                value=decision_latency,
                threshold=self.thresholds["system"]["ai_decision_latency"],
                metadata={'model_name': model_name}
            ))
    
    async def _trigger_alert(self, alert: Alert):
        """Process and send alert through configured channels"""
        # Check suppression rules
        alert_key = f"{alert.type.value}_{alert.symbol or 'global'}"
        if alert_key in self.suppression_rules:
            if datetime.now() < self.suppression_rules[alert_key]:
                logger.debug(f"Alert suppressed: {alert.title}")
                return
        
        # Add to active alerts
        self.active_alerts.append(alert)
        self.alert_history.append(alert)
        
        # Send notifications
        await self._send_notifications(alert)
        
        # Set suppression rule (prevent spam)
        suppression_time = self._get_suppression_time(alert.severity)
        self.suppression_rules[alert_key] = datetime.now() + suppression_time
        
        logger.warning(f"Alert triggered: {alert.title} - {alert.message}")
    
    async def _send_notifications(self, alert: Alert):
        """Send alert through all configured channels"""
        # Telegram notification
        if self.telegram_notifier:
            try:
                message = self._format_telegram_message(alert)
                await self.telegram_notifier.send_alert(message)
            except Exception as e:
                logger.error(f"Failed to send Telegram alert: {e}")
        
        # Email notification (for critical alerts)
        if alert.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL] and self.email_config:
            try:
                await self._send_email_alert(alert)
            except Exception as e:
                logger.error(f"Failed to send email alert: {e}")
    
    def _format_telegram_message(self, alert: Alert) -> str:
        """Format alert for Telegram"""
        severity_emoji = {
            AlertSeverity.LOW: "🟡",
            AlertSeverity.MEDIUM: "🟠", 
            AlertSeverity.HIGH: "🔴",
            AlertSeverity.CRITICAL: "🚨"
        }
        
        emoji = severity_emoji.get(alert.severity, "⚠️")
        
        message = f"{emoji} *{alert.title}*\n\n"
        message += f"📊 {alert.message}\n"
        
        if alert.symbol:
            message += f"💱 Symbol: `{alert.symbol}`\n"
        
        if alert.value is not None and alert.threshold is not None:
            message += f"📈 Value: `{alert.value}`\n"
            message += f"🎯 Threshold: `{alert.threshold}`\n"
        
        message += f"⏰ Time: `{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}`"
        
        return message
    
    async def _send_email_alert(self, alert: Alert):
        """Send email alert for critical issues"""
        if not self.email_config.get('enabled', False):
            return
            
        smtp_server = self.email_config.get('smtp_server')
        smtp_port = self.email_config.get('smtp_port', 587)
        sender_email = self.email_config.get('sender_email')
        sender_password = self.email_config.get('sender_password')
        recipient_emails = self.email_config.get('recipient_emails', [])
        
        if not all([smtp_server, sender_email, sender_password, recipient_emails]):
            logger.warning("Email configuration incomplete, skipping email alert")
            return
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ', '.join(recipient_emails)
        msg['Subject'] = f"[Mirai Agent] {alert.severity.value.upper()}: {alert.title}"
        
        body = f"""
        Alert Details:
        
        Type: {alert.type.value}
        Severity: {alert.severity.value.upper()}
        Symbol: {alert.symbol or 'N/A'}
        Message: {alert.message}
        Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
        
        Please check the trading system immediately.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
    
    def _get_suppression_time(self, severity: AlertSeverity) -> timedelta:
        """Get suppression time based on alert severity"""
        suppression_times = {
            AlertSeverity.LOW: timedelta(hours=1),
            AlertSeverity.MEDIUM: timedelta(minutes=30),
            AlertSeverity.HIGH: timedelta(minutes=15),
            AlertSeverity.CRITICAL: timedelta(minutes=5)
        }
        return suppression_times.get(severity, timedelta(minutes=15))
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        return [
            {
                'type': alert.type.value,
                'severity': alert.severity.value,
                'title': alert.title,
                'message': alert.message,
                'symbol': alert.symbol,
                'timestamp': alert.timestamp.isoformat(),
                'metadata': alert.metadata
            }
            for alert in self.active_alerts
        ]
    
    def clear_alert(self, alert_index: int):
        """Clear an active alert"""
        if 0 <= alert_index < len(self.active_alerts):
            self.active_alerts.pop(alert_index)
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics"""
        total_alerts = len(self.alert_history)
        active_count = len(self.active_alerts)
        
        severity_counts = {}
        type_counts = {}
        
        for alert in self.alert_history:
            severity_counts[alert.severity.value] = severity_counts.get(alert.severity.value, 0) + 1
            type_counts[alert.type.value] = type_counts.get(alert.type.value, 0) + 1
        
        return {
            'total_alerts': total_alerts,
            'active_alerts': active_count,
            'severity_breakdown': severity_counts,
            'type_breakdown': type_counts,
            'last_24h': len([a for a in self.alert_history if a.timestamp > datetime.now() - timedelta(days=1)])
        }


# Global alert manager instance
alert_manager = AlertManager()


async def process_monitoring_data(monitoring_data: Dict[str, Any]):
    """Process monitoring data and trigger alerts as needed"""
    try:
        # Portfolio risk checks
        if 'portfolio' in monitoring_data:
            await alert_manager.check_portfolio_risk(monitoring_data['portfolio'])
        
        # Position risk checks
        if 'positions' in monitoring_data:
            for symbol, position in monitoring_data['positions'].items():
                await alert_manager.check_position_risk(symbol, position)
        
        # Performance checks
        if 'performance' in monitoring_data:
            await alert_manager.check_performance_metrics(monitoring_data['performance'])
        
        # AI model checks
        if 'ai_models' in monitoring_data:
            for model_data in monitoring_data['ai_models']:
                await alert_manager.check_ai_model_performance(model_data)
                
    except Exception as e:
        logger.error(f"Error processing monitoring data: {e}")


def get_alerts_summary() -> Dict[str, Any]:
    """Get current alerts summary"""
    return alert_manager.get_alert_summary()


def get_active_alerts() -> List[Dict[str, Any]]:
    """Get active alerts"""
    return alert_manager.get_active_alerts()
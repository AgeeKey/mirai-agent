
"""
Telegram notification system for Mirai Agent
"""

import logging
import os
from datetime import datetime
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Telegram notification service for trading alerts
    """

    def __init__(self):
        """Initialize Telegram notifier"""
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.bot_token and self.chat_id)

    def send_message(self, message: str, parse_mode: Optional[str] = None) -> bool:
        """
        Send message to Telegram chat

        Args:
            message: Message text to send
            parse_mode: Optional parsing mode (HTML/Markdown)

        Returns:
            True if message was sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Telegram notifications disabled - no bot token or chat ID")
            return False

        try:
            import requests

            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }

            response = requests.post(url, json=data)
            response.raise_for_status()

            result = response.json()
            if result.get("ok"):
                logger.info("Telegram notification sent successfully")
                return True
            else:
                logger.error(f"Failed to send Telegram notification: {result}")
                return False

        except Exception as e:
            logger.error(f"Error sending Telegram notification: {str(e)}")
            return False

    def send_trade_alert(self, trade_data: Dict[str, Any]) -> bool:
        """
        Send trade execution alert

        Args:
            trade_data: Dictionary with trade information

        Returns:
            True if alert was sent successfully, False otherwise
        """
        if not self.enabled:
            return False

        symbol = trade_data.get("symbol", "N/A")
        action = trade_data.get("action", "N/A")
        price = trade_data.get("price", 0)
        quantity = trade_data.get("quantity", 0)
        timestamp = trade_data.get("timestamp", datetime.now().isoformat())

        message = f"""
🤖 <b>Mirai Agent Trade Alert</b>

📊 <b>Trade Executed</b>
• Symbol: {symbol}
• Action: {action}
• Price: ${price:,.2f}
• Quantity: {quantity}
• Time: {timestamp}

⚠️ <b>Always verify trades before execution</b>
        """

        return self.send_message(message, parse_mode="HTML")

    def send_risk_alert(self, alert_type: str, details: Dict[str, Any]) -> bool:
        """
        Send risk management alert

        Args:
            alert_type: Type of risk alert
            details: Dictionary with alert details

        Returns:
            True if alert was sent successfully, False otherwise
        """
        if not self.enabled:
            return False

        message = f"""
🚨 <b>Mirai Agent Risk Alert</b>

🔴 <b>{alert_type}</b>
• Details: {details}

⚠️ <b>Please check your trading system immediately</b>
        """

        return self.send_message(message, parse_mode="HTML")

    def send_system_alert(self, alert_type: str, message: str) -> bool:
        """
        Send system status alert

        Args:
            alert_type: Type of system alert
            message: Alert message

        Returns:
            True if alert was sent successfully, False otherwise
        """
        if not self.enabled:
            return False

        formatted_message = f"""
🖥️ <b>Mirai Agent System Alert</b>

📢 <b>{alert_type}</b>
• Message: {message}

⚠️ <b>Please check your trading system</b>
        """

        return self.send_message(formatted_message, parse_mode="HTML")

    def send_daily_report(self, report_data: Dict[str, Any]) -> bool:
        """
        Send daily trading report

        Args:
            report_data: Dictionary with report data

        Returns:
            True if report was sent successfully, False otherwise
        """
        if not self.enabled:
            return False

        total_trades = report_data.get("total_trades", 0)
        profit_loss = report_data.get("profit_loss", 0)
        best_performer = report_data.get("best_performer", "N/A")
        timestamp = report_data.get("timestamp", datetime.now().isoformat())

        message = f"""
📊 <b>Mirai Agent Daily Report</b>

📅 <b>{timestamp}</b>
• Total Trades: {total_trades}
• P/L: ${profit_loss:,.2f}
• Best Performer: {best_performer}

🤖 <b>Mirai Agent - Automated Trading System</b>
        """

        return self.send_message(message, parse_mode="HTML")

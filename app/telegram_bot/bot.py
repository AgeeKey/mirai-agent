#!/usr/bin/env python3
"""
Telegram Bot for Mirai Agent - Real-time trading notifications and control
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

try:
    from telegram import Bot, Update
    from telegram.constants import ParseMode
    from telegram.ext import Application, CommandHandler, ContextTypes

    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

    # Create dummy classes for graceful degradation
    class Update:
        pass

    class ContextTypes:
        DEFAULT_TYPE = None

    class ParseMode:
        MARKDOWN = "Markdown"


from agent.loop import AgentLoop
from trader.binance_client import BinanceClient
from trader.orders import OrderManager
from trader.risk_engine import get_risk_engine

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Telegram notification service for trading events
    """

    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.bot = None
        self._enabled = TELEGRAM_AVAILABLE and token and chat_id

        if self._enabled:
            self.bot = Bot(token=token)
        else:
            logger.warning("Telegram notifications disabled - missing dependencies or configuration")

    async def send_message(self, message: str, parse_mode: str = ParseMode.MARKDOWN):
        """Send a message to the configured chat"""
        if not self._enabled:
            logger.debug(f"Telegram disabled, would send: {message}")
            return

        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message, parse_mode=parse_mode)
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")

    def send_message_sync(self, message: str):
        """Synchronous wrapper for sending messages"""
        if not self._enabled:
            logger.debug(f"Telegram disabled, would send: {message}")
            return

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, schedule the coroutine
                future = asyncio.run_coroutine_threadsafe(self.send_message(message), loop)
                future.result()  # Wait for completion
            else:
                # If we're in sync context, run the coroutine
                loop.run_until_complete(self.send_message(message))
        except Exception:
            # Fallback for complex async scenarios
            logger.debug(f"Async send failed, logging message: {message}")

    def notify_entry(
        self,
        symbol: str,
        side: str,
        qty: float,
        sl: float | None,
        tp: float | None,
        rationale: str,
    ):
        """Notify about new trade entry"""
        sl_text = f"SL: {sl:.2f}" if sl else "SL: None"
        tp_text = f"TP: {tp:.2f}" if tp else "TP: None"

        message = f"""🚀 *New Entry*
Symbol: `{symbol}`
Side: *{side}*
Quantity: `{qty}`
{sl_text}
{tp_text}
Rationale: {rationale}"""

        self.send_message_sync(message)

    def notify_sl_tp_trigger(self, symbol: str, trigger_type: str, price: float, pnl: float):
        """Notify about SL/TP trigger"""
        emoji = "💰" if pnl > 0 else "💥"
        message = f"""{emoji} *{trigger_type} Triggered*
Symbol: `{symbol}`
Price: `{price:.2f}`
PnL: `{pnl:+.2f} USDT`"""

        self.send_message_sync(message)

    def notify_risk_block(self, symbol: str, reason: str):
        """Notify about risk management block"""
        message = f"""🛑 *Risk Block*
Symbol: `{symbol}`
Reason: {reason}"""

        self.send_message_sync(message)


class TelegramBot:
    """
    Main Telegram bot class for Mirai Agent control and monitoring
    """

    def __init__(self, token: str, chat_id: str, agent_loop: AgentLoop | None = None):
        self.token = token
        self.chat_id = chat_id
        self.agent_loop = agent_loop
        self.application = None
        self._enabled = TELEGRAM_AVAILABLE and token and chat_id

        # Trading mode state (for /mode command)
        self.trading_mode = "auto"  # advisor, semi, auto

        if not self._enabled:
            logger.warning("Telegram bot disabled - missing dependencies or configuration")
            return

        # Initialize the application
        self.application = Application.builder().token(token).build()

        # Add command handlers
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("pause", self.pause_command))
        self.application.add_handler(CommandHandler("resume", self.resume_command))
        self.application.add_handler(CommandHandler("kill", self.kill_command))
        self.application.add_handler(CommandHandler("mode", self.mode_command))

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command - return JSON summary from Risk Engine"""
        try:
            risk_engine = get_risk_engine()
            now_utc = datetime.now(timezone.utc)
            day_state = risk_engine.get_day_state(now_utc)

            # Get open positions count (mock for now)
            open_positions = 0
            if self.agent_loop and hasattr(self.agent_loop, "positions"):
                open_positions = len(self.agent_loop.positions)

            # Get advisor state if available
            advisor_state = {}
            if self.agent_loop and hasattr(self.agent_loop, "get_advisor_state"):
                advisor_state = self.agent_loop.get_advisor_state()

            status_data = {
                "day_pnl": day_state.day_pnl,
                "max_day_pnl": day_state.max_day_pnl,
                "trades_today": day_state.trades_today,
                "consecutive_losses": day_state.consecutive_losses,
                "cooldown_until": day_state.cooldown_until,
                "open_positions": open_positions,
                "trading_mode": self.trading_mode,
                "agent_paused": (getattr(self.agent_loop, "paused", False) if self.agent_loop else False),
                "last_score": advisor_state.get("score", 0.0),
                "last_rationale": advisor_state.get("rationale", "No advisor data")[:100],  # Truncate for display
            }

            # Create more readable message
            message = f"""📊 *Agent Status*

💰 Day PnL: `{status_data['day_pnl']:.2f}`
📈 Max Day PnL: `{status_data['max_day_pnl']:.2f}`
📊 Trades Today: `{status_data['trades_today']}`
❌ Consecutive Losses: ````{status_data['consecutive_losses']}`
🏪 Open Positions: `{status_data['open_positions']}`
🎯 Trading Mode: `{status_data['trading_mode']}`
⏸️ Agent Paused: `{status_data['agent_paused']}`

🤖 *AI Advisor*
Score: `e: `e: `e: `{status_data['last_score']:.3f}`
Rationale: _{status_data['last_rationale']}_

Use /mode <advisor|semi|auto> to change mode"""

            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Error in status command: {e}")
            await update.message.reply_text(f"❌ Error getting status: {str(e)}")

    async def pause_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /pause command - pause trading"""
        try:
            if self.agent_loop:
                self.agent_loop.paused = True
                message = "⏸️ *Agent Paused*\nTrading has been paused. Use /resume to continue."
            else:
                message = "⚠️ Agent not available for pause control"

            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Error in pause command: {e}")
            await update.message.reply_text(f"❌ Error pausing agent: {str(e)}")

    async def resume_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /resume command - resume trading"""
        try:
            if self.agent_loop:
                self.agent_loop.paused = False
                message = "▶️ *Agent Resumed*\nTrading has been resumed."
            else:
                message = "⚠️ Agent not available for resume control"

            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Error in resume command: {e}")
            await update.message.reply_text(f"❌ Error resuming agent: {str(e)}")

    async def kill_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /kill <symbol> command - trigger kill switch"""
        try:
            # Parse symbol from command arguments
            if not context.args:
                await update.message.reply_text("❌ Usage: /kill <symbol>\nExample: /kill BTCUSDT")
                return

            symbol = context.args[0].upper()

            # Execute kill switch
            try:
                client = BinanceClient(dry_run=True, testnet=True)
                order_manager = OrderManager(client)

                # Cancel all orders
                order_manager.cancel_all_orders(symbol)

                # Close position
                order_manager.close_position(symbol)

                message = f"💥 *Kill Switch Executed*\nSymbol: `{symbol}`\n✅ Orders cancelled\n✅ Position closed"

            except Exception as e:
                message = f"💥 *Kill Switch Failed*\nSymbol: `{symbol}`\nError: {str(e)}"

            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Error in kill command: {e}")
            await update.message.reply_text(f"❌ Error executing kill switch: {str(e)}")

    async def mode_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /mode <advisor|semi|auto> command - change trading mode"""
        try:
            if not context.args:
                await update.message.reply_text(
                    f"🔧 *Current Mode*: `{self.trading_mode}`\n\nUsage: /mode <advisor|semi|auto>"
                )
                return

            new_mode = context.args[0].lower()
            valid_modes = ["advisor", "semi", "auto"]

            if new_mode not in valid_modes:
                await update.message.reply_text(f"❌ Invalid mode. Valid modes: {', '.join(valid_modes)}")
                return

            self.trading_mode = new_mode
            message = f"🔧 *Mode Changed*\nNew mode: `{new_mode}`"

            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            logger.error(f"Error in mode command: {e}")
            await update.message.reply_text(f"❌ Error changing mode: {str(e)}")

    def is_enabled(self) -> bool:
        """Check if bot is enabled and configured"""
        return self._enabled

    async def start_polling(self):
        """Start the bot with polling"""
        if not self._enabled:
            logger.warning("Cannot start polling - bot not enabled")
            return

        logger.info("Starting Telegram bot polling...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

        # Keep the bot running
        await self.application.updater.idle()

    def start_polling_sync(self):
        """Synchronous wrapper for starting polling"""
        if not self._enabled:
            logger.warning("Cannot start polling - bot not enabled")
            return

        asyncio.run(self.start_polling())


def create_notifier_from_env() -> TelegramNotifier | None:
    """Create a TelegramNotifier from environment variables"""
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        logger.info("Telegram configuration not found in environment")
        return None

    return TelegramNotifier(token, chat_id)


def create_bot_from_env(agent_loop: AgentLoop | None = None) -> TelegramBot | None:
    """Create a TelegramBot from environment variables"""
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        logger.info("Telegram configuration not found in environment")
        return None

    return TelegramBot(token, chat_id, agent_loop)


def start_bot():
    """Main function to start the Telegram bot"""
    if not TELEGRAM_AVAILABLE:
        print("❌ python-telegram-bot not installed. Install it with: pip install python-telegram-bot>=20")
        return

    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("❌ Missing Telegram configuration. Set TELEGRAM_TOKEN and TELEGRAM_CHAT_ID environment variables.")
        return

    # Create agent loop for bot control
    try:
        client = BinanceClient(dry_run=True, testnet=True)
        agent_loop = AgentLoop(client)

        bot = TelegramBot(token, chat_id, agent_loop)

        if bot.is_enabled():
            print(f"🚀 Starting Telegram bot for chat ID: {chat_id}")
            bot.start_polling_sync()
        else:
            print("❌ Failed to initialize Telegram bot")

    except Exception as e:
        print(f"❌ Error starting bot: {e}")


if __name__ == "__main__":
    start_bot()

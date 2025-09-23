#!/usr/bin/env python3
"""
Standalone Telegram Bot service for Mirai Agent
This can run as a separate Docker container
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the parent app directory to Python path
app_root = Path(__file__).parent.parent
sys.path.insert(0, str(app_root))

from telegram_bot.bot import create_bot_from_env

# Configure logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

logger = logging.getLogger(__name__)


async def main():
    """Main function to run the Telegram bot service"""
    logger.info("Starting Mirai Telegram Bot service...")

    # Check required environment variables
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID_ADMIN")

    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
        sys.exit(1)

    if not chat_id:
        logger.error("TELEGRAM_CHAT_ID_ADMIN environment variable not set")
        sys.exit(1)

    # Override the env var names for the bot
    os.environ["TELEGRAM_TOKEN"] = token
    os.environ["TELEGRAM_CHAT_ID"] = chat_id

    # Create and start the bot
    bot = create_bot_from_env()

    if not bot:
        logger.error("Failed to create Telegram bot")
        sys.exit(1)

    if not bot.is_enabled():
        logger.error("Telegram bot is not properly configured")
        sys.exit(1)

    logger.info(f"Bot starting for chat ID: {chat_id}")

    try:
        await bot.start_polling()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

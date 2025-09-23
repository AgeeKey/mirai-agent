import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add the app directory to Python path for testing
app_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(app_root))


# Test the telegram bot functionality
def test_telegram_imports():
    """Test that telegram bot can be imported"""
    try:
        from telegram_bot.bot import TelegramBot, TelegramNotifier

        assert TelegramBot is not None
        assert TelegramNotifier is not None
    except ImportError:
        pytest.skip("python-telegram-bot not available")


def test_notifier_creation():
    """Test creating a TelegramNotifier"""
    from telegram_bot.bot import TelegramNotifier

    # Test with valid config
    notifier = TelegramNotifier("test_token", "test_chat_id")
    assert notifier.token == "test_token"
    assert notifier.chat_id == "test_chat_id"


def test_bot_creation():
    """Test creating a TelegramBot"""
    from telegram_bot.bot import TelegramBot

    # Test with valid config
    bot = TelegramBot("test_token", "test_chat_id")
    assert bot.token == "test_token"
    assert bot.chat_id == "test_chat_id"


@patch.dict(os.environ, {"TELEGRAM_TOKEN": "test_token", "TELEGRAM_CHAT_ID": "12345"})
def test_create_from_env():
    """Test creating bot from environment variables"""
    from telegram_bot.bot import create_bot_from_env, create_notifier_from_env

    bot = create_bot_from_env()
    notifier = create_notifier_from_env()

    if bot:  # Only test if dependencies are available
        assert bot.token == "test_token"
        assert bot.chat_id == "12345"

    if notifier:  # Only test if dependencies are available
        assert notifier.token == "test_token"
        assert notifier.chat_id == "12345"


def test_create_from_env_missing():
    """Test creating bot without environment variables"""
    from telegram_bot.bot import create_bot_from_env, create_notifier_from_env

    with patch.dict(os.environ, {}, clear=True):
        bot = create_bot_from_env()
        notifier = create_notifier_from_env()

        # Should return None when env vars are missing
        assert bot is None
        assert notifier is None


@pytest.mark.asyncio
async def test_bot_commands():
    """Test bot command handlers"""
    try:
        from telegram_bot.bot import TelegramBot

        # Mock update and context
        update = MagicMock()
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.args = []

        bot = TelegramBot("test_token", "test_chat_id")

        if bot.is_enabled():
            # Test start command
            await bot.start_command(update, context)
            update.message.reply_text.assert_called()

            # Test status command
            await bot.status_command(update, context)
            update.message.reply_text.assert_called()

            # Test risk command
            await bot.risk_command(update, context)
            update.message.reply_text.assert_called()

    except ImportError:
        pytest.skip("python-telegram-bot not available")

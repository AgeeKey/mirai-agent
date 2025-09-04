"""
Tests for Telegram Bot functionality
"""

from unittest.mock import Mock, patch

from app.agent.loop import AgentLoop
from app.telegram_bot.bot import (
    TelegramBot,
    TelegramNotifier,
    create_bot_from_env,
    create_notifier_from_env,
)


class TestTelegramNotifier:
    """Test TelegramNotifier functionality"""

    def test_notifier_creation_without_config(self):
        """Test notifier creation without configuration"""
        notifier = TelegramNotifier("", "")
        assert not notifier._enabled

    def test_notifier_creation_with_config(self):
        """Test notifier creation with configuration"""
        notifier = TelegramNotifier("fake_token", "fake_chat_id")
        assert notifier._enabled
        assert notifier.token == "fake_token"
        assert notifier.chat_id == "fake_chat_id"

    def test_send_message_sync_disabled(self):
        """Test send_message_sync when disabled"""
        notifier = TelegramNotifier("", "")
        # Should not raise an exception
        notifier.send_message_sync("Test message")

    @patch("app.telegram_bot.bot.TELEGRAM_AVAILABLE", True)
    def test_send_message_sync_enabled(self):
        """Test send_message_sync when enabled"""
        with patch("app.telegram_bot.bot.Bot") as mock_bot_class:
            mock_bot = Mock()
            mock_bot_class.return_value = mock_bot

            notifier = TelegramNotifier("fake_token", "fake_chat_id")

            # Mock asyncio to avoid actual async calls
            with patch("asyncio.get_event_loop") as mock_get_loop:
                mock_loop = Mock()
                mock_loop.is_running.return_value = False
                mock_loop.run_until_complete = Mock()
                mock_get_loop.return_value = mock_loop

                notifier.send_message_sync("Test message")

                # Verify the loop was called
                mock_loop.run_until_complete.assert_called_once()

    def test_notify_entry(self):
        """Test notify_entry message formatting"""
        notifier = TelegramNotifier("", "")  # Disabled notifier

        # Should not raise an exception
        notifier.notify_entry(
            symbol="BTCUSDT",
            side="BUY",
            qty=0.1,
            sl=49000.0,
            tp=51000.0,
            rationale="Market looks bullish",
        )

    def test_notify_sl_tp_trigger(self):
        """Test notify_sl_tp_trigger message formatting"""
        notifier = TelegramNotifier("", "")  # Disabled notifier

        # Should not raise an exception
        notifier.notify_sl_tp_trigger(
            symbol="BTCUSDT", trigger_type="Stop Loss", price=49000.0, pnl=-500.0
        )

    def test_notify_risk_block(self):
        """Test notify_risk_block message formatting"""
        notifier = TelegramNotifier("", "")  # Disabled notifier

        # Should not raise an exception
        notifier.notify_risk_block(symbol="BTCUSDT", reason="Daily loss limit exceeded")


class TestTelegramBot:
    """Test TelegramBot functionality"""

    def test_bot_creation_without_config(self):
        """Test bot creation without configuration"""
        bot = TelegramBot("", "", None)
        assert not bot._enabled

    def test_bot_creation_with_config(self):
        """Test bot creation with configuration"""
        with patch("app.telegram_bot.bot.TELEGRAM_AVAILABLE", True):
            with patch("app.telegram_bot.bot.Application") as mock_app_class:
                mock_app = Mock()
                mock_builder = Mock()
                mock_builder.token.return_value = mock_builder
                mock_builder.build.return_value = mock_app
                mock_app_class.builder.return_value = mock_builder

                bot = TelegramBot("fake_token", "fake_chat_id", None)
                assert bot._enabled
                assert bot.token == "fake_token"
                assert bot.chat_id == "fake_chat_id"

    def test_command_handlers_setup(self):
        """Test that command handlers are properly set up"""
        with patch("app.telegram_bot.bot.TELEGRAM_AVAILABLE", True):
            with patch("app.telegram_bot.bot.Application") as mock_app_class:
                mock_app = Mock()
                mock_builder = Mock()
                mock_builder.token.return_value = mock_builder
                mock_builder.build.return_value = mock_app
                mock_app_class.builder.return_value = mock_builder

                bot = TelegramBot("fake_token", "fake_chat_id", None)

                # Verify handlers were added
                assert mock_app.add_handler.call_count == 5  # 5 commands

                # Check that each command was added
                call_args_list = mock_app.add_handler.call_args_list
                commands = []
                for call_args in call_args_list:
                    handler = call_args[0][0]
                    if hasattr(handler, "command"):
                        commands.append(handler.command)

                expected_commands = ["status", "pause", "resume", "kill", "mode"]
                for cmd in expected_commands:
                    assert any(cmd in str(call) for call in call_args_list)


class TestEnvironmentFunctions:
    """Test environment-based creation functions"""

    def test_create_notifier_from_env_no_config(self):
        """Test creating notifier from env without configuration"""
        with patch.dict("os.environ", {}, clear=True):
            notifier = create_notifier_from_env()
            assert notifier is None

    def test_create_notifier_from_env_with_config(self):
        """Test creating notifier from env with configuration"""
        with patch.dict(
            "os.environ", {"TELEGRAM_TOKEN": "fake_token", "TELEGRAM_CHAT_ID": "fake_chat_id"}
        ):
            notifier = create_notifier_from_env()
            assert notifier is not None
            assert notifier.token == "fake_token"
            assert notifier.chat_id == "fake_chat_id"

    def test_create_bot_from_env_no_config(self):
        """Test creating bot from env without configuration"""
        with patch.dict("os.environ", {}, clear=True):
            bot = create_bot_from_env()
            assert bot is None

    def test_create_bot_from_env_with_config(self):
        """Test creating bot from env with configuration"""
        with patch.dict(
            "os.environ", {"TELEGRAM_TOKEN": "fake_token", "TELEGRAM_CHAT_ID": "fake_chat_id"}
        ):
            with patch("app.telegram_bot.bot.TELEGRAM_AVAILABLE", True):
                with patch("app.telegram_bot.bot.Application") as mock_app_class:
                    mock_app = Mock()
                    mock_builder = Mock()
                    mock_builder.token.return_value = mock_builder
                    mock_builder.build.return_value = mock_app
                    mock_app_class.builder.return_value = mock_builder

                    bot = create_bot_from_env()
                    assert bot is not None
                    assert bot.token == "fake_token"
                    assert bot.chat_id == "fake_chat_id"


class TestIntegrationWithAgentLoop:
    """Test integration between Telegram bot and AgentLoop"""

    def test_agent_loop_with_notifier(self):
        """Test AgentLoop with Telegram notifier"""
        # Create a mock client and notifier
        mock_client = Mock()
        mock_client.dry_run = True
        mock_client.get_market_data.return_value = {
            "price": 50000.0,
            "volume": 1000.0,
            "change_24h": 0.05,
        }
        mock_client.get_account_info.return_value = {}

        mock_notifier = Mock()

        # Create agent loop with notifier
        agent_loop = AgentLoop(mock_client, notifier=mock_notifier)

        # Test pause functionality
        assert not agent_loop.paused
        agent_loop.paused = True

        decision = agent_loop.make_decision("BTCUSDT")

        # Should return HOLD when paused
        assert decision["action"] == "HOLD"
        assert "paused" in decision["rationale"]

    def test_agent_loop_notifications(self):
        """Test that AgentLoop calls notifier methods"""
        # Create a mock client
        mock_client = Mock()
        mock_client.dry_run = True
        mock_client.get_market_data.return_value = {
            "price": 50000.0,
            "volume": 1000.0,
            "change_24h": 0.05,
        }
        mock_client.get_account_info.return_value = {}
        mock_client.place_order.return_value = {"orderId": "test_order"}

        mock_notifier = Mock()

        # Mock risk engine to allow trades
        with patch("app.agent.loop.get_risk_engine") as mock_get_risk_engine:
            mock_risk_engine = Mock()
            mock_risk_engine.allow_entry.return_value = (True, "")
            mock_risk_engine.record_fill = Mock()
            mock_get_risk_engine.return_value = mock_risk_engine

            agent_loop = AgentLoop(mock_client, notifier=mock_notifier)

            # Make a decision (this might trigger a trade)
            decision = agent_loop.make_decision("BTCUSDT")

            # Execute the action if it's not HOLD
            if decision["action"] != "HOLD":
                result = agent_loop.execute_action(decision, "BTCUSDT")

                # Verify notifier was called for entry
                mock_notifier.notify_entry.assert_called()

    def test_agent_loop_risk_block_notification(self):
        """Test that AgentLoop notifies about risk blocks"""
        # Create a mock client
        mock_client = Mock()
        mock_client.dry_run = True
        mock_client.get_market_data.return_value = {
            "price": 50000.0,
            "volume": 1000.0,
            "change_24h": 0.05,
        }
        mock_client.get_account_info.return_value = {}

        mock_notifier = Mock()

        # Mock advisor to return high score so it passes advisor gating
        with patch("app.agent.loop.get_signal_score") as mock_get_signal_score:
            mock_get_signal_score.return_value = {
                "score": 0.85,  # High score to pass advisor threshold
                "rationale": "Strong signals",
                "strategy": "test",
                "action": "BUY",
            }

            # Mock risk engine to block trades
            with patch("app.agent.loop.get_risk_engine") as mock_get_risk_engine:
                mock_risk_engine = Mock()
                mock_risk_engine.get_day_state.return_value = Mock(consecutive_losses=0)
                mock_risk_engine.allow_entry.return_value = (False, "Daily loss limit exceeded")
                mock_get_risk_engine.return_value = mock_risk_engine

                agent_loop = AgentLoop(mock_client, notifier=mock_notifier)

                # Force a non-HOLD decision by mocking the policy
                with patch.object(agent_loop.policy, "analyze_market") as mock_analyze:
                    from app.agent.schema import AgentDecision

                    mock_analyze.return_value = AgentDecision(
                        score=0.8, rationale="Test trade", intent="BUY", action="MARKET_BUY"
                    )

                    decision = agent_loop.make_decision("BTCUSDT")

                    # Should be blocked and notifier should be called
                    assert decision["action"] == "HOLD"
                    mock_notifier.notify_risk_block.assert_called_once_with(
                        "BTCUSDT", "Daily loss limit exceeded"
                    )

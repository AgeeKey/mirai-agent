"""
Tests for the CLI module
"""

from click.testing import CliRunner

from app.cli import cli


class TestCLI:
    def setup_method(self):
        self.runner = CliRunner()

    def test_cli_help(self):
        """Test CLI help command"""
        result = self.runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Mirai Agent" in result.output

    def test_dry_run_check_command(self):
        """Test dry-run-check command"""
        result = self.runner.invoke(cli, ["dry-run-check"])
        assert result.exit_code == 0
        assert "dry-run check" in result.output.lower()

    def test_agent_once_command(self):
        """Test agent-once command"""
        result = self.runner.invoke(cli, ["agent-once", "--symbol", "BTCUSDT"])
        assert result.exit_code == 0
        assert "BTCUSDT" in result.output

    def test_sanity_trade_command(self):
        """Test sanity-trade command logs 3 orders in DRY_RUN"""
        result = self.runner.invoke(cli, ["sanity-trade", "--symbol", "BTCUSDT"])
        assert result.exit_code == 0
        assert "MARKET order" in result.output
        assert "STOP_MARKET (SL)" in result.output
        assert "TAKE_PROFIT_MARKET (TP)" in result.output
        assert "DRY_RUN mode" in result.output

    def test_cancel_all_command(self):
        """Test cancel-all command parses symbol argument"""
        result = self.runner.invoke(cli, ["cancel-all", "BTCUSDT"])
        assert result.exit_code == 0
        assert "BTCUSDT" in result.output
        assert "cancel all" in result.output.lower()
        assert "DRY_RUN" in result.output

    def test_kill_switch_command(self):
        """Test kill-switch command executes cancel-all and close position"""
        result = self.runner.invoke(cli, ["kill-switch", "BTCUSDT"])
        assert result.exit_code == 0
        assert "BTCUSDT" in result.output
        assert "cancel all" in result.output.lower()
        assert "close position" in result.output.lower()
        assert "DRY_RUN" in result.output

"""
Tests for the CLI module
"""
import pytest
from click.testing import CliRunner
from app.cli import cli


class TestCLI:
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_cli_help(self):
        """Test CLI help command"""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Mirai Agent' in result.output
    
    def test_dry_run_check_command(self):
        """Test dry-run-check command"""
        result = self.runner.invoke(cli, ['dry-run-check'])
        assert result.exit_code == 0
        assert 'dry-run check' in result.output.lower()
    
    def test_agent_once_command(self):
        """Test agent-once command"""
        result = self.runner.invoke(cli, ['agent-once', '--symbol', 'BTCUSDT'])
        assert result.exit_code == 0
        assert 'BTCUSDT' in result.output
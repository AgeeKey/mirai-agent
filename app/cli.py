#!/usr/bin/env python3
"""
Mirai Agent CLI - Trading agent command line interface
"""
import os
import sys
import click
import yaml
import logging
import logging.config
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.loop import AgentLoop
from trader.binance_client import BinanceClient


def setup_logging():
    """Setup logging configuration"""
    config_path = Path(__file__).parent.parent / "configs" / "logging.yaml"
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=logging.INFO)


@click.group()
@click.version_option(version="0.1.0", prog_name="mirai-agent")
def cli():
    """Mirai Agent - Advanced Trading Bot with AI-powered decision making"""
    setup_logging()


@cli.command()
@click.option('--config', '-c', default='configs/strategies.yaml', 
              help='Path to strategy configuration file')
@click.option('--dry-run', is_flag=True, default=True,
              help='Run in dry-run mode (no actual trades)')
def dry_run_check(config, dry_run):
    """Perform a dry run check of the trading system"""
    click.echo("🔍 Starting dry-run check...")
    
    try:
        # Initialize components
        client = BinanceClient(dry_run=True)
        agent = AgentLoop(client)
        
        # Test connection
        click.echo("📡 Testing Binance connection...")
        if client.test_connection():
            click.echo("✅ Binance connection successful")
        else:
            click.echo("❌ Binance connection failed")
            return
        
        # Test agent decision making
        click.echo("🤖 Testing agent decision making...")
        decision = agent.make_decision()
        click.echo(f"📊 Agent decision: {decision}")
        
        # Load strategy config
        config_path = Path(config)
        if config_path.exists():
            with open(config_path, 'r') as f:
                strategies = yaml.safe_load(f)
            click.echo(f"📋 Loaded {len(strategies.get('strategies', []))} strategies")
        else:
            click.echo(f"⚠️  Strategy config not found: {config}")
        
        click.echo("✅ Dry-run check completed successfully!")
        
    except Exception as e:
        click.echo(f"❌ Dry-run check failed: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option('--symbol', '-s', default='BTCUSDT', 
              help='Trading symbol (default: BTCUSDT)')
@click.option('--dry-run', is_flag=True, default=True,
              help='Run in dry-run mode (no actual trades)')
def agent_once(symbol, dry_run):
    """Run the trading agent once for a single decision cycle"""
    click.echo(f"🚀 Running agent once for {symbol}...")
    
    try:
        # Initialize components
        client = BinanceClient(dry_run=dry_run)
        agent = AgentLoop(client)
        
        # Get market data
        click.echo("📈 Fetching market data...")
        market_data = client.get_market_data(symbol)
        click.echo(f"💰 Current price: ${market_data.get('price', 'N/A')}")
        
        # Make agent decision
        click.echo("🤖 Agent analyzing market conditions...")
        decision = agent.make_decision(symbol=symbol)
        
        click.echo("📋 Agent Decision:")
        click.echo(f"  Score: {decision['score']}")
        click.echo(f"  Intent: {decision['intent']}")
        click.echo(f"  Action: {decision['action']}")
        click.echo(f"  Rationale: {decision['rationale']}")
        
        # Execute action if not dry run
        if not dry_run and decision['action'] != 'HOLD':
            click.echo("⚡ Executing trade...")
            result = agent.execute_action(decision, symbol)
            click.echo(f"📝 Trade result: {result}")
        else:
            click.echo("🔍 Dry-run mode - no actual trades executed")
        
        click.echo("✅ Agent cycle completed!")
        
    except Exception as e:
        click.echo(f"❌ Agent execution failed: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    cli()
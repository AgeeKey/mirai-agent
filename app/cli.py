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
from trader.orders import OrderManager


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


@cli.command()
@click.option('--symbol', '-s', default='BTCUSDT', 
              help='Trading symbol (default: BTCUSDT)')
@click.option('--dry-run', is_flag=True, default=True,
              help='Run in dry-run mode (no actual trades)')
def sanity_trade(symbol, dry_run):
    """Place a tiny MARKET order with SL (STOP_MARKET) and TP (TAKE_PROFIT_MARKET) for testing"""
    click.echo(f"🧪 Running sanity trade for {symbol}...")
    
    try:
        # Initialize components
        client = BinanceClient(dry_run=dry_run, testnet=True)
        order_manager = OrderManager(client)
        
        # Execute sanity trade
        click.echo("📊 Placing sanity trade orders...")
        result = order_manager.sanity_trade(symbol)
        
        if dry_run:
            click.echo("🔍 DRY_RUN mode - logging orders:")
            if result['main_order']:
                click.echo(f"  📈 MARKET order: {result['main_order']}")
            if result['stop_loss_order']:
                click.echo(f"  🛑 STOP_MARKET (SL): {result['stop_loss_order']}")
            if result['take_profit_order']:
                click.echo(f"  🎯 TAKE_PROFIT_MARKET (TP): {result['take_profit_order']}")
        else:
            click.echo(f"📝 Sanity trade result: {result}")
        
        click.echo("✅ Sanity trade completed!")
        
    except Exception as e:
        click.echo(f"❌ Sanity trade failed: {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument('symbol')
@click.option('--dry-run', is_flag=True, default=True,
              help='Run in dry-run mode (no actual cancellation)')
def cancel_all(symbol, dry_run):
    """Cancel all open orders for a given symbol"""
    click.echo(f"🚫 Cancelling all orders for {symbol}...")
    
    try:
        # Initialize components
        client = BinanceClient(dry_run=dry_run, testnet=True)
        order_manager = OrderManager(client)
        
        # Cancel all orders
        result = order_manager.cancel_all_orders(symbol)
        
        if dry_run:
            click.echo(f"🔍 DRY_RUN: cancel all for {symbol}")
        else:
            click.echo(f"📝 Cancel result: {result}")
        
        click.echo("✅ Cancel all completed!")
        
    except Exception as e:
        click.echo(f"❌ Cancel all failed: {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument('symbol')
@click.option('--dry-run', is_flag=True, default=True,
              help='Run in dry-run mode (no actual trades)')
def kill_switch(symbol, dry_run):
    """Cancel all orders and close position with MARKET order (reduceOnly)"""
    click.echo(f"💥 Executing kill switch for {symbol}...")
    
    try:
        # Initialize components
        client = BinanceClient(dry_run=dry_run, testnet=True)
        order_manager = OrderManager(client)
        
        # First, cancel all orders
        click.echo("🚫 Cancelling all orders...")
        cancel_result = order_manager.cancel_all_orders(symbol)
        
        if dry_run:
            click.echo(f"🔍 DRY_RUN: cancel all for {symbol}")
        else:
            click.echo(f"📝 Cancel result: {cancel_result}")
        
        # Then, close position
        click.echo("🔄 Closing position...")
        close_result = order_manager.close_position(symbol)
        
        if dry_run:
            click.echo(f"🔍 DRY_RUN: close position MARKET reduceOnly for {symbol}")
        else:
            click.echo(f"📝 Close result: {close_result}")
        
        click.echo("✅ Kill switch completed!")
        
    except Exception as e:
        click.echo(f"❌ Kill switch failed: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    cli()
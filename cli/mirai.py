#!/usr/bin/env python3
"""
Mirai Trading System - CLI Tool
Comprehensive command-line interface for managing the Mirai trading system.
"""

import os
import sys
import json
import click
import asyncio
import sqlite3
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.tree import Tree
from rich import print as rprint

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

console = Console()

# Configuration
DEFAULT_API_URL = "http://localhost:8001"
CONFIG_FILE = Path.home() / ".mirai" / "config.json"


class MiraiConfig:
    """Configuration management for Mirai CLI."""
    
    def __init__(self):
        self.config_file = CONFIG_FILE
        self.config_file.parent.mkdir(exist_ok=True)
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_file.exists():
            with open(self.config_file) as f:
                return json.load(f)
        return {
            "api_url": DEFAULT_API_URL,
            "api_key": None,
            "default_format": "table"
        }
    
    def save_config(self):
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        self.config[key] = value
        self.save_config()


class MiraiAPI:
    """API client for Mirai trading system."""
    
    def __init__(self, config: MiraiConfig):
        self.config = config
        self.base_url = config.get("api_url")
        self.api_key = config.get("api_key")
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}"
            })
    
    def request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make API request."""
        url = f"{self.base_url}/api{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            console.print(f"[red]API Error: {e}[/red]")
            sys.exit(1)
    
    def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """GET request."""
        return self.request("GET", endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """POST request."""
        return self.request("POST", endpoint, **kwargs)
    
    def put(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """PUT request."""
        return self.request("PUT", endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """DELETE request."""
        return self.request("DELETE", endpoint, **kwargs)


def get_database_path() -> Path:
    """Get path to Mirai database."""
    db_path = Path(__file__).parent.parent / "state" / "mirai.db"
    if not db_path.exists():
        console.print(f"[red]Database not found at {db_path}[/red]")
        sys.exit(1)
    return db_path


@click.group()
@click.pass_context
def cli(ctx):
    """Mirai Trading System CLI - Manage your trading system from the command line."""
    ctx.ensure_object(dict)
    ctx.obj['config'] = MiraiConfig()
    ctx.obj['api'] = MiraiAPI(ctx.obj['config'])


@cli.group()
def config():
    """Manage CLI configuration."""
    pass


@config.command()
@click.option('--api-url', help='API URL')
@click.option('--api-key', help='API Key')
@click.option('--format', type=click.Choice(['table', 'json', 'yaml']), help='Default output format')
@click.pass_context
def set(ctx, api_url, api_key, format):
    """Set configuration values."""
    config = ctx.obj['config']
    
    if api_url:
        config.set('api_url', api_url)
        console.print(f"[green]Set API URL to: {api_url}[/green]")
    
    if api_key:
        config.set('api_key', api_key)
        console.print("[green]API key set successfully[/green]")
    
    if format:
        config.set('default_format', format)
        console.print(f"[green]Set default format to: {format}[/green]")


@config.command()
@click.pass_context
def show(ctx):
    """Show current configuration."""
    config = ctx.obj['config']
    
    table = Table(title="Mirai CLI Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("API URL", config.get('api_url'))
    table.add_row("API Key", "***" if config.get('api_key') else "Not set")
    table.add_row("Default Format", config.get('default_format'))
    table.add_row("Config File", str(config.config_file))
    
    console.print(table)


@cli.group()
def status():
    """Check system status and health."""
    pass


@status.command()
@click.pass_context
def health(ctx):
    """Check system health."""
    api = ctx.obj['api']
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Checking system health...", total=None)
        
        try:
            health_data = api.get("/health")
            progress.update(task, completed=True)
            
            if health_data.get('status') == 'healthy':
                console.print("[green]✓ System is healthy[/green]")
            else:
                console.print("[red]✗ System is unhealthy[/red]")
            
            # Display detailed health checks
            table = Table(title="Health Checks")
            table.add_column("Service", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Details")
            
            checks = health_data.get('checks', {})
            for service, status in checks.items():
                status_icon = "✓" if status else "✗"
                status_color = "green" if status else "red"
                table.add_row(
                    service.title(),
                    f"[{status_color}]{status_icon}[/{status_color}]",
                    "OK" if status else "Failed"
                )
            
            console.print(table)
            
        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"[red]Failed to check health: {e}[/red]")


@status.command()
@click.pass_context
def trading(ctx):
    """Check trading status."""
    api = ctx.obj['api']
    
    try:
        status_data = api.get("/trading/status")
        
        # Create status panel
        status_text = f"""
[bold]Trading Status:[/bold] {status_data.get('status', 'Unknown')}
[bold]Mode:[/bold] {'DRY RUN' if status_data.get('dry_run') else 'LIVE TRADING'}
[bold]Daily P&L:[/bold] ${status_data.get('daily_pnl', 0):.2f}
[bold]Total P&L:[/bold] ${status_data.get('total_pnl', 0):.2f}
[bold]Active Positions:[/bold] {status_data.get('active_positions', 0)}
[bold]Last Updated:[/bold] {status_data.get('timestamp', 'Unknown')}
        """
        
        color = "green" if status_data.get('status') == 'active' else "yellow"
        panel = Panel(status_text, title="Trading System Status", border_style=color)
        console.print(panel)
        
    except Exception as e:
        console.print(f"[red]Failed to get trading status: {e}[/red]")


@cli.group()
def trading():
    """Trading operations."""
    pass


@trading.command()
@click.option('--symbol', required=True, help='Trading symbol (e.g., BTCUSDT)')
@click.option('--side', type=click.Choice(['BUY', 'SELL']), required=True, help='Order side')
@click.option('--quantity', type=float, required=True, help='Order quantity')
@click.option('--type', 'order_type', type=click.Choice(['MARKET', 'LIMIT']), default='MARKET', help='Order type')
@click.option('--price', type=float, help='Order price (for limit orders)')
@click.option('--dry-run', is_flag=True, help='Simulate order without execution')
@click.pass_context
def order(ctx, symbol, side, quantity, order_type, price, dry_run):
    """Place a trading order."""
    api = ctx.obj['api']
    
    order_data = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "quantity": quantity,
        "dry_run": dry_run
    }
    
    if order_type == 'LIMIT' and price is None:
        console.print("[red]Price is required for limit orders[/red]")
        return
    
    if price:
        order_data["price"] = price
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Placing order...", total=None)
            
            result = api.post("/trading/order", json=order_data)
            progress.update(task, completed=True)
        
        if dry_run:
            console.print("[yellow]DRY RUN - Order simulated successfully[/yellow]")
        else:
            console.print("[green]Order placed successfully[/green]")
        
        table = Table(title="Order Details")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in result.items():
            table.add_row(key.title(), str(value))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Failed to place order: {e}[/red]")


@trading.command()
@click.option('--limit', default=10, help='Number of trades to show')
@click.option('--symbol', help='Filter by symbol')
@click.option('--strategy', help='Filter by strategy')
@click.pass_context
def trades(ctx, limit, symbol, strategy):
    """Show recent trades."""
    try:
        db_path = get_database_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        query = "SELECT * FROM trades WHERE 1=1"
        params = []
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        if strategy:
            query += " AND strategy = ?"
            params.append(strategy)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor = conn.execute(query, params)
        trades = cursor.fetchall()
        
        if not trades:
            console.print("[yellow]No trades found[/yellow]")
            return
        
        table = Table(title=f"Recent Trades (Last {len(trades)})")
        table.add_column("ID", style="cyan")
        table.add_column("Symbol", style="green")
        table.add_column("Side", style="yellow")
        table.add_column("Quantity", style="blue")
        table.add_column("Price", style="magenta")
        table.add_column("P&L", style="red")
        table.add_column("Strategy")
        table.add_column("Timestamp")
        
        for trade in trades:
            pnl_color = "green" if trade['pnl'] and trade['pnl'] > 0 else "red"
            table.add_row(
                str(trade['id']),
                trade['symbol'],
                trade['side'],
                f"{trade['quantity']:.6f}",
                f"${trade['price']:.2f}" if trade['price'] else "N/A",
                f"[{pnl_color}]${trade['pnl']:.2f}[/{pnl_color}]" if trade['pnl'] else "N/A",
                trade['strategy'] or "N/A",
                trade['timestamp']
            )
        
        console.print(table)
        conn.close()
        
    except Exception as e:
        console.print(f"[red]Failed to get trades: {e}[/red]")


@trading.command()
@click.pass_context
def positions(ctx):
    """Show current positions."""
    api = ctx.obj['api']
    
    try:
        positions_data = api.get("/trading/positions")
        positions = positions_data.get('positions', [])
        
        if not positions:
            console.print("[yellow]No active positions[/yellow]")
            return
        
        table = Table(title="Current Positions")
        table.add_column("Symbol", style="cyan")
        table.add_column("Side", style="green")
        table.add_column("Size", style="blue")
        table.add_column("Entry Price", style="yellow")
        table.add_column("Mark Price", style="magenta")
        table.add_column("Unrealized P&L", style="red")
        table.add_column("ROE %")
        
        for position in positions:
            pnl = position.get('unrealized_pnl', 0)
            pnl_color = "green" if pnl > 0 else "red"
            
            roe = position.get('roe_percentage', 0)
            roe_color = "green" if roe > 0 else "red"
            
            table.add_row(
                position['symbol'],
                position['side'],
                f"{position['size']:.6f}",
                f"${position['entry_price']:.2f}",
                f"${position['mark_price']:.2f}",
                f"[{pnl_color}]${pnl:.2f}[/{pnl_color}]",
                f"[{roe_color}]{roe:.2f}%[/{roe_color}]"
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Failed to get positions: {e}[/red]")


@cli.group()
def strategies():
    """Strategy management."""
    pass


@strategies.command()
@click.pass_context
def list(ctx):
    """List available strategies."""
    api = ctx.obj['api']
    
    try:
        strategies_data = api.get("/strategies")
        strategies = strategies_data.get('strategies', [])
        
        if not strategies:
            console.print("[yellow]No strategies configured[/yellow]")
            return
        
        table = Table(title="Available Strategies")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Description")
        table.add_column("Last Run")
        
        for strategy in strategies:
            status_color = "green" if strategy.get('active') else "red"
            status_text = "Active" if strategy.get('active') else "Inactive"
            
            table.add_row(
                strategy['name'],
                f"[{status_color}]{status_text}[/{status_color}]",
                strategy.get('description', 'N/A'),
                strategy.get('last_run', 'Never')
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Failed to get strategies: {e}[/red]")


@strategies.command()
@click.argument('strategy_name')
@click.option('--action', type=click.Choice(['start', 'stop']), required=True)
@click.pass_context
def control(ctx, strategy_name, action):
    """Start or stop a strategy."""
    api = ctx.obj['api']
    
    try:
        result = api.post(f"/strategies/{strategy_name}/{action}")
        
        if action == 'start':
            console.print(f"[green]Strategy '{strategy_name}' started successfully[/green]")
        else:
            console.print(f"[yellow]Strategy '{strategy_name}' stopped successfully[/yellow]")
        
        if 'message' in result:
            console.print(f"Message: {result['message']}")
            
    except Exception as e:
        console.print(f"[red]Failed to {action} strategy: {e}[/red]")


@cli.group()
def logs():
    """Log management and viewing."""
    pass


@logs.command()
@click.option('--service', type=click.Choice(['api', 'trader', 'agent', 'all']), default='all')
@click.option('--level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']), default='INFO')
@click.option('--lines', default=50, help='Number of lines to show')
@click.option('--follow', '-f', is_flag=True, help='Follow log output')
def show(service, level, lines, follow):
    """Show recent logs."""
    logs_dir = Path(__file__).parent.parent / "logs"
    
    if not logs_dir.exists():
        console.print("[red]Logs directory not found[/red]")
        return
    
    if service == 'all':
        log_files = list(logs_dir.glob("*.log"))
    else:
        log_files = [logs_dir / f"{service}.log"]
    
    if not log_files:
        console.print("[yellow]No log files found[/yellow]")
        return
    
    for log_file in log_files:
        if not log_file.exists():
            continue
        
        console.print(f"[cyan]--- {log_file.name} ---[/cyan]")
        
        if follow:
            # Simple tail -f implementation
            import subprocess
            try:
                subprocess.run(['tail', '-f', str(log_file)])
            except KeyboardInterrupt:
                console.print("\n[yellow]Log following stopped[/yellow]")
        else:
            # Show last N lines
            with open(log_file) as f:
                all_lines = f.readlines()
                for line in all_lines[-lines:]:
                    line = line.strip()
                    if level in line or level == 'DEBUG':
                        if 'ERROR' in line:
                            console.print(f"[red]{line}[/red]")
                        elif 'WARNING' in line:
                            console.print(f"[yellow]{line}[/yellow]")
                        elif 'INFO' in line:
                            console.print(f"[green]{line}[/green]")
                        else:
                            console.print(line)


@cli.group()
def db():
    """Database operations."""
    pass


@db.command()
def info():
    """Show database information."""
    try:
        db_path = get_database_path()
        conn = sqlite3.connect(db_path)
        
        # Get table information
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        console.print(f"[cyan]Database:[/cyan] {db_path}")
        console.print(f"[cyan]Size:[/cyan] {db_path.stat().st_size / 1024:.1f} KB")
        console.print(f"[cyan]Tables:[/cyan] {len(tables)}")
        
        # Table details
        table = Table(title="Database Tables")
        table.add_column("Table", style="cyan")
        table.add_column("Rows", style="green")
        table.add_column("Columns", style="yellow")
        
        for table_name in tables:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            column_count = len(cursor.fetchall())
            
            table.add_row(table_name, str(row_count), str(column_count))
        
        console.print(table)
        conn.close()
        
    except Exception as e:
        console.print(f"[red]Failed to get database info: {e}[/red]")


@db.command()
@click.argument('query')
def query(query):
    """Execute SQL query."""
    try:
        db_path = get_database_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute(query)
        results = cursor.fetchall()
        
        if not results:
            console.print("[yellow]No results[/yellow]")
            return
        
        # Dynamic table creation based on results
        table = Table(title=f"Query Results ({len(results)} rows)")
        
        # Add columns based on first row
        for column in results[0].keys():
            table.add_column(column, style="cyan")
        
        # Add data rows
        for row in results[:100]:  # Limit to 100 rows for display
            table.add_row(*[str(value) for value in row])
        
        console.print(table)
        
        if len(results) > 100:
            console.print(f"[yellow]Showing first 100 of {len(results)} results[/yellow]")
        
        conn.close()
        
    except Exception as e:
        console.print(f"[red]Query failed: {e}[/red]")


@cli.group()
def dev():
    """Development utilities."""
    pass


@dev.command()
def setup():
    """Setup development environment."""
    console.print("[cyan]Setting up Mirai development environment...[/cyan]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # Check Python version
        task1 = progress.add_task("Checking Python version...", total=None)
        python_version = sys.version_info
        if python_version < (3, 8):
            console.print("[red]Python 3.8+ required[/red]")
            return
        progress.update(task1, completed=True)
        
        # Create directories
        task2 = progress.add_task("Creating directories...", total=None)
        project_root = Path(__file__).parent.parent
        directories = ['logs', 'state', 'reports', 'configs']
        for directory in directories:
            (project_root / directory).mkdir(exist_ok=True)
        progress.update(task2, completed=True)
        
        # Check dependencies
        task3 = progress.add_task("Checking dependencies...", total=None)
        try:
            import fastapi, sqlalchemy, redis
            progress.update(task3, completed=True)
        except ImportError as e:
            console.print(f"[red]Missing dependency: {e}[/red]")
            console.print("[yellow]Run: pip install -e .[dev][/yellow]")
            return
        
        # Check Docker
        task4 = progress.add_task("Checking Docker...", total=None)
        try:
            import subprocess
            result = subprocess.run(['docker', '--version'], capture_output=True)
            if result.returncode == 0:
                progress.update(task4, completed=True)
            else:
                console.print("[yellow]Docker not found - some features may not work[/yellow]")
        except FileNotFoundError:
            console.print("[yellow]Docker not found - some features may not work[/yellow]")
    
    console.print("[green]✓ Development environment setup complete![/green]")
    console.print("\n[cyan]Next steps:[/cyan]")
    console.print("1. Start services: [yellow]docker-compose up -d[/yellow]")
    console.print("2. Run tests: [yellow]pytest[/yellow]")
    console.print("3. Start API: [yellow]mirai api start[/yellow]")


@dev.command()
def test():
    """Run development tests."""
    console.print("[cyan]Running Mirai tests...[/cyan]")
    
    try:
        import subprocess
        result = subprocess.run(['pytest', '-v', '--tb=short'], cwd=Path(__file__).parent.parent)
        
        if result.returncode == 0:
            console.print("[green]✓ All tests passed![/green]")
        else:
            console.print("[red]✗ Some tests failed[/red]")
            
    except FileNotFoundError:
        console.print("[red]pytest not found - install with: pip install pytest[/red]")


@cli.command()
def version():
    """Show version information."""
    try:
        # Try to get version from package
        import pkg_resources
        version = pkg_resources.get_distribution("mirai-agent").version
    except:
        version = "development"
    
    info = f"""
[bold cyan]Mirai Trading System CLI[/bold cyan]

[bold]Version:[/bold] {version}
[bold]Python:[/bold] {sys.version.split()[0]}
[bold]Platform:[/bold] {sys.platform}
[bold]Config:[/bold] {CONFIG_FILE}

[italic]An autonomous trading system powered by AI[/italic]
    """
    
    panel = Panel(info, title="Version Information", border_style="cyan")
    console.print(panel)


if __name__ == '__main__':
    cli()
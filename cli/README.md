# Mirai CLI Tool

The Mirai CLI provides a comprehensive command-line interface for managing and interacting with the Mirai Trading System.

## Installation

### Quick Setup

```bash
# From project root
cd cli
python setup.py
```

This will:
- Install required dependencies (click, rich, requests)
- Create a system-wide `mirai` command
- Set up configuration directory

### Manual Installation

```bash
# Install dependencies
pip install click rich requests

# Make CLI executable
chmod +x cli/mirai.py

# Create symlink (optional)
ln -s $(pwd)/cli/mirai.py ~/.local/bin/mirai

# Add to PATH if needed
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Configuration

Configure the CLI for your environment:

```bash
# Set API URL and key
mirai config set --api-url http://localhost:8001
mirai config set --api-key your_api_key

# View current configuration
mirai config show
```

Configuration is stored in `~/.mirai/config.json`.

## Usage

### System Status

```bash
# Check system health
mirai status health

# Check trading status
mirai status trading
```

### Trading Operations

```bash
# View recent trades
mirai trading trades --limit 20

# View current positions
mirai trading positions

# Place an order (dry-run)
mirai trading order --symbol BTCUSDT --side BUY --quantity 0.001 --dry-run

# Place a live order
mirai trading order --symbol BTCUSDT --side BUY --quantity 0.001 --type MARKET
```

### Strategy Management

```bash
# List available strategies
mirai strategies list

# Start a strategy
mirai strategies control my_strategy --action start

# Stop a strategy
mirai strategies control my_strategy --action stop
```

### Log Management

```bash
# View recent logs
mirai logs show --service api --lines 50

# Follow logs in real-time
mirai logs show --service trader --follow

# Filter by log level
mirai logs show --level ERROR --lines 100
```

### Database Operations

```bash
# Database information
mirai db info

# Execute SQL query
mirai db query "SELECT * FROM trades WHERE symbol='BTCUSDT' LIMIT 10"

# View table structure
mirai db query "PRAGMA table_info(trades)"
```

### Development Utilities

```bash
# Setup development environment
mirai dev setup

# Run tests
mirai dev test

# Show version information
mirai version
```

## Examples

### Daily Trading Review

```bash
# Check system health
mirai status health

# Review today's performance
mirai status trading

# View recent trades
mirai trading trades --limit 20

# Check active positions
mirai trading positions

# Review any errors
mirai logs show --level ERROR --lines 50
```

### Strategy Management

```bash
# List all strategies
mirai strategies list

# Start a specific strategy
mirai strategies control scalping_bot --action start

# Monitor strategy performance
mirai logs show --service agent --follow
```

### Risk Management

```bash
# Check current exposure
mirai trading positions

# Review recent losses
mirai db query "
  SELECT symbol, side, quantity, price, pnl, timestamp 
  FROM trades 
  WHERE pnl < 0 
  ORDER BY timestamp DESC 
  LIMIT 10
"

# Emergency stop all strategies
mirai strategies control all --action stop
```

### Performance Analysis

```bash
# Daily P&L summary
mirai db query "
  SELECT 
    DATE(timestamp) as date,
    COUNT(*) as trades,
    SUM(pnl) as daily_pnl,
    AVG(pnl) as avg_pnl
  FROM trades 
  WHERE timestamp >= date('now', '-7 days')
  GROUP BY DATE(timestamp)
  ORDER BY date DESC
"

# Strategy performance comparison
mirai db query "
  SELECT 
    strategy,
    COUNT(*) as trades,
    SUM(pnl) as total_pnl,
    AVG(pnl) as avg_pnl,
    MAX(pnl) as best_trade,
    MIN(pnl) as worst_trade
  FROM trades 
  WHERE strategy IS NOT NULL
  GROUP BY strategy
  ORDER BY total_pnl DESC
"
```

## Advanced Usage

### Custom Queries

The CLI supports complex SQL queries for advanced analysis:

```bash
# Risk-adjusted returns by symbol
mirai db query "
  SELECT 
    symbol,
    COUNT(*) as trades,
    SUM(pnl) as total_pnl,
    STDEV(pnl) as volatility,
    SUM(pnl) / STDEV(pnl) as sharpe_ratio
  FROM trades 
  WHERE pnl IS NOT NULL
  GROUP BY symbol
  HAVING COUNT(*) > 10
  ORDER BY sharpe_ratio DESC
"

# Hourly trading patterns
mirai db query "
  SELECT 
    strftime('%H', timestamp) as hour,
    COUNT(*) as trades,
    AVG(pnl) as avg_pnl
  FROM trades 
  GROUP BY strftime('%H', timestamp)
  ORDER BY hour
"
```

### Automation Scripts

Use the CLI in shell scripts for automation:

```bash
#!/bin/bash
# Daily trading report script

echo "Mirai Trading Daily Report - $(date)"
echo "=================================="

# System health
echo "System Health:"
mirai status health

# Trading status
echo -e "\nTrading Status:"
mirai status trading

# Recent performance
echo -e "\nRecent Trades:"
mirai trading trades --limit 10

# Active positions
echo -e "\nActive Positions:"
mirai trading positions

# Error summary
echo -e "\nRecent Errors:"
mirai logs show --level ERROR --lines 5
```

### Integration with Other Tools

```bash
# Export data for analysis
mirai db query "SELECT * FROM trades" > trades_export.csv

# Send alerts via webhook
if mirai status health | grep -q "unhealthy"; then
  curl -X POST https://hooks.slack.com/... \
    -d '{"text": "Mirai system health check failed"}'
fi

# Backup database
cp ~/.mirai/state/mirai.db "backup_$(date +%Y%m%d).db"
```

## Troubleshooting

### Common Issues

1. **Command not found**: Ensure `~/.local/bin` is in your PATH
2. **API connection failed**: Check API URL and key configuration
3. **Database not found**: Ensure Mirai system is properly initialized
4. **Permission denied**: Check file permissions on CLI script

### Debug Mode

Enable verbose output for troubleshooting:

```bash
# Add --verbose flag to any command
mirai --verbose status health

# Check configuration
mirai config show

# Test API connectivity
curl $(mirai config show | grep "API URL" | awk '{print $3}')/api/health
```

### Getting Help

```bash
# General help
mirai --help

# Command-specific help
mirai trading --help
mirai logs show --help

# Show version and environment info
mirai version
```

## Contributing

The CLI tool is part of the Mirai Trading System. To contribute:

1. Fork the repository
2. Create a feature branch
3. Add tests for new commands
4. Update documentation
5. Submit a pull request

### Adding New Commands

```python
@cli.group()
def my_feature():
    """My new feature description."""
    pass

@my_feature.command()
@click.option('--param', help='Parameter description')
@click.pass_context
def my_command(ctx, param):
    """Command description."""
    # Implementation here
    pass
```

The CLI follows the Click framework conventions and Rich library for beautiful terminal output.
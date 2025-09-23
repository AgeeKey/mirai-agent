# Log Files

This directory contains application log files:

- `mirai-agent.log`: General application logs
- `mirai-agent-error.log`: Error-specific logs

Log files are automatically rotated when they reach 10MB with 5 backup copies maintained.

## Log Levels

- DEBUG: Detailed information for diagnosing problems
- INFO: General information about program execution
- WARNING: Indication that something unexpected happened
- ERROR: Serious problem that prevented the program from performing a function
- CRITICAL: Serious error that may prevent the program from continuing

## Log Format

```
YYYY-MM-DD HH:MM:SS [LEVEL   ] module_name:line_number - function_name(): message
```

## Configuration

Logging configuration is managed in `configs/logging.yaml`.
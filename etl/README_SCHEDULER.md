# ETL Scheduler Guide

This guide explains how to use the ETL scheduler for automated GPU price monitoring.

## Overview

The ETL scheduler automates the execution of two main tasks:
1. **Price Crawl**: Collects GPU prices from 다나와 (default: daily at 09:00)
2. **Reddit Collection**: Collects market signals from Reddit (default: daily at 10:00)

## Quick Start

### Start the Scheduler Daemon

```bash
# Using the CLI tool (recommended)
python cli.py scheduler start

# Or using main.py
python main.py --task=start_scheduler

# Or using scheduler.py directly
python scheduler.py
```

The scheduler will run in the foreground. Press `Ctrl+C` to stop it.

### Check Scheduler Status

```bash
python cli.py scheduler status
```

### List Scheduled Jobs

```bash
python cli.py scheduler jobs
```

## Manual Task Execution

You can manually trigger tasks without waiting for the scheduled time:

### Trigger Price Crawl

```bash
# Using CLI (recommended)
python cli.py trigger price-crawl

# Or using main.py
python main.py --task=price_crawl
```

### Trigger Reddit Collection

```bash
# Using CLI (recommended)
python cli.py trigger reddit-collection

# Or using main.py
python main.py --task=reddit_collection
```

### Run Full Pipeline

```bash
# Using CLI
python cli.py run full

# Or using main.py
python main.py --task=full
```

## Configuration

The scheduler uses configuration from `.env` file or environment variables:

```bash
# Scheduler Configuration
PRICE_CRAWL_HOUR=9          # Hour to run price crawl (0-23)
PRICE_CRAWL_MINUTE=0        # Minute to run price crawl (0-59)
REDDIT_CRAWL_HOUR=10        # Hour to run Reddit collection (0-23)
REDDIT_CRAWL_MINUTE=0       # Minute to run Reddit collection (0-59)

# Logging
LOG_LEVEL=INFO              # Logging level (DEBUG, INFO, WARNING, ERROR)
```

### Example: Change Schedule Times

To run price crawl at 8:30 AM and Reddit collection at 11:00 AM:

```bash
# In .env file
PRICE_CRAWL_HOUR=8
PRICE_CRAWL_MINUTE=30
REDDIT_CRAWL_HOUR=11
REDDIT_CRAWL_MINUTE=0
```

## Logging

The scheduler logs to two locations:
1. **Console output**: Real-time logs displayed in terminal
2. **scheduler.log**: Persistent log file in the `etl/` directory

### View Logs

```bash
# View real-time logs (when scheduler is running)
# Logs are displayed in the terminal

# View historical logs
tail -f scheduler.log

# View last 100 lines
tail -n 100 scheduler.log

# Search for errors
grep ERROR scheduler.log
```

## Error Handling

The scheduler is designed to be resilient:

- **Job Failure**: If a scheduled job fails, the error is logged and the scheduler continues running
- **Network Errors**: Temporary network issues are retried with exponential backoff
- **Database Errors**: Connection errors are retried up to 3 times
- **Concurrent Execution**: Only one instance of each job can run at a time

### Monitoring Job Failures

Check the logs for error messages:

```bash
# Check for job failures
grep "job failed" scheduler.log

# Check for specific errors
grep "ERROR" scheduler.log | tail -n 20
```

## Production Deployment

### Running as a Background Service

For production, run the scheduler as a system service:

#### Using systemd (Linux)

Create `/etc/systemd/system/etl-scheduler.service`:

```ini
[Unit]
Description=GPU Price Monitoring ETL Scheduler
After=network.target postgresql.service

[Service]
Type=simple
User=etl
WorkingDirectory=/path/to/etl
Environment="PATH=/path/to/etl/venv/bin"
ExecStart=/path/to/etl/venv/bin/python scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable etl-scheduler
sudo systemctl start etl-scheduler
sudo systemctl status etl-scheduler
```

#### Using Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "scheduler.py"]
```

Build and run:

```bash
docker build -t etl-scheduler .
docker run -d --name etl-scheduler \
  --env-file .env \
  --restart unless-stopped \
  etl-scheduler
```

### Using cron (Alternative)

If you prefer cron over APScheduler:

```bash
# Edit crontab
crontab -e

# Add these lines
0 9 * * * cd /path/to/etl && /path/to/venv/bin/python main.py --task=price_crawl >> /var/log/etl-price-crawl.log 2>&1
0 10 * * * cd /path/to/etl && /path/to/venv/bin/python main.py --task=reddit_collection >> /var/log/etl-reddit.log 2>&1
```

## Troubleshooting

### Scheduler Won't Start

1. Check if another instance is running:
   ```bash
   ps aux | grep scheduler.py
   ```

2. Check for port conflicts or permission issues in logs

3. Verify database connection:
   ```bash
   python -c "from db_connection import db_manager; print('DB OK')"
   ```

### Jobs Not Executing

1. Verify scheduler is running:
   ```bash
   python cli.py scheduler status
   ```

2. Check scheduled times:
   ```bash
   python cli.py scheduler jobs
   ```

3. Review logs for errors:
   ```bash
   tail -f scheduler.log
   ```

### Jobs Failing

1. Test job manually:
   ```bash
   python cli.py trigger price-crawl
   ```

2. Check database connectivity:
   ```bash
   python -c "from db_connection import db_manager; db_manager.test_connection()"
   ```

3. Verify environment variables:
   ```bash
   python -c "from config import settings; print(settings.database_url)"
   ```

## CLI Reference

### Run Commands

```bash
python cli.py run full                  # Run full ETL pipeline
python cli.py run price-crawl           # Run price crawl only
python cli.py run reddit-collection     # Run Reddit collection only
```

### Scheduler Commands

```bash
python cli.py scheduler start           # Start scheduler daemon
python cli.py scheduler status          # Check if scheduler is running
python cli.py scheduler jobs            # List scheduled jobs
```

### Trigger Commands

```bash
python cli.py trigger price-crawl       # Manually trigger price crawl
python cli.py trigger reddit-collection # Manually trigger Reddit collection
```

## Best Practices

1. **Monitor Logs**: Regularly check logs for errors and warnings
2. **Test Manually**: Test jobs manually before relying on scheduled execution
3. **Set Alerts**: Configure monitoring alerts for job failures
4. **Backup Data**: Regularly backup the PostgreSQL database
5. **Update Dependencies**: Keep Python packages up to date for security
6. **Resource Monitoring**: Monitor CPU, memory, and disk usage
7. **Network Reliability**: Ensure stable network connection for web scraping

## Support

For issues or questions:
1. Check logs: `tail -f scheduler.log`
2. Review error messages in console output
3. Test components individually using manual triggers
4. Verify configuration in `.env` file

#!/usr/bin/env python3
"""
Command-line interface for GPU Price Monitoring ETL System.

This module provides a comprehensive CLI for managing ETL tasks and the scheduler.

Usage:
    python cli.py run full                  # Run full ETL pipeline
    python cli.py run price-crawl           # Run price crawl only
    python cli.py run reddit-collection     # Run Reddit collection only
    
    python cli.py scheduler start           # Start scheduler daemon
    python cli.py scheduler status          # Check scheduler status
    python cli.py scheduler jobs            # List scheduled jobs
    
    python cli.py trigger price-crawl       # Manually trigger price crawl
    python cli.py trigger reddit-collection # Manually trigger Reddit collection

Validates: Requirement 9.4
"""

import argparse
import logging
import sys
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


def run_etl_task(task: str) -> int:
    """
    Run an ETL task.
    
    Args:
        task: Task to run ('full', 'price-crawl', or 'reddit-collection')
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    from main import ETLPipeline, run_price_crawl_only, run_reddit_collection_only
    
    logger.info(f"Running ETL task: {task}")
    
    try:
        if task == 'price-crawl':
            stats = run_price_crawl_only()
        elif task == 'reddit-collection':
            stats = run_reddit_collection_only()
        else:  # full
            pipeline = ETLPipeline()
            stats = pipeline.run_full_pipeline()
        
        return 0 if stats.get('success', False) else 1
        
    except Exception as e:
        logger.error(f"Task failed: {e}", exc_info=True)
        return 1


def start_scheduler() -> int:
    """
    Start the scheduler daemon.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    from scheduler import ETLScheduler
    
    logger.info("Starting scheduler daemon...")
    
    try:
        scheduler = ETLScheduler()
        scheduler.schedule_price_crawl()
        scheduler.schedule_reddit_collection()
        scheduler.start()
        
        # Keep running until interrupted
        import time
        try:
            logger.info("Scheduler is running. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Received shutdown signal")
            scheduler.stop()
            logger.info("Scheduler shutdown complete")
            return 0
        
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}", exc_info=True)
        return 1


def check_scheduler_status() -> int:
    """
    Check if scheduler is running.
    
    Returns:
        Exit code (0 if running, 1 if not running)
    """
    # Check if scheduler process is running by looking for PID file
    pid_file = '/tmp/etl_scheduler.pid'
    
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process is running
            try:
                os.kill(pid, 0)  # Signal 0 just checks if process exists
                logger.info(f"✓ Scheduler is running (PID: {pid})")
                return 0
            except OSError:
                logger.info("✗ Scheduler is not running (stale PID file)")
                os.remove(pid_file)
                return 1
        except Exception as e:
            logger.error(f"Error checking scheduler status: {e}")
            return 1
    else:
        logger.info("✗ Scheduler is not running")
        return 1


def list_scheduled_jobs() -> int:
    """
    List all scheduled jobs.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    from config import settings
    
    logger.info("Scheduled Jobs:")
    logger.info("-" * 60)
    
    # Price crawl job
    logger.info(f"1. Daily Price Crawl")
    logger.info(f"   Schedule: Every day at {settings.price_crawl_hour:02d}:{settings.price_crawl_minute:02d}")
    logger.info(f"   Task: Crawl GPU prices from 다나와")
    logger.info("")
    
    # Reddit collection job
    logger.info(f"2. Daily Reddit Collection")
    logger.info(f"   Schedule: Every day at {settings.reddit_crawl_hour:02d}:{settings.reddit_crawl_minute:02d}")
    logger.info(f"   Task: Collect market signals from Reddit")
    logger.info("")
    
    logger.info("-" * 60)
    logger.info("Note: These jobs run when the scheduler daemon is active.")
    logger.info("Use 'python cli.py scheduler start' to start the daemon.")
    
    return 0


def trigger_task(task: str) -> int:
    """
    Manually trigger a scheduled task.
    
    Args:
        task: Task to trigger ('price-crawl' or 'reddit-collection')
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    from scheduler import ETLScheduler
    
    logger.info(f"Manually triggering task: {task}")
    
    try:
        scheduler = ETLScheduler()
        
        if task == 'price-crawl':
            scheduler.run_price_crawl_now()
        elif task == 'reddit-collection':
            scheduler.run_reddit_collection_now()
        else:
            logger.error(f"Unknown task: {task}")
            return 1
        
        logger.info(f"✓ Task '{task}' completed")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to trigger task: {e}", exc_info=True)
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='GPU Price Monitoring ETL System CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run ETL tasks
  python cli.py run full
  python cli.py run price-crawl
  python cli.py run reddit-collection
  
  # Manage scheduler
  python cli.py scheduler start
  python cli.py scheduler status
  python cli.py scheduler jobs
  
  # Manually trigger tasks
  python cli.py trigger price-crawl
  python cli.py trigger reddit-collection
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run an ETL task')
    run_parser.add_argument(
        'task',
        choices=['full', 'price-crawl', 'reddit-collection'],
        help='Task to run'
    )
    
    # Scheduler command
    scheduler_parser = subparsers.add_parser('scheduler', help='Manage scheduler')
    scheduler_parser.add_argument(
        'action',
        choices=['start', 'status', 'jobs'],
        help='Scheduler action'
    )
    
    # Trigger command
    trigger_parser = subparsers.add_parser('trigger', help='Manually trigger a task')
    trigger_parser.add_argument(
        'task',
        choices=['price-crawl', 'reddit-collection'],
        help='Task to trigger'
    )
    
    args = parser.parse_args()
    
    # Handle commands
    if args.command == 'run':
        exit_code = run_etl_task(args.task)
    elif args.command == 'scheduler':
        if args.action == 'start':
            exit_code = start_scheduler()
        elif args.action == 'status':
            exit_code = check_scheduler_status()
        elif args.action == 'jobs':
            exit_code = list_scheduled_jobs()
        else:
            logger.error(f"Unknown scheduler action: {args.action}")
            exit_code = 1
    elif args.command == 'trigger':
        exit_code = trigger_task(args.task)
    else:
        parser.print_help()
        exit_code = 1
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

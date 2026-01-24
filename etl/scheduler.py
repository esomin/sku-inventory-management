"""
Scheduler for GPU Price Monitoring ETL System.

This module provides automated scheduling for ETL tasks using APScheduler,
allowing daily execution of price crawling and Reddit collection jobs.

Validates: Requirements 9.1, 9.2, 9.3
"""

import logging
import sys
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from config import settings
from main import run_price_crawl_only, run_reddit_collection_only

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scheduler.log')
    ]
)

logger = logging.getLogger(__name__)


class ETLScheduler:
    """
    Scheduler for ETL tasks.
    
    This class manages scheduled execution of price crawling and Reddit collection
    tasks using APScheduler. It provides both automated scheduling and manual
    trigger capabilities.
    
    Validates: Requirements 9.1, 9.2, 9.3
    """
    
    def __init__(self):
        """Initialize the ETL scheduler."""
        logger.info("Initializing ETL Scheduler")
        
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_listener(self._job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        
        # Track job execution
        self.job_history = []
    
    def schedule_price_crawl(self, hour: Optional[int] = None, minute: Optional[int] = None) -> None:
        """
        Schedule daily price crawl at specified time.
        
        Args:
            hour: Hour to run (0-23), defaults to config value
            minute: Minute to run (0-59), defaults to config value
        
        Validates: Requirement 9.1
        """
        hour = hour if hour is not None else settings.price_crawl_hour
        minute = minute if minute is not None else settings.price_crawl_minute
        
        trigger = CronTrigger(hour=hour, minute=minute)
        
        self.scheduler.add_job(
            func=self._run_price_crawl_job,
            trigger=trigger,
            id='price_crawl',
            name='Daily Price Crawl',
            replace_existing=True,
            max_instances=1  # Prevent concurrent execution
        )
        
        logger.info(f"Scheduled price crawl for daily execution at {hour:02d}:{minute:02d}")
    
    def schedule_reddit_collection(self, hour: Optional[int] = None, minute: Optional[int] = None) -> None:
        """
        Schedule daily Reddit collection at specified time.
        
        Args:
            hour: Hour to run (0-23), defaults to config value
            minute: Minute to run (0-59), defaults to config value
        
        Validates: Requirement 9.2
        """
        hour = hour if hour is not None else settings.reddit_crawl_hour
        minute = minute if minute is not None else settings.reddit_crawl_minute
        
        trigger = CronTrigger(hour=hour, minute=minute)
        
        self.scheduler.add_job(
            func=self._run_reddit_collection_job,
            trigger=trigger,
            id='reddit_collection',
            name='Daily Reddit Collection',
            replace_existing=True,
            max_instances=1  # Prevent concurrent execution
        )
        
        logger.info(f"Scheduled Reddit collection for daily execution at {hour:02d}:{minute:02d}")
    
    def run_price_crawl_now(self) -> None:
        """
        Manually trigger price crawl immediately.
        
        This method runs the price crawl job synchronously and returns
        when the job completes.
        """
        logger.info("Manually triggering price crawl...")
        self._run_price_crawl_job()
    
    def run_reddit_collection_now(self) -> None:
        """
        Manually trigger Reddit collection immediately.
        
        This method runs the Reddit collection job synchronously and returns
        when the job completes.
        """
        logger.info("Manually triggering Reddit collection...")
        self._run_reddit_collection_job()
    
    def start(self) -> None:
        """
        Start the scheduler daemon.
        
        This method starts the background scheduler and blocks until
        interrupted (e.g., by Ctrl+C).
        """
        if not self.scheduler.running:
            logger.info("Starting ETL Scheduler...")
            self.scheduler.start()
            logger.info("✓ Scheduler started successfully")
            
            # Log scheduled jobs
            jobs = self.scheduler.get_jobs()
            if jobs:
                logger.info(f"Scheduled jobs ({len(jobs)}):")
                for job in jobs:
                    logger.info(f"  - {job.name} (ID: {job.id})")
                    logger.info(f"    Next run: {job.next_run_time}")
            else:
                logger.warning("No jobs scheduled")
        else:
            logger.warning("Scheduler is already running")
    
    def stop(self) -> None:
        """
        Stop the scheduler daemon.
        
        This method gracefully shuts down the scheduler, allowing
        currently running jobs to complete.
        """
        if self.scheduler.running:
            logger.info("Stopping ETL Scheduler...")
            self.scheduler.shutdown(wait=True)
            logger.info("✓ Scheduler stopped successfully")
        else:
            logger.warning("Scheduler is not running")
    
    def _run_price_crawl_job(self) -> None:
        """
        Execute the price crawl job.
        
        This method wraps the price crawl execution with error handling
        to ensure scheduler continues even if the job fails.
        
        Validates: Requirement 9.3
        """
        job_start = datetime.now()
        logger.info("=" * 80)
        logger.info("EXECUTING SCHEDULED JOB: Price Crawl")
        logger.info("=" * 80)
        
        try:
            stats = run_price_crawl_only()
            
            job_end = datetime.now()
            duration = (job_end - job_start).total_seconds()
            
            # Record job execution
            self.job_history.append({
                'job': 'price_crawl',
                'start_time': job_start,
                'end_time': job_end,
                'duration_seconds': duration,
                'success': stats.get('success', False),
                'stats': stats
            })
            
            if stats.get('success', False):
                logger.info(f"✓ Price crawl job completed successfully in {duration:.2f}s")
            else:
                logger.error(f"✗ Price crawl job failed after {duration:.2f}s")
                logger.error(f"Error: {stats.get('fatal_error', 'Unknown error')}")
            
        except Exception as e:
            job_end = datetime.now()
            duration = (job_end - job_start).total_seconds()
            
            logger.error(f"✗ Price crawl job failed with exception after {duration:.2f}s", exc_info=True)
            
            # Record failed job execution
            self.job_history.append({
                'job': 'price_crawl',
                'start_time': job_start,
                'end_time': job_end,
                'duration_seconds': duration,
                'success': False,
                'error': str(e)
            })
            
            # Don't re-raise - scheduler should continue
        
        logger.info("=" * 80)
    
    def _run_reddit_collection_job(self) -> None:
        """
        Execute the Reddit collection job.
        
        This method wraps the Reddit collection execution with error handling
        to ensure scheduler continues even if the job fails.
        
        Validates: Requirement 9.3
        """
        job_start = datetime.now()
        logger.info("=" * 80)
        logger.info("EXECUTING SCHEDULED JOB: Reddit Collection")
        logger.info("=" * 80)
        
        try:
            stats = run_reddit_collection_only()
            
            job_end = datetime.now()
            duration = (job_end - job_start).total_seconds()
            
            # Record job execution
            self.job_history.append({
                'job': 'reddit_collection',
                'start_time': job_start,
                'end_time': job_end,
                'duration_seconds': duration,
                'success': stats.get('success', False),
                'stats': stats
            })
            
            if stats.get('success', False):
                logger.info(f"✓ Reddit collection job completed successfully in {duration:.2f}s")
            else:
                logger.error(f"✗ Reddit collection job failed after {duration:.2f}s")
                logger.error(f"Error: {stats.get('fatal_error', 'Unknown error')}")
            
        except Exception as e:
            job_end = datetime.now()
            duration = (job_end - job_start).total_seconds()
            
            logger.error(f"✗ Reddit collection job failed with exception after {duration:.2f}s", exc_info=True)
            
            # Record failed job execution
            self.job_history.append({
                'job': 'reddit_collection',
                'start_time': job_start,
                'end_time': job_end,
                'duration_seconds': duration,
                'success': False,
                'error': str(e)
            })
            
            # Don't re-raise - scheduler should continue
        
        logger.info("=" * 80)
    
    def _job_listener(self, event) -> None:
        """
        Listen to job execution events.
        
        This method logs job execution and error events for monitoring.
        
        Args:
            event: APScheduler event object
        """
        if event.exception:
            logger.error(
                f"Job {event.job_id} raised an exception: {event.exception}",
                exc_info=True
            )
        else:
            logger.debug(f"Job {event.job_id} executed successfully")


def main():
    """
    Main entry point for the scheduler.
    
    This function initializes the scheduler, sets up scheduled jobs,
    and runs the scheduler daemon until interrupted.
    """
    logger.info("Starting GPU Price Monitoring ETL Scheduler")
    
    # Create scheduler instance
    scheduler = ETLScheduler()
    
    # Schedule jobs with configured times
    scheduler.schedule_price_crawl()
    scheduler.schedule_reddit_collection()
    
    # Start scheduler
    scheduler.start()
    
    try:
        # Keep the main thread alive
        logger.info("Scheduler is running. Press Ctrl+C to stop.")
        
        import time
        while True:
            time.sleep(1)
    
    except (KeyboardInterrupt, SystemExit):
        logger.info("Received shutdown signal")
        scheduler.stop()
        logger.info("Scheduler shutdown complete")
        sys.exit(0)


if __name__ == '__main__':
    main()

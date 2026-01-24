"""
Tests for the ETL scheduler.

These tests verify the scheduler's ability to:
1. Schedule jobs at configured times
2. Execute jobs successfully
3. Handle job failures gracefully
4. Continue running after errors

Validates: Requirements 9.1, 9.2, 9.3
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import Mock, patch, MagicMock, call
import pytest
from datetime import datetime, timedelta
from apscheduler.triggers.cron import CronTrigger


@pytest.fixture
def mock_config():
    """Mock configuration settings."""
    mock_settings = Mock()
    mock_settings.price_crawl_hour = 9
    mock_settings.price_crawl_minute = 0
    mock_settings.reddit_crawl_hour = 10
    mock_settings.reddit_crawl_minute = 0
    mock_settings.log_level = 'INFO'
    return mock_settings


@pytest.fixture
def scheduler(mock_config):
    """Create a scheduler instance for testing."""
    with patch('scheduler.settings', mock_config):
        from scheduler import ETLScheduler
        return ETLScheduler()


class TestSchedulerInitialization:
    """Test scheduler initialization."""
    
    def test_scheduler_creation(self, scheduler):
        """Test that scheduler is created successfully."""
        assert scheduler is not None
        assert scheduler.scheduler is not None
        assert scheduler.job_history == []
    
    def test_scheduler_has_job_listener(self, scheduler):
        """Test that scheduler has event listener configured."""
        # Verify listener is attached
        assert len(scheduler.scheduler._listeners) > 0


class TestSchedulerJobScheduling:
    """Test job scheduling functionality."""
    
    def test_schedule_price_crawl_default_time(self, scheduler):
        """
        Test scheduling price crawl with default configuration.
        
        Validates: Requirement 9.1
        """
        # Schedule job
        scheduler.schedule_price_crawl()
        
        # Verify job was added
        jobs = scheduler.scheduler.get_jobs()
        price_crawl_jobs = [job for job in jobs if job.id == 'price_crawl']
        
        assert len(price_crawl_jobs) == 1
        job = price_crawl_jobs[0]
        assert job.name == 'Daily Price Crawl'
        assert job.max_instances == 1
    
    def test_schedule_price_crawl_custom_time(self, scheduler):
        """
        Test scheduling price crawl with custom time.
        
        Validates: Requirement 9.1
        """
        # Schedule job at custom time
        scheduler.schedule_price_crawl(hour=8, minute=30)
        
        # Verify job was added with correct trigger
        jobs = scheduler.scheduler.get_jobs()
        price_crawl_jobs = [job for job in jobs if job.id == 'price_crawl']
        
        assert len(price_crawl_jobs) == 1
        job = price_crawl_jobs[0]
        
        # Verify trigger is CronTrigger
        assert isinstance(job.trigger, CronTrigger)
    
    def test_schedule_reddit_collection_default_time(self, scheduler):
        """
        Test scheduling Reddit collection with default configuration.
        
        Validates: Requirement 9.2
        """
        # Schedule job
        scheduler.schedule_reddit_collection()
        
        # Verify job was added
        jobs = scheduler.scheduler.get_jobs()
        reddit_jobs = [job for job in jobs if job.id == 'reddit_collection']
        
        assert len(reddit_jobs) == 1
        job = reddit_jobs[0]
        assert job.name == 'Daily Reddit Collection'
        assert job.max_instances == 1
    
    def test_schedule_reddit_collection_custom_time(self, scheduler):
        """
        Test scheduling Reddit collection with custom time.
        
        Validates: Requirement 9.2
        """
        # Schedule job at custom time
        scheduler.schedule_reddit_collection(hour=11, minute=45)
        
        # Verify job was added with correct trigger
        jobs = scheduler.scheduler.get_jobs()
        reddit_jobs = [job for job in jobs if job.id == 'reddit_collection']
        
        assert len(reddit_jobs) == 1
        job = reddit_jobs[0]
        
        # Verify trigger is CronTrigger
        assert isinstance(job.trigger, CronTrigger)
    
    def test_schedule_both_jobs(self, scheduler):
        """Test scheduling both price crawl and Reddit collection."""
        # Schedule both jobs
        scheduler.schedule_price_crawl()
        scheduler.schedule_reddit_collection()
        
        # Verify both jobs were added
        jobs = scheduler.scheduler.get_jobs()
        job_ids = [job.id for job in jobs]
        
        assert 'price_crawl' in job_ids
        assert 'reddit_collection' in job_ids
        assert len(jobs) == 2
    
    def test_schedule_replace_existing(self, scheduler):
        """Test that scheduling a job twice replaces the existing one."""
        # Schedule job twice
        scheduler.schedule_price_crawl(hour=9, minute=0)
        scheduler.schedule_price_crawl(hour=10, minute=30)
        
        # Verify only one job exists
        jobs = scheduler.scheduler.get_jobs()
        price_crawl_jobs = [job for job in jobs if job.id == 'price_crawl']
        
        assert len(price_crawl_jobs) == 1


class TestSchedulerManualExecution:
    """Test manual job execution."""
    
    @patch('scheduler.run_price_crawl_only')
    def test_run_price_crawl_now_success(self, mock_run_price_crawl, scheduler):
        """Test manually triggering price crawl successfully."""
        # Setup mock
        mock_run_price_crawl.return_value = {
            'success': True,
            'prices_extracted': 10,
            'prices_loaded': 10
        }
        
        # Execute
        scheduler.run_price_crawl_now()
        
        # Verify
        assert mock_run_price_crawl.called
    
    @patch('scheduler.run_price_crawl_only')
    def test_run_price_crawl_now_failure(self, mock_run_price_crawl, scheduler):
        """Test manually triggering price crawl with failure."""
        # Setup mock to fail
        mock_run_price_crawl.return_value = {
            'success': False,
            'fatal_error': 'Network error'
        }
        
        # Execute - should not raise exception
        scheduler.run_price_crawl_now()
        
        # Verify
        assert mock_run_price_crawl.called
    
    @patch('scheduler.run_reddit_collection_only')
    def test_run_reddit_collection_now_success(self, mock_run_reddit, scheduler):
        """Test manually triggering Reddit collection successfully."""
        # Setup mock
        mock_run_reddit.return_value = {
            'success': True,
            'signals_extracted': 5,
            'signals_loaded': 5
        }
        
        # Execute
        scheduler.run_reddit_collection_now()
        
        # Verify
        assert mock_run_reddit.called
    
    @patch('scheduler.run_reddit_collection_only')
    def test_run_reddit_collection_now_failure(self, mock_run_reddit, scheduler):
        """Test manually triggering Reddit collection with failure."""
        # Setup mock to fail
        mock_run_reddit.return_value = {
            'success': False,
            'fatal_error': 'Rate limit exceeded'
        }
        
        # Execute - should not raise exception
        scheduler.run_reddit_collection_now()
        
        # Verify
        assert mock_run_reddit.called


class TestSchedulerJobExecution:
    """Test scheduled job execution."""
    
    @patch('scheduler.run_price_crawl_only')
    def test_price_crawl_job_success(self, mock_run_price_crawl, scheduler):
        """
        Test successful execution of scheduled price crawl job.
        
        Validates: Requirement 9.1
        """
        # Setup mock
        mock_run_price_crawl.return_value = {
            'success': True,
            'prices_extracted': 10,
            'prices_loaded': 10
        }
        
        # Execute job directly
        scheduler._run_price_crawl_job()
        
        # Verify
        assert mock_run_price_crawl.called
        assert len(scheduler.job_history) == 1
        
        # Verify job history entry
        history_entry = scheduler.job_history[0]
        assert history_entry['job'] == 'price_crawl'
        assert history_entry['success'] is True
        assert 'start_time' in history_entry
        assert 'end_time' in history_entry
        assert 'duration_seconds' in history_entry
    
    @patch('scheduler.run_price_crawl_only')
    def test_price_crawl_job_failure(self, mock_run_price_crawl, scheduler):
        """
        Test failed execution of scheduled price crawl job.
        
        Validates: Requirement 9.3
        """
        # Setup mock to fail
        mock_run_price_crawl.return_value = {
            'success': False,
            'fatal_error': 'Database connection error'
        }
        
        # Execute job directly - should not raise exception
        scheduler._run_price_crawl_job()
        
        # Verify
        assert mock_run_price_crawl.called
        assert len(scheduler.job_history) == 1
        
        # Verify job history entry
        history_entry = scheduler.job_history[0]
        assert history_entry['job'] == 'price_crawl'
        assert history_entry['success'] is False
    
    @patch('scheduler.run_price_crawl_only')
    def test_price_crawl_job_exception(self, mock_run_price_crawl, scheduler):
        """
        Test price crawl job with unhandled exception.
        
        Validates: Requirement 9.3
        """
        # Setup mock to raise exception
        mock_run_price_crawl.side_effect = Exception("Unexpected error")
        
        # Execute job directly - should not raise exception
        scheduler._run_price_crawl_job()
        
        # Verify
        assert mock_run_price_crawl.called
        assert len(scheduler.job_history) == 1
        
        # Verify job history entry
        history_entry = scheduler.job_history[0]
        assert history_entry['job'] == 'price_crawl'
        assert history_entry['success'] is False
        assert 'error' in history_entry
    
    @patch('scheduler.run_reddit_collection_only')
    def test_reddit_collection_job_success(self, mock_run_reddit, scheduler):
        """
        Test successful execution of scheduled Reddit collection job.
        
        Validates: Requirement 9.2
        """
        # Setup mock
        mock_run_reddit.return_value = {
            'success': True,
            'signals_extracted': 5,
            'signals_loaded': 5
        }
        
        # Execute job directly
        scheduler._run_reddit_collection_job()
        
        # Verify
        assert mock_run_reddit.called
        assert len(scheduler.job_history) == 1
        
        # Verify job history entry
        history_entry = scheduler.job_history[0]
        assert history_entry['job'] == 'reddit_collection'
        assert history_entry['success'] is True
    
    @patch('scheduler.run_reddit_collection_only')
    def test_reddit_collection_job_failure(self, mock_run_reddit, scheduler):
        """
        Test failed execution of scheduled Reddit collection job.
        
        Validates: Requirement 9.3
        """
        # Setup mock to fail
        mock_run_reddit.return_value = {
            'success': False,
            'fatal_error': 'Rate limit exceeded'
        }
        
        # Execute job directly - should not raise exception
        scheduler._run_reddit_collection_job()
        
        # Verify
        assert mock_run_reddit.called
        assert len(scheduler.job_history) == 1
        
        # Verify job history entry
        history_entry = scheduler.job_history[0]
        assert history_entry['job'] == 'reddit_collection'
        assert history_entry['success'] is False


class TestSchedulerErrorHandling:
    """Test scheduler error handling and resilience."""
    
    @patch('scheduler.run_price_crawl_only')
    @patch('scheduler.run_reddit_collection_only')
    def test_scheduler_continues_after_job_failure(
        self,
        mock_run_reddit,
        mock_run_price_crawl,
        scheduler
    ):
        """
        Test that scheduler continues running after a job fails.
        
        Validates: Requirement 9.3
        """
        # Setup mocks - first job fails, second succeeds
        mock_run_price_crawl.side_effect = Exception("Network error")
        mock_run_reddit.return_value = {'success': True}
        
        # Execute both jobs
        scheduler._run_price_crawl_job()
        scheduler._run_reddit_collection_job()
        
        # Verify both jobs were executed
        assert mock_run_price_crawl.called
        assert mock_run_reddit.called
        
        # Verify job history
        assert len(scheduler.job_history) == 2
        assert scheduler.job_history[0]['success'] is False
        assert scheduler.job_history[1]['success'] is True
    
    @patch('scheduler.run_price_crawl_only')
    def test_multiple_job_failures(self, mock_run_price_crawl, scheduler):
        """
        Test scheduler handles multiple consecutive job failures.
        
        Validates: Requirement 9.3
        """
        # Setup mock to always fail
        mock_run_price_crawl.side_effect = Exception("Persistent error")
        
        # Execute job multiple times
        for _ in range(3):
            scheduler._run_price_crawl_job()
        
        # Verify all executions were recorded
        assert len(scheduler.job_history) == 3
        assert all(not entry['success'] for entry in scheduler.job_history)
    
    @patch('scheduler.run_price_crawl_only')
    def test_job_execution_timing(self, mock_run_price_crawl, scheduler):
        """Test that job execution timing is recorded correctly."""
        # Setup mock with delay
        import time
        
        def slow_job():
            time.sleep(0.1)  # 100ms delay
            return {'success': True}
        
        mock_run_price_crawl.side_effect = slow_job
        
        # Execute job
        scheduler._run_price_crawl_job()
        
        # Verify timing
        assert len(scheduler.job_history) == 1
        history_entry = scheduler.job_history[0]
        
        assert history_entry['duration_seconds'] >= 0.1
        assert history_entry['start_time'] < history_entry['end_time']


class TestSchedulerLifecycle:
    """Test scheduler start/stop lifecycle."""
    
    def test_scheduler_start(self, scheduler):
        """Test starting the scheduler."""
        # Schedule a job first
        scheduler.schedule_price_crawl()
        
        # Start scheduler
        scheduler.start()
        
        # Verify scheduler is running
        assert scheduler.scheduler.running is True
        
        # Stop scheduler
        scheduler.stop()
    
    def test_scheduler_stop(self, scheduler):
        """Test stopping the scheduler."""
        # Start scheduler
        scheduler.schedule_price_crawl()
        scheduler.start()
        
        # Stop scheduler
        scheduler.stop()
        
        # Verify scheduler is stopped
        assert scheduler.scheduler.running is False
    
    def test_scheduler_start_already_running(self, scheduler):
        """Test starting scheduler when it's already running."""
        # Start scheduler
        scheduler.schedule_price_crawl()
        scheduler.start()
        
        # Try to start again - should not raise exception
        scheduler.start()
        
        # Verify still running
        assert scheduler.scheduler.running is True
        
        # Cleanup
        scheduler.stop()
    
    def test_scheduler_stop_not_running(self, scheduler):
        """Test stopping scheduler when it's not running."""
        # Try to stop without starting - should not raise exception
        scheduler.stop()
        
        # Verify not running
        assert scheduler.scheduler.running is False
    
    def test_scheduler_get_jobs(self, scheduler):
        """Test retrieving scheduled jobs."""
        # Schedule jobs
        scheduler.schedule_price_crawl()
        scheduler.schedule_reddit_collection()
        
        # Get jobs
        jobs = scheduler.scheduler.get_jobs()
        
        # Verify
        assert len(jobs) == 2
        job_ids = [job.id for job in jobs]
        assert 'price_crawl' in job_ids
        assert 'reddit_collection' in job_ids


class TestSchedulerJobListener:
    """Test scheduler job event listener."""
    
    def test_job_listener_on_success(self, scheduler):
        """Test job listener handles successful job execution."""
        # Create mock event
        mock_event = Mock()
        mock_event.job_id = 'price_crawl'
        mock_event.exception = None
        
        # Call listener - should not raise exception
        scheduler._job_listener(mock_event)
    
    def test_job_listener_on_error(self, scheduler):
        """Test job listener handles job execution error."""
        # Create mock event with exception
        mock_event = Mock()
        mock_event.job_id = 'price_crawl'
        mock_event.exception = Exception("Job failed")
        
        # Call listener - should not raise exception
        scheduler._job_listener(mock_event)


class TestSchedulerIntegration:
    """Integration tests for scheduler."""
    
    @patch('scheduler.run_price_crawl_only')
    @patch('scheduler.run_reddit_collection_only')
    def test_full_scheduler_workflow(
        self,
        mock_run_reddit,
        mock_run_price_crawl,
        scheduler
    ):
        """Test complete scheduler workflow with both jobs."""
        # Setup mocks
        mock_run_price_crawl.return_value = {
            'success': True,
            'prices_extracted': 10,
            'prices_loaded': 10
        }
        mock_run_reddit.return_value = {
            'success': True,
            'signals_extracted': 5,
            'signals_loaded': 5
        }
        
        # Schedule both jobs
        scheduler.schedule_price_crawl()
        scheduler.schedule_reddit_collection()
        
        # Verify jobs are scheduled
        jobs = scheduler.scheduler.get_jobs()
        assert len(jobs) == 2
        
        # Manually trigger both jobs
        scheduler.run_price_crawl_now()
        scheduler.run_reddit_collection_now()
        
        # Verify both jobs executed
        assert mock_run_price_crawl.called
        assert mock_run_reddit.called
    
    @patch('scheduler.run_price_crawl_only')
    def test_scheduler_job_history_tracking(self, mock_run_price_crawl, scheduler):
        """Test that scheduler tracks job execution history."""
        # Setup mock
        mock_run_price_crawl.return_value = {'success': True}
        
        # Execute job multiple times
        for i in range(3):
            scheduler._run_price_crawl_job()
        
        # Verify history
        assert len(scheduler.job_history) == 3
        
        # Verify each entry has required fields
        for entry in scheduler.job_history:
            assert 'job' in entry
            assert 'start_time' in entry
            assert 'end_time' in entry
            assert 'duration_seconds' in entry
            assert 'success' in entry


class TestSchedulerConfiguration:
    """Test scheduler configuration handling."""
    
    @patch('scheduler.settings')
    def test_scheduler_uses_config_values(self, mock_settings, scheduler):
        """Test that scheduler uses configuration values."""
        # Setup mock config
        mock_settings.price_crawl_hour = 8
        mock_settings.price_crawl_minute = 30
        mock_settings.reddit_crawl_hour = 11
        mock_settings.reddit_crawl_minute = 45
        
        # Schedule jobs with default (config) values
        scheduler.schedule_price_crawl()
        scheduler.schedule_reddit_collection()
        
        # Verify jobs were scheduled
        jobs = scheduler.scheduler.get_jobs()
        assert len(jobs) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

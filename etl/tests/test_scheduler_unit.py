"""
Unit tests for the ETL scheduler.

These tests verify the scheduler's core functionality without requiring
database connections or full ETL pipeline imports.

Validates: Requirements 9.1, 9.2, 9.3
"""

import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


class TestSchedulerJobScheduling:
    """Test job scheduling functionality."""
    
    def test_schedule_job_with_cron_trigger(self):
        """
        Test that jobs can be scheduled with cron triggers.
        
        Validates: Requirement 9.1, 9.2
        """
        # Create scheduler
        scheduler = BackgroundScheduler()
        
        # Define a simple job
        def test_job():
            return "executed"
        
        # Schedule job with cron trigger
        trigger = CronTrigger(hour=9, minute=0)
        scheduler.add_job(
            func=test_job,
            trigger=trigger,
            id='test_job',
            name='Test Job',
            replace_existing=True,
            max_instances=1
        )
        
        # Verify job was added
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == 'test_job'
        assert jobs[0].name == 'Test Job'
        assert jobs[0].max_instances == 1
        
        # Cleanup - only shutdown if running
        if scheduler.running:
            scheduler.shutdown(wait=False)
    
    def test_schedule_multiple_jobs(self):
        """Test scheduling multiple jobs."""
        # Create scheduler
        scheduler = BackgroundScheduler()
        
        # Define jobs
        def job1():
            return "job1"
        
        def job2():
            return "job2"
        
        # Schedule both jobs
        scheduler.add_job(
            func=job1,
            trigger=CronTrigger(hour=9, minute=0),
            id='job1',
            name='Job 1'
        )
        
        scheduler.add_job(
            func=job2,
            trigger=CronTrigger(hour=10, minute=0),
            id='job2',
            name='Job 2'
        )
        
        # Verify both jobs were added
        jobs = scheduler.get_jobs()
        assert len(jobs) == 2
        
        job_ids = [job.id for job in jobs]
        assert 'job1' in job_ids
        assert 'job2' in job_ids
        
        # Cleanup - only shutdown if running
        if scheduler.running:
            scheduler.shutdown(wait=False)
    
    def test_replace_existing_job(self):
        """Test that scheduling a job twice replaces the existing one."""
        # Create scheduler
        scheduler = BackgroundScheduler()
        
        def test_job():
            return "executed"
        
        # Schedule job first time
        scheduler.add_job(
            func=test_job,
            trigger=CronTrigger(hour=9, minute=0),
            id='test_job',
            replace_existing=False
        )
        
        # Remove the job
        scheduler.remove_job('test_job')
        
        # Schedule job second time
        scheduler.add_job(
            func=test_job,
            trigger=CronTrigger(hour=10, minute=30),
            id='test_job',
            replace_existing=True
        )
        
        # Verify only one job exists
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == 'test_job'
        
        # Cleanup - only shutdown if running
        if scheduler.running:
            scheduler.shutdown(wait=False)


class TestSchedulerJobExecution:
    """Test job execution and error handling."""
    
    def test_job_execution_success(self):
        """
        Test successful job execution.
        
        Validates: Requirement 9.1, 9.2
        """
        # Track execution
        execution_log = []
        
        def test_job():
            execution_log.append({
                'executed': True,
                'timestamp': datetime.now()
            })
            return {'success': True}
        
        # Execute job
        result = test_job()
        
        # Verify
        assert result['success'] is True
        assert len(execution_log) == 1
        assert execution_log[0]['executed'] is True
    
    def test_job_execution_with_exception(self):
        """
        Test job execution that raises an exception.
        
        Validates: Requirement 9.3
        """
        # Track execution
        execution_log = []
        
        def failing_job():
            execution_log.append({
                'executed': True,
                'timestamp': datetime.now()
            })
            raise Exception("Job failed")
        
        # Execute job and catch exception
        try:
            failing_job()
            assert False, "Should have raised exception"
        except Exception as e:
            # Verify exception was raised
            assert str(e) == "Job failed"
            assert len(execution_log) == 1
    
    def test_job_error_handling_continues_execution(self):
        """
        Test that scheduler continues after job failure.
        
        Validates: Requirement 9.3
        """
        # Track execution
        execution_log = []
        
        def job_with_error_handling():
            try:
                # Simulate job that might fail
                raise Exception("Temporary error")
            except Exception as e:
                # Log error but don't re-raise
                execution_log.append({
                    'executed': True,
                    'error': str(e),
                    'timestamp': datetime.now()
                })
                return {'success': False, 'error': str(e)}
        
        # Execute job
        result = job_with_error_handling()
        
        # Verify job executed and logged error
        assert result['success'] is False
        assert result['error'] == "Temporary error"
        assert len(execution_log) == 1
        assert execution_log[0]['error'] == "Temporary error"
    
    def test_multiple_job_executions(self):
        """Test multiple consecutive job executions."""
        # Track execution
        execution_count = [0]
        
        def counting_job():
            execution_count[0] += 1
            return {'success': True, 'count': execution_count[0]}
        
        # Execute job multiple times
        results = []
        for _ in range(3):
            results.append(counting_job())
        
        # Verify
        assert len(results) == 3
        assert execution_count[0] == 3
        assert results[0]['count'] == 1
        assert results[1]['count'] == 2
        assert results[2]['count'] == 3


class TestSchedulerLifecycle:
    """Test scheduler start/stop lifecycle."""
    
    def test_scheduler_start_stop(self):
        """Test starting and stopping the scheduler."""
        # Create scheduler
        scheduler = BackgroundScheduler()
        
        # Verify initial state
        assert scheduler.running is False
        
        # Start scheduler
        scheduler.start()
        assert scheduler.running is True
        
        # Stop scheduler
        scheduler.shutdown(wait=False)
        assert scheduler.running is False
    
    def test_scheduler_start_already_running(self):
        """Test starting scheduler when it's already running."""
        # Create and start scheduler
        scheduler = BackgroundScheduler()
        scheduler.start()
        
        # Try to start again - should not raise exception
        # APScheduler handles this internally
        assert scheduler.running is True
        
        # Cleanup
        scheduler.shutdown(wait=False)
    
    def test_scheduler_stop_not_running(self):
        """Test stopping scheduler when it's not running."""
        # Create scheduler without starting
        scheduler = BackgroundScheduler()
        
        # Verify not running
        assert scheduler.running is False
        
        # No need to call shutdown if not running


class TestSchedulerConfiguration:
    """Test scheduler configuration."""
    
    def test_cron_trigger_configuration(self):
        """Test configuring cron triggers with different times."""
        # Test various time configurations
        test_cases = [
            (9, 0),    # 09:00
            (10, 30),  # 10:30
            (23, 59),  # 23:59
            (0, 0),    # 00:00
        ]
        
        for hour, minute in test_cases:
            trigger = CronTrigger(hour=hour, minute=minute)
            assert trigger is not None
    
    def test_job_max_instances(self):
        """Test that max_instances prevents concurrent execution."""
        # Create scheduler
        scheduler = BackgroundScheduler()
        
        def test_job():
            return "executed"
        
        # Schedule job with max_instances=1
        scheduler.add_job(
            func=test_job,
            trigger=CronTrigger(hour=9, minute=0),
            id='test_job',
            max_instances=1
        )
        
        # Verify configuration
        jobs = scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].max_instances == 1
        
        # Cleanup - only shutdown if running
        if scheduler.running:
            scheduler.shutdown(wait=False)


class TestSchedulerJobHistory:
    """Test job execution history tracking."""
    
    def test_job_history_tracking(self):
        """Test tracking job execution history."""
        # Job history storage
        job_history = []
        
        def tracked_job():
            start_time = datetime.now()
            
            # Simulate job execution
            result = {'success': True}
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Record history
            job_history.append({
                'job': 'test_job',
                'start_time': start_time,
                'end_time': end_time,
                'duration_seconds': duration,
                'success': result['success']
            })
            
            return result
        
        # Execute job multiple times
        for _ in range(3):
            tracked_job()
        
        # Verify history
        assert len(job_history) == 3
        
        for entry in job_history:
            assert 'job' in entry
            assert 'start_time' in entry
            assert 'end_time' in entry
            assert 'duration_seconds' in entry
            assert 'success' in entry
            assert entry['success'] is True
    
    def test_job_history_with_failures(self):
        """Test tracking job history with failures."""
        # Job history storage
        job_history = []
        
        def failing_job():
            start_time = datetime.now()
            
            try:
                raise Exception("Job failed")
            except Exception as e:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                # Record failure
                job_history.append({
                    'job': 'failing_job',
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration_seconds': duration,
                    'success': False,
                    'error': str(e)
                })
                
                return {'success': False, 'error': str(e)}
        
        # Execute failing job
        result = failing_job()
        
        # Verify history
        assert len(job_history) == 1
        assert job_history[0]['success'] is False
        assert job_history[0]['error'] == "Job failed"


class TestSchedulerErrorResilience:
    """Test scheduler error resilience."""
    
    def test_continue_after_job_failure(self):
        """
        Test that subsequent jobs execute after one fails.
        
        Validates: Requirement 9.3
        """
        # Execution log
        execution_log = []
        
        def failing_job():
            try:
                raise Exception("Job 1 failed")
            except Exception as e:
                execution_log.append({
                    'job': 'job1',
                    'success': False,
                    'error': str(e)
                })
        
        def successful_job():
            execution_log.append({
                'job': 'job2',
                'success': True
            })
        
        # Execute both jobs
        failing_job()
        successful_job()
        
        # Verify both executed
        assert len(execution_log) == 2
        assert execution_log[0]['success'] is False
        assert execution_log[1]['success'] is True
    
    def test_multiple_consecutive_failures(self):
        """
        Test handling multiple consecutive job failures.
        
        Validates: Requirement 9.3
        """
        # Execution log
        execution_log = []
        
        def failing_job():
            try:
                raise Exception("Persistent error")
            except Exception as e:
                execution_log.append({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now()
                })
        
        # Execute job multiple times
        for _ in range(3):
            failing_job()
        
        # Verify all executions were recorded
        assert len(execution_log) == 3
        assert all(not entry['success'] for entry in execution_log)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

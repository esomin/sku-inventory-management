"""
Unit tests for database connection module.

These tests verify the connection pool management and retry logic.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from psycopg2 import OperationalError, DatabaseError

from db_connection import DatabaseManager, DatabaseConnectionError


class TestDatabaseManager:
    """Test suite for DatabaseManager class."""
    
    def test_singleton_pattern(self):
        """Test that DatabaseManager implements singleton pattern."""
        manager1 = DatabaseManager()
        manager2 = DatabaseManager()
        assert manager1 is manager2
    
    @patch('db_connection.pool.SimpleConnectionPool')
    def test_initialize_pool_success(self, mock_pool):
        """Test successful connection pool initialization."""
        mock_pool_instance = Mock()
        mock_pool.return_value = mock_pool_instance
        
        manager = DatabaseManager()
        assert manager._pool is not None
    
    @patch('db_connection.pool.SimpleConnectionPool')
    def test_initialize_pool_retry_on_failure(self, mock_pool):
        """Test retry logic when connection fails initially."""
        # Fail twice, then succeed
        mock_pool.side_effect = [
            OperationalError("Connection refused"),
            OperationalError("Connection refused"),
            Mock()
        ]
        
        with patch('db_connection.time.sleep'):  # Skip actual sleep
            manager = DatabaseManager()
            assert manager._pool is not None
            assert mock_pool.call_count == 3
    
    @patch('db_connection.pool.SimpleConnectionPool')
    def test_initialize_pool_max_retries_exceeded(self, mock_pool):
        """Test that DatabaseConnectionError is raised after max retries."""
        mock_pool.side_effect = OperationalError("Connection refused")
        
        with patch('db_connection.time.sleep'):  # Skip actual sleep
            with pytest.raises(DatabaseConnectionError):
                # Force re-initialization
                DatabaseManager._pool = None
                DatabaseManager()
    
    def test_get_connection_context_manager(self):
        """Test get_connection context manager returns and releases connection."""
        manager = DatabaseManager()
        mock_conn = Mock()
        manager._pool = Mock()
        manager._pool.getconn.return_value = mock_conn
        
        with manager.get_connection() as conn:
            assert conn is mock_conn
        
        manager._pool.putconn.assert_called_once_with(mock_conn)
    
    def test_get_connection_rollback_on_error(self):
        """Test that connection is rolled back on error."""
        manager = DatabaseManager()
        mock_conn = Mock()
        manager._pool = Mock()
        manager._pool.getconn.return_value = mock_conn
        
        with pytest.raises(ValueError):
            with manager.get_connection() as conn:
                raise ValueError("Test error")
        
        mock_conn.rollback.assert_called_once()
        manager._pool.putconn.assert_called_once_with(mock_conn)
    
    def test_get_cursor_commits_by_default(self):
        """Test that get_cursor commits transaction by default."""
        manager = DatabaseManager()
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        manager._pool = Mock()
        manager._pool.getconn.return_value = mock_conn
        
        with manager.get_cursor() as cursor:
            assert cursor is mock_cursor
        
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
    
    def test_get_cursor_no_commit_when_disabled(self):
        """Test that get_cursor doesn't commit when commit=False."""
        manager = DatabaseManager()
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        manager._pool = Mock()
        manager._pool.getconn.return_value = mock_conn
        
        with manager.get_cursor(commit=False) as cursor:
            pass
        
        mock_conn.commit.assert_not_called()
    
    def test_execute_with_retry_success(self):
        """Test successful query execution."""
        manager = DatabaseManager()
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [(1,)]
        mock_conn.cursor.return_value = mock_cursor
        manager._pool = Mock()
        manager._pool.getconn.return_value = mock_conn
        
        result = manager.execute_with_retry("SELECT 1", fetch=True)
        assert result == [(1,)]
        mock_cursor.execute.assert_called_once_with("SELECT 1", None)
    
    def test_execute_with_retry_retries_on_failure(self):
        """Test retry logic for transient failures."""
        manager = DatabaseManager()
        mock_conn = Mock()
        mock_cursor = Mock()
        # Fail twice, then succeed
        mock_cursor.execute.side_effect = [
            OperationalError("Transient error"),
            OperationalError("Transient error"),
            None
        ]
        mock_conn.cursor.return_value = mock_cursor
        manager._pool = Mock()
        manager._pool.getconn.return_value = mock_conn
        
        with patch('db_connection.time.sleep'):  # Skip actual sleep
            manager.execute_with_retry("INSERT INTO test VALUES (1)")
            assert mock_cursor.execute.call_count == 3
    
    def test_test_connection_success(self):
        """Test connection test returns True on success."""
        manager = DatabaseManager()
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor
        manager._pool = Mock()
        manager._pool.getconn.return_value = mock_conn
        
        assert manager.test_connection() is True
    
    def test_test_connection_failure(self):
        """Test connection test returns False on failure."""
        manager = DatabaseManager()
        manager._pool = Mock()
        manager._pool.getconn.side_effect = OperationalError("Connection failed")
        
        assert manager.test_connection() is False
    
    def test_close_pool(self):
        """Test that close_pool closes all connections."""
        manager = DatabaseManager()
        manager._pool = Mock()
        
        manager.close_pool()
        
        manager._pool.closeall.assert_called_once()
        assert manager._pool is None

"""
Database connection management for the ETL system.

This module provides a connection pool manager with automatic retry logic
and error handling for PostgreSQL database operations.
"""

import logging
import time
from contextlib import contextmanager
from typing import Generator, Optional

import psycopg2
from psycopg2 import pool, OperationalError, DatabaseError
from psycopg2.extensions import connection

from config import settings

logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """Raised when database connection fails after all retries."""
    pass


class DatabaseManager:
    """
    Manages PostgreSQL connection pool with retry logic.
    
    This class implements a singleton pattern to ensure only one connection pool
    exists throughout the application lifecycle.
    """
    
    _instance: Optional['DatabaseManager'] = None
    _pool: Optional[pool.SimpleConnectionPool] = None
    
    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the database manager (only once)."""
        if self._pool is None:
            self._initialize_pool()
    
    def _initialize_pool(self) -> None:
        """
        Initialize the connection pool with retry logic.
        
        Raises:
            DatabaseConnectionError: If connection fails after max retries
        """
        retries = 0
        last_error = None
        
        while retries < settings.max_retries:
            try:
                logger.info(f"Initializing database connection pool (attempt {retries + 1}/{settings.max_retries})")
                
                self._pool = pool.SimpleConnectionPool(
                    minconn=1,
                    maxconn=10,
                    host=settings.db_host,
                    port=settings.db_port,
                    database=settings.db_name,
                    user=settings.db_user,
                    password=settings.db_password,
                    connect_timeout=10
                )
                
                logger.info("Database connection pool initialized successfully")
                return
                
            except (OperationalError, DatabaseError) as e:
                last_error = e
                retries += 1
                
                if retries < settings.max_retries:
                    backoff_time = settings.retry_backoff_seconds * (2 ** (retries - 1))
                    logger.warning(
                        f"Database connection failed: {e}. "
                        f"Retrying in {backoff_time} seconds..."
                    )
                    time.sleep(backoff_time)
                else:
                    logger.error(f"Database connection failed after {settings.max_retries} attempts")
        
        raise DatabaseConnectionError(
            f"Failed to connect to database after {settings.max_retries} attempts: {last_error}"
        )
    
    @contextmanager
    def get_connection(self) -> Generator[connection, None, None]:
        """
        Get a database connection from the pool with automatic cleanup.
        
        This context manager ensures connections are properly returned to the pool
        even if an error occurs.
        
        Yields:
            psycopg2 connection object
            
        Raises:
            DatabaseConnectionError: If unable to get connection from pool
            
        Example:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM products")
                results = cursor.fetchall()
        """
        if self._pool is None:
            raise DatabaseConnectionError("Connection pool not initialized")
        
        conn = None
        try:
            conn = self._pool.getconn()
            if conn is None:
                raise DatabaseConnectionError("Failed to get connection from pool")
            
            yield conn
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
            
        finally:
            if conn:
                self._pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, commit: bool = True) -> Generator:
        """
        Get a database cursor with automatic transaction management.
        
        This is a convenience method that combines connection and cursor management
        with automatic commit/rollback handling.
        
        Args:
            commit: Whether to commit the transaction on success (default: True)
            
        Yields:
            psycopg2 cursor object
            
        Example:
            with db_manager.get_cursor() as cursor:
                cursor.execute("INSERT INTO products VALUES (%s, %s)", (1, "RTX 4070"))
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                if commit:
                    conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Transaction rolled back due to error: {e}")
                raise
            finally:
                cursor.close()
    
    def execute_with_retry(self, query: str, params: tuple = None, fetch: bool = False):
        """
        Execute a query with automatic retry logic.
        
        This method handles transient database errors by retrying the operation
        with exponential backoff.
        
        Args:
            query: SQL query to execute
            params: Query parameters (optional)
            fetch: Whether to fetch and return results (default: False)
            
        Returns:
            Query results if fetch=True, otherwise None
            
        Raises:
            DatabaseError: If query fails after all retries
        """
        retries = 0
        last_error = None
        
        while retries < settings.max_retries:
            try:
                with self.get_cursor(commit=not fetch) as cursor:
                    cursor.execute(query, params)
                    
                    if fetch:
                        return cursor.fetchall()
                    return None
                    
            except (OperationalError, DatabaseError) as e:
                last_error = e
                retries += 1
                
                if retries < settings.max_retries:
                    backoff_time = settings.retry_backoff_seconds * (2 ** (retries - 1))
                    logger.warning(
                        f"Query execution failed: {e}. "
                        f"Retrying in {backoff_time} seconds... (attempt {retries}/{settings.max_retries})"
                    )
                    time.sleep(backoff_time)
                else:
                    logger.error(f"Query failed after {settings.max_retries} attempts: {query}")
        
        raise DatabaseError(
            f"Query failed after {settings.max_retries} attempts: {last_error}"
        )
    
    def close_pool(self) -> None:
        """
        Close all connections in the pool.
        
        This should be called when shutting down the application.
        """
        if self._pool:
            self._pool.closeall()
            logger.info("Database connection pool closed")
            self._pool = None
    
    def test_connection(self) -> bool:
        """
        Test database connectivity.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result[0] == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()

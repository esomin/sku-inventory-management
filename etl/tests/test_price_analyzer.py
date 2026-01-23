"""
Unit tests for price analyzer.

These tests verify the price change calculation logic, including accuracy,
edge cases, and error handling.
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock psycopg2 before any imports
sys.modules['psycopg2'] = Mock()
sys.modules['psycopg2.pool'] = Mock()
sys.modules['psycopg2.extensions'] = Mock()

# Mock config module
mock_settings = Mock()
mock_settings.max_retries = 3
mock_settings.retry_backoff_seconds = 5
sys.modules['config'] = Mock(settings=mock_settings)

# Mock the db_connection module before importing transformers
mock_db_manager = Mock()
sys.modules['db_connection'] = Mock(db_manager=mock_db_manager)

from transformers.price_analyzer import PriceAnalyzer, InsufficientDataError


class TestPriceAnalyzer:
    """Test suite for PriceAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a PriceAnalyzer instance for testing."""
        return PriceAnalyzer()
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database manager."""
        return Mock()
    
    # Test successful price change calculation
    
    def test_calculate_price_change_price_increase(self, analyzer, mock_db):
        """Test price change calculation with price increase."""
        # Setup: Current price 1,100,000 KRW, 7-day avg 1,000,000 KRW
        # Expected: +10% change
        sku_id = 1
        current_price = 1_100_000.0
        historical_prices = [1_000_000.0, 1_000_000.0, 1_000_000.0]
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        result = analyzer.calculate_price_change(sku_id, current_price)
        
        assert result == 10.0
        mock_db.execute_with_retry.assert_called_once()
    
    def test_calculate_price_change_price_decrease(self, analyzer, mock_db):
        """Test price change calculation with price decrease."""
        # Setup: Current price 900,000 KRW, 7-day avg 1,000,000 KRW
        # Expected: -10% change
        sku_id = 1
        current_price = 900_000.0
        historical_prices = [1_000_000.0, 1_000_000.0, 1_000_000.0]
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        result = analyzer.calculate_price_change(sku_id, current_price)
        
        assert result == -10.0
    
    def test_calculate_price_change_no_change(self, analyzer, mock_db):
        """Test price change calculation with no price change."""
        # Setup: Current price 1,000,000 KRW, 7-day avg 1,000,000 KRW
        # Expected: 0% change
        sku_id = 1
        current_price = 1_000_000.0
        historical_prices = [1_000_000.0, 1_000_000.0, 1_000_000.0]
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        result = analyzer.calculate_price_change(sku_id, current_price)
        
        assert result == 0.0
    
    def test_calculate_price_change_with_varying_historical_prices(self, analyzer, mock_db):
        """Test price change calculation with varying historical prices."""
        # Setup: Current price 1,100,000 KRW
        # Historical: 950,000, 1,000,000, 1,050,000 (avg = 1,000,000)
        # Expected: +10% change
        sku_id = 1
        current_price = 1_100_000.0
        historical_prices = [950_000.0, 1_000_000.0, 1_050_000.0]
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        result = analyzer.calculate_price_change(sku_id, current_price)
        
        assert result == 10.0
    
    def test_calculate_price_change_large_increase(self, analyzer, mock_db):
        """Test price change calculation with large price increase."""
        # Setup: Current price 1,500,000 KRW, 7-day avg 1,000,000 KRW
        # Expected: +50% change
        sku_id = 1
        current_price = 1_500_000.0
        historical_prices = [1_000_000.0]
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        result = analyzer.calculate_price_change(sku_id, current_price)
        
        assert result == 50.0
    
    def test_calculate_price_change_large_decrease(self, analyzer, mock_db):
        """Test price change calculation with large price decrease."""
        # Setup: Current price 500,000 KRW, 7-day avg 1,000,000 KRW
        # Expected: -50% change
        sku_id = 1
        current_price = 500_000.0
        historical_prices = [1_000_000.0]
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        result = analyzer.calculate_price_change(sku_id, current_price)
        
        assert result == -50.0
    
    def test_calculate_price_change_small_change(self, analyzer, mock_db):
        """Test price change calculation with small price change."""
        # Setup: Current price 1,005,000 KRW, 7-day avg 1,000,000 KRW
        # Expected: +0.5% change
        sku_id = 1
        current_price = 1_005_000.0
        historical_prices = [1_000_000.0]
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        result = analyzer.calculate_price_change(sku_id, current_price)
        
        assert result == 0.5
    
    def test_calculate_price_change_rounding(self, analyzer, mock_db):
        """Test that price change is rounded to 2 decimal places."""
        # Setup: Current price 1,003,333 KRW, 7-day avg 1,000,000 KRW
        # Expected: +0.33% change (rounded)
        sku_id = 1
        current_price = 1_003_333.0
        historical_prices = [1_000_000.0]
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        result = analyzer.calculate_price_change(sku_id, current_price)
        
        assert result == 0.33
    
    # Test edge cases
    
    def test_calculate_price_change_insufficient_data(self, analyzer, mock_db):
        """Test that InsufficientDataError is raised when no historical data exists."""
        sku_id = 1
        current_price = 1_000_000.0
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = []  # No historical data
        
        with pytest.raises(InsufficientDataError, match="Insufficient historical data"):
            analyzer.calculate_price_change(sku_id, current_price)
    
    def test_calculate_price_change_negative_price(self, analyzer, mock_db):
        """Test that ValueError is raised for negative current price."""
        sku_id = 1
        current_price = -1_000_000.0
        
        analyzer.db = mock_db
        
        with pytest.raises(ValueError, match="Invalid price"):
            analyzer.calculate_price_change(sku_id, current_price)
    
    def test_calculate_price_change_zero_price(self, analyzer, mock_db):
        """Test that ValueError is raised for zero current price."""
        sku_id = 1
        current_price = 0.0
        
        analyzer.db = mock_db
        
        with pytest.raises(ValueError, match="Invalid price"):
            analyzer.calculate_price_change(sku_id, current_price)
    
    def test_calculate_price_change_zero_historical_average(self, analyzer, mock_db):
        """Test that ValueError is raised when historical average is zero."""
        sku_id = 1
        current_price = 1_000_000.0
        historical_prices = [0.0, 0.0]
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        with pytest.raises(ValueError, match="Historical average price is zero"):
            analyzer.calculate_price_change(sku_id, current_price)
    
    def test_calculate_price_change_single_historical_price(self, analyzer, mock_db):
        """Test price change calculation with single historical price."""
        sku_id = 1
        current_price = 1_100_000.0
        historical_prices = [1_000_000.0]
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        result = analyzer.calculate_price_change(sku_id, current_price)
        
        assert result == 10.0
    
    def test_calculate_price_change_many_historical_prices(self, analyzer, mock_db):
        """Test price change calculation with many historical prices."""
        sku_id = 1
        current_price = 1_100_000.0
        # 10 prices averaging to 1,000,000
        historical_prices = [1_000_000.0] * 10
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        result = analyzer.calculate_price_change(sku_id, current_price)
        
        assert result == 10.0
    
    # Test get_price_history method
    
    def test_get_price_history_success(self, analyzer, mock_db):
        """Test successful retrieval of price history."""
        sku_id = 1
        days = 30
        
        now = datetime.now()
        mock_data = [
            (now - timedelta(days=i), 1_000_000.0 + i * 10_000)
            for i in range(10)
        ]
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = mock_data
        
        result = analyzer.get_price_history(sku_id, days)
        
        assert len(result) == 10
        assert all(isinstance(item, tuple) for item in result)
        assert all(len(item) == 2 for item in result)
        mock_db.execute_with_retry.assert_called_once()
    
    def test_get_price_history_empty(self, analyzer, mock_db):
        """Test price history retrieval with no data."""
        sku_id = 1
        days = 30
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = []
        
        result = analyzer.get_price_history(sku_id, days)
        
        assert result == []
    
    def test_get_price_history_default_days(self, analyzer, mock_db):
        """Test that default days parameter is 90."""
        sku_id = 1
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = []
        
        analyzer.get_price_history(sku_id)
        
        # Verify the query was called (default 90 days)
        mock_db.execute_with_retry.assert_called_once()
    
    # Test has_sufficient_data method
    
    def test_has_sufficient_data_true(self, analyzer, mock_db):
        """Test has_sufficient_data returns True when data is sufficient."""
        sku_id = 1
        earliest_date = datetime.now() - timedelta(days=10)
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [(earliest_date,)]
        
        result = analyzer.has_sufficient_data(sku_id, required_days=7)
        
        assert result is True
    
    def test_has_sufficient_data_false(self, analyzer, mock_db):
        """Test has_sufficient_data returns False when data is insufficient."""
        sku_id = 1
        earliest_date = datetime.now() - timedelta(days=5)
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [(earliest_date,)]
        
        result = analyzer.has_sufficient_data(sku_id, required_days=7)
        
        assert result is False
    
    def test_has_sufficient_data_no_data(self, analyzer, mock_db):
        """Test has_sufficient_data returns False when no data exists."""
        sku_id = 1
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [(None,)]
        
        result = analyzer.has_sufficient_data(sku_id, required_days=7)
        
        assert result is False
    
    def test_has_sufficient_data_empty_result(self, analyzer, mock_db):
        """Test has_sufficient_data returns False when query returns empty."""
        sku_id = 1
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = []
        
        result = analyzer.has_sufficient_data(sku_id, required_days=7)
        
        assert result is False
    
    def test_has_sufficient_data_exactly_required_days(self, analyzer, mock_db):
        """Test has_sufficient_data with exactly required days."""
        sku_id = 1
        earliest_date = datetime.now() - timedelta(days=7)
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [(earliest_date,)]
        
        result = analyzer.has_sufficient_data(sku_id, required_days=7)
        
        assert result is True
    
    def test_has_sufficient_data_error_handling(self, analyzer, mock_db):
        """Test has_sufficient_data returns False on database error."""
        sku_id = 1
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.side_effect = Exception("Database error")
        
        result = analyzer.has_sufficient_data(sku_id, required_days=7)
        
        assert result is False
    
    # Test _get_historical_prices internal method
    
    def test_get_historical_prices_with_window(self, analyzer, mock_db):
        """Test _get_historical_prices retrieves prices within window."""
        sku_id = 1
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (1_000_000.0,),
            (1_010_000.0,),
            (990_000.0,)
        ]
        
        result = analyzer._get_historical_prices(sku_id, days_ago=7, window_days=1)
        
        assert len(result) == 3
        assert result == [1_000_000.0, 1_010_000.0, 990_000.0]
    
    def test_get_historical_prices_empty(self, analyzer, mock_db):
        """Test _get_historical_prices with no data."""
        sku_id = 1
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = []
        
        result = analyzer._get_historical_prices(sku_id, days_ago=7, window_days=1)
        
        assert result == []
    
    def test_get_historical_prices_custom_days(self, analyzer, mock_db):
        """Test _get_historical_prices with custom days_ago parameter."""
        sku_id = 1
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [(1_000_000.0,)]
        
        result = analyzer._get_historical_prices(sku_id, days_ago=14, window_days=2)
        
        assert len(result) == 1
        mock_db.execute_with_retry.assert_called_once()
    
    # Test calculation accuracy with real-world scenarios
    
    def test_calculate_price_change_rtx_4070_price_drop(self, analyzer, mock_db):
        """Test realistic RTX 4070 price drop scenario."""
        # Scenario: RTX 4070 drops from 750,000 to 712,500 KRW (-5%)
        sku_id = 1
        current_price = 712_500.0
        historical_prices = [750_000.0, 750_000.0, 750_000.0]
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        result = analyzer.calculate_price_change(sku_id, current_price)
        
        assert result == -5.0
    
    def test_calculate_price_change_rtx_4070_super_release_impact(self, analyzer, mock_db):
        """Test RTX 4070 price drop after Super release."""
        # Scenario: RTX 4070 drops from 800,000 to 720,000 KRW (-10%)
        sku_id = 1
        current_price = 720_000.0
        historical_prices = [800_000.0, 800_000.0, 800_000.0]
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        result = analyzer.calculate_price_change(sku_id, current_price)
        
        assert result == -10.0
    
    def test_calculate_price_change_volatile_market(self, analyzer, mock_db):
        """Test price change calculation in volatile market conditions."""
        # Scenario: Prices fluctuating between 700k-800k, avg 750k
        sku_id = 1
        current_price = 825_000.0
        historical_prices = [700_000.0, 750_000.0, 800_000.0]
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        result = analyzer.calculate_price_change(sku_id, current_price)
        
        assert result == 10.0
    
    # Test error propagation
    
    def test_calculate_price_change_database_error(self, analyzer, mock_db):
        """Test that database errors are propagated."""
        sku_id = 1
        current_price = 1_000_000.0
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.side_effect = Exception("Database connection failed")
        
        with pytest.raises(Exception, match="Database connection failed"):
            analyzer.calculate_price_change(sku_id, current_price)
    
    def test_get_price_history_database_error(self, analyzer, mock_db):
        """Test that database errors are propagated in get_price_history."""
        sku_id = 1
        
        analyzer.db = mock_db
        mock_db.execute_with_retry.side_effect = Exception("Query timeout")
        
        with pytest.raises(Exception, match="Query timeout"):
            analyzer.get_price_history(sku_id, days=30)


class TestPriceAnalyzerIntegration:
    """Integration tests for PriceAnalyzer with more complex scenarios."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a PriceAnalyzer instance for testing."""
        return PriceAnalyzer()
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database manager."""
        return Mock()
    
    def test_multiple_products_price_analysis(self, analyzer, mock_db):
        """Test analyzing multiple products sequentially."""
        analyzer.db = mock_db
        
        # Product 1: Price increase
        mock_db.execute_with_retry.return_value = [(1_000_000.0,)]
        result1 = analyzer.calculate_price_change(1, 1_100_000.0)
        assert result1 == 10.0
        
        # Product 2: Price decrease
        mock_db.execute_with_retry.return_value = [(800_000.0,)]
        result2 = analyzer.calculate_price_change(2, 760_000.0)
        assert result2 == -5.0
        
        # Product 3: No change
        mock_db.execute_with_retry.return_value = [(750_000.0,)]
        result3 = analyzer.calculate_price_change(3, 750_000.0)
        assert result3 == 0.0
    
    def test_price_trend_over_time(self, analyzer, mock_db):
        """Test calculating price changes over multiple time periods."""
        sku_id = 1
        analyzer.db = mock_db
        
        # Week 1: Price at 1,000,000
        mock_db.execute_with_retry.return_value = [(900_000.0,)]
        week1_change = analyzer.calculate_price_change(sku_id, 1_000_000.0)
        assert week1_change == pytest.approx(11.11, rel=0.01)
        
        # Week 2: Price at 1,050,000
        mock_db.execute_with_retry.return_value = [(1_000_000.0,)]
        week2_change = analyzer.calculate_price_change(sku_id, 1_050_000.0)
        assert week2_change == 5.0
        
        # Week 3: Price at 950,000
        mock_db.execute_with_retry.return_value = [(1_050_000.0,)]
        week3_change = analyzer.calculate_price_change(sku_id, 950_000.0)
        assert week3_change == pytest.approx(-9.52, rel=0.01)

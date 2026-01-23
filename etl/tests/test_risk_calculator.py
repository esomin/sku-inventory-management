"""
Unit tests for risk calculator.

These tests verify the risk index calculation logic, threshold checking,
and various scenarios including price drops and new release mentions.
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
mock_settings.risk_threshold = -100.0
mock_settings.sentiment_weight_new_release = 3.0
mock_settings.sentiment_weight_price_drop = 2.0
mock_settings.sentiment_weight_default = 1.0
sys.modules['config'] = Mock(settings=mock_settings)

# Mock the db_connection module
mock_db_manager = Mock()
sys.modules['db_connection'] = Mock(db_manager=mock_db_manager)

from transformers.risk_calculator import RiskCalculator
from transformers.price_analyzer import InsufficientDataError


class TestRiskCalculator:
    """Test suite for RiskCalculator."""
    
    @pytest.fixture
    def calculator(self):
        """Create a RiskCalculator instance for testing."""
        calc = RiskCalculator()
        calc.threshold = -100.0  # Set threshold explicitly
        return calc
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database manager."""
        return Mock()

    
    # Test basic risk index calculation
    
    def test_calculate_risk_index_price_drop_no_mentions(self, calculator, mock_db):
        """Test risk calculation with price drop and no new release mentions."""
        # Scenario: Price drops from 1,000,000 to 950,000 (-50,000)
        # No new release mentions
        # Expected risk_index: -50,000 + 0 = -50,000
        sku_id = 1
        current_price = 950_000.0
        historical_prices = [1_000_000.0, 1_000_000.0, 1_000_000.0]
        
        calculator.db = mock_db
        calculator.price_analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        result = calculator.calculate_risk_index(sku_id, current_price, new_release_mentions=0)
        
        assert result == -50_000.0
    
    def test_calculate_risk_index_price_drop_with_mentions(self, calculator, mock_db):
        """Test risk calculation with price drop and new release mentions."""
        # Scenario: Price drops from 1,000,000 to 950,000 (-50,000)
        # 10 new release mentions (10 * 0.3 = 3.0)
        # Expected risk_index: -50,000 + 3.0 = -49,997.0
        sku_id = 1
        current_price = 950_000.0
        new_release_mentions = 10
        historical_prices = [1_000_000.0]
        
        calculator.db = mock_db
        calculator.price_analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        result = calculator.calculate_risk_index(sku_id, current_price, new_release_mentions)
        
        assert result == -49_997.0
    
    def test_calculate_risk_index_price_increase_no_mentions(self, calculator, mock_db):
        """Test risk calculation with price increase and no mentions."""
        # Scenario: Price increases from 1,000,000 to 1,050,000 (+50,000)
        # No new release mentions
        # Expected risk_index: 50,000 + 0 = 50,000
        sku_id = 1
        current_price = 1_050_000.0
        historical_prices = [1_000_000.0]
        
        calculator.db = mock_db
        calculator.price_analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        result = calculator.calculate_risk_index(sku_id, current_price, new_release_mentions=0)
        
        assert result == 50_000.0
    
    def test_calculate_risk_index_price_increase_with_mentions(self, calculator, mock_db):
        """Test risk calculation with price increase and new release mentions."""
        # Scenario: Price increases from 1,000,000 to 1,050,000 (+50,000)
        # 10 new release mentions (10 * 0.3 = 3.0)
        # Expected risk_index: 50,000 + 3.0 = 50,003.0
        sku_id = 1
        current_price = 1_050_000.0
        new_release_mentions = 10
        historical_prices = [1_000_000.0]
        
        calculator.db = mock_db
        calculator.price_analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        result = calculator.calculate_risk_index(sku_id, current_price, new_release_mentions)
        
        assert result == 50_003.0

    
    def test_calculate_risk_index_no_price_change(self, calculator, mock_db):
        """Test risk calculation with no price change."""
        # Scenario: Price stays at 1,000,000
        # 5 new release mentions (5 * 0.3 = 1.5)
        # Expected risk_index: 0 + 1.5 = 1.5
        sku_id = 1
        current_price = 1_000_000.0
        new_release_mentions = 5
        historical_prices = [1_000_000.0]
        
        calculator.db = mock_db
        calculator.price_analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        result = calculator.calculate_risk_index(sku_id, current_price, new_release_mentions)
        
        assert result == 1.5
    
    def test_calculate_risk_index_large_price_drop(self, calculator, mock_db):
        """Test risk calculation with large price drop."""
        # Scenario: Price drops from 1,000,000 to 800,000 (-200,000)
        # 20 new release mentions (20 * 0.3 = 6.0)
        # Expected risk_index: -200,000 + 6.0 = -199,994.0
        sku_id = 1
        current_price = 800_000.0
        new_release_mentions = 20
        historical_prices = [1_000_000.0]
        
        calculator.db = mock_db
        calculator.price_analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        result = calculator.calculate_risk_index(sku_id, current_price, new_release_mentions)
        
        assert result == -199_994.0
    
    def test_calculate_risk_index_high_mentions_no_price_change(self, calculator, mock_db):
        """Test risk calculation with high mentions but no price change."""
        # Scenario: Price stays at 1,000,000
        # 100 new release mentions (100 * 0.3 = 30.0)
        # Expected risk_index: 0 + 30.0 = 30.0
        sku_id = 1
        current_price = 1_000_000.0
        new_release_mentions = 100
        historical_prices = [1_000_000.0]
        
        calculator.db = mock_db
        calculator.price_analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        result = calculator.calculate_risk_index(sku_id, current_price, new_release_mentions)
        
        assert result == 30.0
    
    # Test edge cases
    
    def test_calculate_risk_index_negative_price(self, calculator, mock_db):
        """Test that ValueError is raised for negative current price."""
        sku_id = 1
        current_price = -1_000_000.0
        
        calculator.db = mock_db
        
        with pytest.raises(ValueError, match="Invalid price"):
            calculator.calculate_risk_index(sku_id, current_price, new_release_mentions=0)
    
    def test_calculate_risk_index_zero_price(self, calculator, mock_db):
        """Test that ValueError is raised for zero current price."""
        sku_id = 1
        current_price = 0.0
        
        calculator.db = mock_db
        
        with pytest.raises(ValueError, match="Invalid price"):
            calculator.calculate_risk_index(sku_id, current_price, new_release_mentions=0)

    
    def test_calculate_risk_index_negative_mentions(self, calculator, mock_db):
        """Test that ValueError is raised for negative mentions."""
        sku_id = 1
        current_price = 1_000_000.0
        
        calculator.db = mock_db
        
        with pytest.raises(ValueError, match="Invalid new_release_mentions"):
            calculator.calculate_risk_index(sku_id, current_price, new_release_mentions=-5)
    
    def test_calculate_risk_index_insufficient_data(self, calculator, mock_db):
        """Test that InsufficientDataError is raised when no historical data exists."""
        sku_id = 1
        current_price = 1_000_000.0
        
        calculator.db = mock_db
        calculator.price_analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = []  # No historical data
        
        with pytest.raises(InsufficientDataError, match="Insufficient historical data"):
            calculator.calculate_risk_index(sku_id, current_price, new_release_mentions=0)
    
    # Test threshold checking
    
    def test_check_threshold_high_risk(self, calculator):
        """Test threshold check identifies high risk."""
        # Threshold is -100.0
        # Risk index -150.0 is below threshold (high risk)
        risk_index = -150.0
        
        result = calculator.check_threshold(risk_index)
        
        assert result is True
    
    def test_check_threshold_low_risk(self, calculator):
        """Test threshold check identifies low risk."""
        # Threshold is -100.0
        # Risk index -50.0 is above threshold (low risk)
        risk_index = -50.0
        
        result = calculator.check_threshold(risk_index)
        
        assert result is False
    
    def test_check_threshold_exactly_at_threshold(self, calculator):
        """Test threshold check at exact threshold value."""
        # Threshold is -100.0
        # Risk index -100.0 is at threshold (not high risk)
        risk_index = -100.0
        
        result = calculator.check_threshold(risk_index)
        
        assert result is False
    
    def test_check_threshold_positive_risk_index(self, calculator):
        """Test threshold check with positive risk index."""
        # Threshold is -100.0
        # Risk index 50.0 is above threshold (low risk)
        risk_index = 50.0
        
        result = calculator.check_threshold(risk_index)
        
        assert result is False
    
    def test_check_threshold_very_negative(self, calculator):
        """Test threshold check with very negative risk index."""
        # Threshold is -100.0
        # Risk index -500,000.0 is well below threshold (high risk)
        risk_index = -500_000.0
        
        result = calculator.check_threshold(risk_index)
        
        assert result is True

    
    # Test calculate_risk_with_sentiment
    
    def test_calculate_risk_with_sentiment_new_release_keywords(self, calculator, mock_db):
        """Test risk calculation with sentiment data containing new release keywords."""
        sku_id = 1
        current_price = 950_000.0
        sentiment_data = {
            "New Release": 5,
            "Leak": 3,
            "Price Drop": 2,
            "Issues": 1
        }
        historical_prices = [1_000_000.0]
        
        calculator.db = mock_db
        calculator.price_analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        risk_index, is_high_risk = calculator.calculate_risk_with_sentiment(
            sku_id, current_price, sentiment_data
        )
        
        # Expected: 5 + 3 = 8 new release mentions
        # Risk index: -50,000 + (8 * 0.3) = -49,997.6
        assert risk_index == -49_997.6
        assert is_high_risk is True  # Below -100 threshold
    
    def test_calculate_risk_with_sentiment_5070_keyword(self, calculator, mock_db):
        """Test risk calculation with 5070 release date keyword."""
        sku_id = 1
        current_price = 950_000.0
        sentiment_data = {
            "5070 release date": 10,
            "Price Drop": 2
        }
        historical_prices = [1_000_000.0]
        
        calculator.db = mock_db
        calculator.price_analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        risk_index, is_high_risk = calculator.calculate_risk_with_sentiment(
            sku_id, current_price, sentiment_data
        )
        
        # Expected: 10 new release mentions
        # Risk index: -50,000 + (10 * 0.3) = -49,997.0
        assert risk_index == -49_997.0
        assert is_high_risk is True
    
    def test_calculate_risk_with_sentiment_no_new_release(self, calculator, mock_db):
        """Test risk calculation with sentiment data but no new release keywords."""
        sku_id = 1
        current_price = 950_000.0
        sentiment_data = {
            "Price Drop": 5,
            "Issues": 3,
            "Used Market": 2
        }
        historical_prices = [1_000_000.0]
        
        calculator.db = mock_db
        calculator.price_analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        risk_index, is_high_risk = calculator.calculate_risk_with_sentiment(
            sku_id, current_price, sentiment_data
        )
        
        # Expected: 0 new release mentions
        # Risk index: -50,000 + 0 = -50,000.0
        assert risk_index == -50_000.0
        assert is_high_risk is True
    
    def test_calculate_risk_with_sentiment_empty_data(self, calculator, mock_db):
        """Test risk calculation with empty sentiment data."""
        sku_id = 1
        current_price = 950_000.0
        sentiment_data = {}
        historical_prices = [1_000_000.0]
        
        calculator.db = mock_db
        calculator.price_analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        risk_index, is_high_risk = calculator.calculate_risk_with_sentiment(
            sku_id, current_price, sentiment_data
        )
        
        # Expected: 0 new release mentions
        # Risk index: -50,000 + 0 = -50,000.0
        assert risk_index == -50_000.0
        assert is_high_risk is True

    
    # Test real-world scenarios
    
    def test_rtx_4070_super_release_scenario(self, calculator, mock_db):
        """Test realistic scenario: RTX 4070 price drop when Super is released."""
        # Scenario: RTX 4070 drops from 800,000 to 720,000 (-80,000)
        # Reddit has 15 mentions of "New Release" and 10 mentions of "5070 release date"
        # Total new release mentions: 25
        # Expected risk_index: -80,000 + (25 * 0.3) = -79,992.5
        sku_id = 1
        current_price = 720_000.0
        new_release_mentions = 25
        historical_prices = [800_000.0]
        
        calculator.db = mock_db
        calculator.price_analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        risk_index = calculator.calculate_risk_index(
            sku_id, current_price, new_release_mentions
        )
        
        assert risk_index == -79_992.5
        assert calculator.check_threshold(risk_index) is True
    
    def test_stable_market_scenario(self, calculator, mock_db):
        """Test scenario with stable prices and low sentiment."""
        # Scenario: Price stable at 750,000
        # Only 2 new release mentions
        # Expected risk_index: 0 + (2 * 0.3) = 0.6
        sku_id = 1
        current_price = 750_000.0
        new_release_mentions = 2
        historical_prices = [750_000.0]
        
        calculator.db = mock_db
        calculator.price_analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        risk_index = calculator.calculate_risk_index(
            sku_id, current_price, new_release_mentions
        )
        
        assert risk_index == 0.6
        assert calculator.check_threshold(risk_index) is False
    
    def test_price_increase_with_high_sentiment(self, calculator, mock_db):
        """Test scenario with price increase despite high new release mentions."""
        # Scenario: Price increases from 700,000 to 750,000 (+50,000)
        # High sentiment: 50 new release mentions
        # Expected risk_index: 50,000 + (50 * 0.3) = 50,015.0
        sku_id = 1
        current_price = 750_000.0
        new_release_mentions = 50
        historical_prices = [700_000.0]
        
        calculator.db = mock_db
        calculator.price_analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        risk_index = calculator.calculate_risk_index(
            sku_id, current_price, new_release_mentions
        )
        
        assert risk_index == 50_015.0
        assert calculator.check_threshold(risk_index) is False
    
    def test_moderate_price_drop_high_sentiment(self, calculator, mock_db):
        """Test scenario with moderate price drop and high sentiment."""
        # Scenario: Price drops from 800,000 to 760,000 (-40,000)
        # High sentiment: 30 new release mentions
        # Expected risk_index: -40,000 + (30 * 0.3) = -39,991.0
        sku_id = 1
        current_price = 760_000.0
        new_release_mentions = 30
        historical_prices = [800_000.0]
        
        calculator.db = mock_db
        calculator.price_analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        risk_index = calculator.calculate_risk_index(
            sku_id, current_price, new_release_mentions
        )
        
        assert risk_index == -39_991.0
        assert calculator.check_threshold(risk_index) is True

    
    # Test get_contributing_factors
    
    def test_get_contributing_factors_success(self, calculator, mock_db):
        """Test getting contributing factors for risk calculation."""
        sku_id = 1
        current_price = 950_000.0
        new_release_mentions = 10
        historical_prices = [1_000_000.0]
        
        calculator.db = mock_db
        calculator.price_analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        factors = calculator.get_contributing_factors(
            sku_id, current_price, new_release_mentions
        )
        
        assert factors["current_price"] == 950_000.0
        assert factors["last_week_avg_price"] == 1_000_000.0
        assert factors["price_delta"] == -50_000.0
        assert factors["price_change_pct"] == -5.0
        assert factors["new_release_mentions"] == 10
        assert factors["sentiment_impact"] == 3.0
        assert factors["threshold"] == -100.0
    
    def test_get_contributing_factors_insufficient_data(self, calculator, mock_db):
        """Test getting contributing factors with insufficient data."""
        sku_id = 1
        current_price = 950_000.0
        new_release_mentions = 10
        
        calculator.db = mock_db
        calculator.price_analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = []  # No historical data
        
        factors = calculator.get_contributing_factors(
            sku_id, current_price, new_release_mentions
        )
        
        assert "error" in factors
        assert factors["error"] == "Insufficient historical data"
        assert factors["current_price"] == 950_000.0
        assert factors["new_release_mentions"] == 10
    
    # Test get_new_release_mentions
    
    def test_get_new_release_mentions_success(self, calculator, mock_db):
        """Test querying new release mentions from database."""
        calculator.db = mock_db
        mock_db.execute_with_retry.return_value = [
            ("New Release", 10),
            ("Leak", 5),
            ("5070 release date", 8)
        ]
        
        result = calculator.get_new_release_mentions(days=7)
        
        assert result == {
            "New Release": 10,
            "Leak": 5,
            "5070 release date": 8
        }
        assert sum(result.values()) == 23
    
    def test_get_new_release_mentions_empty(self, calculator, mock_db):
        """Test querying new release mentions with no data."""
        calculator.db = mock_db
        mock_db.execute_with_retry.return_value = []
        
        result = calculator.get_new_release_mentions(days=7)
        
        assert result == {}
    
    def test_get_new_release_mentions_custom_days(self, calculator, mock_db):
        """Test querying new release mentions with custom days parameter."""
        calculator.db = mock_db
        mock_db.execute_with_retry.return_value = [
            ("New Release", 15)
        ]
        
        result = calculator.get_new_release_mentions(days=14)
        
        assert result == {"New Release": 15}
        mock_db.execute_with_retry.assert_called_once()
    
    # Test calculate_risk_for_all_skus
    
    def test_calculate_risk_for_all_skus_success(self, calculator, mock_db):
        """Test calculating risk for all SKUs."""
        calculator.db = mock_db
        
        # Mock new release mentions query
        # Mock SKU price query
        mock_db.execute_with_retry.side_effect = [
            [("New Release", 10)],  # New release mentions
            [(1, 950_000.0), (2, 1_050_000.0)]  # SKU prices
        ]
        
        # Mock historical prices for each SKU
        calculator.price_analyzer.db = mock_db
        
        def mock_historical_prices(sku_id, *args, **kwargs):
            return [1_000_000.0]  # Return list of floats, not tuples
        
        calculator.price_analyzer._get_historical_prices = mock_historical_prices
        
        result = calculator.calculate_risk_for_all_skus(days=7)
        
        assert len(result) == 2
        assert 1 in result
        assert 2 in result
        
        # SKU 1: price drop, high risk
        risk_index_1, is_high_risk_1 = result[1]
        assert risk_index_1 < 0
        
        # SKU 2: price increase, low risk
        risk_index_2, is_high_risk_2 = result[2]
        assert risk_index_2 > 0

    
    def test_calculate_risk_for_all_skus_with_insufficient_data(self, calculator, mock_db):
        """Test calculating risk for all SKUs when some have insufficient data."""
        calculator.db = mock_db
        
        # Mock queries
        mock_db.execute_with_retry.side_effect = [
            [("New Release", 10)],  # New release mentions
            [(1, 950_000.0), (2, 1_050_000.0)]  # SKU prices
        ]
        
        # Mock historical prices - SKU 1 has data, SKU 2 doesn't
        def mock_historical_prices(sku_id, *args, **kwargs):
            if sku_id == 1:
                return [1_000_000.0]  # Return list of floats
            else:
                return []  # No data for SKU 2
        
        calculator.price_analyzer._get_historical_prices = mock_historical_prices
        
        result = calculator.calculate_risk_for_all_skus(days=7)
        
        # Only SKU 1 should be in results
        assert len(result) == 1
        assert 1 in result
        assert 2 not in result
    
    def test_calculate_risk_for_all_skus_empty(self, calculator, mock_db):
        """Test calculating risk for all SKUs with no recent price data."""
        calculator.db = mock_db
        
        # Mock queries
        mock_db.execute_with_retry.side_effect = [
            [("New Release", 10)],  # New release mentions
            []  # No SKU prices
        ]
        
        result = calculator.calculate_risk_for_all_skus(days=7)
        
        assert result == {}


class TestRiskCalculatorIntegration:
    """Integration tests for RiskCalculator with complex scenarios."""
    
    @pytest.fixture
    def calculator(self):
        """Create a RiskCalculator instance for testing."""
        calc = RiskCalculator()
        calc.threshold = -100.0
        return calc
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database manager."""
        return Mock()
    
    def test_complete_risk_assessment_workflow(self, calculator, mock_db):
        """Test complete workflow from price data to risk assessment."""
        sku_id = 1
        current_price = 720_000.0
        sentiment_data = {
            "New Release": 10,
            "Leak": 5,
            "5070 release date": 8,
            "Price Drop": 3
        }
        historical_prices = [800_000.0]
        
        calculator.db = mock_db
        calculator.price_analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        # Calculate risk with sentiment
        risk_index, is_high_risk = calculator.calculate_risk_with_sentiment(
            sku_id, current_price, sentiment_data
        )
        
        # Get contributing factors
        factors = calculator.get_contributing_factors(
            sku_id, current_price, 23  # 10 + 5 + 8 new release mentions
        )
        
        # Verify results
        assert risk_index < -100.0  # High risk
        assert is_high_risk is True
        assert factors["price_delta"] == -80_000.0
        assert factors["price_change_pct"] == -10.0
        assert factors["sentiment_impact"] == 6.9
    
    def test_multiple_products_risk_comparison(self, calculator, mock_db):
        """Test comparing risk across multiple products."""
        calculator.db = mock_db
        calculator.price_analyzer.db = mock_db
        
        # Product 1: High risk (price drop + high sentiment)
        mock_db.execute_with_retry.return_value = [(800_000.0,)]
        risk1 = calculator.calculate_risk_index(1, 720_000.0, new_release_mentions=20)
        
        # Product 2: Low risk (price stable + low sentiment)
        mock_db.execute_with_retry.return_value = [(750_000.0,)]
        risk2 = calculator.calculate_risk_index(2, 750_000.0, new_release_mentions=2)
        
        # Product 3: Medium risk (price drop + low sentiment)
        mock_db.execute_with_retry.return_value = [(800_000.0,)]
        risk3 = calculator.calculate_risk_index(3, 780_000.0, new_release_mentions=5)
        
        # Verify risk ordering
        assert risk1 < risk3 < risk2
        assert calculator.check_threshold(risk1) is True
        assert calculator.check_threshold(risk2) is False
        assert calculator.check_threshold(risk3) is True
    
    def test_threshold_sensitivity_analysis(self, calculator, mock_db):
        """Test how different thresholds affect risk classification."""
        sku_id = 1
        current_price = 950_000.0
        new_release_mentions = 10
        historical_prices = [1_000_000.0]
        
        calculator.db = mock_db
        calculator.price_analyzer.db = mock_db
        mock_db.execute_with_retry.return_value = [
            (price,) for price in historical_prices
        ]
        
        risk_index = calculator.calculate_risk_index(
            sku_id, current_price, new_release_mentions
        )
        
        # Test different thresholds
        calculator.threshold = -100_000.0
        assert calculator.check_threshold(risk_index) is False
        
        calculator.threshold = -40_000.0
        assert calculator.check_threshold(risk_index) is True
        
        calculator.threshold = -50_000.0
        assert calculator.check_threshold(risk_index) is False

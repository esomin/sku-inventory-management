"""
Unit tests for database loader module.

These tests verify the data loading functions for Products, Price_Logs,
Market_Signals, and Risk_Alerts tables with proper upsert logic and
transaction handling.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
from psycopg2 import DatabaseError

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

from loaders.db_loader import (
    upsert_product,
    upsert_products_batch,
    insert_price_log,
    insert_price_logs_batch,
    insert_market_signal,
    insert_market_signals_batch,
    insert_risk_alert,
    insert_risk_alerts_batch,
    _format_alert_message,
    LoaderError
)
from models import NormalizedProduct, PriceData, MarketSignal


class TestUpsertProduct:
    """Test suite for upsert_product function."""
    
    @patch('loaders.db_loader.db_manager')
    def test_upsert_product_success(self, mock_db_manager):
        """Test successful product upsert returns sku_id."""
        product = NormalizedProduct(
            brand="ASUS",
            chipset="RTX 4070 Super",
            model_name="TUF Gaming OC",
            vram="12GB",
            is_oc=True
        )
        
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (123,)
        mock_db_manager.get_cursor.return_value.__enter__.return_value = mock_cursor
        
        sku_id = upsert_product(product)
        
        assert sku_id == 123
        mock_cursor.execute.assert_called_once()
        
        # Verify the query includes all required fields
        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "INSERT INTO products" in query
        assert "ON CONFLICT" in query
        assert params[0] == "그래픽카드"  # category
        assert params[1] == "RTX 4070 Super"  # chipset
        assert params[2] == "ASUS"  # brand
        assert params[3] == "TUF Gaming OC"  # model_name
        assert params[4] == "12GB"  # vram
        assert params[5] is True  # is_oc
    
    @patch('loaders.db_loader.db_manager')
    def test_upsert_product_no_result(self, mock_db_manager):
        """Test that LoaderError is raised when no ID is returned."""
        product = NormalizedProduct(
            brand="MSI",
            chipset="RTX 4070 Ti",
            model_name="Gaming X Trio",
            vram="12GB",
            is_oc=False
        )
        
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_db_manager.get_cursor.return_value.__enter__.return_value = mock_cursor
        
        with pytest.raises(LoaderError, match="Failed to retrieve product ID"):
            upsert_product(product)
    
    @patch('loaders.db_loader.db_manager')
    def test_upsert_product_database_error(self, mock_db_manager):
        """Test that database errors are properly wrapped."""
        product = NormalizedProduct(
            brand="GIGABYTE",
            chipset="RTX 4070",
            model_name="Eagle OC",
            vram="12GB",
            is_oc=True
        )
        
        mock_db_manager.get_cursor.return_value.__enter__.side_effect = DatabaseError("Connection lost")
        
        with pytest.raises(LoaderError, match="Product upsert failed"):
            upsert_product(product)


class TestUpsertProductsBatch:
    """Test suite for upsert_products_batch function."""
    
    @patch('loaders.db_loader.upsert_product')
    def test_batch_upsert_success(self, mock_upsert):
        """Test successful batch upsert returns all sku_ids."""
        products = [
            NormalizedProduct("ASUS", "RTX 4070", "TUF", "12GB", True),
            NormalizedProduct("MSI", "RTX 4070 Super", "Gaming X", "12GB", False),
            NormalizedProduct("GIGABYTE", "RTX 4070 Ti", "Eagle", "12GB", True)
        ]
        
        mock_upsert.side_effect = [1, 2, 3]
        
        sku_ids = upsert_products_batch(products)
        
        assert sku_ids == [1, 2, 3]
        assert mock_upsert.call_count == 3
    
    @patch('loaders.db_loader.upsert_product')
    def test_batch_upsert_empty_list(self, mock_upsert):
        """Test that empty list returns empty result."""
        sku_ids = upsert_products_batch([])
        
        assert sku_ids == []
        mock_upsert.assert_not_called()
    
    @patch('loaders.db_loader.upsert_product')
    def test_batch_upsert_failure(self, mock_upsert):
        """Test that failure in batch raises LoaderError."""
        products = [
            NormalizedProduct("ASUS", "RTX 4070", "TUF", "12GB", True),
            NormalizedProduct("MSI", "RTX 4070 Super", "Gaming X", "12GB", False)
        ]
        
        mock_upsert.side_effect = [1, LoaderError("Database error")]
        
        with pytest.raises(LoaderError, match="Batch product upsert failed"):
            upsert_products_batch(products)


class TestInsertPriceLog:
    """Test suite for insert_price_log function."""
    
    @patch('loaders.db_loader.db_manager')
    def test_insert_price_log_success(self, mock_db_manager):
        """Test successful price log insertion."""
        price_data = PriceData(
            product_name="ASUS RTX 4070 Super",
            price=899000.0,
            source="다나와",
            source_url="https://example.com/product/123",
            recorded_at=datetime(2024, 1, 15, 10, 30),
            price_change_pct=-5.2
        )
        
        mock_cursor = Mock()
        mock_db_manager.get_cursor.return_value.__enter__.return_value = mock_cursor
        
        insert_price_log(sku_id=1, price_data=price_data)
        
        mock_cursor.execute.assert_called_once()
        
        # Verify the query and parameters
        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "INSERT INTO price_logs" in query
        assert "ON CONFLICT" in query
        assert params[0] == 1  # sku_id
        assert params[1] == 899000.0  # price
        assert params[2] == "다나와"  # source
        assert params[3] == "https://example.com/product/123"  # source_url
        assert params[4] == datetime(2024, 1, 15, 10, 30)  # recorded_at
        assert params[5] == -5.2  # price_change_pct
    
    @patch('loaders.db_loader.db_manager')
    def test_insert_price_log_without_change_pct(self, mock_db_manager):
        """Test price log insertion without price change percentage."""
        price_data = PriceData(
            product_name="MSI RTX 4070 Ti",
            price=1200000.0,
            source="다나와",
            source_url="https://example.com/product/456",
            recorded_at=datetime(2024, 1, 15, 10, 30),
            price_change_pct=None
        )
        
        mock_cursor = Mock()
        mock_db_manager.get_cursor.return_value.__enter__.return_value = mock_cursor
        
        insert_price_log(sku_id=2, price_data=price_data)
        
        call_args = mock_cursor.execute.call_args
        params = call_args[0][1]
        assert params[5] is None  # price_change_pct should be None
    
    @patch('loaders.db_loader.db_manager')
    def test_insert_price_log_database_error(self, mock_db_manager):
        """Test that database errors are properly wrapped."""
        price_data = PriceData(
            product_name="Test Product",
            price=100000.0,
            source="다나와",
            source_url="https://example.com",
            recorded_at=datetime.now()
        )
        
        mock_db_manager.get_cursor.return_value.__enter__.side_effect = DatabaseError("Insert failed")
        
        with pytest.raises(LoaderError, match="Price log insert failed"):
            insert_price_log(sku_id=1, price_data=price_data)


class TestInsertPriceLogsBatch:
    """Test suite for insert_price_logs_batch function."""
    
    @patch('loaders.db_loader.insert_price_log')
    def test_batch_insert_success(self, mock_insert):
        """Test successful batch price log insertion."""
        price_logs = [
            PriceData("Product 1", 100000.0, "다나와", "url1", datetime.now()),
            PriceData("Product 1", 95000.0, "다나와", "url1", datetime.now()),
            PriceData("Product 1", 90000.0, "다나와", "url1", datetime.now())
        ]
        
        insert_price_logs_batch(sku_id=1, price_logs=price_logs)
        
        assert mock_insert.call_count == 3
    
    @patch('loaders.db_loader.insert_price_log')
    def test_batch_insert_empty_list(self, mock_insert):
        """Test that empty list is handled gracefully."""
        insert_price_logs_batch(sku_id=1, price_logs=[])
        
        mock_insert.assert_not_called()


class TestInsertMarketSignal:
    """Test suite for insert_market_signal function."""
    
    @patch('loaders.db_loader.db_manager')
    def test_insert_market_signal_success(self, mock_db_manager):
        """Test successful market signal insertion."""
        signal = MarketSignal(
            keyword="New Release",
            post_title="RTX 5070 leaked specs",
            post_url="https://reddit.com/r/nvidia/comments/abc123",
            subreddit="nvidia",
            timestamp=datetime(2024, 1, 15, 14, 30),
            sentiment_score=3.0
        )
        
        mock_cursor = Mock()
        mock_db_manager.get_cursor.return_value.__enter__.return_value = mock_cursor
        
        insert_market_signal(signal)
        
        mock_cursor.execute.assert_called_once()
        
        # Verify the query and parameters
        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "INSERT INTO market_signals" in query
        assert "ON CONFLICT" in query
        assert params[0] == "New Release"  # keyword
        assert params[1] == "RTX 5070 leaked specs"  # post_title
        assert params[2] == "https://reddit.com/r/nvidia/comments/abc123"  # post_url
        assert params[3] == "nvidia"  # subreddit
        assert params[4] == 3.0  # sentiment_score
        assert params[5] == date(2024, 1, 15)  # date extracted from timestamp
    
    @patch('loaders.db_loader.db_manager')
    def test_insert_market_signal_database_error(self, mock_db_manager):
        """Test that database errors are properly wrapped."""
        signal = MarketSignal(
            keyword="Price Drop",
            post_title="Test",
            post_url="https://reddit.com/test",
            subreddit="nvidia",
            timestamp=datetime.now()
        )
        
        mock_db_manager.get_cursor.return_value.__enter__.side_effect = DatabaseError("Insert failed")
        
        with pytest.raises(LoaderError, match="Market signal insert failed"):
            insert_market_signal(signal)


class TestInsertMarketSignalsBatch:
    """Test suite for insert_market_signals_batch function."""
    
    @patch('loaders.db_loader.insert_market_signal')
    def test_batch_insert_success(self, mock_insert):
        """Test successful batch market signal insertion."""
        signals = [
            MarketSignal("New Release", "Title 1", "url1", "nvidia", datetime.now()),
            MarketSignal("Price Drop", "Title 2", "url2", "pcmasterrace", datetime.now()),
            MarketSignal("Issues", "Title 3", "url3", "nvidia", datetime.now())
        ]
        
        insert_market_signals_batch(signals)
        
        assert mock_insert.call_count == 3
    
    @patch('loaders.db_loader.insert_market_signal')
    def test_batch_insert_empty_list(self, mock_insert):
        """Test that empty list is handled gracefully."""
        insert_market_signals_batch([])
        
        mock_insert.assert_not_called()


class TestInsertRiskAlert:
    """Test suite for insert_risk_alert function."""
    
    @patch('loaders.db_loader.db_manager')
    def test_insert_risk_alert_success(self, mock_db_manager):
        """Test successful risk alert insertion."""
        factors = {
            "price_change_pct": -5.2,
            "new_release_mentions": 15,
            "sentiment_score": 45.0,
            "reason": "Price drop + high new release mentions"
        }
        
        mock_cursor = Mock()
        mock_db_manager.get_cursor.return_value.__enter__.return_value = mock_cursor
        
        insert_risk_alert(
            sku_id=1,
            product_name="ASUS RTX 4070 Super TUF Gaming",
            risk_index=125.5,
            threshold=100.0,
            contributing_factors=factors
        )
        
        mock_cursor.execute.assert_called_once()
        
        # Verify the query and parameters
        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "INSERT INTO risk_alerts" in query
        assert params[0] == 1  # sku_id
        assert params[1] == 125.5  # risk_index
        assert params[2] == 100.0  # threshold
        assert '"price_change_pct": -5.2' in params[3]  # contributing_factors JSON
        assert params[4] is False  # acknowledged
    
    @patch('loaders.db_loader.db_manager')
    def test_insert_risk_alert_database_error(self, mock_db_manager):
        """Test that database errors are properly wrapped."""
        mock_db_manager.get_cursor.return_value.__enter__.side_effect = DatabaseError("Insert failed")
        
        with pytest.raises(LoaderError, match="Risk alert insert failed"):
            insert_risk_alert(
                sku_id=1,
                product_name="Test Product",
                risk_index=150.0,
                threshold=100.0,
                contributing_factors={}
            )


class TestFormatAlertMessage:
    """Test suite for _format_alert_message function."""
    
    def test_format_basic_alert(self):
        """Test basic alert message formatting."""
        message = _format_alert_message(
            product_name="ASUS RTX 4070 Super",
            risk_index=125.5,
            threshold=100.0,
            factors={}
        )
        
        assert "ASUS RTX 4070 Super" in message
        assert "125.5" in message
        assert "100.0" in message
    
    def test_format_alert_with_all_factors(self):
        """Test alert message with all contributing factors."""
        factors = {
            "price_change_pct": -5.2,
            "new_release_mentions": 15,
            "sentiment_score": 45.0,
            "reason": "Market shift detected"
        }
        
        message = _format_alert_message(
            product_name="MSI RTX 4070 Ti",
            risk_index=180.0,
            threshold=100.0,
            factors=factors
        )
        
        assert "MSI RTX 4070 Ti" in message
        assert "-5.2" in message
        assert "15" in message
        assert "45.0" in message
        assert "Market shift detected" in message
    
    def test_format_alert_high_risk_recommendation(self):
        """Test that high risk alerts include immediate action recommendation."""
        message = _format_alert_message(
            product_name="Test Product",
            risk_index=200.0,  # > threshold * 1.5
            threshold=100.0,
            factors={}
        )
        
        assert "즉시 재고 처분 검토 필요" in message
    
    def test_format_alert_moderate_risk_recommendation(self):
        """Test that moderate risk alerts include monitoring recommendation."""
        message = _format_alert_message(
            product_name="Test Product",
            risk_index=120.0,  # > threshold but < threshold * 1.5
            threshold=100.0,
            factors={}
        )
        
        assert "재고 모니터링 강화" in message


class TestInsertRiskAlertsBatch:
    """Test suite for insert_risk_alerts_batch function."""
    
    @patch('loaders.db_loader.insert_risk_alert')
    def test_batch_insert_success(self, mock_insert):
        """Test successful batch risk alert insertion."""
        alerts = [
            {
                "sku_id": 1,
                "product_name": "Product 1",
                "risk_index": 120.0,
                "threshold": 100.0,
                "contributing_factors": {"reason": "Test 1"}
            },
            {
                "sku_id": 2,
                "product_name": "Product 2",
                "risk_index": 150.0,
                "threshold": 100.0,
                "contributing_factors": {"reason": "Test 2"}
            }
        ]
        
        insert_risk_alerts_batch(alerts)
        
        assert mock_insert.call_count == 2
    
    @patch('loaders.db_loader.insert_risk_alert')
    def test_batch_insert_empty_list(self, mock_insert):
        """Test that empty list is handled gracefully."""
        insert_risk_alerts_batch([])
        
        mock_insert.assert_not_called()
    
    @patch('loaders.db_loader.insert_risk_alert')
    def test_batch_insert_failure(self, mock_insert):
        """Test that failure in batch raises LoaderError."""
        alerts = [
            {
                "sku_id": 1,
                "product_name": "Product 1",
                "risk_index": 120.0,
                "threshold": 100.0,
                "contributing_factors": {}
            }
        ]
        
        mock_insert.side_effect = LoaderError("Database error")
        
        with pytest.raises(LoaderError, match="Batch risk alert insert failed"):
            insert_risk_alerts_batch(alerts)

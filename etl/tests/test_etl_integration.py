"""
Simplified integration tests for the ETL pipeline.

These tests verify the ETL pipeline logic without requiring database connections.
All external dependencies are mocked.

Validates: Requirements 3.5, 8.5
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
from typing import List
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def mock_price_data():
    """Create mock price data for testing."""
    from models import PriceData
    return [
        PriceData(
            product_name="ASUS TUF Gaming 지포스 RTX 4070 Super OC D6X 12GB",
            price=899000.0,
            source="다나와",
            source_url="http://example.com/product1",
            recorded_at=datetime.now(),
            price_change_pct=None
        ),
        PriceData(
            product_name="MSI 지포스 RTX 4070 Ti Gaming X 트라이오 D6X 12GB",
            price=1099000.0,
            source="다나와",
            source_url="http://example.com/product2",
            recorded_at=datetime.now(),
            price_change_pct=None
        )
    ]


@pytest.fixture
def mock_market_signals():
    """Create mock market signals for testing."""
    from models import MarketSignal
    return [
        MarketSignal(
            keyword="New Release",
            post_title="RTX 5070 leaked specs",
            post_url="http://reddit.com/post1",
            subreddit="nvidia",
            timestamp=datetime.now(),
            sentiment_score=None
        ),
        MarketSignal(
            keyword="Price Drop",
            post_title="RTX 4070 prices dropping",
            post_url="http://reddit.com/post2",
            subreddit="nvidia",
            timestamp=datetime.now(),
            sentiment_score=None
        )
    ]


class TestETLPipelineComponents:
    """Test individual ETL pipeline components."""
    
    @patch('main.db_manager')
    @patch('main.DanawaCrawler')
    def test_extract_prices_workflow(self, mock_crawler_class, mock_db, mock_price_data):
        """Test price extraction workflow."""
        from main import ETLPipeline
        
        # Setup mock crawler
        mock_crawler = Mock()
        mock_crawler.crawl_danawa.return_value = mock_price_data
        mock_crawler.close.return_value = None
        mock_crawler_class.return_value = mock_crawler
        
        # Create pipeline
        pipeline = ETLPipeline()
        pipeline.price_crawler = mock_crawler
        
        # Execute extraction
        result = pipeline.extract_prices()
        
        # Verify
        assert len(result) > 0
        assert pipeline.stats['prices_extracted'] > 0
        assert mock_crawler.crawl_danawa.called
    
    @patch('main.db_manager')
    @patch('main.RedditCollector')
    def test_extract_market_signals_workflow(self, mock_collector_class, mock_db, mock_market_signals):
        """Test market signal extraction workflow."""
        from main import ETLPipeline
        
        # Setup mock collector
        mock_collector = Mock()
        mock_collector.collect_signals.return_value = mock_market_signals
        mock_collector.close.return_value = None
        mock_collector_class.return_value = mock_collector
        
        # Create pipeline
        pipeline = ETLPipeline()
        pipeline.reddit_collector = mock_collector
        
        # Execute extraction
        result = pipeline.extract_market_signals()
        
        # Verify
        assert len(result) == len(mock_market_signals)
        assert pipeline.stats['signals_extracted'] == len(mock_market_signals)
    
    @patch('main.db_manager')
    @patch('main.ProductNormalizer')
    @patch('main.SKUMatcher')
    def test_transform_products_workflow(
        self,
        mock_matcher_class,
        mock_normalizer_class,
        mock_db,
        mock_price_data
    ):
        """Test product transformation workflow."""
        from main import ETLPipeline
        from models import NormalizedProduct
        
        # Setup mocks
        mock_normalizer = Mock()
        mock_normalizer.normalize.return_value = NormalizedProduct(
            brand="ASUS",
            chipset="RTX 4070 Super",
            model_name="TUF Gaming OC",
            vram="12GB",
            is_oc=True
        )
        mock_normalizer_class.return_value = mock_normalizer
        
        mock_matcher = Mock()
        mock_matcher.match_or_suggest.return_value = {
            'action': 'use_existing',
            'sku_id': 1
        }
        mock_matcher_class.return_value = mock_matcher
        
        # Create pipeline
        pipeline = ETLPipeline()
        pipeline.product_normalizer = mock_normalizer
        pipeline.sku_matcher = mock_matcher
        
        # Execute transformation
        normalized, sku_mapping = pipeline.transform_products(mock_price_data)
        
        # Verify
        assert len(normalized) == len(mock_price_data)
        assert len(sku_mapping) == len(mock_price_data)
        assert pipeline.stats['products_normalized'] == len(mock_price_data)
    
    @patch('main.db_manager')
    @patch('main.SentimentAnalyzer')
    def test_transform_sentiment_workflow(
        self,
        mock_analyzer_class,
        mock_db,
        mock_market_signals
    ):
        """Test sentiment transformation workflow."""
        from main import ETLPipeline
        from models import MarketSignal
        
        # Setup mock
        enriched_signals = [
            MarketSignal(
                keyword=signal.keyword,
                post_title=signal.post_title,
                post_url=signal.post_url,
                subreddit=signal.subreddit,
                timestamp=signal.timestamp,
                sentiment_score=3.0 if "New Release" in signal.keyword else 2.0
            )
            for signal in mock_market_signals
        ]
        
        mock_analyzer = Mock()
        mock_analyzer.enrich_signals_with_sentiment.return_value = enriched_signals
        mock_analyzer_class.return_value = mock_analyzer
        
        # Create pipeline
        pipeline = ETLPipeline()
        pipeline.sentiment_analyzer = mock_analyzer
        
        # Execute transformation
        result = pipeline.transform_sentiment(mock_market_signals)
        
        # Verify
        assert len(result) == len(mock_market_signals)
        assert all(signal.sentiment_score is not None for signal in result)


class TestETLPipelineErrorHandling:
    """Test error handling in the ETL pipeline."""
    
    @patch('main.db_manager')
    @patch('main.DanawaCrawler')
    def test_extract_prices_handles_crawl_error(self, mock_crawler_class, mock_db):
        """Test that pipeline continues when some chipsets fail to crawl."""
        from main import ETLPipeline
        from extractors.danawa_crawler import CrawlError
        from models import PriceData
        
        # Setup mock to fail on first chipset, succeed on others
        mock_crawler = Mock()
        mock_crawler.crawl_danawa.side_effect = [
            CrawlError("Network error"),
            [PriceData(
                product_name="Test Product",
                price=100000.0,
                source="다나와",
                source_url="http://example.com",
                recorded_at=datetime.now()
            )],
            [],
            []
        ]
        mock_crawler.close.return_value = None
        mock_crawler_class.return_value = mock_crawler
        
        # Create pipeline
        pipeline = ETLPipeline()
        pipeline.price_crawler = mock_crawler
        
        # Execute extraction
        result = pipeline.extract_prices()
        
        # Verify - should continue despite one failure
        assert len(pipeline.stats['errors']) > 0
        assert any('Network error' in str(e) for e in pipeline.stats['errors'])
    
    @patch('main.db_manager')
    @patch('main.RedditCollector')
    def test_extract_signals_handles_rate_limit(self, mock_collector_class, mock_db):
        """Test that pipeline handles Reddit rate limit errors."""
        from main import ETLPipeline
        from extractors.reddit_collector import RateLimitError
        
        # Setup mock to raise rate limit error
        mock_collector = Mock()
        mock_collector.collect_signals.side_effect = RateLimitError("Rate limit exceeded")
        mock_collector.close.return_value = None
        mock_collector_class.return_value = mock_collector
        
        # Create pipeline
        pipeline = ETLPipeline()
        pipeline.reddit_collector = mock_collector
        
        # Execute extraction
        result = pipeline.extract_market_signals()
        
        # Verify - should return empty list and log error
        assert len(result) == 0
        assert len(pipeline.stats['errors']) > 0
        assert any('rate limit' in str(e).lower() for e in pipeline.stats['errors'])
    
    @patch('main.db_manager')
    @patch('main.ProductNormalizer')
    def test_transform_handles_normalization_error(
        self,
        mock_normalizer_class,
        mock_db,
        mock_price_data
    ):
        """Test that pipeline continues when some products fail to normalize."""
        from main import ETLPipeline
        from transformers.product_normalizer import NormalizationError
        from models import NormalizedProduct
        
        # Setup mock to fail on second product
        mock_normalizer = Mock()
        mock_normalizer.normalize.side_effect = [
            NormalizedProduct(
                brand="ASUS",
                chipset="RTX 4070 Super",
                model_name="TUF Gaming OC",
                vram="12GB",
                is_oc=True
            ),
            NormalizationError("Failed to extract chipset")
        ]
        mock_normalizer_class.return_value = mock_normalizer
        
        # Create pipeline
        pipeline = ETLPipeline()
        pipeline.product_normalizer = mock_normalizer
        pipeline.sku_matcher = Mock()
        pipeline.sku_matcher.match_or_suggest.return_value = {
            'action': 'use_existing',
            'sku_id': 1
        }
        
        # Execute transformation
        normalized, sku_mapping = pipeline.transform_products(mock_price_data)
        
        # Verify - should continue despite one failure
        assert len(normalized) == 1  # One succeeded
        assert len(pipeline.stats['errors']) > 0


class TestETLPipelineStatistics:
    """Test that pipeline tracks statistics correctly."""
    
    @patch('main.db_manager')
    def test_pipeline_initializes_statistics(self, mock_db):
        """Test that pipeline initializes statistics correctly."""
        from main import ETLPipeline
        
        pipeline = ETLPipeline()
        
        # Verify initial state
        assert pipeline.stats['prices_extracted'] == 0
        assert pipeline.stats['signals_extracted'] == 0
        assert pipeline.stats['products_normalized'] == 0
        assert pipeline.stats['prices_loaded'] == 0
        assert pipeline.stats['signals_loaded'] == 0
        assert pipeline.stats['alerts_generated'] == 0
        assert len(pipeline.stats['errors']) == 0
    
    @patch('main.db_manager')
    @patch('main.DanawaCrawler')
    def test_pipeline_tracks_extraction_statistics(
        self,
        mock_crawler_class,
        mock_db,
        mock_price_data
    ):
        """Test that pipeline tracks extraction statistics."""
        from main import ETLPipeline
        
        # Setup mock
        mock_crawler = Mock()
        mock_crawler.crawl_danawa.return_value = mock_price_data
        mock_crawler.close.return_value = None
        mock_crawler_class.return_value = mock_crawler
        
        # Create pipeline
        pipeline = ETLPipeline()
        pipeline.price_crawler = mock_crawler
        
        # Execute extraction
        pipeline.extract_prices()
        
        # Verify statistics
        assert pipeline.stats['prices_extracted'] > 0


class TestETLPipelinePartialTasks:
    """Test partial ETL pipeline tasks."""
    
    @patch('main.db_manager')
    @patch('main.ETLPipeline')
    def test_run_price_crawl_only_calls_correct_methods(self, mock_pipeline_class, mock_db):
        """Test that price crawl only task calls the correct methods."""
        from main import run_price_crawl_only
        
        # Setup mock
        mock_pipeline = Mock()
        mock_pipeline.extract_prices.return_value = []
        mock_pipeline.transform_products.return_value = ([], {})
        mock_pipeline.load_products.return_value = None
        mock_pipeline.load_prices.return_value = None
        mock_pipeline._cleanup.return_value = None
        mock_pipeline.stats = {'success': True}
        mock_pipeline_class.return_value = mock_pipeline
        
        # Execute
        stats = run_price_crawl_only()
        
        # Verify correct methods were called
        assert mock_pipeline.extract_prices.called
        assert mock_pipeline.transform_products.called
        assert mock_pipeline.load_products.called
        assert mock_pipeline.load_prices.called
        # Should NOT call Reddit-related methods
        assert not mock_pipeline.extract_market_signals.called
    
    @patch('main.db_manager')
    @patch('main.ETLPipeline')
    def test_run_reddit_collection_only_calls_correct_methods(self, mock_pipeline_class, mock_db):
        """Test that Reddit collection only task calls the correct methods."""
        from main import run_reddit_collection_only
        
        # Setup mock
        mock_pipeline = Mock()
        mock_pipeline.extract_market_signals.return_value = []
        mock_pipeline.transform_sentiment.return_value = []
        mock_pipeline.load_market_signals.return_value = None
        mock_pipeline._cleanup.return_value = None
        mock_pipeline.stats = {'success': True}
        mock_pipeline_class.return_value = mock_pipeline
        
        # Execute
        stats = run_reddit_collection_only()
        
        # Verify correct methods were called
        assert mock_pipeline.extract_market_signals.called
        assert mock_pipeline.transform_sentiment.called
        assert mock_pipeline.load_market_signals.called
        # Should NOT call price-related methods
        assert not mock_pipeline.extract_prices.called


def test_main_module_imports():
    """Test that main module can be imported without errors."""
    # This test verifies that the module structure is correct
    import main
    assert hasattr(main, 'ETLPipeline')
    assert hasattr(main, 'run_price_crawl_only')
    assert hasattr(main, 'run_reddit_collection_only')
    assert hasattr(main, 'main')

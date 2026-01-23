"""
Integration tests for the ETL pipeline.

These tests verify the complete Extract → Transform → Load workflow
with mocked external dependencies and a test database.

Validates: Requirements 3.5, 8.5
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock database manager before importing main
from unittest.mock import Mock, patch, MagicMock
import pytest

# Mock the database manager to avoid connection attempts during import
with patch('db_connection.DatabaseManager'):
    from main import ETLPipeline, run_price_crawl_only, run_reddit_collection_only
    from models import PriceData, MarketSignal, NormalizedProduct
    from extractors.danawa_crawler import CrawlError
    from extractors.reddit_collector import RateLimitError
    from transformers.product_normalizer import NormalizationError
    from loaders.db_loader import LoaderError

from datetime import datetime, timedelta
from typing import List


@pytest.fixture
def mock_price_data() -> List[PriceData]:
    """Create mock price data for testing."""
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
        ),
        PriceData(
            product_name="GIGABYTE 지포스 RTX 4070 WINDFORCE OC D6X 12GB",
            price=799000.0,
            source="다나와",
            source_url="http://example.com/product3",
            recorded_at=datetime.now(),
            price_change_pct=None
        )
    ]


@pytest.fixture
def mock_market_signals() -> List[MarketSignal]:
    """Create mock market signals for testing."""
    return [
        MarketSignal(
            keyword="New Release",
            post_title="RTX 5070 leaked specs look amazing",
            post_url="http://reddit.com/r/nvidia/post1",
            subreddit="nvidia",
            timestamp=datetime.now(),
            sentiment_score=None
        ),
        MarketSignal(
            keyword="Price Drop",
            post_title="RTX 4070 prices dropping fast",
            post_url="http://reddit.com/r/nvidia/post2",
            subreddit="nvidia",
            timestamp=datetime.now(),
            sentiment_score=None
        ),
        MarketSignal(
            keyword="New Release",
            post_title="5070 release date confirmed",
            post_url="http://reddit.com/r/pcmasterrace/post3",
            subreddit="pcmasterrace",
            timestamp=datetime.now(),
            sentiment_score=None
        )
    ]


@pytest.fixture
def etl_pipeline():
    """Create an ETL pipeline instance for testing."""
    return ETLPipeline()


class TestETLPipelineExtraction:
    """Test the extraction phase of the ETL pipeline."""
    
    @patch('main.DanawaCrawler')
    def test_extract_prices_success(self, mock_crawler_class, etl_pipeline, mock_price_data):
        """Test successful price extraction from all chipsets."""
        # Setup mock
        mock_crawler = Mock()
        mock_crawler.crawl_danawa.return_value = mock_price_data
        mock_crawler_class.return_value = mock_crawler
        
        # Create new pipeline with mocked crawler
        pipeline = ETLPipeline()
        pipeline.price_crawler = mock_crawler
        
        # Execute
        result = pipeline.extract_prices()
        
        # Verify
        assert len(result) > 0
        assert pipeline.stats['prices_extracted'] > 0
        assert mock_crawler.crawl_danawa.called
    
    @patch('main.DanawaCrawler')
    def test_extract_prices_partial_failure(self, mock_crawler_class, etl_pipeline, mock_price_data):
        """Test price extraction when some chipsets fail."""
        # Setup mock to fail on first chipset, succeed on others
        mock_crawler = Mock()
        mock_crawler.crawl_danawa.side_effect = [
            CrawlError("Network error"),
            mock_price_data,
            mock_price_data,
            mock_price_data
        ]
        mock_crawler_class.return_value = mock_crawler
        
        # Create new pipeline with mocked crawler
        pipeline = ETLPipeline()
        pipeline.price_crawler = mock_crawler
        
        # Execute
        result = pipeline.extract_prices()
        
        # Verify - should continue despite one failure
        assert len(result) > 0
        assert len(pipeline.stats['errors']) > 0
        assert any('Network error' in str(e) for e in pipeline.stats['errors'])
    
    @patch('main.RedditCollector')
    def test_extract_market_signals_success(self, mock_collector_class, etl_pipeline, mock_market_signals):
        """Test successful market signal extraction."""
        # Setup mock
        mock_collector = Mock()
        mock_collector.collect_signals.return_value = mock_market_signals
        mock_collector_class.return_value = mock_collector
        
        # Create new pipeline with mocked collector
        pipeline = ETLPipeline()
        pipeline.reddit_collector = mock_collector
        
        # Execute
        result = pipeline.extract_market_signals()
        
        # Verify
        assert len(result) == len(mock_market_signals)
        assert pipeline.stats['signals_extracted'] == len(mock_market_signals)
    
    @patch('main.RedditCollector')
    def test_extract_market_signals_rate_limit(self, mock_collector_class, etl_pipeline):
        """Test market signal extraction with rate limit error."""
        # Setup mock to raise rate limit error
        mock_collector = Mock()
        mock_collector.collect_signals.side_effect = RateLimitError("Rate limit exceeded")
        mock_collector_class.return_value = mock_collector
        
        # Create new pipeline with mocked collector
        pipeline = ETLPipeline()
        pipeline.reddit_collector = mock_collector
        
        # Execute
        result = pipeline.extract_market_signals()
        
        # Verify - should return empty list and log error
        assert len(result) == 0
        assert len(pipeline.stats['errors']) > 0
        assert any('rate limit' in str(e).lower() for e in pipeline.stats['errors'])


class TestETLPipelineTransformation:
    """Test the transformation phase of the ETL pipeline."""
    
    @patch('main.ProductNormalizer')
    @patch('main.SKUMatcher')
    def test_transform_products_success(
        self,
        mock_matcher_class,
        mock_normalizer_class,
        etl_pipeline,
        mock_price_data
    ):
        """Test successful product normalization and SKU matching."""
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
        
        # Create new pipeline with mocked components
        pipeline = ETLPipeline()
        pipeline.product_normalizer = mock_normalizer
        pipeline.sku_matcher = mock_matcher
        
        # Execute
        normalized, sku_mapping = pipeline.transform_products(mock_price_data)
        
        # Verify
        assert len(normalized) == len(mock_price_data)
        assert len(sku_mapping) == len(mock_price_data)
        assert pipeline.stats['products_normalized'] == len(mock_price_data)
    
    @patch('main.ProductNormalizer')
    def test_transform_products_normalization_error(
        self,
        mock_normalizer_class,
        etl_pipeline,
        mock_price_data
    ):
        """Test product transformation with normalization errors."""
        # Setup mock to fail on some products
        mock_normalizer = Mock()
        mock_normalizer.normalize.side_effect = [
            NormalizedProduct(
                brand="ASUS",
                chipset="RTX 4070 Super",
                model_name="TUF Gaming OC",
                vram="12GB",
                is_oc=True
            ),
            NormalizationError("Failed to extract chipset"),
            NormalizedProduct(
                brand="GIGABYTE",
                chipset="RTX 4070",
                model_name="WINDFORCE OC",
                vram="12GB",
                is_oc=True
            )
        ]
        mock_normalizer_class.return_value = mock_normalizer
        
        # Create new pipeline with mocked normalizer
        pipeline = ETLPipeline()
        pipeline.product_normalizer = mock_normalizer
        pipeline.sku_matcher = Mock()
        pipeline.sku_matcher.match_or_suggest.return_value = {
            'action': 'use_existing',
            'sku_id': 1
        }
        
        # Execute
        normalized, sku_mapping = pipeline.transform_products(mock_price_data)
        
        # Verify - should continue despite one failure
        assert len(normalized) == 2  # One failed
        assert len(pipeline.stats['errors']) > 0
    
    @patch('main.SentimentAnalyzer')
    def test_transform_sentiment_success(
        self,
        mock_analyzer_class,
        etl_pipeline,
        mock_market_signals
    ):
        """Test successful sentiment analysis."""
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
        
        # Create new pipeline with mocked analyzer
        pipeline = ETLPipeline()
        pipeline.sentiment_analyzer = mock_analyzer
        
        # Execute
        result = pipeline.transform_sentiment(mock_market_signals)
        
        # Verify
        assert len(result) == len(mock_market_signals)
        assert all(signal.sentiment_score is not None for signal in result)


class TestETLPipelineLoading:
    """Test the loading phase of the ETL pipeline."""
    
    @patch('main.upsert_product')
    def test_load_products_success(self, mock_upsert, etl_pipeline):
        """Test successful product loading."""
        # Setup mock
        mock_upsert.return_value = 1
        
        # Create test products
        products = [
            NormalizedProduct(
                brand="ASUS",
                chipset="RTX 4070 Super",
                model_name="TUF Gaming OC",
                vram="12GB",
                is_oc=True
            ),
            NormalizedProduct(
                brand="MSI",
                chipset="RTX 4070 Ti",
                model_name="Gaming X Trio",
                vram="12GB",
                is_oc=False
            )
        ]
        
        # Execute
        etl_pipeline.load_products(products)
        
        # Verify
        assert mock_upsert.call_count == len(products)
    
    @patch('main.upsert_product')
    def test_load_products_partial_failure(self, mock_upsert, etl_pipeline):
        """Test product loading with some failures."""
        # Setup mock to fail on second product
        mock_upsert.side_effect = [
            1,
            LoaderError("Database error"),
            3
        ]
        
        # Create test products
        products = [
            NormalizedProduct(
                brand="ASUS",
                chipset="RTX 4070 Super",
                model_name="TUF Gaming OC",
                vram="12GB",
                is_oc=True
            ),
            NormalizedProduct(
                brand="MSI",
                chipset="RTX 4070 Ti",
                model_name="Gaming X Trio",
                vram="12GB",
                is_oc=False
            ),
            NormalizedProduct(
                brand="GIGABYTE",
                chipset="RTX 4070",
                model_name="WINDFORCE OC",
                vram="12GB",
                is_oc=True
            )
        ]
        
        # Execute
        etl_pipeline.load_products(products)
        
        # Verify - should continue despite one failure
        assert len(etl_pipeline.stats['errors']) > 0
        assert any('Database error' in str(e) for e in etl_pipeline.stats['errors'])
    
    @patch('main.insert_price_log')
    @patch('main.upsert_product')
    @patch('main.PriceAnalyzer')
    def test_load_prices_success(
        self,
        mock_analyzer_class,
        mock_upsert,
        mock_insert_price,
        etl_pipeline,
        mock_price_data
    ):
        """Test successful price loading with price change calculation."""
        # Setup mocks
        mock_upsert.return_value = 1
        mock_insert_price.return_value = None
        
        mock_analyzer = Mock()
        mock_analyzer.calculate_price_change.return_value = -5.2
        mock_analyzer_class.return_value = mock_analyzer
        
        # Create SKU mapping
        sku_mapping = {
            price_data.product_name: 1
            for price_data in mock_price_data
        }
        
        # Create new pipeline with mocked analyzer
        pipeline = ETLPipeline()
        pipeline.price_analyzer = mock_analyzer
        
        # Execute
        pipeline.load_prices(mock_price_data, sku_mapping)
        
        # Verify
        assert mock_insert_price.call_count == len(mock_price_data)
        assert pipeline.stats['prices_loaded'] == len(mock_price_data)
    
    @patch('main.insert_market_signal')
    def test_load_market_signals_success(
        self,
        mock_insert_signal,
        etl_pipeline,
        mock_market_signals
    ):
        """Test successful market signal loading."""
        # Setup mock
        mock_insert_signal.return_value = None
        
        # Execute
        etl_pipeline.load_market_signals(mock_market_signals)
        
        # Verify
        assert mock_insert_signal.call_count == len(mock_market_signals)
        assert etl_pipeline.stats['signals_loaded'] == len(mock_market_signals)


class TestETLPipelineRiskAnalysis:
    """Test the risk analysis phase of the ETL pipeline."""
    
    @patch('main.insert_risk_alert')
    @patch('main.RiskCalculator')
    @patch('main.db_manager')
    def test_generate_risk_alerts_success(
        self,
        mock_db,
        mock_calculator_class,
        mock_insert_alert,
        etl_pipeline
    ):
        """Test successful risk alert generation."""
        # Setup mocks
        mock_calculator = Mock()
        mock_calculator.calculate_risk_for_all_skus.return_value = {
            1: (-150.0, True),  # High risk
            2: (-50.0, False),  # Low risk
            3: (-200.0, True)   # High risk
        }
        mock_calculator.threshold = -100.0
        mock_calculator.get_new_release_mentions.return_value = {"New Release": 15}
        mock_calculator.get_contributing_factors.return_value = {
            "current_price": 800000.0,
            "last_week_avg_price": 850000.0,
            "price_delta": -50000.0,
            "price_change_pct": -5.88,
            "new_release_mentions": 15,
            "sentiment_impact": 4.5
        }
        mock_calculator_class.return_value = mock_calculator
        
        # Setup database mock
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            ("ASUS", "TUF Gaming OC", "RTX 4070 Super"),  # Product 1
            (800000.0,),  # Price 1
            ("MSI", "Gaming X Trio", "RTX 4070 Ti"),  # Product 3
            (1000000.0,)  # Price 3
        ]
        mock_db.get_cursor.return_value.__enter__.return_value = mock_cursor
        
        mock_insert_alert.return_value = None
        
        # Create new pipeline with mocked calculator
        pipeline = ETLPipeline()
        pipeline.risk_calculator = mock_calculator
        
        # Execute
        pipeline.generate_risk_alerts()
        
        # Verify - should generate alerts for 2 high-risk products
        assert mock_insert_alert.call_count == 2
        assert pipeline.stats['alerts_generated'] == 2


class TestETLPipelineFullWorkflow:
    """Test the complete ETL pipeline workflow."""
    
    @patch('main.insert_risk_alert')
    @patch('main.insert_market_signal')
    @patch('main.insert_price_log')
    @patch('main.upsert_product')
    @patch('main.RiskCalculator')
    @patch('main.SentimentAnalyzer')
    @patch('main.PriceAnalyzer')
    @patch('main.SKUMatcher')
    @patch('main.ProductNormalizer')
    @patch('main.RedditCollector')
    @patch('main.DanawaCrawler')
    @patch('main.db_manager')
    def test_full_pipeline_success(
        self,
        mock_db,
        mock_crawler_class,
        mock_collector_class,
        mock_normalizer_class,
        mock_matcher_class,
        mock_price_analyzer_class,
        mock_sentiment_analyzer_class,
        mock_risk_calculator_class,
        mock_upsert,
        mock_insert_price,
        mock_insert_signal,
        mock_insert_alert,
        mock_price_data,
        mock_market_signals
    ):
        """Test complete ETL pipeline execution."""
        # Setup all mocks
        mock_crawler = Mock()
        mock_crawler.crawl_danawa.return_value = mock_price_data
        mock_crawler.close.return_value = None
        mock_crawler_class.return_value = mock_crawler
        
        mock_collector = Mock()
        mock_collector.collect_signals.return_value = mock_market_signals
        mock_collector.close.return_value = None
        mock_collector_class.return_value = mock_collector
        
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
        
        mock_price_analyzer = Mock()
        mock_price_analyzer.calculate_price_change.return_value = -5.2
        mock_price_analyzer_class.return_value = mock_price_analyzer
        
        enriched_signals = [
            MarketSignal(
                keyword=signal.keyword,
                post_title=signal.post_title,
                post_url=signal.post_url,
                subreddit=signal.subreddit,
                timestamp=signal.timestamp,
                sentiment_score=3.0
            )
            for signal in mock_market_signals
        ]
        mock_sentiment_analyzer = Mock()
        mock_sentiment_analyzer.enrich_signals_with_sentiment.return_value = enriched_signals
        mock_sentiment_analyzer_class.return_value = mock_sentiment_analyzer
        
        mock_risk_calculator = Mock()
        mock_risk_calculator.calculate_risk_for_all_skus.return_value = {}
        mock_risk_calculator.threshold = -100.0
        mock_risk_calculator_class.return_value = mock_risk_calculator
        
        mock_upsert.return_value = 1
        mock_insert_price.return_value = None
        mock_insert_signal.return_value = None
        
        # Create and run pipeline
        pipeline = ETLPipeline()
        stats = pipeline.run_full_pipeline()
        
        # Verify
        assert stats['success'] is True
        assert stats['prices_extracted'] > 0
        assert stats['signals_extracted'] > 0
        assert stats['products_normalized'] > 0
        assert stats['prices_loaded'] > 0
        assert stats['signals_loaded'] > 0
    
    @patch('main.DanawaCrawler')
    def test_full_pipeline_extraction_failure(self, mock_crawler_class):
        """Test pipeline behavior when extraction fails completely."""
        # Setup mock to fail
        mock_crawler = Mock()
        mock_crawler.crawl_danawa.side_effect = Exception("Fatal network error")
        mock_crawler.close.return_value = None
        mock_crawler_class.return_value = mock_crawler
        
        # Create and run pipeline
        pipeline = ETLPipeline()
        stats = pipeline.run_full_pipeline()
        
        # Verify - pipeline should handle error gracefully
        assert stats['success'] is False
        assert 'fatal_error' in stats


class TestETLPipelinePartialTasks:
    """Test partial ETL pipeline tasks."""
    
    @patch('main.ETLPipeline')
    def test_run_price_crawl_only(self, mock_pipeline_class):
        """Test running only the price crawl task."""
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
        
        # Verify
        assert mock_pipeline.extract_prices.called
        assert mock_pipeline.transform_products.called
        assert mock_pipeline.load_products.called
        assert mock_pipeline.load_prices.called
        assert not mock_pipeline.extract_market_signals.called
    
    @patch('main.ETLPipeline')
    def test_run_reddit_collection_only(self, mock_pipeline_class):
        """Test running only the Reddit collection task."""
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
        
        # Verify
        assert mock_pipeline.extract_market_signals.called
        assert mock_pipeline.transform_sentiment.called
        assert mock_pipeline.load_market_signals.called
        assert not mock_pipeline.extract_prices.called


class TestETLPipelineErrorScenarios:
    """Test error handling scenarios in the ETL pipeline."""
    
    def test_pipeline_statistics_tracking(self, etl_pipeline):
        """Test that pipeline tracks statistics correctly."""
        # Verify initial state
        assert etl_pipeline.stats['prices_extracted'] == 0
        assert etl_pipeline.stats['signals_extracted'] == 0
        assert etl_pipeline.stats['products_normalized'] == 0
        assert etl_pipeline.stats['prices_loaded'] == 0
        assert etl_pipeline.stats['signals_loaded'] == 0
        assert etl_pipeline.stats['alerts_generated'] == 0
        assert len(etl_pipeline.stats['errors']) == 0
    
    @patch('main.DanawaCrawler')
    @patch('main.RedditCollector')
    def test_pipeline_cleanup_on_error(
        self,
        mock_collector_class,
        mock_crawler_class,
        etl_pipeline
    ):
        """Test that pipeline cleans up resources even on error."""
        # Setup mocks
        mock_crawler = Mock()
        mock_crawler.crawl_danawa.side_effect = Exception("Fatal error")
        mock_crawler.close.return_value = None
        mock_crawler_class.return_value = mock_crawler
        
        mock_collector = Mock()
        mock_collector.close.return_value = None
        mock_collector_class.return_value = mock_collector
        
        # Create pipeline
        pipeline = ETLPipeline()
        
        # Run pipeline (will fail)
        stats = pipeline.run_full_pipeline()
        
        # Verify cleanup was called
        assert mock_crawler.close.called
        assert mock_collector.close.called

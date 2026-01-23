"""
Unit tests for Sentiment Analyzer.

These tests verify the analyzer's ability to count keyword frequencies,
calculate weighted sentiment scores, and enrich market signals.
"""

import pytest
from datetime import datetime, date
from unittest.mock import patch

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import directly to avoid __init__.py imports that require database
import importlib.util
spec = importlib.util.spec_from_file_location(
    "sentiment_analyzer",
    os.path.join(os.path.dirname(__file__), '..', 'transformers', 'sentiment_analyzer.py')
)
sentiment_analyzer_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sentiment_analyzer_module)
SentimentAnalyzer = sentiment_analyzer_module.SentimentAnalyzer
analyze_sentiment = sentiment_analyzer_module.analyze_sentiment

from models import MarketSignal


class TestSentimentAnalyzer:
    """Test suite for SentimentAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a SentimentAnalyzer instance for testing."""
        return SentimentAnalyzer()
    
    @pytest.fixture
    def sample_signals(self):
        """Create sample market signals for testing."""
        return [
            MarketSignal(
                keyword="New Release",
                post_title="RTX 5070 announced!",
                post_url="https://reddit.com/post1",
                subreddit="nvidia",
                timestamp=datetime(2024, 1, 15, 10, 0, 0)
            ),
            MarketSignal(
                keyword="New Release",
                post_title="Another post about new release",
                post_url="https://reddit.com/post2",
                subreddit="nvidia",
                timestamp=datetime(2024, 1, 15, 11, 0, 0)
            ),
            MarketSignal(
                keyword="Price Drop",
                post_title="RTX 4070 price dropped",
                post_url="https://reddit.com/post3",
                subreddit="pcmasterrace",
                timestamp=datetime(2024, 1, 15, 12, 0, 0)
            ),
            MarketSignal(
                keyword="Issues",
                post_title="Driver issues with RTX 4070",
                post_url="https://reddit.com/post4",
                subreddit="nvidia",
                timestamp=datetime(2024, 1, 15, 13, 0, 0)
            ),
        ]
    
    def test_analyze_keyword_frequency_basic(self, analyzer, sample_signals):
        """Test basic keyword frequency counting."""
        frequency_map = analyzer.analyze_keyword_frequency(sample_signals)
        
        # Check that all keywords are present
        assert "New Release" in frequency_map
        assert "Price Drop" in frequency_map
        assert "Issues" in frequency_map
        
        # Check counts for January 15, 2024
        target_date = date(2024, 1, 15)
        assert frequency_map["New Release"][target_date] == 2
        assert frequency_map["Price Drop"][target_date] == 1
        assert frequency_map["Issues"][target_date] == 1
    
    def test_analyze_keyword_frequency_prevents_duplicates(self, analyzer):
        """Test that duplicate keywords from the same post are not counted twice."""
        signals = [
            MarketSignal(
                keyword="Price Drop",
                post_title="Price drop on RTX 4070",
                post_url="https://reddit.com/post1",
                subreddit="nvidia",
                timestamp=datetime(2024, 1, 15, 10, 0, 0)
            ),
            MarketSignal(
                keyword="Price Drop",
                post_title="Price drop on RTX 4070",
                post_url="https://reddit.com/post1",  # Same URL
                subreddit="nvidia",
                timestamp=datetime(2024, 1, 15, 10, 0, 0)
            ),
        ]
        
        frequency_map = analyzer.analyze_keyword_frequency(signals)
        
        # Should only count once since it's the same post URL
        target_date = date(2024, 1, 15)
        assert frequency_map["Price Drop"][target_date] == 1
    
    def test_analyze_keyword_frequency_multiple_keywords_same_post(self, analyzer):
        """Test that different keywords from the same post are counted separately."""
        signals = [
            MarketSignal(
                keyword="New Release",
                post_title="New release has issues",
                post_url="https://reddit.com/post1",
                subreddit="nvidia",
                timestamp=datetime(2024, 1, 15, 10, 0, 0)
            ),
            MarketSignal(
                keyword="Issues",
                post_title="New release has issues",
                post_url="https://reddit.com/post1",  # Same URL but different keyword
                subreddit="nvidia",
                timestamp=datetime(2024, 1, 15, 10, 0, 0)
            ),
        ]
        
        frequency_map = analyzer.analyze_keyword_frequency(signals)
        
        # Both keywords should be counted
        target_date = date(2024, 1, 15)
        assert frequency_map["New Release"][target_date] == 1
        assert frequency_map["Issues"][target_date] == 1
    
    def test_analyze_keyword_frequency_multiple_dates(self, analyzer):
        """Test keyword frequency counting across multiple dates."""
        signals = [
            MarketSignal(
                keyword="New Release",
                post_title="Post 1",
                post_url="https://reddit.com/post1",
                subreddit="nvidia",
                timestamp=datetime(2024, 1, 15, 10, 0, 0)
            ),
            MarketSignal(
                keyword="New Release",
                post_title="Post 2",
                post_url="https://reddit.com/post2",
                subreddit="nvidia",
                timestamp=datetime(2024, 1, 16, 10, 0, 0)
            ),
            MarketSignal(
                keyword="New Release",
                post_title="Post 3",
                post_url="https://reddit.com/post3",
                subreddit="nvidia",
                timestamp=datetime(2024, 1, 16, 11, 0, 0)
            ),
        ]
        
        frequency_map = analyzer.analyze_keyword_frequency(signals)
        
        # Check counts for each date
        assert frequency_map["New Release"][date(2024, 1, 15)] == 1
        assert frequency_map["New Release"][date(2024, 1, 16)] == 2
    
    def test_analyze_keyword_frequency_empty_signals(self, analyzer):
        """Test keyword frequency with empty signal list."""
        frequency_map = analyzer.analyze_keyword_frequency([])
        
        assert frequency_map == {}
    
    def test_calculate_sentiment_score_basic(self, analyzer):
        """Test basic sentiment score calculation with known weights."""
        keyword_counts = {
            "New Release": 5,
            "Price Drop": 3,
            "Issues": 2
        }
        
        score = analyzer.calculate_sentiment_score(keyword_counts)
        
        # Expected: (5 * 3.0) + (3 * 2.0) + (2 * 1.0) = 15 + 6 + 2 = 23.0
        assert score == 23.0
    
    def test_calculate_sentiment_score_new_release_weight(self, analyzer):
        """Test that 'New Release' keyword has 3x weight."""
        keyword_counts = {"New Release": 10}
        
        score = analyzer.calculate_sentiment_score(keyword_counts)
        
        # Expected: 10 * 3.0 = 30.0
        assert score == 30.0
    
    def test_calculate_sentiment_score_leak_weight(self, analyzer):
        """Test that 'Leak' keyword has 3x weight (same as New Release)."""
        keyword_counts = {"Leak": 5}
        
        score = analyzer.calculate_sentiment_score(keyword_counts)
        
        # Expected: 5 * 3.0 = 15.0
        assert score == 15.0
    
    def test_calculate_sentiment_score_5070_release_date_weight(self, analyzer):
        """Test that '5070 release date' keyword has 3x weight."""
        keyword_counts = {"5070 release date": 8}
        
        score = analyzer.calculate_sentiment_score(keyword_counts)
        
        # Expected: 8 * 3.0 = 24.0
        assert score == 24.0
    
    def test_calculate_sentiment_score_price_drop_weight(self, analyzer):
        """Test that 'Price Drop' keyword has 2x weight."""
        keyword_counts = {"Price Drop": 7}
        
        score = analyzer.calculate_sentiment_score(keyword_counts)
        
        # Expected: 7 * 2.0 = 14.0
        assert score == 14.0
    
    def test_calculate_sentiment_score_default_weight(self, analyzer):
        """Test that 'Issues' and 'Used Market' keywords have 1x weight."""
        keyword_counts = {
            "Issues": 4,
            "Used Market": 3
        }
        
        score = analyzer.calculate_sentiment_score(keyword_counts)
        
        # Expected: (4 * 1.0) + (3 * 1.0) = 7.0
        assert score == 7.0
    
    def test_calculate_sentiment_score_empty_counts(self, analyzer):
        """Test sentiment score calculation with empty keyword counts."""
        score = analyzer.calculate_sentiment_score({})
        
        assert score == 0.0
    
    def test_calculate_sentiment_score_unknown_keyword(self, analyzer):
        """Test that unknown keywords default to 1x weight."""
        keyword_counts = {"Unknown Keyword": 5}
        
        score = analyzer.calculate_sentiment_score(keyword_counts)
        
        # Expected: 5 * 1.0 = 5.0 (default weight)
        assert score == 5.0
    
    def test_calculate_sentiment_score_mixed_keywords(self, analyzer):
        """Test sentiment score with all keyword types."""
        keyword_counts = {
            "New Release": 2,
            "Leak": 1,
            "5070 release date": 1,
            "Price Drop": 3,
            "Issues": 2,
            "Used Market": 1
        }
        
        score = analyzer.calculate_sentiment_score(keyword_counts)
        
        # Expected:
        # (2 * 3.0) + (1 * 3.0) + (1 * 3.0) + (3 * 2.0) + (2 * 1.0) + (1 * 1.0)
        # = 6 + 3 + 3 + 6 + 2 + 1 = 21.0
        assert score == 21.0
    
    def test_calculate_daily_sentiment_scores_single_day(self, analyzer):
        """Test daily sentiment score calculation for a single day."""
        signals = [
            MarketSignal(
                keyword="New Release",
                post_title="Post 1",
                post_url="https://reddit.com/post1",
                subreddit="nvidia",
                timestamp=datetime(2024, 1, 15, 10, 0, 0)
            ),
            MarketSignal(
                keyword="Price Drop",
                post_title="Post 2",
                post_url="https://reddit.com/post2",
                subreddit="nvidia",
                timestamp=datetime(2024, 1, 15, 11, 0, 0)
            ),
        ]
        
        daily_scores = analyzer.calculate_daily_sentiment_scores(signals)
        
        target_date = date(2024, 1, 15)
        assert target_date in daily_scores
        
        # Expected: (1 * 3.0) + (1 * 2.0) = 5.0
        assert daily_scores[target_date] == 5.0
    
    def test_calculate_daily_sentiment_scores_multiple_days(self, analyzer):
        """Test daily sentiment score calculation across multiple days."""
        signals = [
            MarketSignal(
                keyword="New Release",
                post_title="Post 1",
                post_url="https://reddit.com/post1",
                subreddit="nvidia",
                timestamp=datetime(2024, 1, 15, 10, 0, 0)
            ),
            MarketSignal(
                keyword="Price Drop",
                post_title="Post 2",
                post_url="https://reddit.com/post2",
                subreddit="nvidia",
                timestamp=datetime(2024, 1, 16, 10, 0, 0)
            ),
            MarketSignal(
                keyword="Issues",
                post_title="Post 3",
                post_url="https://reddit.com/post3",
                subreddit="nvidia",
                timestamp=datetime(2024, 1, 16, 11, 0, 0)
            ),
        ]
        
        daily_scores = analyzer.calculate_daily_sentiment_scores(signals)
        
        # Check both dates are present
        assert date(2024, 1, 15) in daily_scores
        assert date(2024, 1, 16) in daily_scores
        
        # Expected for Jan 15: 1 * 3.0 = 3.0
        assert daily_scores[date(2024, 1, 15)] == 3.0
        
        # Expected for Jan 16: (1 * 2.0) + (1 * 1.0) = 3.0
        assert daily_scores[date(2024, 1, 16)] == 3.0
    
    def test_calculate_daily_sentiment_scores_empty_signals(self, analyzer):
        """Test daily sentiment scores with empty signal list."""
        daily_scores = analyzer.calculate_daily_sentiment_scores([])
        
        assert daily_scores == {}
    
    def test_enrich_signals_with_sentiment(self, analyzer):
        """Test enriching signals with calculated sentiment scores."""
        signals = [
            MarketSignal(
                keyword="New Release",
                post_title="Post 1",
                post_url="https://reddit.com/post1",
                subreddit="nvidia",
                timestamp=datetime(2024, 1, 15, 10, 0, 0),
                sentiment_score=None
            ),
            MarketSignal(
                keyword="Price Drop",
                post_title="Post 2",
                post_url="https://reddit.com/post2",
                subreddit="nvidia",
                timestamp=datetime(2024, 1, 15, 11, 0, 0),
                sentiment_score=None
            ),
        ]
        
        enriched_signals = analyzer.enrich_signals_with_sentiment(signals)
        
        # All signals should have sentiment scores
        assert all(s.sentiment_score is not None for s in enriched_signals)
        
        # All signals from the same day should have the same sentiment score
        expected_score = 5.0  # (1 * 3.0) + (1 * 2.0)
        assert all(s.sentiment_score == expected_score for s in enriched_signals)
    
    def test_enrich_signals_with_sentiment_multiple_days(self, analyzer):
        """Test enriching signals across multiple days with different scores."""
        signals = [
            MarketSignal(
                keyword="New Release",
                post_title="Post 1",
                post_url="https://reddit.com/post1",
                subreddit="nvidia",
                timestamp=datetime(2024, 1, 15, 10, 0, 0),
                sentiment_score=None
            ),
            MarketSignal(
                keyword="Issues",
                post_title="Post 2",
                post_url="https://reddit.com/post2",
                subreddit="nvidia",
                timestamp=datetime(2024, 1, 16, 10, 0, 0),
                sentiment_score=None
            ),
        ]
        
        enriched_signals = analyzer.enrich_signals_with_sentiment(signals)
        
        # Signals from different days should have different scores
        assert enriched_signals[0].sentiment_score == 3.0  # New Release: 1 * 3.0
        assert enriched_signals[1].sentiment_score == 1.0  # Issues: 1 * 1.0
    
    def test_enrich_signals_with_sentiment_empty_list(self, analyzer):
        """Test enriching empty signal list."""
        enriched_signals = analyzer.enrich_signals_with_sentiment([])
        
        assert enriched_signals == []
    
    def test_keyword_weights_initialization(self, analyzer):
        """Test that keyword weights are correctly initialized."""
        assert analyzer.keyword_weights["New Release"] == 3.0
        assert analyzer.keyword_weights["Leak"] == 3.0
        assert analyzer.keyword_weights["5070 release date"] == 3.0
        assert analyzer.keyword_weights["Price Drop"] == 2.0
        assert analyzer.keyword_weights["Issues"] == 1.0
        assert analyzer.keyword_weights["Used Market"] == 1.0
    
    def test_analyze_keyword_frequency_handles_exceptions(self, analyzer):
        """Test that keyword frequency analysis handles malformed signals gracefully."""
        # Create a signal with missing timestamp
        class BadSignal:
            keyword = "New Release"
            post_url = "https://reddit.com/post1"
            timestamp = None  # This will cause an error
        
        signals = [BadSignal()]
        
        # Should not raise exception, just skip the bad signal
        frequency_map = analyzer.analyze_keyword_frequency(signals)
        
        # Should return empty map since the signal was skipped
        assert frequency_map == {}


class TestAnalyzeSentiment:
    """Test the convenience function for sentiment analysis."""
    
    def test_analyze_sentiment_success(self):
        """Test the convenience function for analyzing sentiment."""
        signals = [
            MarketSignal(
                keyword="New Release",
                post_title="Post 1",
                post_url="https://reddit.com/post1",
                subreddit="nvidia",
                timestamp=datetime(2024, 1, 15, 10, 0, 0),
                sentiment_score=None
            ),
        ]
        
        enriched_signals = analyze_sentiment(signals)
        
        assert len(enriched_signals) == 1
        assert enriched_signals[0].sentiment_score == 3.0
    
    def test_analyze_sentiment_empty_list(self):
        """Test convenience function with empty list."""
        enriched_signals = analyze_sentiment([])
        
        assert enriched_signals == []


class TestSentimentAnalyzerIntegration:
    """Integration tests for sentiment analyzer with realistic scenarios."""
    
    def test_realistic_scenario_new_gpu_release(self):
        """Test sentiment analysis for a realistic new GPU release scenario."""
        analyzer = SentimentAnalyzer()
        
        # Simulate a day with high new release mentions
        signals = [
            MarketSignal(
                keyword="New Release",
                post_title="RTX 5070 announced!",
                post_url="https://reddit.com/post1",
                subreddit="nvidia",
                timestamp=datetime(2024, 1, 15, 10, 0, 0)
            ),
            MarketSignal(
                keyword="Leak",
                post_title="Leaked specs for RTX 5070",
                post_url="https://reddit.com/post2",
                subreddit="nvidia",
                timestamp=datetime(2024, 1, 15, 11, 0, 0)
            ),
            MarketSignal(
                keyword="5070 release date",
                post_title="When is the 5070 release date?",
                post_url="https://reddit.com/post3",
                subreddit="pcmasterrace",
                timestamp=datetime(2024, 1, 15, 12, 0, 0)
            ),
            MarketSignal(
                keyword="Price Drop",
                post_title="RTX 4070 prices dropping",
                post_url="https://reddit.com/post4",
                subreddit="nvidia",
                timestamp=datetime(2024, 1, 15, 13, 0, 0)
            ),
        ]
        
        enriched_signals = analyzer.enrich_signals_with_sentiment(signals)
        
        # All signals should have high sentiment score
        # Expected: (1 * 3.0) + (1 * 3.0) + (1 * 3.0) + (1 * 2.0) = 11.0
        assert all(s.sentiment_score == 11.0 for s in enriched_signals)
    
    def test_realistic_scenario_quiet_day(self):
        """Test sentiment analysis for a quiet day with few mentions."""
        analyzer = SentimentAnalyzer()
        
        signals = [
            MarketSignal(
                keyword="Issues",
                post_title="Minor driver issue",
                post_url="https://reddit.com/post1",
                subreddit="nvidia",
                timestamp=datetime(2024, 1, 15, 10, 0, 0)
            ),
        ]
        
        enriched_signals = analyzer.enrich_signals_with_sentiment(signals)
        
        # Low sentiment score for quiet day
        # Expected: 1 * 1.0 = 1.0
        assert enriched_signals[0].sentiment_score == 1.0

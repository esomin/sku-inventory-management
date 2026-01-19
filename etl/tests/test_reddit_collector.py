"""
Unit tests for Reddit RSS feed collector.

These tests verify the collector's ability to extract market signals from Reddit,
filter by keywords, handle rate limits, and parse RSS feeds correctly.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import requests
import time

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from extractors.reddit_collector import RedditCollector, RateLimitError
from models import MarketSignal


class TestRedditCollector:
    """Test suite for RedditCollector."""
    
    @pytest.fixture
    def collector(self):
        """Create a RedditCollector instance for testing."""
        return RedditCollector(max_retries=2, retry_backoff=1)
    
    @pytest.fixture
    def sample_rss_feed(self):
        """Sample RSS feed data structure from feedparser."""
        return {
            'entries': [
                {
                    'title': 'RTX 5070 release date leaked!',
                    'link': 'https://reddit.com/r/nvidia/comments/abc123',
                    'summary': 'New information about the upcoming RTX 5070 release date has been leaked...',
                    'published_parsed': time.struct_time((2024, 1, 15, 10, 30, 0, 0, 15, 0))
                },
                {
                    'title': 'Great Price Drop on RTX 4070 Super',
                    'link': 'https://reddit.com/r/nvidia/comments/def456',
                    'summary': 'Just saw a massive price drop on the RTX 4070 Super at my local store',
                    'published_parsed': time.struct_time((2024, 1, 15, 11, 0, 0, 0, 15, 0))
                },
                {
                    'title': 'My new gaming setup',
                    'link': 'https://reddit.com/r/nvidia/comments/ghi789',
                    'summary': 'Just finished building my new PC with an RTX 4070',
                    'published_parsed': time.struct_time((2024, 1, 15, 12, 0, 0, 0, 15, 0))
                },
                {
                    'title': 'Issues with RTX 4070 Ti drivers',
                    'link': 'https://reddit.com/r/nvidia/comments/jkl012',
                    'summary': 'Anyone else experiencing driver issues with the RTX 4070 Ti?',
                    'published_parsed': time.struct_time((2024, 1, 15, 13, 0, 0, 0, 15, 0))
                }
            ],
            'bozo': False
        }
    
    def test_collect_signals_success(self, collector, sample_rss_feed):
        """Test successful signal collection from multiple subreddits."""
        mock_feed = MagicMock()
        mock_feed.entries = sample_rss_feed['entries']
        mock_feed.bozo = False
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<rss>test</rss>'
        
        with patch('feedparser.parse', return_value=mock_feed):
            with patch.object(collector.session, 'get', return_value=mock_response):
                signals = collector.collect_signals()
                
                # Should collect signals from both subreddits
                assert len(signals) > 0
                assert all(isinstance(s, MarketSignal) for s in signals)
                assert any(s.subreddit == 'nvidia' for s in signals)
                assert any(s.subreddit == 'pcmasterrace' for s in signals)
    
    def test_fetch_rss_feed_success(self, collector, sample_rss_feed):
        """Test successful RSS feed fetching."""
        mock_feed = MagicMock()
        mock_feed.entries = sample_rss_feed['entries']
        mock_feed.bozo = False
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<rss>test</rss>'
        
        with patch('feedparser.parse', return_value=mock_feed):
            with patch.object(collector.session, 'get', return_value=mock_response):
                entries = collector._fetch_rss_feed('nvidia')
                
                assert len(entries) == 4
                assert entries[0]['title'] == 'RTX 5070 release date leaked!'
    
    def test_fetch_rss_feed_rate_limit_with_retry(self, collector, sample_rss_feed):
        """Test rate limit handling with successful retry."""
        mock_feed = MagicMock()
        mock_feed.entries = sample_rss_feed['entries']
        mock_feed.bozo = False
        
        mock_rate_limit_response = Mock()
        mock_rate_limit_response.status_code = 429
        mock_rate_limit_response.headers = {'Retry-After': '2'}
        
        mock_success_response = Mock()
        mock_success_response.status_code = 200
        mock_success_response.content = b'<rss>test</rss>'
        
        with patch('feedparser.parse', return_value=mock_feed):
            with patch.object(collector.session, 'get') as mock_get:
                # First call returns 429, second succeeds
                mock_get.side_effect = [mock_rate_limit_response, mock_success_response]
                
                with patch('time.sleep'):  # Mock sleep to speed up test
                    entries = collector._fetch_rss_feed('nvidia')
                
                assert len(entries) == 4
                assert mock_get.call_count == 2
    
    def test_fetch_rss_feed_rate_limit_exhausted(self, collector):
        """Test that RateLimitError is raised when retries are exhausted."""
        mock_rate_limit_response = Mock()
        mock_rate_limit_response.status_code = 429
        mock_rate_limit_response.headers = {'Retry-After': '60'}
        
        with patch.object(collector.session, 'get', return_value=mock_rate_limit_response):
            with patch('time.sleep'):  # Mock sleep to speed up test
                with pytest.raises(RateLimitError, match="Rate limit exceeded"):
                    collector._fetch_rss_feed('nvidia')
    
    def test_fetch_rss_feed_http_error_4xx(self, collector):
        """Test handling of 4xx HTTP errors."""
        mock_response = Mock()
        mock_response.status_code = 404
        
        with patch.object(collector.session, 'get') as mock_get:
            mock_get.side_effect = requests.exceptions.HTTPError(response=mock_response)
            
            entries = collector._fetch_rss_feed('nvidia')
            
            # Should return empty list on 4xx errors
            assert entries == []
            assert mock_get.call_count == 1  # No retries on 4xx
    
    def test_fetch_rss_feed_timeout_with_retry(self, collector, sample_rss_feed):
        """Test retry logic after timeout."""
        mock_feed = MagicMock()
        mock_feed.entries = sample_rss_feed['entries']
        mock_feed.bozo = False
        
        mock_success_response = Mock()
        mock_success_response.status_code = 200
        mock_success_response.content = b'<rss>test</rss>'
        
        with patch('feedparser.parse', return_value=mock_feed):
            with patch.object(collector.session, 'get') as mock_get:
                # First call times out, second succeeds
                mock_get.side_effect = [
                    requests.exceptions.Timeout("Timeout"),
                    mock_success_response
                ]
                
                with patch('time.sleep'):  # Mock sleep to speed up test
                    entries = collector._fetch_rss_feed('nvidia')
                
                assert len(entries) == 4
                assert mock_get.call_count == 2
    
    def test_fetch_rss_feed_all_retries_fail(self, collector):
        """Test that empty list is returned after all retries fail."""
        with patch.object(collector.session, 'get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Timeout")
            
            with patch('time.sleep'):  # Mock sleep to speed up test
                entries = collector._fetch_rss_feed('nvidia')
            
            assert entries == []
            assert mock_get.call_count == collector.max_retries
    
    def test_filter_by_keywords_matching_posts(self, collector, sample_rss_feed):
        """Test keyword filtering with matching posts."""
        entries = sample_rss_feed['entries']
        
        signals = collector._filter_by_keywords(entries, 'nvidia')
        
        # Should match:
        # - "Leak" and "5070 release date" in first post (2 signals)
        # - "Price Drop" in second post (1 signal)
        # - "Issues" in fourth post (1 signal)
        assert len(signals) == 4
        
        keywords = [s.keyword for s in signals]
        assert "Leak" in keywords
        assert "5070 release date" in keywords
        assert "Price Drop" in keywords
        assert "Issues" in keywords
    
    def test_filter_by_keywords_case_insensitive(self, collector):
        """Test that keyword matching is case-insensitive."""
        entries = [
            {
                'title': 'new release of RTX 5070',
                'link': 'https://reddit.com/test',
                'summary': 'Details about the NEW RELEASE',
                'published_parsed': time.struct_time((2024, 1, 15, 10, 0, 0, 0, 15, 0))
            }
        ]
        
        signals = collector._filter_by_keywords(entries, 'nvidia')
        
        assert len(signals) == 1
        assert signals[0].keyword == "New Release"
    
    def test_filter_by_keywords_no_duplicates_per_post(self, collector):
        """Test that each keyword is counted once per post even if it appears multiple times."""
        entries = [
            {
                'title': 'Price Drop! Huge Price Drop on RTX 4070',
                'link': 'https://reddit.com/test',
                'summary': 'Another price drop mentioned here',
                'published_parsed': time.struct_time((2024, 1, 15, 10, 0, 0, 0, 15, 0))
            }
        ]
        
        signals = collector._filter_by_keywords(entries, 'nvidia')
        
        # Should only create one signal for "Price Drop" even though it appears multiple times
        assert len(signals) == 1
        assert signals[0].keyword == "Price Drop"
    
    def test_filter_by_keywords_multiple_keywords_per_post(self, collector):
        """Test that multiple different keywords in one post create multiple signals."""
        entries = [
            {
                'title': 'New Release has Issues with drivers',
                'link': 'https://reddit.com/test',
                'summary': 'The new release is having some issues',
                'published_parsed': time.struct_time((2024, 1, 15, 10, 0, 0, 0, 15, 0))
            }
        ]
        
        signals = collector._filter_by_keywords(entries, 'nvidia')
        
        # Should create two signals: one for "New Release" and one for "Issues"
        assert len(signals) == 2
        keywords = [s.keyword for s in signals]
        assert "New Release" in keywords
        assert "Issues" in keywords
    
    def test_filter_by_keywords_no_matches(self, collector):
        """Test filtering when no keywords match."""
        entries = [
            {
                'title': 'My gaming setup',
                'link': 'https://reddit.com/test',
                'summary': 'Just built a new PC',
                'published_parsed': time.struct_time((2024, 1, 15, 10, 0, 0, 0, 15, 0))
            }
        ]
        
        signals = collector._filter_by_keywords(entries, 'nvidia')
        
        assert len(signals) == 0
    
    def test_filter_by_keywords_extracts_all_fields(self, collector):
        """Test that all required fields are extracted into MarketSignal."""
        # Create a mock entry object with attributes and get method
        class MockEntry:
            def __init__(self):
                self.title = 'Price Drop on RTX 4070'
                self.link = 'https://reddit.com/r/nvidia/comments/test123'
                self.summary = 'Great price drop today'
                self.published_parsed = time.struct_time((2024, 1, 15, 10, 30, 45, 0, 15, 0))
            
            def get(self, key, default=''):
                return getattr(self, key, default)
        
        entries = [MockEntry()]
        
        signals = collector._filter_by_keywords(entries, 'nvidia')
        
        assert len(signals) == 1
        signal = signals[0]
        
        assert signal.keyword == "Price Drop"
        assert signal.post_title == "Price Drop on RTX 4070"
        assert signal.post_url == "https://reddit.com/r/nvidia/comments/test123"
        assert signal.subreddit == "nvidia"
        assert signal.timestamp == datetime(2024, 1, 15, 10, 30, 45)
        assert signal.sentiment_score is None
    
    def test_filter_by_keywords_handles_missing_fields(self, collector):
        """Test that filtering handles entries with missing fields gracefully."""
        entries = [
            {
                'title': 'Price Drop',
                # Missing link
                'summary': 'Test',
                'published_parsed': time.struct_time((2024, 1, 15, 10, 0, 0, 0, 15, 0))
            }
        ]
        
        signals = collector._filter_by_keywords(entries, 'nvidia')
        
        # Should still create signal with empty URL
        assert len(signals) == 1
        assert signals[0].post_url == ''
    
    def test_parse_timestamp_published_parsed(self, collector):
        """Test timestamp parsing from published_parsed field."""
        # Create a mock entry object with attributes
        class MockEntry:
            def __init__(self):
                self.published_parsed = time.struct_time((2024, 1, 15, 14, 30, 45, 0, 15, 0))
        
        entry = MockEntry()
        
        timestamp = collector._parse_timestamp(entry)
        
        assert timestamp == datetime(2024, 1, 15, 14, 30, 45)
    
    def test_parse_timestamp_updated_parsed(self, collector):
        """Test timestamp parsing from updated_parsed field when published_parsed is missing."""
        # Create a mock entry object with attributes
        class MockEntry:
            def __init__(self):
                self.updated_parsed = time.struct_time((2024, 1, 15, 16, 45, 30, 0, 15, 0))
        
        entry = MockEntry()
        
        timestamp = collector._parse_timestamp(entry)
        
        assert timestamp == datetime(2024, 1, 15, 16, 45, 30)
    
    def test_parse_timestamp_fallback_to_now(self, collector):
        """Test that current time is used when no timestamp is available."""
        entry = {}
        
        before = datetime.now()
        timestamp = collector._parse_timestamp(entry)
        after = datetime.now()
        
        assert before <= timestamp <= after
    
    def test_collect_signals_continues_on_subreddit_error(self, collector, sample_rss_feed):
        """Test that collection continues with remaining subreddits if one fails."""
        mock_feed = MagicMock()
        mock_feed.entries = sample_rss_feed['entries']
        mock_feed.bozo = False
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<rss>test</rss>'
        
        call_count = [0]
        
        def side_effect_func(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Network error")
            return mock_response
        
        with patch('feedparser.parse', return_value=mock_feed):
            with patch.object(collector.session, 'get', side_effect=side_effect_func):
                with patch('time.sleep'):  # Mock sleep to speed up test
                    signals = collector.collect_signals()
                
                # Should still get signals from second subreddit
                assert len(signals) > 0
    
    def test_collect_signals_raises_on_rate_limit(self, collector):
        """Test that RateLimitError is propagated from collect_signals."""
        with patch.object(collector, '_fetch_rss_feed') as mock_fetch:
            mock_fetch.side_effect = RateLimitError("Rate limit exceeded")
            
            with pytest.raises(RateLimitError):
                collector.collect_signals()
    
    def test_close_session(self, collector):
        """Test that session is properly closed."""
        with patch.object(collector.session, 'close') as mock_close:
            collector.close()
            mock_close.assert_called_once()
    
    def test_rss_feed_url_format(self, collector):
        """Test that RSS feed URL is correctly formatted."""
        expected_url = "https://www.reddit.com/r/nvidia/.rss"
        actual_url = collector.RSS_BASE_URL.format(subreddit='nvidia')
        
        assert actual_url == expected_url
    
    def test_keywords_list(self, collector):
        """Test that all required keywords are present."""
        expected_keywords = [
            "New Release",
            "Leak",
            "Issues",
            "Price Drop",
            "Used Market",
            "5070 release date"
        ]
        
        assert collector.KEYWORDS == expected_keywords
    
    def test_subreddits_list(self, collector):
        """Test that all required subreddits are configured."""
        expected_subreddits = ["nvidia", "pcmasterrace"]
        
        assert collector.SUBREDDITS == expected_subreddits


class TestCollectAllSignals:
    """Test the convenience function for collecting all signals."""
    
    def test_collect_all_signals_success(self):
        """Test collecting signals from all subreddits."""
        from extractors.reddit_collector import collect_all_signals, RedditCollector
        
        mock_signals = [
            MarketSignal(
                keyword="Price Drop",
                post_title="Test Post",
                post_url="https://reddit.com/test",
                subreddit="nvidia",
                timestamp=datetime.now()
            )
        ]
        
        with patch.object(RedditCollector, 'collect_signals', return_value=mock_signals):
            with patch.object(RedditCollector, 'close'):
                signals = collect_all_signals()
                
                assert len(signals) == 1
                assert signals[0].keyword == "Price Drop"
    
    def test_collect_all_signals_closes_collector(self):
        """Test that collector is properly closed even if collection fails."""
        from extractors.reddit_collector import collect_all_signals, RedditCollector
        
        with patch.object(RedditCollector, 'collect_signals', side_effect=Exception("Error")):
            with patch.object(RedditCollector, 'close') as mock_close:
                with pytest.raises(Exception):
                    collect_all_signals()
                
                # Should still close the collector
                mock_close.assert_called_once()

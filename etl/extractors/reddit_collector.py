"""
Reddit RSS Feed Collector for GPU Market Signals.

This module extracts community signals from Reddit RSS feeds,
filtering posts by keywords related to GPU market trends.
"""

import logging
import time
from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin

import feedparser
import requests

from models import MarketSignal

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Raised when Reddit API rate limit is exceeded."""
    pass


class RedditCollector:
    """
    Collector for extracting GPU-related market signals from Reddit RSS feeds.
    
    This collector monitors specific subreddits for posts containing keywords
    that indicate market trends, new releases, or price changes.
    """
    
    KEYWORDS = [
        "New Release",
        "Leak",
        "Issues",
        "Price Drop",
        "Used Market",
        "5070 release date"
    ]
    
    SUBREDDITS = ["nvidia", "pcmasterrace"]
    
    RSS_BASE_URL = "https://www.reddit.com/r/{subreddit}/.rss"
    
    HEADERS = {
        "User-Agent": "GPU-Price-Monitor-ETL/1.0 (Educational Project)",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }
    
    def __init__(self, max_retries: int = 3, retry_backoff: int = 5):
        """
        Initialize the Reddit collector.
        
        Args:
            max_retries: Maximum number of retry attempts for failed requests
            retry_backoff: Initial backoff time in seconds for retries
        """
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def collect_signals(self) -> List[MarketSignal]:
        """
        Collect Reddit posts matching target keywords.
        
        Returns:
            List of MarketSignal objects with keyword, title, timestamp
        
        Raises:
            RateLimitError: If Reddit API rate limit is exceeded
        """
        logger.info("Starting Reddit signal collection")
        
        all_signals = []
        
        for subreddit in self.SUBREDDITS:
            try:
                logger.info(f"Collecting signals from r/{subreddit}")
                
                # Fetch RSS feed
                entries = self._fetch_rss_feed(subreddit)
                
                if not entries:
                    logger.warning(f"No entries found in r/{subreddit} RSS feed")
                    continue
                
                logger.info(f"Found {len(entries)} entries in r/{subreddit}")
                
                # Filter by keywords
                signals = self._filter_by_keywords(entries, subreddit)
                
                logger.info(f"Extracted {len(signals)} signals from r/{subreddit}")
                all_signals.extend(signals)
                
                # Be respectful with rate limiting - add delay between subreddits
                if subreddit != self.SUBREDDITS[-1]:
                    time.sleep(2)
                
            except RateLimitError as e:
                logger.error(f"Rate limit exceeded for r/{subreddit}: {e}")
                raise
            except Exception as e:
                logger.error(f"Failed to collect signals from r/{subreddit}: {e}")
                # Continue with remaining subreddits
                continue
        
        logger.info(f"Total signals collected: {len(all_signals)}")
        return all_signals
    
    def _fetch_rss_feed(self, subreddit: str) -> List:
        """
        Fetch RSS feed for a subreddit.
        
        Args:
            subreddit: Name of the subreddit (without r/ prefix)
        
        Returns:
            List of RSS feed entries
        
        Raises:
            RateLimitError: If rate limit is exceeded
        """
        url = self.RSS_BASE_URL.format(subreddit=subreddit)
        
        logger.debug(f"Fetching RSS feed from: {url}")
        
        retries = 0
        last_error = None
        
        while retries < self.max_retries:
            try:
                # Fetch RSS feed with timeout
                response = self.session.get(url, timeout=30)
                
                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After', '60')
                    try:
                        wait_time = int(retry_after)
                    except ValueError:
                        wait_time = 60
                    
                    logger.warning(f"Rate limit hit. Retry-After: {wait_time} seconds")
                    
                    if retries < self.max_retries - 1:
                        logger.info(f"Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                        retries += 1
                        continue
                    else:
                        raise RateLimitError(f"Rate limit exceeded for r/{subreddit}. Retry after {wait_time} seconds")
                
                response.raise_for_status()
                
                # Parse RSS feed
                feed = feedparser.parse(response.content)
                
                if feed.bozo:
                    # Feed has parsing errors
                    logger.warning(f"RSS feed parsing warning for r/{subreddit}: {feed.bozo_exception}")
                
                entries = feed.entries if hasattr(feed, 'entries') else []
                
                logger.debug(f"Successfully fetched {len(entries)} entries from r/{subreddit}")
                return entries
                
            except requests.exceptions.Timeout as e:
                last_error = e
                retries += 1
                logger.warning(f"Request timeout for r/{subreddit}: {e}")
                
            except requests.exceptions.HTTPError as e:
                last_error = e
                status_code = e.response.status_code if e.response else 'unknown'
                logger.error(f"HTTP error {status_code} for r/{subreddit}: {e}")
                
                # Don't retry on 4xx errors (except 429 which is handled above)
                if e.response and 400 <= e.response.status_code < 500:
                    logger.error(f"Client error for r/{subreddit}, skipping")
                    return []
                
                retries += 1
                
            except requests.exceptions.RequestException as e:
                last_error = e
                retries += 1
                logger.warning(f"Request failed for r/{subreddit}: {e}")
            
            # Exponential backoff
            if retries < self.max_retries:
                backoff_time = self.retry_backoff * (2 ** (retries - 1))
                logger.info(f"Retrying in {backoff_time} seconds...")
                time.sleep(backoff_time)
        
        logger.error(f"Failed to fetch RSS feed for r/{subreddit} after {self.max_retries} attempts: {last_error}")
        return []
    
    def _filter_by_keywords(self, entries: List, subreddit: str) -> List[MarketSignal]:
        """
        Filter entries by keyword presence in title or body.
        
        Args:
            entries: List of RSS feed entries
            subreddit: Name of the subreddit
        
        Returns:
            List of MarketSignal objects for matching posts
        """
        signals = []
        
        for entry in entries:
            try:
                # Extract post data
                post_title = entry.get('title', '')
                post_url = entry.get('link', '')
                
                # Get post content (summary or content)
                post_content = ''
                if hasattr(entry, 'summary'):
                    post_content = entry.summary
                elif hasattr(entry, 'content') and entry.content:
                    post_content = entry.content[0].value if isinstance(entry.content, list) else entry.content
                
                # Combine title and content for keyword matching
                full_text = f"{post_title} {post_content}".lower()
                
                # Extract timestamp
                timestamp = self._parse_timestamp(entry)
                
                # Check for keyword matches (case-insensitive)
                matched_keywords = []
                for keyword in self.KEYWORDS:
                    if keyword.lower() in full_text:
                        matched_keywords.append(keyword)
                
                # Create a MarketSignal for each matched keyword
                # Count each keyword once per post (no duplicates)
                for keyword in matched_keywords:
                    signal = MarketSignal(
                        keyword=keyword,
                        post_title=post_title,
                        post_url=post_url,
                        subreddit=subreddit,
                        timestamp=timestamp,
                        sentiment_score=None  # Will be calculated later
                    )
                    signals.append(signal)
                    
                    logger.debug(f"Matched keyword '{keyword}' in post: {post_title[:50]}...")
                
            except Exception as e:
                logger.warning(f"Failed to process entry: {e}")
                # Continue with remaining entries
                continue
        
        return signals
    
    def _parse_timestamp(self, entry) -> datetime:
        """
        Parse timestamp from RSS entry.
        
        Args:
            entry: RSS feed entry
        
        Returns:
            Datetime object, or current time if parsing fails
        """
        try:
            # Try to parse published_parsed or updated_parsed
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                return datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                return datetime(*entry.updated_parsed[:6])
            else:
                logger.warning("No timestamp found in entry, using current time")
                return datetime.now()
        except Exception as e:
            logger.warning(f"Failed to parse timestamp: {e}, using current time")
            return datetime.now()
    
    def close(self):
        """Close the HTTP session."""
        self.session.close()
        logger.debug("Reddit collector session closed")


def collect_all_signals() -> List[MarketSignal]:
    """
    Convenience function to collect signals from all configured subreddits.
    
    Returns:
        List of MarketSignal objects from all subreddits
    """
    collector = RedditCollector()
    
    try:
        signals = collector.collect_signals()
        return signals
    finally:
        collector.close()

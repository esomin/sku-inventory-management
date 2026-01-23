"""
Sentiment Analyzer for GPU Market Signals.

This module analyzes community signals from Reddit to calculate
sentiment scores based on keyword frequency and weighted importance.
"""

import logging
from collections import defaultdict
from datetime import date, datetime
from typing import Dict, List

from models import MarketSignal
from config import settings

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Analyzer for calculating sentiment scores from Reddit market signals.
    
    This analyzer counts keyword mentions per day and calculates weighted
    sentiment scores based on keyword importance.
    """
    
    def __init__(self):
        """Initialize the sentiment analyzer."""
        self.keyword_weights = {
            "New Release": settings.sentiment_weight_new_release,
            "Leak": settings.sentiment_weight_new_release,  # Same weight as New Release
            "Price Drop": settings.sentiment_weight_price_drop,
            "Issues": settings.sentiment_weight_default,
            "Used Market": settings.sentiment_weight_default,
            "5070 release date": settings.sentiment_weight_new_release,
        }
    
    def analyze_keyword_frequency(self, signals: List[MarketSignal]) -> Dict[str, Dict[date, int]]:
        """
        Count keyword mentions per day, preventing duplicate counts from the same post.
        
        This method aggregates keyword mentions by date, ensuring that each keyword
        is counted at most once per post, even if it appears multiple times.
        
        Args:
            signals: List of MarketSignal objects from Reddit
        
        Returns:
            Dictionary mapping keyword to date to mention count
            Format: {keyword: {date: count}}
        
        Example:
            >>> signals = [
            ...     MarketSignal(keyword="New Release", post_url="url1", timestamp=datetime(2024, 1, 1)),
            ...     MarketSignal(keyword="New Release", post_url="url2", timestamp=datetime(2024, 1, 1)),
            ...     MarketSignal(keyword="Price Drop", post_url="url1", timestamp=datetime(2024, 1, 1)),
            ... ]
            >>> analyzer = SentimentAnalyzer()
            >>> result = analyzer.analyze_keyword_frequency(signals)
            >>> result["New Release"][date(2024, 1, 1)]
            2
            >>> result["Price Drop"][date(2024, 1, 1)]
            1
        """
        logger.info(f"Analyzing keyword frequency for {len(signals)} signals")
        
        # Track unique (keyword, date, post_url) combinations to prevent duplicates
        # This ensures each keyword is counted once per post per day
        unique_mentions = set()
        
        # Build frequency map: keyword -> date -> count
        frequency_map: Dict[str, Dict[date, int]] = defaultdict(lambda: defaultdict(int))
        
        for signal in signals:
            try:
                # Extract date from timestamp
                signal_date = signal.timestamp.date()
                
                # Create unique key to prevent duplicate counting
                mention_key = (signal.keyword, signal_date, signal.post_url)
                
                # Only count if we haven't seen this exact combination before
                if mention_key not in unique_mentions:
                    unique_mentions.add(mention_key)
                    frequency_map[signal.keyword][signal_date] += 1
                    
                    logger.debug(
                        f"Counted keyword '{signal.keyword}' on {signal_date} "
                        f"from post: {signal.post_title[:50]}..."
                    )
                else:
                    logger.debug(
                        f"Skipped duplicate keyword '{signal.keyword}' on {signal_date} "
                        f"from same post URL"
                    )
                    
            except Exception as e:
                logger.warning(f"Failed to process signal: {e}")
                continue
        
        # Convert defaultdict to regular dict for cleaner output
        result = {
            keyword: dict(date_counts)
            for keyword, date_counts in frequency_map.items()
        }
        
        # Log summary
        total_mentions = sum(
            sum(date_counts.values())
            for date_counts in result.values()
        )
        logger.info(
            f"Keyword frequency analysis complete: "
            f"{len(result)} unique keywords, {total_mentions} total mentions"
        )
        
        return result
    
    def calculate_sentiment_score(self, keyword_counts: Dict[str, int]) -> float:
        """
        Calculate weighted sentiment score from keyword mention counts.
        
        The sentiment score is calculated as the sum of (mention_count × weight)
        for each keyword, where weights are:
        - "New Release", "Leak", "5070 release date": 3.0
        - "Price Drop": 2.0
        - Others: 1.0
        
        Args:
            keyword_counts: Dictionary mapping keyword to mention count
        
        Returns:
            Weighted sentiment score
        
        Example:
            >>> analyzer = SentimentAnalyzer()
            >>> counts = {"New Release": 5, "Price Drop": 3, "Issues": 2}
            >>> score = analyzer.calculate_sentiment_score(counts)
            >>> score
            23.0  # (5 * 3.0) + (3 * 2.0) + (2 * 1.0)
        """
        logger.debug(f"Calculating sentiment score for {len(keyword_counts)} keywords")
        
        sentiment_score = 0.0
        
        for keyword, count in keyword_counts.items():
            # Get weight for this keyword (default to 1.0 if not found)
            weight = self.keyword_weights.get(keyword, settings.sentiment_weight_default)
            
            # Calculate weighted contribution
            contribution = count * weight
            sentiment_score += contribution
            
            logger.debug(
                f"Keyword '{keyword}': count={count}, weight={weight}, "
                f"contribution={contribution}"
            )
        
        logger.info(f"Calculated sentiment score: {sentiment_score}")
        
        return sentiment_score
    
    def calculate_daily_sentiment_scores(
        self,
        signals: List[MarketSignal]
    ) -> Dict[date, float]:
        """
        Calculate sentiment scores for each day based on keyword frequencies.
        
        This method combines keyword frequency analysis with weighted scoring
        to produce a daily sentiment score.
        
        Args:
            signals: List of MarketSignal objects from Reddit
        
        Returns:
            Dictionary mapping date to sentiment score
        
        Example:
            >>> signals = [
            ...     MarketSignal(keyword="New Release", post_url="url1", timestamp=datetime(2024, 1, 1)),
            ...     MarketSignal(keyword="Price Drop", post_url="url2", timestamp=datetime(2024, 1, 1)),
            ... ]
            >>> analyzer = SentimentAnalyzer()
            >>> scores = analyzer.calculate_daily_sentiment_scores(signals)
            >>> scores[date(2024, 1, 1)]
            5.0  # (1 * 3.0) + (1 * 2.0)
        """
        logger.info(f"Calculating daily sentiment scores for {len(signals)} signals")
        
        # Get keyword frequency by date
        frequency_map = self.analyze_keyword_frequency(signals)
        
        # Calculate sentiment score for each date
        daily_scores: Dict[date, float] = {}
        
        # Collect all unique dates
        all_dates = set()
        for date_counts in frequency_map.values():
            all_dates.update(date_counts.keys())
        
        # Calculate score for each date
        for target_date in all_dates:
            # Build keyword counts for this specific date
            keyword_counts_for_date = {}
            for keyword, date_counts in frequency_map.items():
                if target_date in date_counts:
                    keyword_counts_for_date[keyword] = date_counts[target_date]
            
            # Calculate sentiment score for this date
            score = self.calculate_sentiment_score(keyword_counts_for_date)
            daily_scores[target_date] = score
            
            logger.debug(f"Date {target_date}: sentiment score = {score}")
        
        logger.info(f"Calculated sentiment scores for {len(daily_scores)} days")
        
        return daily_scores
    
    def enrich_signals_with_sentiment(
        self,
        signals: List[MarketSignal]
    ) -> List[MarketSignal]:
        """
        Enrich market signals with calculated sentiment scores.
        
        This method calculates daily sentiment scores and assigns them
        to each signal based on its date.
        
        Args:
            signals: List of MarketSignal objects from Reddit
        
        Returns:
            List of MarketSignal objects with sentiment_score populated
        """
        logger.info(f"Enriching {len(signals)} signals with sentiment scores")
        
        # Calculate daily sentiment scores
        daily_scores = self.calculate_daily_sentiment_scores(signals)
        
        # Enrich each signal with its corresponding daily score
        enriched_signals = []
        for signal in signals:
            signal_date = signal.timestamp.date()
            signal.sentiment_score = daily_scores.get(signal_date, 0.0)
            enriched_signals.append(signal)
        
        logger.info("Signal enrichment complete")
        
        return enriched_signals


def analyze_sentiment(signals: List[MarketSignal]) -> List[MarketSignal]:
    """
    Convenience function to analyze sentiment and enrich signals.
    
    Args:
        signals: List of MarketSignal objects from Reddit
    
    Returns:
        List of MarketSignal objects with sentiment scores
    """
    analyzer = SentimentAnalyzer()
    return analyzer.enrich_signals_with_sentiment(signals)

"""
Risk Calculator for GPU Inventory Management.

This module calculates inventory risk indices by combining price trends
and community sentiment signals to identify products at risk of value depreciation.
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, Optional, Tuple

from db_connection import db_manager
from config import settings
from transformers.price_analyzer import PriceAnalyzer, InsufficientDataError

logger = logging.getLogger(__name__)


class RiskCalculator:
    """
    Calculator for inventory risk indices based on price trends and sentiment.
    
    The risk index combines:
    1. Price change (current price - last week average price)
    2. New release sentiment (new release mentions × 0.3)
    
    A higher risk index indicates greater risk of inventory value depreciation.
    
    Validates: Requirements 7.1, 7.2, 7.3, 7.4
    """
    
    def __init__(self):
        """Initialize the risk calculator."""
        self.db = db_manager
        self.price_analyzer = PriceAnalyzer()
        self.threshold = settings.risk_threshold
    
    def calculate_risk_index(
        self,
        sku_id: int,
        current_price: float,
        new_release_mentions: int = 0
    ) -> float:
        """
        Calculate risk index using the formula:
        risk_index = (current_price - last_week_avg_price) + (new_release_mentions × 0.3)
        
        A negative risk index indicates the product is losing value (price dropping),
        which combined with high new release mentions suggests inventory should be cleared.
        
        Args:
            sku_id: Product identifier
            current_price: Current price in KRW
            new_release_mentions: Number of new release mentions in recent period
        
        Returns:
            Risk index value (more negative = higher risk)
        
        Raises:
            ValueError: If current_price is negative or zero
            InsufficientDataError: If less than 7 days of historical data
        
        Validates: Requirements 7.1, 7.2
        """
        # Validate input
        if current_price <= 0:
            raise ValueError(f"Invalid price: {current_price}. Price must be positive.")
        
        if new_release_mentions < 0:
            raise ValueError(
                f"Invalid new_release_mentions: {new_release_mentions}. "
                f"Must be non-negative."
            )
        
        try:
            # Get historical average price from 7 days ago
            historical_prices = self.price_analyzer._get_historical_prices(
                sku_id,
                days_ago=7,
                window_days=1
            )
            
            if not historical_prices:
                logger.warning(
                    f"Insufficient historical data for SKU {sku_id}. "
                    f"Cannot calculate risk index."
                )
                raise InsufficientDataError(
                    f"Insufficient historical data for SKU {sku_id}. "
                    f"Need at least 7 days of price history."
                )
            
            # Calculate average price from 7 days ago
            last_week_avg_price = sum(historical_prices) / len(historical_prices)
            
            # Calculate price delta (negative = price drop)
            price_delta = current_price - last_week_avg_price
            
            # Calculate sentiment impact (new release mentions weighted by 0.3)
            sentiment_impact = new_release_mentions * 0.3
            
            # Calculate risk index
            # Note: A negative price_delta (price drop) combined with high sentiment_impact
            # (many new release mentions) results in a more negative risk index,
            # indicating higher risk
            risk_index = price_delta + sentiment_impact
            
            logger.info(
                f"SKU {sku_id} Risk Calculation: "
                f"current_price={current_price:.2f}, "
                f"last_week_avg={last_week_avg_price:.2f}, "
                f"price_delta={price_delta:.2f}, "
                f"new_release_mentions={new_release_mentions}, "
                f"sentiment_impact={sentiment_impact:.2f}, "
                f"risk_index={risk_index:.2f}"
            )
            
            return round(risk_index, 2)
            
        except InsufficientDataError:
            # Re-raise to caller
            raise
        except Exception as e:
            logger.error(f"Error calculating risk index for SKU {sku_id}: {e}")
            raise
    
    def check_threshold(self, risk_index: float) -> bool:
        """
        Check if risk index exceeds the configured threshold.
        
        The threshold is typically set to a negative value (e.g., -100.0).
        A risk index below this threshold indicates high risk.
        
        Args:
            risk_index: Calculated risk index value
        
        Returns:
            True if risk index indicates high risk (exceeds threshold), False otherwise
        
        Validates: Requirements 7.3
        """
        # Risk is high if the index is below the threshold (more negative)
        # For example, if threshold is -100 and risk_index is -150, that's high risk
        is_high_risk = risk_index < self.threshold
        
        if is_high_risk:
            logger.warning(
                f"High risk detected: risk_index={risk_index:.2f} < "
                f"threshold={self.threshold:.2f}"
            )
        else:
            logger.debug(
                f"Risk within acceptable range: risk_index={risk_index:.2f} >= "
                f"threshold={self.threshold:.2f}"
            )
        
        return is_high_risk
    
    def calculate_risk_with_sentiment(
        self,
        sku_id: int,
        current_price: float,
        sentiment_data: Dict[str, int]
    ) -> Tuple[float, bool]:
        """
        Calculate risk index using sentiment data from multiple keywords.
        
        This method extracts new release mentions from sentiment data and
        calculates the risk index, then checks if it exceeds the threshold.
        
        Args:
            sku_id: Product identifier
            current_price: Current price in KRW
            sentiment_data: Dictionary mapping keyword to mention count
        
        Returns:
            Tuple of (risk_index, is_high_risk)
        
        Example:
            >>> calculator = RiskCalculator()
            >>> sentiment = {"New Release": 10, "Price Drop": 5, "Issues": 2}
            >>> risk_index, is_high_risk = calculator.calculate_risk_with_sentiment(
            ...     sku_id=1,
            ...     current_price=500000,
            ...     sentiment_data=sentiment
            ... )
        """
        # Extract new release mentions from sentiment data
        new_release_mentions = 0
        for keyword, count in sentiment_data.items():
            keyword_lower = keyword.lower()
            if any(term in keyword_lower for term in ["new release", "leak", "5070"]):
                new_release_mentions += count
        
        logger.debug(
            f"Extracted {new_release_mentions} new release mentions from sentiment data"
        )
        
        # Calculate risk index
        risk_index = self.calculate_risk_index(
            sku_id=sku_id,
            current_price=current_price,
            new_release_mentions=new_release_mentions
        )
        
        # Check threshold
        is_high_risk = self.check_threshold(risk_index)
        
        return risk_index, is_high_risk
    
    def get_new_release_mentions(self, days: int = 7) -> Dict[str, int]:
        """
        Query database for new release keyword mentions over a specified period.
        
        This method aggregates mentions of keywords related to new releases
        (e.g., "New Release", "Leak", "5070 release date") from the market_signals table.
        
        Args:
            days: Number of days to look back (default: 7)
        
        Returns:
            Dictionary mapping keyword to total mention count
        """
        start_date = datetime.now() - timedelta(days=days)
        
        query = """
            SELECT keyword, SUM(mention_count) as total_mentions
            FROM market_signals
            WHERE date >= %s
              AND (
                  LOWER(keyword) LIKE '%new release%'
                  OR LOWER(keyword) LIKE '%leak%'
                  OR LOWER(keyword) LIKE '%5070%'
              )
            GROUP BY keyword
        """
        
        try:
            results = self.db.execute_with_retry(
                query,
                (start_date.date(),),
                fetch=True
            )
            
            mentions = {row[0]: int(row[1]) for row in results}
            
            logger.info(
                f"Retrieved new release mentions for last {days} days: "
                f"{sum(mentions.values())} total mentions across {len(mentions)} keywords"
            )
            
            return mentions
            
        except Exception as e:
            logger.error(f"Error querying new release mentions: {e}")
            raise
    
    def calculate_risk_for_all_skus(
        self,
        days: int = 7
    ) -> Dict[int, Tuple[float, bool]]:
        """
        Calculate risk indices for all SKUs with recent price data.
        
        This method is useful for batch processing and generating risk alerts
        for all products in the inventory.
        
        Args:
            days: Number of days to consider for sentiment data (default: 7)
        
        Returns:
            Dictionary mapping sku_id to (risk_index, is_high_risk) tuple
        """
        logger.info("Calculating risk indices for all SKUs")
        
        # Get new release mentions
        new_release_mentions = self.get_new_release_mentions(days=days)
        total_mentions = sum(new_release_mentions.values())
        
        # Get all SKUs with recent price data
        query = """
            SELECT DISTINCT pl.sku_id, pl.price
            FROM price_logs pl
            INNER JOIN (
                SELECT sku_id, MAX(recorded_at) as latest_date
                FROM price_logs
                GROUP BY sku_id
            ) latest ON pl.sku_id = latest.sku_id AND pl.recorded_at = latest.latest_date
            WHERE pl.recorded_at >= %s
        """
        
        start_date = datetime.now() - timedelta(days=1)  # Last 24 hours
        
        try:
            results = self.db.execute_with_retry(
                query,
                (start_date,),
                fetch=True
            )
            
            risk_results = {}
            
            for row in results:
                sku_id = int(row[0])
                current_price = float(row[1])
                
                try:
                    # Calculate risk index for this SKU
                    risk_index = self.calculate_risk_index(
                        sku_id=sku_id,
                        current_price=current_price,
                        new_release_mentions=total_mentions
                    )
                    
                    # Check threshold
                    is_high_risk = self.check_threshold(risk_index)
                    
                    risk_results[sku_id] = (risk_index, is_high_risk)
                    
                except InsufficientDataError:
                    logger.warning(
                        f"Skipping SKU {sku_id}: insufficient historical data"
                    )
                    continue
                except Exception as e:
                    logger.error(f"Error calculating risk for SKU {sku_id}: {e}")
                    continue
            
            logger.info(
                f"Calculated risk indices for {len(risk_results)} SKUs. "
                f"High risk: {sum(1 for _, is_high in risk_results.values() if is_high)}"
            )
            
            return risk_results
            
        except Exception as e:
            logger.error(f"Error calculating risk for all SKUs: {e}")
            raise
    
    def get_contributing_factors(
        self,
        sku_id: int,
        current_price: float,
        new_release_mentions: int
    ) -> dict:
        """
        Get detailed contributing factors for a risk calculation.
        
        This method provides transparency into what factors contributed to
        the risk index, useful for generating detailed alert messages.
        
        Args:
            sku_id: Product identifier
            current_price: Current price in KRW
            new_release_mentions: Number of new release mentions
        
        Returns:
            Dictionary with detailed factor breakdown
        """
        try:
            # Get historical prices
            historical_prices = self.price_analyzer._get_historical_prices(
                sku_id,
                days_ago=7,
                window_days=1
            )
            
            if not historical_prices:
                return {
                    "error": "Insufficient historical data",
                    "current_price": current_price,
                    "new_release_mentions": new_release_mentions
                }
            
            last_week_avg_price = sum(historical_prices) / len(historical_prices)
            price_delta = current_price - last_week_avg_price
            price_change_pct = (price_delta / last_week_avg_price) * 100
            sentiment_impact = new_release_mentions * 0.3
            
            return {
                "current_price": round(current_price, 2),
                "last_week_avg_price": round(last_week_avg_price, 2),
                "price_delta": round(price_delta, 2),
                "price_change_pct": round(price_change_pct, 2),
                "new_release_mentions": new_release_mentions,
                "sentiment_impact": round(sentiment_impact, 2),
                "threshold": self.threshold
            }
            
        except Exception as e:
            logger.error(f"Error getting contributing factors for SKU {sku_id}: {e}")
            return {
                "error": str(e),
                "current_price": current_price,
                "new_release_mentions": new_release_mentions
            }

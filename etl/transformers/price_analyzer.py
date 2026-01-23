"""
Price analysis module for calculating price change percentages.

This module calculates week-over-week price changes by comparing current prices
with historical averages from 7 days ago.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from db_connection import db_manager
from config import settings

logger = logging.getLogger(__name__)


class InsufficientDataError(Exception):
    """Raised when there is insufficient historical data for price analysis."""
    pass


class PriceAnalyzer:
    """
    Analyzes GPU price trends and calculates price change percentages.
    
    This class implements the price change calculation logic as specified in
    Requirements 5.1, 5.2, 5.3, 5.4.
    """
    
    def __init__(self):
        """Initialize the price analyzer."""
        self.db = db_manager
    
    def calculate_price_change(self, sku_id: int, current_price: float) -> Optional[float]:
        """
        Calculate week-over-week price change percentage.
        
        Compares the current price with the average price from 7 days ago
        (using a 6-8 day window for robustness).
        
        Formula: ((current_price - avg_price_7_days_ago) / avg_price_7_days_ago) × 100
        
        Args:
            sku_id: Product identifier
            current_price: Current price in KRW
        
        Returns:
            Price change percentage (negative = price drop, positive = price increase)
            Returns None if insufficient historical data
        
        Raises:
            InsufficientDataError: If less than 7 days of historical data exists
            ValueError: If current_price is negative or zero
        
        Validates: Requirements 5.1, 5.2, 5.3, 5.4
        """
        # Validate input
        if current_price <= 0:
            raise ValueError(f"Invalid price: {current_price}. Price must be positive.")
        
        # Get historical prices from 6-8 days ago
        try:
            historical_prices = self._get_historical_prices(sku_id, days_ago=7, window_days=1)
            
            if not historical_prices:
                logger.warning(
                    f"Insufficient historical data for SKU {sku_id}. "
                    f"Need at least 7 days of price history."
                )
                raise InsufficientDataError(
                    f"Insufficient historical data for SKU {sku_id}. "
                    f"Need at least 7 days of price history."
                )
            
            # Calculate average price from 7 days ago
            avg_price_7_days_ago = sum(historical_prices) / len(historical_prices)
            
            # Avoid division by zero
            if avg_price_7_days_ago == 0:
                logger.error(
                    f"Historical average price is zero for SKU {sku_id}. "
                    f"Cannot calculate price change."
                )
                raise ValueError(f"Historical average price is zero for SKU {sku_id}")
            
            # Calculate percentage change
            price_change_pct = (
                (current_price - avg_price_7_days_ago) / avg_price_7_days_ago
            ) * 100
            
            logger.info(
                f"SKU {sku_id}: Current price {current_price:.2f} KRW, "
                f"7-day avg {avg_price_7_days_ago:.2f} KRW, "
                f"Change: {price_change_pct:+.2f}%"
            )
            
            return round(price_change_pct, 2)
            
        except InsufficientDataError:
            # Re-raise to caller
            raise
        except Exception as e:
            logger.error(f"Error calculating price change for SKU {sku_id}: {e}")
            raise
    
    def _get_historical_prices(
        self,
        sku_id: int,
        days_ago: int = 7,
        window_days: int = 1
    ) -> list[float]:
        """
        Query historical prices from the database.
        
        Retrieves prices from a time window around the specified number of days ago.
        For example, with days_ago=7 and window_days=1, retrieves prices from 6-8 days ago.
        
        Args:
            sku_id: Product identifier
            days_ago: Number of days in the past to query (default: 7)
            window_days: Size of the time window in days (default: 1)
        
        Returns:
            List of price values from the historical window
        """
        # Calculate date range
        target_date = datetime.now() - timedelta(days=days_ago)
        start_date = target_date - timedelta(days=window_days)
        end_date = target_date + timedelta(days=window_days)
        
        query = """
            SELECT price
            FROM price_logs
            WHERE sku_id = %s
              AND recorded_at >= %s
              AND recorded_at <= %s
            ORDER BY recorded_at DESC
        """
        
        try:
            results = self.db.execute_with_retry(
                query,
                (sku_id, start_date, end_date),
                fetch=True
            )
            
            prices = [float(row[0]) for row in results]
            
            logger.debug(
                f"Retrieved {len(prices)} historical prices for SKU {sku_id} "
                f"from {start_date.date()} to {end_date.date()}"
            )
            
            return prices
            
        except Exception as e:
            logger.error(f"Error querying historical prices for SKU {sku_id}: {e}")
            raise
    
    def get_price_history(
        self,
        sku_id: int,
        days: int = 90
    ) -> list[tuple[datetime, float]]:
        """
        Get price history for a product over a specified period.
        
        This is a utility method for retrieving complete price history,
        useful for charting and analysis.
        
        Args:
            sku_id: Product identifier
            days: Number of days of history to retrieve (default: 90)
        
        Returns:
            List of (timestamp, price) tuples ordered by date descending
        """
        start_date = datetime.now() - timedelta(days=days)
        
        query = """
            SELECT recorded_at, price
            FROM price_logs
            WHERE sku_id = %s
              AND recorded_at >= %s
            ORDER BY recorded_at DESC
        """
        
        try:
            results = self.db.execute_with_retry(
                query,
                (sku_id, start_date),
                fetch=True
            )
            
            history = [(row[0], float(row[1])) for row in results]
            
            logger.debug(
                f"Retrieved {len(history)} price records for SKU {sku_id} "
                f"over last {days} days"
            )
            
            return history
            
        except Exception as e:
            logger.error(f"Error querying price history for SKU {sku_id}: {e}")
            raise
    
    def has_sufficient_data(self, sku_id: int, required_days: int = 7) -> bool:
        """
        Check if a product has sufficient historical data for analysis.
        
        Args:
            sku_id: Product identifier
            required_days: Minimum number of days of data required (default: 7)
        
        Returns:
            True if sufficient data exists, False otherwise
        """
        query = """
            SELECT MIN(recorded_at) as earliest_date
            FROM price_logs
            WHERE sku_id = %s
        """
        
        try:
            results = self.db.execute_with_retry(
                query,
                (sku_id,),
                fetch=True
            )
            
            if not results or results[0][0] is None:
                return False
            
            earliest_date = results[0][0]
            days_of_data = (datetime.now() - earliest_date).days
            
            return days_of_data >= required_days
            
        except Exception as e:
            logger.error(f"Error checking data sufficiency for SKU {sku_id}: {e}")
            return False

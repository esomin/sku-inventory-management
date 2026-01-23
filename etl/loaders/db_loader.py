"""
Database loader module for the ETL pipeline.

This module provides functions to load normalized data into PostgreSQL tables
with upsert logic to handle duplicates and maintain data integrity.
"""

import logging
import json
from datetime import datetime
from typing import Optional, List, Dict

from db_connection import db_manager
from models import NormalizedProduct, PriceData, MarketSignal

logger = logging.getLogger(__name__)


class LoaderError(Exception):
    """Raised when data loading fails."""
    pass


def upsert_product(product: NormalizedProduct) -> int:
    """
    Insert or update a product in the Products table.
    
    This function uses ON CONFLICT to handle duplicates based on the unique
    constraint (brand, model_name). If a product a≤lready exists, it updates
    the record; otherwise, it inserts a new one.
    
    Args:
        product: NormalizedProduct object with GPU attributes
        
    Returns:
        The sku_id (product ID) of the inserted or updated product
        
    Raises:
        LoaderError: If the insert/update operation fails
        
    Example:
        >>> product = NormalizedProduct(
        ...     brand="ASUS",
        ...     chipset="RTX 4070 Super",
        ...     model_name="TUF Gaming OC",
        ...     vram="12GB",
        ...     is_oc=True
        ... )
        >>> sku_id = upsert_product(product)
        >>> print(f"Product ID: {sku_id}")
    """
    query = """
        INSERT INTO products (category, chipset, brand, model_name, vram, is_oc, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (brand, model_name)
        DO UPDATE SET
            chipset = EXCLUDED.chipset,
            vram = EXCLUDED.vram,
            is_oc = EXCLUDED.is_oc,
            updated_at = EXCLUDED.updated_at
        RETURNING id
    """
    
    params = (
        "그래픽카드",  # category is always "그래픽카드" for GPU products
        product.chipset,
        product.brand,
        product.model_name,
        product.vram,
        product.is_oc,
        datetime.now()
    )
    
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            if result is None:
                raise LoaderError("Failed to retrieve product ID after upsert")
            
            sku_id = result[0]
            logger.info(
                f"Upserted product: {product.brand} {product.model_name} "
                f"(chipset: {product.chipset}, sku_id: {sku_id})"
            )
            return sku_id
            
    except Exception as e:
        logger.error(f"Failed to upsert product {product.brand} {product.model_name}: {e}")
        raise LoaderError(f"Product upsert failed: {e}") from e


def upsert_products_batch(products: List[NormalizedProduct]) -> List[int]:
    """
    Insert or update multiple products in a single transaction.
    
    This function processes a batch of products efficiently while maintaining
    transactional integrity. If any product fails, the entire batch is rolled back.
    
    Args:
        products: List of NormalizedProduct objects
        
    Returns:
        List of sku_ids in the same order as input products
        
    Raises:
        LoaderError: If the batch operation fails
    """
    if not products:
        logger.warning("Empty product list provided to upsert_products_batch")
        return []
    
    sku_ids = []
    
    try:
        for product in products:
            sku_id = upsert_product(product)
            sku_ids.append(sku_id)
        
        logger.info(f"Successfully upserted {len(products)} products")
        return sku_ids
        
    except Exception as e:
        logger.error(f"Batch product upsert failed: {e}")
        raise LoaderError(f"Batch product upsert failed: {e}") from e


def insert_price_log(sku_id: int, price_data: PriceData) -> None:
    """
    Insert or update a price log in the Price_Logs table.
    
    This function uses ON CONFLICT to handle duplicates based on the unique
    constraint (sku_id, source, recorded_at). If a price log already exists,
    it updates the record; otherwise, it inserts a new one.
    
    Args:
        sku_id: Product identifier (foreign key to products table)
        price_data: PriceData object with price information
        
    Raises:
        LoaderError: If the insert/update operation fails
        
    Example:
        >>> from datetime import datetime
        >>> price_data = PriceData(
        ...     product_name="ASUS RTX 4070 Super",
        ...     price=899000.0,
        ...     source="다나와",
        ...     source_url="https://example.com/product/123",
        ...     recorded_at=datetime.now(),
        ...     price_change_pct=-5.2
        ... )
        >>> insert_price_log(sku_id=1, price_data=price_data)
    """
    query = """
        INSERT INTO price_logs (sku_id, price, source, source_url, recorded_at, price_change_pct)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (sku_id, source, recorded_at)
        DO UPDATE SET
            price = EXCLUDED.price,
            source_url = EXCLUDED.source_url,
            price_change_pct = EXCLUDED.price_change_pct
    """
    
    params = (
        sku_id,
        price_data.price,
        price_data.source,
        price_data.source_url,
        price_data.recorded_at,
        price_data.price_change_pct
    )
    
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute(query, params)
            
        logger.info(
            f"Inserted price log for sku_id {sku_id}: "
            f"price={price_data.price}, source={price_data.source}, "
            f"recorded_at={price_data.recorded_at}"
        )
        
    except Exception as e:
        logger.error(
            f"Failed to insert price log for sku_id {sku_id} "
            f"at {price_data.recorded_at}: {e}"
        )
        raise LoaderError(f"Price log insert failed: {e}") from e


def insert_price_logs_batch(sku_id: int, price_logs: List[PriceData]) -> None:
    """
    Insert or update multiple price logs for a single product in a transaction.
    
    This function is useful for loading historical price data efficiently.
    All price logs must be for the same product (sku_id).
    
    Args:
        sku_id: Product identifier
        price_logs: List of PriceData objects
        
    Raises:
        LoaderError: If the batch operation fails
    """
    if not price_logs:
        logger.warning(f"Empty price log list provided for sku_id {sku_id}")
        return
    
    try:
        for price_data in price_logs:
            insert_price_log(sku_id, price_data)
        
        logger.info(f"Successfully inserted {len(price_logs)} price logs for sku_id {sku_id}")
        
    except Exception as e:
        logger.error(f"Batch price log insert failed for sku_id {sku_id}: {e}")
        raise LoaderError(f"Batch price log insert failed: {e}") from e


def insert_market_signal(signal: MarketSignal) -> None:
    """
    Insert or update a market signal in the Market_Signals table.
    
    This function uses ON CONFLICT to handle duplicates based on the unique
    constraint (keyword, date, post_url). If a signal already exists, it updates
    the record; otherwise, it inserts a new one.
    
    Args:
        signal: MarketSignal object with Reddit community data
        
    Raises:
        LoaderError: If the insert/update operation fails
        
    Example:
        >>> from datetime import datetime
        >>> signal = MarketSignal(
        ...     keyword="New Release",
        ...     post_title="RTX 5070 leaked specs",
        ...     post_url="https://reddit.com/r/nvidia/comments/abc123",
        ...     subreddit="nvidia",
        ...     timestamp=datetime.now(),
        ...     sentiment_score=3.0
        ... )
        >>> insert_market_signal(signal)
    """
    # Extract date from timestamp for the unique constraint
    signal_date = signal.timestamp.date()
    
    query = """
        INSERT INTO market_signals (keyword, post_title, post_url, subreddit, sentiment_score, date)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (keyword, date, post_url)
        DO UPDATE SET
            post_title = EXCLUDED.post_title,
            sentiment_score = EXCLUDED.sentiment_score,
            mention_count = market_signals.mention_count + 1
    """
    
    params = (
        signal.keyword,
        signal.post_title,
        signal.post_url,
        signal.subreddit,
        signal.sentiment_score,
        signal_date
    )
    
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute(query, params)
            
        logger.info(
            f"Inserted market signal: keyword={signal.keyword}, "
            f"subreddit={signal.subreddit}, date={signal_date}"
        )
        
    except Exception as e:
        logger.error(
            f"Failed to insert market signal for keyword '{signal.keyword}' "
            f"on {signal_date}: {e}"
        )
        raise LoaderError(f"Market signal insert failed: {e}") from e


def insert_market_signals_batch(signals: List[MarketSignal]) -> None:
    """
    Insert or update multiple market signals in a transaction.
    
    This function processes a batch of Reddit signals efficiently while
    maintaining transactional integrity.
    
    Args:
        signals: List of MarketSignal objects
        
    Raises:
        LoaderError: If the batch operation fails
    """
    if not signals:
        logger.warning("Empty market signal list provided")
        return
    
    try:
        for signal in signals:
            insert_market_signal(signal)
        
        logger.info(f"Successfully inserted {len(signals)} market signals")
        
    except Exception as e:
        logger.error(f"Batch market signal insert failed: {e}")
        raise LoaderError(f"Batch market signal insert failed: {e}") from e


def insert_risk_alert(
    sku_id: int,
    product_name: str,
    risk_index: float,
    threshold: float,
    contributing_factors: Dict
) -> None:
    """
    Insert a risk alert in the Risk_Alerts table.
    
    This function creates a new alert when a product's risk index exceeds
    the configured threshold. The alert includes formatted information about
    the product and the factors contributing to the risk.
    
    Args:
        sku_id: Product identifier (foreign key to products table)
        product_name: Human-readable product name for the alert message
        risk_index: Calculated risk index value
        threshold: The threshold value that was exceeded
        contributing_factors: Dictionary containing factors like price_change,
                            sentiment_score, new_release_mentions, etc.
        
    Raises:
        LoaderError: If the insert operation fails
        
    Example:
        >>> factors = {
        ...     "price_change_pct": -5.2,
        ...     "new_release_mentions": 15,
        ...     "sentiment_score": 45.0,
        ...     "reason": "Price drop + high new release mentions"
        ... }
        >>> insert_risk_alert(
        ...     sku_id=1,
        ...     product_name="ASUS RTX 4070 Super TUF Gaming",
        ...     risk_index=125.5,
        ...     threshold=100.0,
        ...     contributing_factors=factors
        ... )
    """
    # Format alert message with product name, risk index, and contributing factors
    alert_message = _format_alert_message(product_name, risk_index, threshold, contributing_factors)
    
    query = """
        INSERT INTO risk_alerts (sku_id, risk_index, threshold, contributing_factors, acknowledged)
        VALUES (%s, %s, %s, %s, %s)
    """
    
    # Convert contributing_factors dict to JSON string for JSONB storage
    factors_json = json.dumps(contributing_factors, ensure_ascii=False)
    
    params = (
        sku_id,
        risk_index,
        threshold,
        factors_json,
        False  # acknowledged defaults to False
    )
    
    try:
        with db_manager.get_cursor() as cursor:
            cursor.execute(query, params)
            
        logger.warning(
            f"RISK ALERT: {alert_message}"
        )
        logger.info(
            f"Inserted risk alert for sku_id {sku_id}: "
            f"risk_index={risk_index}, threshold={threshold}"
        )
        
    except Exception as e:
        logger.error(
            f"Failed to insert risk alert for sku_id {sku_id}: {e}"
        )
        raise LoaderError(f"Risk alert insert failed: {e}") from e


def _format_alert_message(
    product_name: str,
    risk_index: float,
    threshold: float,
    factors: Dict
) -> str:
    """
    Format a human-readable alert message.
    
    Args:
        product_name: Product name
        risk_index: Risk index value
        threshold: Threshold value
        factors: Contributing factors dictionary
        
    Returns:
        Formatted alert message string
    """
    message_parts = [
        f"제품: {product_name}",
        f"위험 지수: {risk_index:.2f} (임계값: {threshold:.2f})"
    ]
    
    # Add contributing factors
    if "price_change_pct" in factors:
        message_parts.append(f"가격 변동: {factors['price_change_pct']:.2f}%")
    
    if "new_release_mentions" in factors:
        message_parts.append(f"신제품 언급: {factors['new_release_mentions']}회")
    
    if "sentiment_score" in factors:
        message_parts.append(f"감성 점수: {factors['sentiment_score']:.2f}")
    
    if "reason" in factors:
        message_parts.append(f"원인: {factors['reason']}")
    
    # Add recommendation
    if risk_index > threshold * 1.5:
        message_parts.append("권고: 즉시 재고 처분 검토 필요")
    elif risk_index > threshold:
        message_parts.append("권고: 재고 모니터링 강화")
    
    return " | ".join(message_parts)


def insert_risk_alerts_batch(alerts: List[Dict]) -> None:
    """
    Insert multiple risk alerts in a transaction.
    
    This function processes a batch of risk alerts efficiently.
    
    Args:
        alerts: List of dictionaries, each containing:
                - sku_id: int
                - product_name: str
                - risk_index: float
                - threshold: float
                - contributing_factors: dict
        
    Raises:
        LoaderError: If the batch operation fails
    """
    if not alerts:
        logger.info("No risk alerts to insert")
        return
    
    try:
        for alert in alerts:
            insert_risk_alert(
                sku_id=alert["sku_id"],
                product_name=alert["product_name"],
                risk_index=alert["risk_index"],
                threshold=alert["threshold"],
                contributing_factors=alert["contributing_factors"]
            )
        
        logger.warning(f"Generated {len(alerts)} risk alerts")
        
    except Exception as e:
        logger.error(f"Batch risk alert insert failed: {e}")
        raise LoaderError(f"Batch risk alert insert failed: {e}") from e

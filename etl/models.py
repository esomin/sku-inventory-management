"""
Data models for the ETL pipeline.

These dataclasses represent the core data structures used throughout
the Extract, Transform, and Load phases.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PriceData:
    """Price data collected from e-commerce sites."""
    product_name: str
    price: float
    source: str  # '다나와' or '에누리'
    source_url: str
    recorded_at: datetime
    price_change_pct: Optional[float] = None


@dataclass
class NormalizedProduct:
    """Normalized product data after parsing."""
    brand: str
    chipset: str  # RTX 4070 series variant
    model_name: str
    vram: str
    is_oc: bool


@dataclass
class MarketSignal:
    """Community signal data from Reddit."""
    keyword: str
    post_title: str
    post_url: str
    subreddit: str
    timestamp: datetime
    sentiment_score: Optional[float] = None


@dataclass
class RiskAlert:
    """Risk alert for inventory management."""
    sku_id: int
    product_name: str
    risk_index: float
    threshold: float
    contributing_factors: dict
    created_at: datetime
    acknowledged: bool = False

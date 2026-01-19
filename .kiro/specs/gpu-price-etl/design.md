# Design Document: GPU Price Monitoring ETL System

## Overview

The GPU Price Monitoring ETL System is a Python-based data pipeline that extends an existing Spring Boot SKU inventory management system to monitor RTX 4070 series GPU prices and market sentiment. The system crawls price data from 다나와 (Korean e-commerce site) and community signals from Reddit, normalizes product names into structured data, calculates inventory risk indices, and provides a React-based dashboard for visualization.

The system architecture follows a classic ETL pattern with three main phases:
- **Extract**: Web crawlers collect price data and Reddit RSS feeds
- **Transform**: Product name normalization and risk calculation
- **Load**: Persist data to PostgreSQL for frontend consumption

The scope is intentionally limited to RTX 4070 series (4070, 4070 Super, 4070 Ti, 4070 Ti Super) as these represent the most actively traded mainstream GPUs and provide ideal comparison data when new "Super" variants are released.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│  - Price Trend Charts                                        │
│  - Community Dashboard                                       │
│  - Risk Alerts Panel                                         │
│  - Model Comparison View                                     │
└─────────────────────┬───────────────────────────────────────┘
                      │ REST API
┌─────────────────────▼───────────────────────────────────────┐
│              Spring Boot Backend                             │
│  - SKU Entity Management                                     │
│  - API Endpoints for Frontend                                │
└─────────────────────┬───────────────────────────────────────┘
                      │ Database Access
┌─────────────────────▼───────────────────────────────────────┐
│                PostgreSQL Database                           │
│  - Products Table (GPU SKUs)                                 │
│  - Price_Logs Table (Historical Prices)                      │
│  - Market_Signals Table (Reddit Data)                        │
└──────────────────────────────────────────────────────────────┘
                      ▲
                      │ ETL Pipeline
┌─────────────────────┴───────────────────────────────────────┐
│              Python ETL Application                          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Scheduler (APScheduler)                             │  │
│  │  - Daily price crawl (configurable time)             │  │
│  │  - Daily Reddit collection (configurable time)       │  │
│  │  - Manual trigger via CLI                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Extract Layer                                       │  │
│  │  ┌────────────────┐  ┌──────────────────────────┐   │  │
│  │  │ Price_Crawler  │  │  Reddit_Collector        │   │  │
│  │  │ - 다나와 scraper│  │  - RSS feed parser       │   │  │
│  │  │ - 3-month data │  │  - Keyword filter        │   │  │
│  │  │                │  │  - Rate limit handler    │   │  │
│  │  └────────────────┘  └──────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Transform Layer                                     │  │
│  │  ┌────────────────┐  ┌──────────────────────────┐   │  │
│  │  │Product_        │  │  Risk_Calculator         │   │  │
│  │  │Normalizer      │  │  - Price change calc     │   │  │
│  │  │ - Brand extract│  │  - Sentiment scoring     │   │  │
│  │  │ - Chipset parse│  │  - Risk index formula    │   │  │
│  │  │ - VRAM extract │  │  - Threshold alerts      │   │  │
│  │  │ - OC detection │  │                          │   │  │
│  │  └────────────────┘  └──────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Load Layer                                          │  │
│  │  - Database connection pool                          │  │
│  │  - Upsert logic (handle duplicates)                  │  │
│  │  - Retry mechanism (3 attempts)                      │  │
│  │  - Transaction management                            │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Scheduled Extraction**: Scheduler triggers daily crawls
2. **Price Collection**: Price_Crawler fetches data from 다나와
3. **Community Collection**: Reddit_Collector fetches RSS feeds and filters by keywords
4. **Product Normalization**: Product_Normalizer parses product names into structured fields
5. **Risk Calculation**: Risk_Calculator computes price changes and sentiment scores
6. **Data Loading**: Load layer persists to PostgreSQL with upsert logic
7. **Frontend Display**: React dashboard queries Spring Boot API for visualization

### Technology Stack

- **ETL Application**: Python 3.10+
- **Web Scraping**: BeautifulSoup4, requests
- **RSS Parsing**: feedparser
- **Scheduling**: APScheduler
- **Database**: PostgreSQL 14+, psycopg2
- **Backend**: Spring Boot (existing system)
- **Frontend**: React, Chart.js or Recharts
- **Deployment**: Docker containers

## Components and Interfaces

### 1. Price_Crawler

**Responsibility**: Extract GPU price data from 다나와

**Interface**:
```python
class PriceCrawler:
    def crawl_danawa(self, chipset: str) -> List[PriceData]:
        """
        Crawl 다나와 for RTX 4070 series prices
        
        Args:
            chipset: One of ["RTX 4070", "RTX 4070 Super", "RTX 4070 Ti", "RTX 4070 Ti Super"]
        
        Returns:
            List of PriceData objects with current price and 3-month history
        
        Raises:
            CrawlError: If website is unreachable or parsing fails
        """
        pass
```

**Implementation Notes**:
- Use requests with User-Agent headers to avoid blocking
- Implement exponential backoff for retries
- Parse HTML with BeautifulSoup4
- Extract product name, current price, and historical price data
- Log errors but continue with remaining products
- Return empty list on complete failure

### 2. Reddit_Collector

**Responsibility**: Extract community signals from Reddit RSS feeds

**Interface**:
```python
class RedditCollector:
    KEYWORDS = ["New Release", "Leak", "Issues", "Price Drop", "Used Market"]
    SUBREDDITS = ["nvidia", "pcmasterrace"]
    
    def collect_signals(self) -> List[MarketSignal]:
        """
        Collect Reddit posts matching target keywords
        
        Returns:
            List of MarketSignal objects with keyword, title, timestamp
        
        Raises:
            RateLimitError: If Reddit API rate limit is exceeded
        """
        pass
    
    def _fetch_rss_feed(self, subreddit: str) -> List[RSSEntry]:
        """Fetch RSS feed for a subreddit"""
        pass
    
    def _filter_by_keywords(self, entries: List[RSSEntry]) -> List[MarketSignal]:
        """Filter entries by keyword presence in title or body"""
        pass
```

**Implementation Notes**:
- Use feedparser library for RSS parsing
- RSS feed URL format: `https://www.reddit.com/r/{subreddit}/.rss`
- Case-insensitive keyword matching
- Handle rate limits with exponential backoff (start at 60 seconds)
- Extract post title, URL, timestamp, and matched keyword
- Count each keyword once per post (no duplicates)

### 3. Product_Normalizer

**Responsibility**: Parse product names into structured GPU attributes

**Interface**:
```python
class ProductNormalizer:
    RTX_4070_VARIANTS = [
        "RTX 4070",
        "RTX 4070 Super",
        "RTX 4070 Ti",
        "RTX 4070 Ti Super"
    ]
    
    def normalize(self, product_name: str) -> NormalizedProduct:
        """
        Parse product name into structured fields
        
        Args:
            product_name: Raw product name from e-commerce site
        
        Returns:
            NormalizedProduct with brand, chipset, vram, is_oc
        
        Raises:
            NormalizationError: If parsing fails or chipset not in RTX 4070 series
        """
        pass
    
    def _extract_brand(self, name: str) -> str:
        """Extract brand (ASUS, MSI, GIGABYTE, etc.)"""
        pass
    
    def _extract_chipset(self, name: str) -> str:
        """Extract chipset from RTX 4070 variants"""
        pass
    
    def _extract_vram(self, name: str) -> str:
        """Extract VRAM capacity (e.g., '12GB')"""
        pass
    
    def _detect_oc(self, name: str) -> bool:
        """Detect if product is overclocked"""
        pass
```

**Implementation Notes**:
- Use regex patterns for extraction
- Brand patterns: Match common GPU brands (ASUS, MSI, GIGABYTE, ZOTAC, PALIT, etc.)
- Chipset patterns: Match "RTX 4070", "RTX 4070 Super", "RTX 4070 Ti", "RTX 4070 Ti Super"
- VRAM patterns: Match digits followed by "GB" (e.g., "12GB", "16GB")
- OC detection: Check for "OC", "오버클럭", "Overclock" (case-insensitive)
- Reject products not matching RTX 4070 series
- Return detailed error messages indicating which field failed

### 4. Risk_Calculator

**Responsibility**: Calculate inventory risk index from price trends and sentiment

**Interface**:
```python
class RiskCalculator:
    def calculate_price_change(self, sku_id: int, current_price: float) -> float:
        """
        Calculate week-over-week price change percentage
        
        Args:
            sku_id: Product identifier
            current_price: Current price in KRW
        
        Returns:
            Price change percentage (negative = price drop)
        
        Raises:
            InsufficientDataError: If less than 7 days of historical data
        """
        pass
    
    def calculate_sentiment_score(self, keyword_counts: Dict[str, int]) -> float:
        """
        Calculate weighted sentiment score from keyword mentions
        
        Args:
            keyword_counts: Dictionary of keyword to mention count
        
        Returns:
            Weighted sentiment score
        """
        pass
    
    def calculate_risk_index(self, sku_id: int, sentiment_score: float) -> float:
        """
        Calculate risk index using formula:
        risk_index = (current_price - last_week_avg_price) + (new_release_mentions × 0.3)
        
        Args:
            sku_id: Product identifier
            sentiment_score: Calculated sentiment score
        
        Returns:
            Risk index value (higher = more risk)
        """
        pass
    
    def check_threshold(self, risk_index: float, threshold: float) -> bool:
        """Check if risk index exceeds threshold"""
        pass
```

**Implementation Notes**:
- Query database for 7-day historical prices
- Calculate average price from 7 days ago (use 6-8 day window)
- Sentiment weights: "New Release" (3x), "Price Drop" (2x), others (1x)
- Risk formula combines price delta with weighted sentiment
- Default threshold: configurable via environment variable
- Log warnings when historical data is insufficient

### 5. Database Layer

**Responsibility**: Persist and query data in PostgreSQL

**Schema**:

```sql
-- Products table (extends existing SKU entity)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL DEFAULT '그래픽카드',
    chipset VARCHAR(50) NOT NULL CHECK (chipset IN (
        'RTX 4070', 'RTX 4070 Super', 'RTX 4070 Ti', 'RTX 4070 Ti Super'
    )),
    brand VARCHAR(50) NOT NULL,
    model_name VARCHAR(200) NOT NULL,
    vram VARCHAR(10) NOT NULL,
    is_oc BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(brand, model_name)
);

-- Price logs table
CREATE TABLE price_logs (
    id SERIAL PRIMARY KEY,
    sku_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    price DECIMAL(10, 2) NOT NULL,
    source VARCHAR(50) NOT NULL DEFAULT '다나와',
    source_url TEXT,
    recorded_at TIMESTAMP NOT NULL,
    price_change_pct DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(sku_id, source, recorded_at)
);

-- Market signals table
CREATE TABLE market_signals (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(100) NOT NULL,
    post_title TEXT NOT NULL,
    post_url TEXT,
    subreddit VARCHAR(50) NOT NULL,
    sentiment_score DECIMAL(5, 2),
    mention_count INTEGER DEFAULT 1,
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(keyword, date, post_url)
);

-- Risk alerts table
CREATE TABLE risk_alerts (
    id SERIAL PRIMARY KEY,
    sku_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    risk_index DECIMAL(10, 2) NOT NULL,
    threshold DECIMAL(10, 2) NOT NULL,
    contributing_factors JSONB,
    acknowledged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_price_logs_sku_recorded ON price_logs(sku_id, recorded_at DESC);
CREATE INDEX idx_market_signals_date ON market_signals(date DESC);
CREATE INDEX idx_risk_alerts_sku_created ON risk_alerts(sku_id, created_at DESC);
```

**Interface**:
```python
class DatabaseManager:
    def upsert_product(self, product: NormalizedProduct) -> int:
        """Insert or update product, return sku_id"""
        pass
    
    def insert_price_log(self, sku_id: int, price_data: PriceData) -> None:
        """Insert price log with upsert on conflict"""
        pass
    
    def insert_market_signal(self, signal: MarketSignal) -> None:
        """Insert market signal with upsert on conflict"""
        pass
    
    def insert_risk_alert(self, sku_id: int, risk_index: float, factors: dict) -> None:
        """Insert risk alert"""
        pass
    
    def get_historical_prices(self, sku_id: int, days: int) -> List[PriceData]:
        """Query historical prices for risk calculation"""
        pass
    
    def get_keyword_counts(self, days: int) -> Dict[str, int]:
        """Query keyword mention counts for sentiment analysis"""
        pass
```

**Implementation Notes**:
- Use connection pooling (psycopg2.pool)
- Implement retry logic (3 attempts with exponential backoff)
- Use ON CONFLICT DO UPDATE for upserts
- Wrap operations in transactions
- Log all database errors with context

### 6. Scheduler

**Responsibility**: Orchestrate daily ETL jobs and provide manual triggers

**Interface**:
```python
class ETLScheduler:
    def schedule_price_crawl(self, hour: int, minute: int) -> None:
        """Schedule daily price crawl at specified time"""
        pass
    
    def schedule_reddit_collection(self, hour: int, minute: int) -> None:
        """Schedule daily Reddit collection at specified time"""
        pass
    
    def run_price_crawl_now(self) -> None:
        """Manually trigger price crawl"""
        pass
    
    def run_reddit_collection_now(self) -> None:
        """Manually trigger Reddit collection"""
        pass
    
    def start(self) -> None:
        """Start scheduler daemon"""
        pass
```

**Implementation Notes**:
- Use APScheduler with BackgroundScheduler
- Default schedule: Price crawl at 09:00 KST, Reddit at 10:00 KST
- Configure via environment variables or config file
- Implement CLI commands for manual triggers
- Log all job executions and failures
- Continue with next job if one fails

### 7. Frontend Components

**Responsibility**: Visualize price trends, community signals, and risk alerts

**Components**:

1. **PriceTrendChart**
   - Line chart showing 3-month price history
   - Single line for 다나와 prices
   - Tooltip on hover with exact price, date, source
   - Date range filter

2. **CommunityDashboard**
   - Bar chart of keyword mention counts (30 days)
   - Highlight keywords with >50% week-over-week growth
   - Click to show top 5 related posts
   - Auto-refresh every 24 hours

3. **RiskAlertsPanel**
   - List of active alerts sorted by risk index
   - Show product name, risk index, contributing factors
   - Acknowledge button to dismiss alerts
   - Alert history view

4. **ModelComparisonView**
   - Side-by-side table of RTX 4070 series models
   - Columns: Model, Current Price, WoW Change, Risk Index
   - Highlight price drops in non-Super models
   - Price gap calculation between variants
   - Overlay chart for two-model comparison

**API Endpoints** (Spring Boot):
```
GET /api/products?chipset={chipset}
GET /api/prices/{sku_id}?start_date={date}&end_date={date}
GET /api/market-signals?days={days}
GET /api/risk-alerts?acknowledged={bool}
GET /api/comparison?models={model1,model2}
POST /api/risk-alerts/{id}/acknowledge
```

## Data Models

### Python Data Classes

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class PriceData:
    product_name: str
    price: float
    source: str  # '다나와' or '에누리'
    source_url: str
    recorded_at: datetime
    price_change_pct: Optional[float] = None

@dataclass
class NormalizedProduct:
    brand: str
    chipset: str  # RTX 4070 series variant
    model_name: str
    vram: str
    is_oc: bool

@dataclass
class MarketSignal:
    keyword: str
    post_title: str
    post_url: str
    subreddit: str
    timestamp: datetime
    sentiment_score: Optional[float] = None

@dataclass
class RiskAlert:
    sku_id: int
    product_name: str
    risk_index: float
    threshold: float
    contributing_factors: dict
    created_at: datetime
    acknowledged: bool = False
```

### Configuration

```python
# config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "gpu_etl"
    db_user: str = "postgres"
    db_password: str
    
    # Scheduler
    price_crawl_hour: int = 9
    price_crawl_minute: int = 0
    reddit_crawl_hour: int = 10
    reddit_crawl_minute: int = 0
    
    # Risk calculation
    risk_threshold: float = 100.0
    sentiment_weight_new_release: float = 3.0
    sentiment_weight_price_drop: float = 2.0
    sentiment_weight_default: float = 1.0
    
    # Retry settings
    max_retries: int = 3
    retry_backoff_seconds: int = 5
    
    class Config:
        env_file = ".env"
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: GPU Product Category Invariant

*For any* GPU product created in the system, the category field must always be set to "그래픽카드" regardless of other attributes.

**Validates: Requirements 1.2**

### Property 2: Chipset Validation

*For any* chipset value provided to SKU_Entity, the system must accept only RTX 4070 series variants ("RTX 4070", "RTX 4070 Super", "RTX 4070 Ti", "RTX 4070 Ti Super") and reject all other values with an error.

**Validates: Requirements 1.3**

### Property 3: VRAM Format Validation

*For any* VRAM value stored in SKU_Entity, it must follow the format of digits followed by "GB" (e.g., "12GB", "16GB").

**Validates: Requirements 1.4**

### Property 4: Product Name Normalization Completeness

*For any* valid RTX 4070 series product name, the Product_Normalizer must successfully extract all required fields (brand, chipset, VRAM, is_oc) and produce a complete NormalizedProduct object.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

### Property 5: OC Detection Accuracy

*For any* product name containing "OC", "오버클럭", or "Overclock" (case-insensitive), the Product_Normalizer must set is_oc to true; for product names without these indicators, is_oc must be false.

**Validates: Requirements 2.4**

### Property 6: Normalization Error Reporting

*For any* product name that fails normalization, the Product_Normalizer must return an error message that includes the specific field name that failed extraction.

**Validates: Requirements 2.5**

### Property 7: Non-4070 Series Rejection

*For any* product name that does not contain an RTX 4070 series chipset, the Product_Normalizer must reject it with an error.

**Validates: Requirements 2.6**

### Property 8: Price Data Completeness

*For any* price data fetched by Price_Crawler, the resulting PriceData object must include the source URL, recorded timestamp, and price value.

**Validates: Requirements 3.4**

### Property 9: Crawler Error Resilience

*For any* list of products to crawl, if one product fails with an error, the Price_Crawler must continue processing the remaining products and return results for successful crawls.

**Validates: Requirements 3.5**

### Property 10: Reddit Keyword Filtering

*For any* Reddit post processed by Reddit_Collector, the post must be included in results if and only if its title or body contains at least one of the target keywords ("New Release", "Leak", "Issues", "Price Drop", "Used Market").

**Validates: Requirements 4.3**

### Property 11: Reddit Signal Extraction Completeness

*For any* Reddit post that matches keyword filters, the Reddit_Collector must extract all required fields (keyword, post_title, post_url, subreddit, timestamp) into a MarketSignal object.

**Validates: Requirements 4.4**

### Property 12: Price Change Calculation Accuracy

*For any* product with at least 7 days of price history, the calculated week-over-week price change percentage must equal ((current_price - avg_price_7_days_ago) / avg_price_7_days_ago) × 100.

**Validates: Requirements 5.1, 5.2**

### Property 13: Price Change Storage Invariant

*For any* price record inserted into the database, if historical data is sufficient (≥7 days), the price_change_pct field must be populated with the calculated value; otherwise, it must be null.

**Validates: Requirements 5.4**

### Property 14: Keyword Mention Counting

*For any* set of Reddit posts processed on a given day, the system must count each target keyword's mentions per day, counting each keyword at most once per post even if it appears multiple times.

**Validates: Requirements 6.1, 6.2**

### Property 15: Weighted Sentiment Scoring

*For any* distribution of keyword mention counts, the sentiment score must be calculated as the sum of (mention_count × weight) where weights are: "New Release" (3.0), "Price Drop" (2.0), others (1.0).

**Validates: Requirements 6.3, 6.4**

### Property 16: Risk Index Formula Correctness

*For any* product with available price and sentiment data, the risk index must be calculated using the formula: risk_index = (current_price - last_week_avg_price) + (new_release_mentions × 0.3).

**Validates: Requirements 7.1, 7.2**

### Property 17: Risk Threshold Flagging

*For any* calculated risk index, the product must be flagged as high-risk if and only if the risk index exceeds the configured threshold value.

**Validates: Requirements 7.3**

### Property 18: Database Persistence Completeness

*For any* normalized product, price data, or market signal, the ETL system must successfully insert it into the appropriate database table (Products, Price_Logs, or Market_Signals) with all required fields populated.

**Validates: Requirements 8.1, 8.2, 8.3**

### Property 19: Upsert Idempotence

*For any* record inserted into the database, inserting the same record again (same unique key) must result in an update to the existing record rather than creating a duplicate, maintaining exactly one record.

**Validates: Requirements 8.4**

### Property 20: Scheduler Task Isolation

*For any* scheduled task that fails with an error, the Scheduler must log the error and continue executing subsequent scheduled tasks without interruption.

**Validates: Requirements 9.3**

### Property 21: Alert Generation Threshold

*For any* product whose risk index exceeds the configured threshold, the ETL system must generate a risk alert containing the product name, risk index value, and contributing factors.

**Validates: Requirements 12.1, 12.2**

### Property 22: Frontend Trend Highlighting

*For any* keyword with week-over-week mention growth exceeding 50%, the Frontend must visually highlight that keyword in the community dashboard.

**Validates: Requirements 11.2**

### Property 23: Price Gap Calculation

*For any* two RTX 4070 series models selected for comparison, the Frontend must calculate and display the price gap as the absolute difference between their current prices.

**Validates: Requirements 13.4**

### Property 24: Super Model Impact Detection

*For any* RTX 4070 series model comparison where a "Super" variant exists, if the Super model's price drops, the Frontend must highlight corresponding price drops in the non-Super variant of the same tier.

**Validates: Requirements 13.3**

## Error Handling

### Crawler Errors

**Price_Crawler**:
- Network timeouts: Retry with exponential backoff (5s, 10s, 20s), max 3 attempts
- HTTP errors (4xx, 5xx): Log error with URL and status code, skip product
- Parsing errors: Log error with product name and HTML snippet, skip product
- Complete failure: Return empty list, log critical error

**Reddit_Collector**:
- Rate limit (429): Wait for rate limit reset (from headers), retry once
- Network errors: Retry with exponential backoff, max 3 attempts
- RSS parsing errors: Log error with feed URL, skip subreddit
- Missing fields: Log warning, skip post

### Normalization Errors

**Product_Normalizer**:
- Missing brand: Raise NormalizationError("Failed to extract brand from: {product_name}")
- Missing chipset: Raise NormalizationError("Failed to extract chipset from: {product_name}")
- Invalid chipset: Raise NormalizationError("Chipset {chipset} not in RTX 4070 series")
- Missing VRAM: Raise NormalizationError("Failed to extract VRAM from: {product_name}")
- Multiple matches: Use first match, log warning

### Database Errors

**DatabaseManager**:
- Connection errors: Retry 3 times with exponential backoff (5s, 10s, 20s)
- Constraint violations: Log error with details, raise exception
- Transaction failures: Rollback, log error, raise exception
- Query timeouts: Log slow query, raise exception
- Connection pool exhausted: Wait for available connection (max 30s), raise exception if timeout

### Calculation Errors

**Risk_Calculator**:
- Insufficient historical data (<7 days): Skip calculation, set price_change_pct to null, log warning
- Missing sentiment data: Use sentiment_score = 0, log warning
- Division by zero (price = 0): Skip calculation, log error
- Negative prices: Raise ValueError("Invalid negative price")

### Scheduler Errors

**ETLScheduler**:
- Task execution failure: Log error with traceback, mark task as failed, continue
- Scheduler crash: Log critical error, attempt restart, send alert
- Concurrent execution: Skip if previous run still active, log warning
- Configuration errors: Fail fast on startup, log error

### Frontend Errors

**React Components**:
- API errors: Display user-friendly error message, log to console
- Missing data: Show "No data available" message
- Chart rendering errors: Display fallback message, log error
- Network timeouts: Show retry button, log error

## Testing Strategy

### Dual Testing Approach

The testing strategy employs both unit tests and property-based tests to ensure comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, error conditions, and integration points
- **Property tests**: Verify universal properties across all inputs through randomization

Together, these approaches provide comprehensive coverage where unit tests catch concrete bugs and property tests verify general correctness.

### Property-Based Testing

**Library**: Use `hypothesis` for Python (property-based testing library)

**Configuration**:
- Minimum 100 iterations per property test
- Each test must reference its design document property
- Tag format: `# Feature: gpu-price-etl, Property {number}: {property_text}`

**Property Test Coverage**:

Each correctness property (1-24) must be implemented as a single property-based test:

1. **Property 1-3**: Test SKU entity validation with generated GPU products
2. **Property 4-7**: Test Product_Normalizer with generated product names
3. **Property 8-9**: Test Price_Crawler with mocked web responses
4. **Property 10-11**: Test Reddit_Collector with generated RSS feeds
5. **Property 12-13**: Test price change calculation with generated price histories
6. **Property 14-15**: Test sentiment scoring with generated keyword counts
7. **Property 16-17**: Test risk calculation with generated price and sentiment data
8. **Property 18-19**: Test database operations with generated data objects
9. **Property 20**: Test scheduler error isolation with simulated failures
10. **Property 21**: Test alert generation with generated risk indices
11. **Property 22-24**: Test frontend logic with generated market data

**Example Property Test**:
```python
from hypothesis import given, strategies as st

# Feature: gpu-price-etl, Property 4: Product Name Normalization Completeness
@given(
    brand=st.sampled_from(["ASUS", "MSI", "GIGABYTE", "ZOTAC"]),
    chipset=st.sampled_from(["RTX 4070", "RTX 4070 Super", "RTX 4070 Ti", "RTX 4070 Ti Super"]),
    vram=st.sampled_from(["12GB", "16GB"]),
    has_oc=st.booleans()
)
def test_product_normalization_completeness(brand, chipset, vram, has_oc):
    """For any valid RTX 4070 series product name, normalization must extract all fields"""
    oc_suffix = " OC" if has_oc else ""
    product_name = f"{brand} {chipset} {vram}{oc_suffix}"
    
    normalizer = ProductNormalizer()
    result = normalizer.normalize(product_name)
    
    assert result.brand == brand
    assert result.chipset == chipset
    assert result.vram == vram
    assert result.is_oc == has_oc
```

### Unit Testing

**Framework**: pytest for Python, Jest for React

**Unit Test Coverage**:

1. **Price_Crawler**:
   - Test successful crawl from 다나와 (specific example)
   - Test handling of malformed HTML
   - Test network timeout handling
   - Test 3-month history retrieval

2. **Reddit_Collector**:
   - Test RSS feed parsing from r/nvidia (specific example)
   - Test RSS feed parsing from r/pcmasterrace (specific example)
   - Test rate limit handling (specific scenario)
   - Test keyword filtering with edge cases

3. **Product_Normalizer**:
   - Test normalization of specific product names
   - Test error messages for missing fields
   - Test rejection of non-4070 series products
   - Test edge cases (special characters, multiple spaces)

4. **Risk_Calculator**:
   - Test risk calculation with known values
   - Test handling of insufficient data (<7 days)
   - Test threshold flagging with boundary values
   - Test sentiment weight application

5. **DatabaseManager**:
   - Test connection pool management
   - Test transaction rollback on error
   - Test retry logic with simulated failures
   - Test upsert conflict resolution

6. **ETLScheduler**:
   - Test daily schedule execution (specific time)
   - Test manual trigger via CLI (specific command)
   - Test task failure isolation

7. **Frontend Components**:
   - Test PriceTrendChart rendering with sample data
   - Test CommunityDashboard keyword highlighting
   - Test RiskAlertsPanel alert display
   - Test ModelComparisonView price gap calculation
   - Test user interactions (clicks, hovers, filters)

### Integration Testing

**Scope**: Test end-to-end ETL pipeline with test database

1. **Full ETL Pipeline**:
   - Mock external sources (다나와, Reddit)
   - Run complete extraction → transformation → loading
   - Verify data in test database
   - Verify alerts generated correctly

2. **API Integration**:
   - Test Spring Boot API endpoints with test data
   - Verify frontend can fetch and display data
   - Test error responses

3. **Scheduler Integration**:
   - Test scheduled job execution
   - Test manual trigger commands
   - Test error recovery

### Test Data

**Generators**:
- RTX 4070 series product names (various brands, models, VRAM)
- Price histories (3-month ranges, various trends)
- Reddit posts (with and without keywords)
- Market signals (various sentiment scores)
- Risk indices (below and above thresholds)

**Fixtures**:
- Sample HTML from 다나와
- Sample RSS feeds from Reddit
- Sample database records
- Sample API responses

### Continuous Testing

- Run unit tests on every commit
- Run property tests on every pull request
- Run integration tests nightly
- Monitor test coverage (target: >80% for core logic)

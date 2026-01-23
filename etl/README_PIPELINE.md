# ETL Pipeline Implementation

## Overview

The ETL pipeline (`main.py`) orchestrates the complete Extract → Transform → Load workflow for the GPU Price Monitoring system.

## Features

### Main Pipeline (`ETLPipeline` class)

The pipeline integrates all components:

1. **Extract Phase**
   - Crawls GPU prices from 다나와 for all RTX 4070 series variants
   - Collects market signals from Reddit RSS feeds

2. **Transform Phase**
   - Normalizes product names into structured data
   - Matches products to existing SKUs or prepares for creation
   - Calculates sentiment scores from Reddit signals
   - Computes price change percentages

3. **Load Phase**
   - Persists products to database with upsert logic
   - Stores price logs with calculated price changes
   - Saves market signals with sentiment scores

4. **Risk Analysis Phase**
   - Calculates risk indices for all SKUs
   - Generates alerts for high-risk products
   - Stores alerts with contributing factors

### Error Handling

- Each phase handles errors gracefully
- Failed operations are logged but don't stop the pipeline
- Statistics track both successes and errors
- Resources are cleaned up even on failure

### Partial Tasks

The pipeline supports running individual tasks:

- `run_price_crawl_only()` - Only crawl and load prices
- `run_reddit_collection_only()` - Only collect and load Reddit signals
- `run_full_pipeline()` - Complete ETL workflow

## Usage

### Command Line

```bash
# Run full pipeline
python main.py

# Run price crawl only
python main.py --task=price_crawl

# Run Reddit collection only
python main.py --task=reddit_collection
```

### Programmatic

```python
from main import ETLPipeline

# Create pipeline
pipeline = ETLPipeline()

# Run full pipeline
stats = pipeline.run_full_pipeline()

# Check results
if stats['success']:
    print(f"Extracted {stats['prices_extracted']} prices")
    print(f"Generated {stats['alerts_generated']} alerts")
else:
    print(f"Pipeline failed: {stats.get('fatal_error')}")
```

## Statistics

The pipeline tracks comprehensive statistics:

- `prices_extracted` - Number of prices crawled
- `signals_extracted` - Number of Reddit signals collected
- `products_normalized` - Number of products normalized
- `prices_loaded` - Number of price logs inserted
- `signals_loaded` - Number of market signals inserted
- `alerts_generated` - Number of risk alerts created
- `errors` - List of error messages
- `execution_time_seconds` - Total execution time
- `success` - Overall success status

## Logging

The pipeline logs to both console and file (`etl_pipeline.log`):

- INFO level: Progress updates and summaries
- WARNING level: Non-fatal errors and risk alerts
- ERROR level: Failed operations
- DEBUG level: Detailed operation information

## Testing

Integration tests are provided in `tests/test_etl_integration.py`:

- Component-level tests for each phase
- Error handling scenarios
- Statistics tracking verification
- Partial task execution tests

Run tests with:

```bash
pytest tests/test_etl_integration.py -v
```

## Requirements

Validates requirements:
- **3.5**: Error handling during crawling
- **8.5**: Database retry logic and transaction management

## Architecture

```
ETLPipeline
├── Extract
│   ├── DanawaCrawler (prices)
│   └── RedditCollector (signals)
├── Transform
│   ├── ProductNormalizer (product names)
│   ├── SKUMatcher (SKU matching)
│   ├── PriceAnalyzer (price changes)
│   └── SentimentAnalyzer (sentiment scores)
├── Load
│   ├── upsert_product (products)
│   ├── insert_price_log (prices)
│   └── insert_market_signal (signals)
└── Risk Analysis
    ├── RiskCalculator (risk indices)
    └── insert_risk_alert (alerts)
```

## Configuration

The pipeline uses settings from `config.py`:

- Database connection parameters
- Retry configuration
- Risk thresholds
- Sentiment weights
- Logging level

## Next Steps

After implementing the pipeline:

1. Set up scheduler (Task 13) to run pipeline automatically
2. Implement backend API endpoints (Task 15) to expose data
3. Build frontend components (Task 16) to visualize results
4. Run end-to-end integration tests (Task 18)

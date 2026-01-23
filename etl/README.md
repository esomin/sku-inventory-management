# GPU Price Monitoring ETL System

A Python-based ETL pipeline that monitors RTX 4070 series GPU prices from Korean e-commerce sites (다나와) and Reddit community signals to detect inventory risk.

## Features

- **Price Crawling**: Automated collection of GPU prices from 다나와
- **Community Monitoring**: Reddit RSS feed analysis for market signals
- **Product Normalization**: Intelligent parsing of product names into structured data
- **Risk Analysis**: Calculation of inventory risk indices based on price trends and sentiment
- **Automated Scheduling**: Daily execution of ETL tasks via APScheduler

## Project Structure

```
etl/
├── extractors/          # Data extraction modules
├── transformers/        # Data transformation and analysis
├── loaders/            # Database persistence layer
├── tests/              # Unit and integration tests
├── docs/               # Documentation (guides, testing, completion)
├── config.py           # Configuration management
├── models.py           # Data models
├── db_connection.py    # Database connection pool
├── requirements.txt    # Python dependencies
└── .env.template       # Environment variables template
```

## Documentation

Comprehensive documentation is available in the `docs/` folder:

- **[Installation Guides](docs/guides/)** - Setup and configuration instructions
  - [psycopg2 Installation Guide](docs/guides/PSYCOPG2_INSTALLATION_GUIDE.md) - Docker PostgreSQL setup
- **[Testing Documentation](docs/testing/)** - Testing strategies and examples
  - [Mock Testing Guide](docs/testing/MOCK_DETAILED_EXPLANATION.md) - Unit testing with mocks
- **[Completion Summaries](docs/completion/)** - Task completion reports
  - [Task 8 Summary](docs/completion/TASK_8_COMPLETION_SUMMARY.md) - Price analysis module

See [docs/README.md](docs/README.md) for the complete documentation index.

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.template .env
# Edit .env with your database credentials
```

## Configuration

All configuration is managed through environment variables. See `.env.template` for available options:

- **Database**: PostgreSQL connection settings
- **Scheduler**: Cron-like schedule for ETL tasks
- **Risk Calculation**: Thresholds and weights for risk analysis
- **Retry Logic**: Maximum retries and backoff settings

## Usage

### Manual Execution

Run ETL tasks manually:
```bash
python main.py --task=price_crawl
python main.py --task=reddit_collection
```

### Scheduled Execution

Start the scheduler daemon:
```bash
python scheduler.py
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=etl

# Run property-based tests only
pytest -m property
```

## Scope

This system is intentionally limited to **RTX 4070 series** GPUs:
- RTX 4070
- RTX 4070 Super
- RTX 4070 Ti
- RTX 4070 Ti Super

This scope provides ideal comparison data for analyzing price impacts when new "Super" variants are released.

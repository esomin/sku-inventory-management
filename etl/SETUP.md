# Setup Guide

## Prerequisites

- Python 3.10 or higher
- PostgreSQL 14 or higher
- pip (Python package manager)

## Installation Steps

### 1. Create Virtual Environment

```bash
cd etl
python3 -m venv venv
```

### 2. Activate Virtual Environment

**On macOS/Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.template .env
```

Edit `.env` and set your database credentials:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gpu_etl
DB_USER=postgres
DB_PASSWORD=your_actual_password
```

### 5. Verify Installation

Test that the configuration loads correctly:
```bash
python3 -c "from config import settings; print(f'Config loaded: DB={settings.db_name}')"
```

Test database connection (requires PostgreSQL running):
```bash
python3 -c "from db_connection import db_manager; print('Connection test:', db_manager.test_connection())"
```

### 6. Run Tests

```bash
pytest
```

Run with coverage:
```bash
pytest --cov=. --cov-report=html
```

## Troubleshooting

### ModuleNotFoundError

If you see `ModuleNotFoundError`, ensure:
1. Virtual environment is activated
2. Dependencies are installed: `pip install -r requirements.txt`

### Database Connection Errors

If database connection fails:
1. Verify PostgreSQL is running: `pg_isready`
2. Check credentials in `.env` file
3. Ensure database exists: `createdb gpu_etl`
4. Check firewall/network settings

### Import Errors

If you see import errors when running scripts:
1. Ensure you're in the `etl/` directory
2. Or add to PYTHONPATH: `export PYTHONPATH="${PYTHONPATH}:$(pwd)"`

## Next Steps

After successful setup:
1. Review the database schema in `../backend/src/main/resources/db/migration/`
2. Implement extractor modules (tasks 5-6)
3. Implement transformer modules (tasks 7-10)
4. Implement loader modules (task 11)

# Database Migration Scripts

This directory contains SQL migration scripts for the SKU Inventory Management system.

## Migration Files

### V1__add_gpu_fields_to_skus.sql
Adds GPU-specific fields to the `skus` table:
- `chipset` (VARCHAR(50)) - GPU chipset model (RTX 4070 series only)
- `brand` (VARCHAR(50)) - GPU manufacturer brand
- `model_name` (VARCHAR(200)) - GPU model lineup name
- `vram` (VARCHAR(10)) - VRAM capacity (format: digits+GB)
- `is_oc` (BOOLEAN) - Overclocked flag

Also creates indexes on `chipset` and `brand` columns for better query performance.

### V2__create_price_logs_table.sql
Creates the `price_logs` table for storing historical GPU price data:
- `id` (BIGSERIAL PRIMARY KEY) - Auto-incrementing primary key
- `sku_id` (BIGINT) - Foreign key to skus table
- `price` (DECIMAL(10,2)) - Price in KRW
- `recorded_at` (TIMESTAMP) - When the price was recorded from source
- `source_url` (VARCHAR(500)) - URL of the source page
- `source_name` (VARCHAR(50)) - Source name (다나와 or 에누리)
- `price_change_pct` (DECIMAL(5,2)) - Week-over-week price change percentage
- `created_at` (TIMESTAMP) - When the record was inserted

Includes indexes on (sku_id, recorded_at), (recorded_at), and (sku_id, source_name).

### V3__create_market_signals_table.sql
Creates the `market_signals` table for storing Reddit community signals:
- `id` (BIGSERIAL PRIMARY KEY) - Auto-incrementing primary key
- `keyword` (VARCHAR(100)) - Target keyword (e.g., "New Release", "Price Drop")
- `sentiment_score` (DECIMAL(5,2)) - Calculated sentiment score
- `mention_count` (INTEGER) - Number of mentions (counted once per post)
- `date` (DATE) - Date when the signal was recorded
- `post_title` (TEXT) - Reddit post title
- `post_url` (VARCHAR(500)) - Reddit post URL
- `subreddit` (VARCHAR(50)) - Subreddit name
- `created_at` (TIMESTAMP) - When the record was inserted

Includes indexes on (keyword, date), (date), and (subreddit, date).

### V4__create_risk_alerts_table.sql
Creates the `risk_alerts` table for storing inventory risk alerts:
- `id` (BIGSERIAL PRIMARY KEY) - Auto-incrementing primary key
- `sku_id` (BIGINT) - Foreign key to skus table
- `risk_index` (DECIMAL(10,2)) - Calculated risk index value
- `alert_message` (TEXT) - Human-readable alert message
- `created_at` (TIMESTAMP) - When the alert was generated
- `acknowledged` (BOOLEAN) - Whether the alert has been acknowledged
- `threshold` (DECIMAL(10,2)) - Risk threshold that triggered the alert
- `contributing_factors` (JSONB) - JSON object with contributing factors

Includes indexes on (sku_id, created_at), (acknowledged, created_at), and (created_at).

## How to Apply Migrations

### Option 1: Manual Execution (Recommended for Development)

Connect to your PostgreSQL database and run the migration scripts in order:

```bash
# Apply V1 migration (GPU fields)
psql -U postgres -d sku_inventory -f backend/src/main/resources/db/migration/V1__add_gpu_fields_to_skus.sql

# Apply V2 migration (price_logs table)
psql -U postgres -d sku_inventory -f backend/src/main/resources/db/migration/V2__create_price_logs_table.sql

# Apply V3 migration (market_signals table)
psql -U postgres -d sku_inventory -f backend/src/main/resources/db/migration/V3__create_market_signals_table.sql

# Apply V4 migration (risk_alerts table)
psql -U postgres -d sku_inventory -f backend/src/main/resources/db/migration/V4__create_risk_alerts_table.sql
```

Or apply all migrations at once:

```bash
for file in backend/src/main/resources/db/migration/V*.sql; do
  psql -U postgres -d sku_inventory -f "$file"
done
```

### Option 2: Using Flyway (For Production)

If you want to use Flyway for automated migrations:

1. Add Flyway dependency to `build.gradle`:
```gradle
implementation 'org.flywaydb:flyway-core'
```

2. Update `application.yml`:
```yaml
spring:
  flyway:
    enabled: true
    baseline-on-migrate: true
    locations: classpath:db/migration
```

3. Restart the application - Flyway will automatically apply pending migrations.

### Option 3: Using Hibernate Auto-Update (Current Setup)

The current application uses `spring.jpa.hibernate.ddl-auto: update`, which means:
- Hibernate will automatically add the new columns when the application starts
- The migration script serves as documentation and can be used for manual control

## Verification

After applying the migrations, verify the changes:

```sql
-- Check if columns were added to skus table
\d skus

-- Check if new tables were created
\d price_logs
\d market_signals
\d risk_alerts

-- Verify indexes
\di idx_skus_*
\di idx_price_logs_*
\di idx_market_signals_*
\di idx_risk_alerts_*

-- Test chipset constraint on skus table
INSERT INTO skus (sku_code, product_name, category, current_stock, safe_stock, daily_consumption_rate, chipset)
VALUES ('TEST-001', 'Test GPU', '그래픽카드', 10, 5, 1.0, 'RTX 4070');

-- This should fail (invalid chipset)
INSERT INTO skus (sku_code, product_name, category, current_stock, safe_stock, daily_consumption_rate, chipset)
VALUES ('TEST-002', 'Test GPU', '그래픽카드', 10, 5, 1.0, 'RTX 3080');

-- Test price_logs table
INSERT INTO price_logs (sku_id, price, recorded_at, source_name, source_url)
VALUES (1, 599000.00, NOW(), '다나와', 'https://example.com');

-- Test market_signals table
INSERT INTO market_signals (keyword, post_title, post_url, subreddit, date)
VALUES ('New Release', 'RTX 5070 announced!', 'https://reddit.com/r/nvidia/123', 'nvidia', CURRENT_DATE);

-- Test risk_alerts table
INSERT INTO risk_alerts (sku_id, risk_index, alert_message, threshold)
VALUES (1, 150.50, 'High risk: Price drop detected', 100.00);
```

## Rollback

If you need to rollback the migrations:

### Rollback V4 (risk_alerts table)
```sql
DROP TABLE IF EXISTS risk_alerts CASCADE;
```

### Rollback V3 (market_signals table)
```sql
DROP TABLE IF EXISTS market_signals CASCADE;
```

### Rollback V2 (price_logs table)
```sql
DROP TABLE IF EXISTS price_logs CASCADE;
```

### Rollback V1 (GPU fields from skus table)
```sql
-- Remove indexes
DROP INDEX IF EXISTS idx_skus_chipset;
DROP INDEX IF EXISTS idx_skus_brand;
DROP INDEX IF EXISTS idx_skus_chipset_brand;

-- Remove constraints
ALTER TABLE skus DROP CONSTRAINT IF EXISTS check_chipset_rtx_4070_series;
ALTER TABLE skus DROP CONSTRAINT IF EXISTS check_vram_format;

-- Remove columns
ALTER TABLE skus
DROP COLUMN IF EXISTS chipset,
DROP COLUMN IF EXISTS brand,
DROP COLUMN IF EXISTS model_name,
DROP COLUMN IF EXISTS vram,
DROP COLUMN IF EXISTS is_oc;
```

### Rollback All Migrations
```sql
-- Drop all new tables (in reverse order due to foreign keys)
DROP TABLE IF EXISTS risk_alerts CASCADE;
DROP TABLE IF EXISTS market_signals CASCADE;
DROP TABLE IF EXISTS price_logs CASCADE;

-- Remove GPU fields from skus table
DROP INDEX IF EXISTS idx_skus_chipset;
DROP INDEX IF EXISTS idx_skus_brand;
DROP INDEX IF EXISTS idx_skus_chipset_brand;

ALTER TABLE skus DROP CONSTRAINT IF EXISTS check_chipset_rtx_4070_series;
ALTER TABLE skus DROP CONSTRAINT IF EXISTS check_vram_format;

ALTER TABLE skus
DROP COLUMN IF EXISTS chipset,
DROP COLUMN IF EXISTS brand,
DROP COLUMN IF EXISTS model_name,
DROP COLUMN IF EXISTS vram,
DROP COLUMN IF EXISTS is_oc;
```

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

## How to Apply Migrations

### Option 1: Manual Execution (Recommended for Development)

Connect to your PostgreSQL database and run the migration script:

```bash
psql -U postgres -d sku_inventory -f backend/src/main/resources/db/migration/V1__add_gpu_fields_to_skus.sql
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

After applying the migration, verify the changes:

```sql
-- Check if columns were added
\d skus

-- Verify indexes
\di idx_skus_*

-- Test chipset constraint
INSERT INTO skus (sku_code, product_name, category, current_stock, safe_stock, daily_consumption_rate, chipset)
VALUES ('TEST-001', 'Test GPU', '그래픽카드', 10, 5, 1.0, 'RTX 4070');

-- This should fail (invalid chipset)
INSERT INTO skus (sku_code, product_name, category, current_stock, safe_stock, daily_consumption_rate, chipset)
VALUES ('TEST-002', 'Test GPU', '그래픽카드', 10, 5, 1.0, 'RTX 3080');
```

## Rollback

If you need to rollback the migration:

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

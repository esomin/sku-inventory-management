-- Migration script to create price_logs table
-- Version: V2
-- Description: Create price_logs table for storing GPU price history from multiple sources

-- Create price_logs table
CREATE TABLE IF NOT EXISTS price_logs (
    id BIGSERIAL PRIMARY KEY,
    sku_id BIGINT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    recorded_at TIMESTAMP NOT NULL,
    source_url VARCHAR(500),
    source_name VARCHAR(50) NOT NULL DEFAULT '다나와',
    price_change_pct DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraint
    CONSTRAINT fk_price_logs_sku
        FOREIGN KEY (sku_id)
        REFERENCES skus(id)
        ON DELETE CASCADE,
    
    -- Check constraint for source_name
    CONSTRAINT check_source_name
        CHECK (source_name IN ('다나와', '에누리')),
    
    -- Unique constraint to prevent duplicate records
    CONSTRAINT unique_price_log
        UNIQUE (sku_id, source_name, recorded_at)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_price_logs_sku_recorded 
    ON price_logs(sku_id, recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_price_logs_recorded 
    ON price_logs(recorded_at DESC);

CREATE INDEX IF NOT EXISTS idx_price_logs_sku_source 
    ON price_logs(sku_id, source_name);

-- Add comments to document the purpose of columns
COMMENT ON TABLE price_logs IS 'Historical price data for GPU products from multiple sources';
COMMENT ON COLUMN price_logs.sku_id IS 'Reference to the SKU in skus table';
COMMENT ON COLUMN price_logs.price IS 'Price in KRW at the time of recording';
COMMENT ON COLUMN price_logs.recorded_at IS 'Timestamp when the price was recorded from the source';
COMMENT ON COLUMN price_logs.source_url IS 'URL of the source page where price was found';
COMMENT ON COLUMN price_logs.source_name IS 'Name of the price source (다나와 or 에누리)';
COMMENT ON COLUMN price_logs.price_change_pct IS 'Week-over-week price change percentage';
COMMENT ON COLUMN price_logs.created_at IS 'Timestamp when the record was inserted into database';

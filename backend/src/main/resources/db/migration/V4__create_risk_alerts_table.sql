-- Migration script to create risk_alerts table
-- Version: V4
-- Description: Create risk_alerts table for storing inventory risk alerts based on price and sentiment analysis

-- Create risk_alerts table
CREATE TABLE IF NOT EXISTS risk_alerts (
    id BIGSERIAL PRIMARY KEY,
    sku_id BIGINT NOT NULL,
    risk_index DECIMAL(10, 2) NOT NULL,
    alert_message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged BOOLEAN DEFAULT FALSE,
    threshold DECIMAL(10, 2),
    contributing_factors JSONB,
    
    -- Foreign key constraint
    CONSTRAINT fk_risk_alerts_sku
        FOREIGN KEY (sku_id)
        REFERENCES skus(id)
        ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_risk_alerts_sku_created 
    ON risk_alerts(sku_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_risk_alerts_acknowledged 
    ON risk_alerts(acknowledged, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_risk_alerts_created 
    ON risk_alerts(created_at DESC);

-- Add comments to document the purpose of columns
COMMENT ON TABLE risk_alerts IS 'Inventory risk alerts generated when risk index exceeds threshold';
COMMENT ON COLUMN risk_alerts.sku_id IS 'Reference to the SKU in skus table';
COMMENT ON COLUMN risk_alerts.risk_index IS 'Calculated risk index value';
COMMENT ON COLUMN risk_alerts.alert_message IS 'Human-readable alert message describing the risk';
COMMENT ON COLUMN risk_alerts.created_at IS 'Timestamp when the alert was generated';
COMMENT ON COLUMN risk_alerts.acknowledged IS 'Whether the alert has been acknowledged by user';
COMMENT ON COLUMN risk_alerts.threshold IS 'Risk threshold value that triggered this alert';
COMMENT ON COLUMN risk_alerts.contributing_factors IS 'JSON object containing factors that contributed to the risk (price change, sentiment, etc.)';

-- Migration script to add GPU-specific fields to skus table
-- Version: V1
-- Description: Add chipset, brand, model_name, vram, is_oc columns and indexes

-- Add GPU-specific columns to skus table
ALTER TABLE skus
ADD COLUMN IF NOT EXISTS chipset VARCHAR(50),
ADD COLUMN IF NOT EXISTS brand VARCHAR(50),
ADD COLUMN IF NOT EXISTS model_name VARCHAR(200),
ADD COLUMN IF NOT EXISTS vram VARCHAR(10),
ADD COLUMN IF NOT EXISTS is_oc BOOLEAN DEFAULT FALSE;

-- Add check constraint for chipset to ensure only RTX 4070 series
ALTER TABLE skus
ADD CONSTRAINT check_chipset_rtx_4070_series
CHECK (
    chipset IS NULL OR
    chipset IN (
        'RTX 4070',
        'RTX 4070 Super',
        'RTX 4070 Ti',
        'RTX 4070 Ti Super'
    )
);

-- Add check constraint for vram format (digits + GB)
ALTER TABLE skus
ADD CONSTRAINT check_vram_format
CHECK (
    vram IS NULL OR
    vram ~ '^\d+GB$'
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_skus_chipset ON skus(chipset);
CREATE INDEX IF NOT EXISTS idx_skus_brand ON skus(brand);
CREATE INDEX IF NOT EXISTS idx_skus_chipset_brand ON skus(chipset, brand);

-- Add comment to document the purpose of new columns
COMMENT ON COLUMN skus.chipset IS 'GPU chipset model (RTX 4070 series only)';
COMMENT ON COLUMN skus.brand IS 'GPU manufacturer brand (ASUS, MSI, etc.)';
COMMENT ON COLUMN skus.model_name IS 'GPU model lineup name (TUF, Gaming X, Dual, etc.)';
COMMENT ON COLUMN skus.vram IS 'VRAM capacity in format: digits+GB (e.g., 12GB, 16GB)';
COMMENT ON COLUMN skus.is_oc IS 'Whether the GPU is overclocked';

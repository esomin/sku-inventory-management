-- Migration script to create market_signals table
-- Version: V3
-- Description: Create market_signals table for storing Reddit community signals and sentiment data

-- Create market_signals table
CREATE TABLE IF NOT EXISTS market_signals (
    id BIGSERIAL PRIMARY KEY,
    keyword VARCHAR(100) NOT NULL,
    sentiment_score DECIMAL(5, 2),
    mention_count INTEGER NOT NULL DEFAULT 1,
    date DATE NOT NULL,
    post_title TEXT NOT NULL,
    post_url VARCHAR(500),
    subreddit VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Check constraint for mention_count
    CONSTRAINT check_mention_count_positive
        CHECK (mention_count > 0),
    
    -- Unique constraint to prevent duplicate signals
    CONSTRAINT unique_market_signal
        UNIQUE (keyword, date, post_url)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_market_signals_keyword_date 
    ON market_signals(keyword, date DESC);

CREATE INDEX IF NOT EXISTS idx_market_signals_date 
    ON market_signals(date DESC);

CREATE INDEX IF NOT EXISTS idx_market_signals_subreddit 
    ON market_signals(subreddit, date DESC);

-- Add comments to document the purpose of columns
COMMENT ON TABLE market_signals IS 'Community signals and sentiment data from Reddit';
COMMENT ON COLUMN market_signals.keyword IS 'Target keyword found in the post (e.g., "New Release", "Price Drop")';
COMMENT ON COLUMN market_signals.sentiment_score IS 'Calculated sentiment score based on keyword weights';
COMMENT ON COLUMN market_signals.mention_count IS 'Number of times the keyword was mentioned (counted once per post)';
COMMENT ON COLUMN market_signals.date IS 'Date when the signal was recorded';
COMMENT ON COLUMN market_signals.post_title IS 'Title of the Reddit post';
COMMENT ON COLUMN market_signals.post_url IS 'URL of the Reddit post';
COMMENT ON COLUMN market_signals.subreddit IS 'Subreddit where the post was found (e.g., "nvidia", "pcmasterrace")';
COMMENT ON COLUMN market_signals.created_at IS 'Timestamp when the record was inserted into database';

-- TG-Trade Suite Database Schema (Essential tables only)

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    daily_analyses_used INTEGER DEFAULT 0,
    daily_reset_date DATE DEFAULT CURRENT_DATE,
    purchased_analyses INTEGER DEFAULT 0,
    total_analyses INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

-- Chart analyses table
CREATE TABLE IF NOT EXISTS chart_analyses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    image_path TEXT,
    analysis_json JSONB,
    analysis_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_time FLOAT DEFAULT 0,
    ai_confidence FLOAT DEFAULT 0,
    share_id VARCHAR(255) UNIQUE
);

-- Simple payments table (for Tether only for now)
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    payment_method VARCHAR(20) DEFAULT 'tether',
    amount_usd DECIMAL(10, 2),
    tether_transaction_hash VARCHAR(255),
    tether_wallet_address VARCHAR(255),
    analyses_purchased INTEGER,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Usage logs
CREATE TABLE IF NOT EXISTS usage_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_chart_analyses_user_id ON chart_analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);

-- Insert system defaults
INSERT INTO users (telegram_id, username, first_name) 
VALUES (0, 'system', 'System') 
ON CONFLICT (telegram_id) DO NOTHING;


-- Function Calling Database Setup
-- Run this script in your PostgreSQL database

-- Create function_call_logs table
CREATE TABLE IF NOT EXISTS function_call_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL,
    business_id VARCHAR(255) NOT NULL,
    function_name VARCHAR(100) NOT NULL,
    arguments JSONB,
    response TEXT,
    execution_time_ms INTEGER,
    success BOOLEAN DEFAULT false,
    error_message TEXT,
    cached BOOLEAN DEFAULT false,
    fallback_used BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create function_performance_stats table
CREATE TABLE IF NOT EXISTS function_performance_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id VARCHAR(255) NOT NULL,
    function_name VARCHAR(100) NOT NULL,
    date DATE DEFAULT CURRENT_DATE,
    total_calls INTEGER DEFAULT 0,
    successful_calls INTEGER DEFAULT 0,
    failed_calls INTEGER DEFAULT 0,
    avg_execution_time_ms FLOAT DEFAULT 0,
    cache_hit_rate FLOAT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_function_logs_business_id ON function_call_logs(business_id);
CREATE INDEX IF NOT EXISTS idx_function_logs_session_id ON function_call_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_function_logs_function_name ON function_call_logs(function_name);
CREATE INDEX IF NOT EXISTS idx_function_logs_created_at ON function_call_logs(created_at);

CREATE INDEX IF NOT EXISTS idx_function_stats_business_id ON function_performance_stats(business_id);
CREATE INDEX IF NOT EXISTS idx_function_stats_function_name ON function_performance_stats(function_name);
CREATE INDEX IF NOT EXISTS idx_function_stats_date ON function_performance_stats(date);

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON function_call_logs TO your_app_user;
-- GRANT ALL PRIVILEGES ON function_performance_stats TO your_app_user;

COMMIT;

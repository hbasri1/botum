-- Function Calling Schema Extensions
-- Migration script for adding function calling support to the database

-- Function Call Logs Table
-- Tracks all function calls made through the Gemini function calling system
CREATE TABLE IF NOT EXISTS function_call_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL,
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    function_name VARCHAR(100) NOT NULL,
    arguments JSONB NOT NULL,
    response TEXT,
    execution_time_ms INTEGER,
    success BOOLEAN DEFAULT false,
    error_message TEXT,
    cached BOOLEAN DEFAULT false,
    fallback_used BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Function Performance Stats Table
-- Aggregated performance metrics for function calls per business per day
CREATE TABLE IF NOT EXISTS function_performance_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    function_name VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    total_calls INTEGER DEFAULT 0,
    successful_calls INTEGER DEFAULT 0,
    total_execution_time_ms BIGINT DEFAULT 0,
    cache_hits INTEGER DEFAULT 0,
    errors INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Unique constraint for function performance stats (one record per business/function/date)
ALTER TABLE function_performance_stats 
ADD CONSTRAINT unique_business_function_date 
UNIQUE(business_id, function_name, date);

-- Indexes for optimal query performance

-- Function Call Logs Indexes
CREATE INDEX IF NOT EXISTS idx_function_call_logs_session ON function_call_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_function_call_logs_business ON function_call_logs(business_id);
CREATE INDEX IF NOT EXISTS idx_function_call_logs_function ON function_call_logs(function_name);
CREATE INDEX IF NOT EXISTS idx_function_call_logs_created ON function_call_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_function_call_logs_success ON function_call_logs(success);
CREATE INDEX IF NOT EXISTS idx_function_call_logs_business_function ON function_call_logs(business_id, function_name);
CREATE INDEX IF NOT EXISTS idx_function_call_logs_business_created ON function_call_logs(business_id, created_at);

-- Function Performance Stats Indexes
CREATE INDEX IF NOT EXISTS idx_function_stats_business_date ON function_performance_stats(business_id, date);
CREATE INDEX IF NOT EXISTS idx_function_stats_function ON function_performance_stats(function_name);
CREATE INDEX IF NOT EXISTS idx_function_stats_date ON function_performance_stats(date);
CREATE INDEX IF NOT EXISTS idx_function_stats_business_function ON function_performance_stats(business_id, function_name);

-- Trigger function for updating updated_at column
CREATE OR REPLACE FUNCTION update_function_stats_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for function_performance_stats updated_at
CREATE TRIGGER update_function_performance_stats_updated_at 
    BEFORE UPDATE ON function_performance_stats 
    FOR EACH ROW EXECUTE FUNCTION update_function_stats_updated_at();

-- Comments for documentation
COMMENT ON TABLE function_call_logs IS 'Logs all function calls made through Gemini function calling system';
COMMENT ON TABLE function_performance_stats IS 'Aggregated daily performance metrics for function calls per business';

COMMENT ON COLUMN function_call_logs.session_id IS 'Session ID from the user interaction';
COMMENT ON COLUMN function_call_logs.business_id IS 'Business that owns this function call';
COMMENT ON COLUMN function_call_logs.function_name IS 'Name of the function called (getProductInfo, getGeneralInfo)';
COMMENT ON COLUMN function_call_logs.arguments IS 'JSON arguments passed to the function';
COMMENT ON COLUMN function_call_logs.response IS 'Response returned by the function';
COMMENT ON COLUMN function_call_logs.execution_time_ms IS 'Time taken to execute the function in milliseconds';
COMMENT ON COLUMN function_call_logs.success IS 'Whether the function call was successful';
COMMENT ON COLUMN function_call_logs.error_message IS 'Error message if function call failed';
COMMENT ON COLUMN function_call_logs.cached IS 'Whether the response was served from cache';
COMMENT ON COLUMN function_call_logs.fallback_used IS 'Whether fallback to intent detection was used';

COMMENT ON COLUMN function_performance_stats.business_id IS 'Business ID for the performance stats';
COMMENT ON COLUMN function_performance_stats.function_name IS 'Function name for the stats';
COMMENT ON COLUMN function_performance_stats.date IS 'Date for the aggregated stats';
COMMENT ON COLUMN function_performance_stats.total_calls IS 'Total number of function calls for this date';
COMMENT ON COLUMN function_performance_stats.successful_calls IS 'Number of successful function calls';
COMMENT ON COLUMN function_performance_stats.total_execution_time_ms IS 'Total execution time for all calls in milliseconds';
COMMENT ON COLUMN function_performance_stats.cache_hits IS 'Number of cache hits for this function';
COMMENT ON COLUMN function_performance_stats.errors IS 'Number of errors for this function';
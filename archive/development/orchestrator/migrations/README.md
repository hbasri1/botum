# Database Migrations

This directory contains database migration scripts for the orchestrator system.

## Function Calling Migration (001)

The function calling migration adds support for Gemini function calling feature by creating two new tables:

### Tables Created

1. **function_call_logs** - Tracks all function calls made through the Gemini function calling system
   - Logs function name, arguments, response, execution time
   - Tracks success/failure, caching, and fallback usage
   - Indexed for optimal query performance

2. **function_performance_stats** - Aggregated daily performance metrics per business
   - Daily statistics for function call performance
   - Success rates, execution times, cache hit rates
   - Error tracking and analysis

### Usage

#### Apply Migration
```bash
cd orchestrator/migrations
python apply_function_calling_migration.py apply
```

#### Rollback Migration
```bash
cd orchestrator/migrations
python apply_function_calling_migration.py rollback
```

### Requirements

- Python 3.7+
- asyncpg library
- PostgreSQL database with existing orchestrator schema
- Proper database configuration in `config/settings.py`

### Migration Files

- `001_function_calling_schema.sql` - SQL schema definition
- `apply_function_calling_migration.py` - Python migration script

### Indexes Created

The migration creates optimized indexes for:
- Session-based queries
- Business-specific analytics
- Function performance analysis
- Time-based reporting
- Success/failure tracking

### Verification

The migration script automatically verifies:
- Table creation success
- Index creation
- Constraint application
- Trigger setup

### Notes

- Migration is idempotent (safe to run multiple times)
- Rollback removes all function calling related tables and indexes
- Migration logs are recorded in the interactions table
- All foreign key constraints are properly maintained
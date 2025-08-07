#!/usr/bin/env python3
"""
Function Calling Database Migration Script
Applies the function calling schema extensions to the existing database.
"""

import os
import sys
import asyncio
import asyncpg
from datetime import datetime

# Add the parent directory to the path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import Settings

async def apply_migration():
    """Apply the function calling migration to the database"""
    
    settings = Settings()
    
    # Read the migration SQL file
    migration_file = os.path.join(os.path.dirname(__file__), "001_function_calling_schema.sql")
    
    if not os.path.exists(migration_file):
        print(f"Error: Migration file not found: {migration_file}")
        return False
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    try:
        # Connect to the database
        print("Connecting to database...")
        conn = await asyncpg.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name
        )
        
        print("Connected successfully!")
        
        # Execute the migration
        print("Applying function calling schema migration...")
        await conn.execute(migration_sql)
        
        print("Migration applied successfully!")
        
        # Verify the tables were created
        print("Verifying table creation...")
        
        # Check function_call_logs table
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'function_call_logs'
            );
        """)
        
        if result:
            print("✓ function_call_logs table created successfully")
        else:
            print("✗ function_call_logs table creation failed")
            return False
        
        # Check function_performance_stats table
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'function_performance_stats'
            );
        """)
        
        if result:
            print("✓ function_performance_stats table created successfully")
        else:
            print("✗ function_performance_stats table creation failed")
            return False
        
        # Check indexes
        print("Verifying indexes...")
        
        indexes_to_check = [
            'idx_function_call_logs_session',
            'idx_function_call_logs_business',
            'idx_function_call_logs_function',
            'idx_function_call_logs_created',
            'idx_function_stats_business_date',
            'idx_function_stats_function'
        ]
        
        for index_name in indexes_to_check:
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM pg_indexes 
                    WHERE indexname = $1
                );
            """, index_name)
            
            if result:
                print(f"✓ Index {index_name} created successfully")
            else:
                print(f"✗ Index {index_name} creation failed")
        
        # Log the migration
        await conn.execute("""
            INSERT INTO interactions (
                id, request_id, session_id, user_id, business_id, 
                platform, user_message, llm_response, final_response
            ) VALUES (
                gen_random_uuid()::text, 'migration', 'system', 'system', 'test-business-1',
                'system', 'Function calling migration applied', '{}', 
                'Function calling schema migration applied successfully at ' || $1
            )
        """, datetime.utcnow().isoformat())
        
        await conn.close()
        print("Database connection closed.")
        
        return True
        
    except Exception as e:
        print(f"Error applying migration: {str(e)}")
        return False

async def rollback_migration():
    """Rollback the function calling migration"""
    
    settings = Settings()
    
    rollback_sql = """
    -- Drop function calling tables and indexes
    DROP TABLE IF EXISTS function_performance_stats CASCADE;
    DROP TABLE IF EXISTS function_call_logs CASCADE;
    
    -- Drop function calling specific indexes (if they exist independently)
    DROP INDEX IF EXISTS idx_function_call_logs_session;
    DROP INDEX IF EXISTS idx_function_call_logs_business;
    DROP INDEX IF EXISTS idx_function_call_logs_function;
    DROP INDEX IF EXISTS idx_function_call_logs_created;
    DROP INDEX IF EXISTS idx_function_call_logs_success;
    DROP INDEX IF EXISTS idx_function_call_logs_business_function;
    DROP INDEX IF EXISTS idx_function_call_logs_business_created;
    DROP INDEX IF EXISTS idx_function_stats_business_date;
    DROP INDEX IF EXISTS idx_function_stats_function;
    DROP INDEX IF EXISTS idx_function_stats_date;
    DROP INDEX IF EXISTS idx_function_stats_business_function;
    
    -- Drop trigger function
    DROP FUNCTION IF EXISTS update_function_stats_updated_at() CASCADE;
    """
    
    try:
        # Connect to the database
        print("Connecting to database for rollback...")
        conn = await asyncpg.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name
        )
        
        print("Connected successfully!")
        
        # Execute the rollback
        print("Rolling back function calling schema migration...")
        await conn.execute(rollback_sql)
        
        print("Rollback completed successfully!")
        
        await conn.close()
        print("Database connection closed.")
        
        return True
        
    except Exception as e:
        print(f"Error during rollback: {str(e)}")
        return False

def main():
    """Main function to handle command line arguments"""
    
    if len(sys.argv) < 2:
        print("Usage: python apply_function_calling_migration.py [apply|rollback]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "apply":
        print("Applying function calling migration...")
        success = asyncio.run(apply_migration())
        if success:
            print("Migration completed successfully!")
            sys.exit(0)
        else:
            print("Migration failed!")
            sys.exit(1)
    
    elif command == "rollback":
        print("Rolling back function calling migration...")
        success = asyncio.run(rollback_migration())
        if success:
            print("Rollback completed successfully!")
            sys.exit(0)
        else:
            print("Rollback failed!")
            sys.exit(1)
    
    else:
        print("Invalid command. Use 'apply' or 'rollback'")
        sys.exit(1)

if __name__ == "__main__":
    main()
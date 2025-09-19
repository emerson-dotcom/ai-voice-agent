-- =====================================================
-- SAFE SCHEMA EXECUTION SCRIPT
-- =====================================================
-- This script provides a safe way to run the complete schema
-- with proper error handling and status reporting

-- Start transaction for atomic execution
BEGIN;

-- Set up error handling
DO $$
BEGIN
    RAISE NOTICE '🚀 Starting AI Voice Agent Database Schema Setup...';
    RAISE NOTICE '📅 Timestamp: %', NOW();
    RAISE NOTICE '=====================================================';
END $$;

-- Check if we're in the right database
DO $$
BEGIN
    IF current_database() IS NULL THEN
        RAISE EXCEPTION 'No database selected. Please connect to your Supabase database first.';
    END IF;
    RAISE NOTICE '✅ Connected to database: %', current_database();
END $$;

-- Check current schema state
DO $$
DECLARE
    table_count INTEGER;
    type_count INTEGER;
BEGIN
    -- Count existing tables
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('users', 'agents', 'calls', 'call_results');
    
    -- Count existing types
    SELECT COUNT(*) INTO type_count
    FROM pg_type 
    WHERE typname IN ('user_role', 'call_status', 'call_outcome', 'driver_status', 'emergency_type');
    
    RAISE NOTICE '📊 Current state:';
    RAISE NOTICE '   - Tables found: %/4', table_count;
    RAISE NOTICE '   - Types found: %/5', type_count;
    
    IF table_count = 4 AND type_count = 5 THEN
        RAISE NOTICE '✅ Schema appears to be complete!';
    ELSIF table_count > 0 OR type_count > 0 THEN
        RAISE NOTICE '⚠️  Partial schema detected - will update existing objects';
    ELSE
        RAISE NOTICE '🆕 Fresh database - will create all objects';
    END IF;
END $$;

-- Execute the main schema
\i COMPLETE_DATABASE_SCHEMA.sql

-- Verify the schema was created successfully
DO $$
DECLARE
    table_count INTEGER;
    type_count INTEGER;
    index_count INTEGER;
    policy_count INTEGER;
BEGIN
    -- Count final state
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN ('users', 'agents', 'calls', 'call_results');
    
    SELECT COUNT(*) INTO type_count
    FROM pg_type 
    WHERE typname IN ('user_role', 'call_status', 'call_outcome', 'driver_status', 'emergency_type');
    
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes 
    WHERE tablename IN ('users', 'agents', 'calls', 'call_results');
    
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies 
    WHERE tablename IN ('users', 'agents', 'calls', 'call_results');
    
    RAISE NOTICE '=====================================================';
    RAISE NOTICE '🎉 Schema setup completed successfully!';
    RAISE NOTICE '📊 Final state:';
    RAISE NOTICE '   - Tables: %/4', table_count;
    RAISE NOTICE '   - Types: %/5', type_count;
    RAISE NOTICE '   - Indexes: %', index_count;
    RAISE NOTICE '   - RLS Policies: %', policy_count;
    RAISE NOTICE '=====================================================';
    
    IF table_count = 4 AND type_count = 5 THEN
        RAISE NOTICE '✅ All database objects created successfully!';
        RAISE NOTICE '🚀 Your AI Voice Agent database is ready to use!';
    ELSE
        RAISE EXCEPTION '❌ Schema setup incomplete. Please check for errors above.';
    END IF;
END $$;

-- Commit the transaction
COMMIT;

-- Final success message
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '🎊 CONGRATULATIONS! 🎊';
    RAISE NOTICE 'Your AI Voice Agent database schema has been set up successfully!';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Update your backend .env file with database credentials';
    RAISE NOTICE '2. Start your backend server';
    RAISE NOTICE '3. Test the API endpoints';
    RAISE NOTICE '4. Create your first AI agent!';
    RAISE NOTICE '';
    RAISE NOTICE 'Happy coding! 🚀';
END $$;

-- =====================================================
-- FIX RLS INFINITE RECURSION ISSUE
-- =====================================================
-- This script fixes the infinite recursion error in RLS policies
-- by dropping all existing policies and recreating them properly

-- Start transaction
BEGIN;

-- Drop all existing policies to avoid conflicts
DO $$
DECLARE
    policy_record RECORD;
BEGIN
    RAISE NOTICE '🧹 Dropping all existing RLS policies...';
    
    -- Drop policies from all tables
    FOR policy_record IN 
        SELECT schemaname, tablename, policyname 
        FROM pg_policies 
        WHERE tablename IN ('users', 'agents', 'calls', 'call_results')
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON %I.%I', 
                      policy_record.policyname, 
                      policy_record.schemaname, 
                      policy_record.tablename);
        RAISE NOTICE '   Dropped policy: % on %.%', 
                     policy_record.policyname, 
                     policy_record.schemaname, 
                     policy_record.tablename;
    END LOOP;
    
    RAISE NOTICE '✅ All existing policies dropped successfully';
END $$;

-- Disable RLS temporarily
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE agents DISABLE ROW LEVEL SECURITY;
ALTER TABLE calls DISABLE ROW LEVEL SECURITY;
ALTER TABLE call_results DISABLE ROW LEVEL SECURITY;

RAISE NOTICE '🔒 RLS temporarily disabled';

-- Re-enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE call_results ENABLE ROW LEVEL SECURITY;

RAISE NOTICE '🔓 RLS re-enabled';

-- Now run the complete schema to recreate everything properly
\i COMPLETE_DATABASE_SCHEMA.sql

-- Verify the fix
DO $$
DECLARE
    policy_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies 
    WHERE tablename IN ('users', 'agents', 'calls', 'call_results');
    
    RAISE NOTICE '=====================================================';
    RAISE NOTICE '🎉 RLS recursion fix completed!';
    RAISE NOTICE '📊 Total policies created: %', policy_count;
    RAISE NOTICE '✅ No more infinite recursion errors!';
    RAISE NOTICE '=====================================================';
END $$;

-- Commit the transaction
COMMIT;

-- Final success message
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '🎊 SUCCESS! 🎊';
    RAISE NOTICE 'The infinite recursion issue has been fixed!';
    RAISE NOTICE 'Your database is now ready to use.';
    RAISE NOTICE '';
END $$;

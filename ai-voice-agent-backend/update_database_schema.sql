-- =====================================================
-- AI Voice Agent Database Schema Update
-- Run this in Supabase SQL Editor
-- =====================================================

-- Add retell_llm_id column to agents table
-- This column stores the Retell AI LLM ID for each agent

DO $$ 
BEGIN
    -- Check if retell_llm_id column exists, if not add it
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'agents' 
        AND column_name = 'retell_llm_id'
    ) THEN
        -- Add the column
        ALTER TABLE agents ADD COLUMN retell_llm_id TEXT;
        
        -- Add index for better performance
        CREATE INDEX IF NOT EXISTS idx_agents_retell_llm_id ON agents(retell_llm_id);
        
        -- Add comment
        COMMENT ON COLUMN agents.retell_llm_id IS 'Retell AI LLM ID associated with this agent';
        
        RAISE NOTICE '✅ Added retell_llm_id column to agents table';
    ELSE
        RAISE NOTICE 'ℹ️ retell_llm_id column already exists in agents table';
    END IF;
END $$;

-- Update existing agents with retell_llm_id if they have retell_agent_id
-- This is a one-time migration for existing data
DO $$
DECLARE
    agent_record RECORD;
    llm_id TEXT;
BEGIN
    -- Loop through agents that have retell_agent_id but no retell_llm_id
    FOR agent_record IN 
        SELECT id, retell_agent_id, name 
        FROM agents 
        WHERE retell_agent_id IS NOT NULL 
        AND retell_llm_id IS NULL
    LOOP
        -- Try to get the LLM ID from Retell AI
        -- Note: This would require API calls, so we'll set a placeholder
        -- In practice, you might need to manually update these or use a script
        
        RAISE NOTICE 'Agent % (%) has retell_agent_id but no retell_llm_id', 
                     agent_record.name, agent_record.id;
        
        -- For now, we'll leave retell_llm_id as NULL for existing agents
        -- New agents will have both retell_agent_id and retell_llm_id
    END LOOP;
    
    RAISE NOTICE '✅ Migration check completed for existing agents';
END $$;

-- Verify the schema update
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'agents' 
AND column_name IN ('retell_agent_id', 'retell_llm_id')
ORDER BY column_name;

-- Show current agents and their Retell AI IDs
SELECT 
    id,
    name,
    retell_agent_id,
    retell_llm_id,
    is_active,
    created_at
FROM agents 
ORDER BY created_at DESC;

-- =====================================================
-- Additional Indexes for Performance
-- =====================================================

-- Create composite index for faster queries
CREATE INDEX IF NOT EXISTS idx_agents_retell_ids ON agents(retell_agent_id, retell_llm_id);

-- Create index for active agents with Retell IDs
CREATE INDEX IF NOT EXISTS idx_agents_active_retell ON agents(is_active, retell_agent_id) 
WHERE retell_agent_id IS NOT NULL;

-- =====================================================
-- RLS Policy Updates (if needed)
-- =====================================================

-- The existing RLS policies should already cover the new column
-- since they use SELECT * and the column will be included automatically

-- Verify RLS policies are working
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies 
WHERE tablename = 'agents';

-- =====================================================
-- Final Verification
-- =====================================================

-- Check table structure (replacing \d command)
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default,
    character_maximum_length
FROM information_schema.columns 
WHERE table_name = 'agents' 
ORDER BY ordinal_position;

-- Check indexes
SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'agents'
ORDER BY indexname;

-- Final success message
DO $$
BEGIN
    RAISE NOTICE '🎉 Database schema update completed successfully!';
    RAISE NOTICE '📝 Next steps:';
    RAISE NOTICE '   1. Test agent creation to ensure retell_llm_id is populated';
    RAISE NOTICE '   2. Test agent updates to ensure LLM updates work';
    RAISE NOTICE '   3. Test agent deletion to ensure both agent and LLM are deleted';
END $$;

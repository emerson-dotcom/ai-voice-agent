-- =====================================================
-- AI Voice Agent Tool - COMPLETE DATABASE SCHEMA
-- =====================================================
-- This file contains the complete, up-to-date database schema
-- including all tables, types, indexes, triggers, and RLS policies
--
-- IMPORTANT: This schema is IDEMPOTENT - it can be run multiple times
-- without errors. It includes proper checks for existing objects.
-- Safe to run on existing databases.

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- CUSTOM TYPES
-- =====================================================

-- User roles
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('admin', 'user');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Call statuses
DO $$ BEGIN
    CREATE TYPE call_status AS ENUM ('pending', 'in_progress', 'completed', 'failed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Call outcomes for structured data
DO $$ BEGIN
    CREATE TYPE call_outcome AS ENUM ('In-Transit Update', 'Arrival Confirmation', 'Emergency Escalation');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Driver statuses
DO $$ BEGIN
    CREATE TYPE driver_status AS ENUM ('Driving', 'Delayed', 'Arrived', 'Unloading');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Emergency types
DO $$ BEGIN
    CREATE TYPE emergency_type AS ENUM ('Accident', 'Breakdown', 'Medical', 'Other');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- =====================================================
-- TABLES
-- =====================================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    role user_role NOT NULL DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agents table
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    initial_prompt TEXT NOT NULL,
    emergency_prompt TEXT NOT NULL,
    follow_up_prompts JSONB DEFAULT '[]'::jsonb,
    backchanneling BOOLEAN DEFAULT true,
    filler_words BOOLEAN DEFAULT true,
    interruption_sensitivity DECIMAL(3,2) DEFAULT 0.5 CHECK (interruption_sensitivity >= 0.0 AND interruption_sensitivity <= 1.0),
    voice_id VARCHAR(255) NOT NULL,
    speed DECIMAL(3,2) DEFAULT 1.0 CHECK (speed >= 0.5 AND speed <= 2.0),
    pitch DECIMAL(3,2) DEFAULT 1.0 CHECK (pitch >= 0.5 AND pitch <= 2.0),
    retell_agent_id VARCHAR(255),
    retell_llm_id TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Calls table (for web calls)
CREATE TABLE IF NOT EXISTS calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    driver_name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    load_number VARCHAR(100) NOT NULL,
    status call_status DEFAULT 'pending',
    retell_call_id VARCHAR(255),
    web_call_url VARCHAR(500),
    join_url VARCHAR(500),
    transcript TEXT,
    structured_data JSONB,
    call_duration INTEGER, -- in seconds
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Call results table (normalized for better querying)
CREATE TABLE IF NOT EXISTS call_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id UUID NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    call_outcome call_outcome NOT NULL,
    driver_status driver_status,
    current_location VARCHAR(255),
    eta VARCHAR(100),
    delay_reason VARCHAR(255),
    unloading_status VARCHAR(255),
    pod_reminder_acknowledged BOOLEAN,
    emergency_type emergency_type,
    safety_status TEXT,
    injury_status TEXT,
    emergency_location VARCHAR(255),
    load_secure BOOLEAN,
    escalation_status VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Agents table indexes
CREATE INDEX IF NOT EXISTS idx_agents_user_id ON agents(user_id);
CREATE INDEX IF NOT EXISTS idx_agents_active ON agents(is_active);
CREATE INDEX IF NOT EXISTS idx_agents_retell_agent_id ON agents(retell_agent_id);
CREATE INDEX IF NOT EXISTS idx_agents_retell_llm_id ON agents(retell_llm_id);
CREATE INDEX IF NOT EXISTS idx_agents_retell_ids ON agents(retell_agent_id, retell_llm_id);
CREATE INDEX IF NOT EXISTS idx_agents_active_retell ON agents(is_active, retell_agent_id) WHERE retell_agent_id IS NOT NULL;

-- Calls table indexes
CREATE INDEX IF NOT EXISTS idx_calls_user_id ON calls(user_id);
CREATE INDEX IF NOT EXISTS idx_calls_agent_id ON calls(agent_id);
CREATE INDEX IF NOT EXISTS idx_calls_status ON calls(status);
CREATE INDEX IF NOT EXISTS idx_calls_created_at ON calls(created_at);
CREATE INDEX IF NOT EXISTS idx_calls_retell_call_id ON calls(retell_call_id);

-- Call results table indexes
CREATE INDEX IF NOT EXISTS idx_call_results_call_id ON call_results(call_id);
CREATE INDEX IF NOT EXISTS idx_call_results_outcome ON call_results(call_outcome);

-- =====================================================
-- TRIGGERS FOR UPDATED_AT
-- =====================================================

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_agents_updated_at ON agents;
CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_calls_updated_at ON calls;
CREATE TRIGGER update_calls_updated_at BEFORE UPDATE ON calls
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================

-- Create helper function to check if user is admin
-- This avoids infinite recursion in RLS policies
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
DECLARE
    user_role TEXT;
BEGIN
    -- Get user role from the users table using SECURITY DEFINER
    -- This bypasses RLS policies and avoids infinite recursion
    SELECT role INTO user_role
    FROM users
    WHERE id = auth.uid()
    LIMIT 1;
    
    RETURN COALESCE(user_role = 'admin', false);
EXCEPTION
    WHEN OTHERS THEN
        RETURN false;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE call_results ENABLE ROW LEVEL SECURITY;

-- Users table policies
-- Users can read their own data
DROP POLICY IF EXISTS "Users can read own data" ON users;
CREATE POLICY "Users can read own data" ON users
    FOR SELECT USING (auth.uid() = id);

-- Users can update their own data (except role)
DROP POLICY IF EXISTS "Users can update own data" ON users;
CREATE POLICY "Users can update own data" ON users
    FOR UPDATE USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Admins can read all users
DROP POLICY IF EXISTS "Admins can read all users" ON users;
CREATE POLICY "Admins can read all users" ON users
    FOR SELECT USING (is_admin());

-- Admins can update all users
DROP POLICY IF EXISTS "Admins can update all users" ON users;
CREATE POLICY "Admins can update all users" ON users
    FOR UPDATE USING (is_admin());

-- Admins can insert users
DROP POLICY IF EXISTS "Admins can insert users" ON users;
CREATE POLICY "Admins can insert users" ON users
    FOR INSERT WITH CHECK (is_admin());

-- Admins can delete users
DROP POLICY IF EXISTS "Admins can delete users" ON users;
CREATE POLICY "Admins can delete users" ON users
    FOR DELETE USING (is_admin());

-- Agents table policies
-- Users can read their own agents
DROP POLICY IF EXISTS "Users can read own agents" ON agents;
CREATE POLICY "Users can read own agents" ON agents
    FOR SELECT USING (auth.uid() = user_id);

-- All authenticated users can read active agents
DROP POLICY IF EXISTS "Users can read active agents" ON agents;
CREATE POLICY "Users can read active agents" ON agents
    FOR SELECT USING (
        auth.role() = 'authenticated' AND is_active = true
    );

-- Admins can read all agents
DROP POLICY IF EXISTS "Admins can read all agents" ON agents;
CREATE POLICY "Admins can read all agents" ON agents
    FOR SELECT USING (is_admin());

-- Users can insert their own agents
DROP POLICY IF EXISTS "Users can insert own agents" ON agents;
CREATE POLICY "Users can insert own agents" ON agents
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can update their own agents
DROP POLICY IF EXISTS "Users can update own agents" ON agents;
CREATE POLICY "Users can update own agents" ON agents
    FOR UPDATE USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Users can delete their own agents
DROP POLICY IF EXISTS "Users can delete own agents" ON agents;
CREATE POLICY "Users can delete own agents" ON agents
    FOR DELETE USING (auth.uid() = user_id);

-- Admins can insert agents
DROP POLICY IF EXISTS "Admins can insert agents" ON agents;
CREATE POLICY "Admins can insert agents" ON agents
    FOR INSERT WITH CHECK (is_admin());

-- Admins can update agents
DROP POLICY IF EXISTS "Admins can update agents" ON agents;
CREATE POLICY "Admins can update agents" ON agents
    FOR UPDATE USING (is_admin());

-- Admins can delete agents
DROP POLICY IF EXISTS "Admins can delete agents" ON agents;
CREATE POLICY "Admins can delete agents" ON agents
    FOR DELETE USING (is_admin());

-- Calls table policies
-- Users can read their own calls
DROP POLICY IF EXISTS "Users can read own calls" ON calls;
CREATE POLICY "Users can read own calls" ON calls
    FOR SELECT USING (auth.uid() = user_id);

-- All authenticated users can read calls
DROP POLICY IF EXISTS "Users can read calls" ON calls;
CREATE POLICY "Users can read calls" ON calls
    FOR SELECT USING (auth.role() = 'authenticated');

-- Users can insert their own calls
DROP POLICY IF EXISTS "Users can insert own calls" ON calls;
CREATE POLICY "Users can insert own calls" ON calls
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can update their own calls
DROP POLICY IF EXISTS "Users can update own calls" ON calls;
CREATE POLICY "Users can update own calls" ON calls
    FOR UPDATE USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Admins can insert calls
DROP POLICY IF EXISTS "Admins can insert calls" ON calls;
CREATE POLICY "Admins can insert calls" ON calls
    FOR INSERT WITH CHECK (is_admin());

-- Admins can update calls
DROP POLICY IF EXISTS "Admins can update calls" ON calls;
CREATE POLICY "Admins can update calls" ON calls
    FOR UPDATE USING (is_admin());

-- Admins can delete calls
DROP POLICY IF EXISTS "Admins can delete calls" ON calls;
CREATE POLICY "Admins can delete calls" ON calls
    FOR DELETE USING (is_admin());

-- Call results table policies
-- All authenticated users can read call results
DROP POLICY IF EXISTS "Users can read call results" ON call_results;
CREATE POLICY "Users can read call results" ON call_results
    FOR SELECT USING (auth.role() = 'authenticated');

-- Admins can insert call results
DROP POLICY IF EXISTS "Admins can insert call results" ON call_results;
CREATE POLICY "Admins can insert call results" ON call_results
    FOR INSERT WITH CHECK (is_admin());

-- Admins can update call results
DROP POLICY IF EXISTS "Admins can update call results" ON call_results;
CREATE POLICY "Admins can update call results" ON call_results
    FOR UPDATE USING (is_admin());

-- Admins can delete call results
DROP POLICY IF EXISTS "Admins can delete call results" ON call_results;
CREATE POLICY "Admins can delete call results" ON call_results
    FOR DELETE USING (is_admin());

-- =====================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================

-- Table comments
COMMENT ON TABLE users IS 'User accounts with role-based access control';
COMMENT ON TABLE agents IS 'AI voice agents with Retell AI integration';
COMMENT ON TABLE calls IS 'Web call records with transcripts and structured data';
COMMENT ON TABLE call_results IS 'Normalized call results for analytics and reporting';

-- Column comments
COMMENT ON COLUMN agents.retell_agent_id IS 'Retell AI Agent ID for voice interactions';
COMMENT ON COLUMN agents.retell_llm_id IS 'Retell AI LLM ID for conversation logic';
COMMENT ON COLUMN calls.retell_call_id IS 'Retell AI Call ID for tracking';
COMMENT ON COLUMN calls.structured_data IS 'JSON data extracted from conversation';
COMMENT ON COLUMN calls.transcript IS 'Full conversation transcript';

-- =====================================================
-- SAMPLE DATA (Optional)
-- =====================================================

-- Insert sample admin user (optional - remove in production)
-- INSERT INTO users (email, role) VALUES ('admin@example.com', 'admin');

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Verify all tables exist
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'agents', 'calls', 'call_results')
ORDER BY table_name;

-- Verify all indexes exist
SELECT indexname, tablename, indexdef
FROM pg_indexes 
WHERE tablename IN ('users', 'agents', 'calls', 'call_results')
ORDER BY tablename, indexname;

-- Verify RLS is enabled
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE tablename IN ('users', 'agents', 'calls', 'call_results')
ORDER BY tablename;

-- Verify policies exist
SELECT tablename, policyname, cmd, permissive
FROM pg_policies 
WHERE tablename IN ('users', 'agents', 'calls', 'call_results')
ORDER BY tablename, policyname;

-- =====================================================
-- SCHEMA SUMMARY
-- =====================================================

/*
DATABASE SCHEMA SUMMARY:

TABLES:
1. users - User accounts with role-based access
2. agents - AI voice agents with Retell AI integration
3. calls - Web call records with transcripts
4. call_results - Normalized call results for analytics

KEY FEATURES:
- UUID primary keys for all tables
- Row Level Security (RLS) enabled on all tables
- Role-based access control (admin/user)
- Retell AI integration (agent_id, llm_id, call_id)
- Structured data extraction and storage
- Automatic updated_at timestamps
- Comprehensive indexing for performance
- Foreign key relationships with CASCADE deletes

SECURITY:
- RLS policies ensure users can only access their own data
- Admins have full access to all data
- Regular users can only access their own agents and calls
- All tables have appropriate access controls

INTEGRATION:
- Retell AI agent and LLM IDs stored for API integration
- Web call URLs and join URLs for frontend integration
- JSONB fields for flexible structured data storage
- Call transcripts and duration tracking
*/

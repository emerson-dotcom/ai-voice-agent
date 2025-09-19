-- Row Level Security (RLS) Policies for AI Voice Agent Tool
-- Enable RLS on all tables and create appropriate policies

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE call_results ENABLE ROW LEVEL SECURITY;

-- Users table policies
-- Users can read their own data
CREATE POLICY "Users can read own data" ON users
    FOR SELECT USING (auth.uid() = id);

-- Users can update their own data (except role)
CREATE POLICY "Users can update own data" ON users
    FOR UPDATE USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Admins can read all users
CREATE POLICY "Admins can read all users" ON users
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Admins can update all users
CREATE POLICY "Admins can update all users" ON users
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Agents table policies
-- All authenticated users can read active agents
CREATE POLICY "Users can read active agents" ON agents
    FOR SELECT USING (
        auth.role() = 'authenticated' AND is_active = true
    );

-- Admins can read all agents
CREATE POLICY "Admins can read all agents" ON agents
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Admins can insert agents
CREATE POLICY "Admins can insert agents" ON agents
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Admins can update agents
CREATE POLICY "Admins can update agents" ON agents
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Admins can delete agents
CREATE POLICY "Admins can delete agents" ON agents
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Calls table policies
-- All authenticated users can read calls
CREATE POLICY "Users can read calls" ON calls
    FOR SELECT USING (auth.role() = 'authenticated');

-- Admins can insert calls
CREATE POLICY "Admins can insert calls" ON calls
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Admins can update calls
CREATE POLICY "Admins can update calls" ON calls
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Admins can delete calls
CREATE POLICY "Admins can delete calls" ON calls
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Call results table policies
-- All authenticated users can read call results
CREATE POLICY "Users can read call results" ON call_results
    FOR SELECT USING (auth.role() = 'authenticated');

-- Admins can insert call results
CREATE POLICY "Admins can insert call results" ON call_results
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Admins can update call results
CREATE POLICY "Admins can update call results" ON call_results
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Admins can delete call results
CREATE POLICY "Admins can delete call results" ON call_results
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

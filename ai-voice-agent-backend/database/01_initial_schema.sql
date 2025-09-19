-- AI Voice Agent Tool Database Schema
-- Initial setup with users, agents, calls, and results tables

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom types
CREATE TYPE user_role AS ENUM ('admin', 'user');
CREATE TYPE call_status AS ENUM ('pending', 'in_progress', 'completed', 'failed');
CREATE TYPE call_outcome AS ENUM ('In-Transit Update', 'Arrival Confirmation', 'Emergency Escalation');
CREATE TYPE driver_status AS ENUM ('Driving', 'Delayed', 'Arrived', 'Unloading');
CREATE TYPE emergency_type AS ENUM ('Accident', 'Breakdown', 'Medical', 'Other');

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    role user_role NOT NULL DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agents table
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Calls table (for web calls)
CREATE TABLE calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
CREATE TABLE call_results (
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

-- Create indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_agents_active ON agents(is_active);
CREATE INDEX idx_calls_agent_id ON calls(agent_id);
CREATE INDEX idx_calls_status ON calls(status);
CREATE INDEX idx_calls_created_at ON calls(created_at);
CREATE INDEX idx_call_results_call_id ON call_results(call_id);
CREATE INDEX idx_call_results_outcome ON call_results(call_outcome);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_calls_updated_at BEFORE UPDATE ON calls
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

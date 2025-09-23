-- AI Voice Agent Complete Database Schema
-- Combined migration file for complete database setup
-- Run this in Supabase SQL Editor

-- ================================================
-- EXTENSIONS AND BASIC SETUP
-- ================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ================================================
-- CUSTOM TYPES
-- ================================================

-- Create custom types
CREATE TYPE call_status AS ENUM ('created', 'registered', 'ongoing', 'ended', 'error');
CREATE TYPE call_outcome AS ENUM ('in_transit_update', 'arrival_confirmation', 'emergency_escalation');
CREATE TYPE driver_status AS ENUM ('driving', 'delayed', 'arrived', 'unloading');
CREATE TYPE emergency_type AS ENUM ('accident', 'breakdown', 'medical', 'other');

-- ================================================
-- CORE TABLES
-- ================================================

-- Agents table - stores agent configurations
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Retell AI Configuration
    retell_llm_id VARCHAR(255),
    retell_agent_id VARCHAR(255),

    -- Agent Settings
    general_prompt TEXT NOT NULL,
    begin_message TEXT,
    voice_id VARCHAR(255) NOT NULL,
    voice_model VARCHAR(100),
    voice_temperature DECIMAL(3,2) DEFAULT 1.0,
    voice_speed DECIMAL(3,2) DEFAULT 1.0,

    -- LLM Configuration
    max_tokens INTEGER DEFAULT 200,
    temperature DECIMAL(3,2) DEFAULT 0.7,

    -- Prompt System
    system_prompt TEXT,
    greeting_message TEXT,
    initial_message TEXT,
    fallback_message TEXT,
    end_call_message TEXT,

    -- Advanced Voice Features
    enable_backchannel BOOLEAN DEFAULT true,
    backchannel_frequency DECIMAL(3,2) DEFAULT 0.8,
    backchannel_words JSONB DEFAULT '["yeah", "uh-huh", "mm-hmm"]'::jsonb,
    interruption_sensitivity DECIMAL(3,2) DEFAULT 1.0,
    responsiveness DECIMAL(3,2) DEFAULT 1.0,

    -- Conversation Control
    enable_transcription BOOLEAN DEFAULT true,
    response_delay_ms INTEGER DEFAULT 300,

    -- Configuration
    scenario_type VARCHAR(50) NOT NULL, -- 'driver_checkin' or 'emergency_protocol'
    is_active BOOLEAN DEFAULT true,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

-- Agent States table - for conversation flow states
CREATE TABLE agent_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    state_prompt TEXT NOT NULL,
    is_starting_state BOOLEAN DEFAULT false,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(agent_id, name)
);

-- Agent Tools table - for agent tools configuration
CREATE TABLE agent_tools (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    state_id UUID REFERENCES agent_states(id) ON DELETE SET NULL, -- NULL for general tools

    tool_type VARCHAR(50) NOT NULL, -- 'end_call', 'transfer_call', 'custom', etc.
    tool_name VARCHAR(255) NOT NULL,
    tool_description TEXT NOT NULL,
    tool_config JSONB DEFAULT '{}'::jsonb, -- Tool-specific configuration

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Calls table - stores call information and results
CREATE TABLE calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Retell AI Call Information
    retell_call_id VARCHAR(255) UNIQUE,
    retell_access_token TEXT,

    -- Agent and Configuration
    agent_id UUID REFERENCES agents(id),
    agent_version INTEGER DEFAULT 1,

    -- Call Context (Driver Information)
    driver_name VARCHAR(255),
    driver_phone VARCHAR(20),
    load_number VARCHAR(100),

    -- Call Status and Timing
    call_status call_status DEFAULT 'created',
    start_timestamp TIMESTAMP WITH TIME ZONE,
    end_timestamp TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,

    -- Call Content
    transcript TEXT,
    transcript_object JSONB,
    recording_url TEXT,
    public_log_url TEXT,

    -- Disconnection and Analysis
    disconnection_reason VARCHAR(100),
    call_analysis JSONB,

    -- Dynamic Variables
    retell_llm_dynamic_variables JSONB DEFAULT '{}'::jsonb,
    collected_dynamic_variables JSONB DEFAULT '{}'::jsonb,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

-- Call Results table - stores structured data extracted from calls
CREATE TABLE call_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id UUID REFERENCES calls(id) ON DELETE CASCADE,

    -- Common Fields
    call_outcome call_outcome,

    -- Driver Check-in Scenario Fields
    driver_status driver_status,
    current_location TEXT,
    eta TEXT,
    delay_reason TEXT,
    unloading_status TEXT,
    pod_reminder_acknowledged BOOLEAN,

    -- Emergency Protocol Scenario Fields
    emergency_type emergency_type,
    safety_status TEXT,
    injury_status TEXT,
    emergency_location TEXT,
    load_secure BOOLEAN,
    escalation_status TEXT,

    -- Additional extracted data
    custom_analysis_data JSONB DEFAULT '{}'::jsonb,
    confidence_score DECIMAL(3,2), -- AI extraction confidence

    -- Metadata
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    extraction_method VARCHAR(50) DEFAULT 'llm_analysis' -- How data was extracted
);

-- Load Information table - for tracking loads
CREATE TABLE loads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    load_number VARCHAR(100) UNIQUE NOT NULL,

    -- Load Details
    origin_location TEXT,
    destination_location TEXT,
    pickup_date DATE,
    delivery_date DATE,

    -- Driver Assignment
    assigned_driver_name VARCHAR(255),
    assigned_driver_phone VARCHAR(20),

    -- Load Status
    current_status VARCHAR(50) DEFAULT 'assigned',
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

-- Conversation States table - for real-time conversation state
CREATE TABLE conversation_states (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    call_id UUID REFERENCES calls(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    state VARCHAR(50) NOT NULL DEFAULT 'initializing',
    context_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit log table for tracking user actions
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ================================================
-- INDEXES
-- ================================================

-- Core indexes for better performance
CREATE INDEX idx_calls_retell_call_id ON calls(retell_call_id);
CREATE INDEX idx_calls_agent_id ON calls(agent_id);
CREATE INDEX idx_calls_created_at ON calls(created_at);
CREATE INDEX idx_calls_call_status ON calls(call_status);
CREATE INDEX idx_call_results_call_id ON call_results(call_id);
CREATE INDEX idx_call_results_call_outcome ON call_results(call_outcome);
CREATE INDEX idx_agents_scenario_type ON agents(scenario_type);
CREATE INDEX idx_agents_is_active ON agents(is_active);
CREATE INDEX idx_loads_load_number ON loads(load_number);

-- Additional indexes
CREATE UNIQUE INDEX idx_conversation_states_call_id ON conversation_states(call_id);
CREATE INDEX idx_conversation_states_state ON conversation_states(state);
CREATE INDEX idx_conversation_states_updated_at ON conversation_states(updated_at);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);

-- ================================================
-- TRIGGERS AND FUNCTIONS
-- ================================================

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_calls_updated_at BEFORE UPDATE ON calls
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Conversation states updated_at trigger
CREATE OR REPLACE FUNCTION update_conversation_states_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_conversation_states_updated_at
    BEFORE UPDATE ON conversation_states
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_states_updated_at();

-- ================================================
-- ROW LEVEL SECURITY (RLS)
-- ================================================

-- Enable RLS on all tables
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_tools ENABLE ROW LEVEL SECURITY;
ALTER TABLE calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE call_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE loads ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- ================================================
-- RLS POLICIES
-- ================================================

-- Agents policies
CREATE POLICY "Users can view all agents" ON agents FOR SELECT USING (true);
CREATE POLICY "Users can insert agents" ON agents FOR INSERT WITH CHECK (true);
CREATE POLICY "Users can update agents" ON agents FOR UPDATE USING (true);
CREATE POLICY "Admins can delete agents" ON agents
    FOR DELETE USING (COALESCE((auth.jwt() -> 'user_metadata' ->> 'role'), 'user') = 'admin');

-- Calls policies
CREATE POLICY "Users can view all calls" ON calls FOR SELECT USING (true);
CREATE POLICY "Users can insert calls" ON calls FOR INSERT WITH CHECK (true);
CREATE POLICY "Users can update calls" ON calls FOR UPDATE USING (true);
CREATE POLICY "Users can delete own calls" ON calls
    FOR DELETE USING (
        created_by = auth.uid() OR
        COALESCE((auth.jwt() -> 'user_metadata' ->> 'role'), 'user') = 'admin'
    );

-- Call results policies
CREATE POLICY "Users can view all call results" ON call_results FOR SELECT USING (true);
CREATE POLICY "Users can insert call results" ON call_results FOR INSERT WITH CHECK (true);

-- Loads policies
CREATE POLICY "Users can view all loads" ON loads FOR SELECT USING (true);
CREATE POLICY "Users can insert loads" ON loads FOR INSERT WITH CHECK (true);
CREATE POLICY "Users can update loads" ON loads FOR UPDATE USING (true);

-- Conversation states policies
CREATE POLICY "Users can view conversation states" ON conversation_states
    FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Service role can manage conversation states" ON conversation_states
    FOR ALL USING (auth.role() = 'service_role');

-- Audit logs policies
CREATE POLICY "Users can see own audit logs" ON audit_logs
    FOR SELECT USING (
        user_id = auth.uid() OR
        COALESCE((auth.jwt() -> 'user_metadata' ->> 'role'), 'user') = 'admin'
    );
CREATE POLICY "Allow inserting audit logs" ON audit_logs
    FOR INSERT WITH CHECK (true);

-- Full access policies for related tables
CREATE POLICY "Full access to agent_states" ON agent_states FOR ALL USING (true);
CREATE POLICY "Full access to agent_tools" ON agent_tools FOR ALL USING (true);

-- ================================================
-- SAMPLE DATA
-- ================================================

-- Insert sample loads
INSERT INTO loads (load_number, origin_location, destination_location, pickup_date, delivery_date, assigned_driver_name, assigned_driver_phone, current_status) VALUES
('7891-B', 'Barstow, CA', 'Phoenix, AZ', CURRENT_DATE, CURRENT_DATE + INTERVAL '2 days', 'Mike Johnson', '+1234567890', 'in_transit'),
('8829-A', 'Los Angeles, CA', 'Las Vegas, NV', CURRENT_DATE - INTERVAL '1 day', CURRENT_DATE + INTERVAL '1 day', 'Sarah Williams', '+1987654321', 'assigned'),
('9234-C', 'San Diego, CA', 'Tucson, AZ', CURRENT_DATE, CURRENT_DATE + INTERVAL '3 days', 'David Martinez', '+1555666777', 'assigned');

-- Insert Driver Check-in Agent
INSERT INTO agents (
    name,
    description,
    scenario_type,
    voice_id,
    voice_model,
    voice_temperature,
    voice_speed,
    temperature,
    max_tokens,
    general_prompt,
    begin_message,
    system_prompt,
    greeting_message,
    initial_message,
    fallback_message,
    end_call_message,
    enable_backchannel,
    backchannel_frequency,
    interruption_sensitivity,
    responsiveness,
    enable_transcription,
    response_delay_ms,
    is_active
) VALUES (
    'Driver Check-in Agent',
    'Handles end-to-end driver check-in conversations with dynamic flow based on driver status. Extracts comprehensive status information.',
    'driver_checkin',
    'sarah',
    'eleven_turbo_v2',
    0.8,
    1.0,
    0.7,
    200,
    'You are a professional logistics dispatcher calling drivers for status updates. Your mission is to conduct comprehensive end-to-end driver check-ins with dynamic conversation flow that adapts based on the driver''s current status.

CORE RESPONSIBILITIES:
- Determine driver''s current status through open-ended inquiry ("Can you give me an update on your status?")
- Gather comprehensive information about location, timing, and delivery progress
- Handle both in-transit updates and arrival confirmations in a single fluid conversation
- Extract structured data while maintaining natural conversation flow
- Detect and immediately respond to emergency situations

DYNAMIC CONVERSATION STRATEGY:
1. BEGIN: Start with open-ended status question to understand current situation
2. ADAPT: Dynamically pivot questioning based on driver''s response:
   • If DRIVING → Ask about current location, ETA, any delays or traffic issues
   • If ARRIVED → Ask about unloading status, dock assignment, expected completion time
   • If DELAYED → Identify specific delay reason and get updated ETA
   • If UNLOADING → Check progress, any detention time, POD status

COMMUNICATION EXCELLENCE:
- Maintain professional yet conversational tone throughout
- Use natural speech patterns with strategic backchannel responses ("uh-huh", "I see", "got it")
- Allow for natural interruptions and respond appropriately
- Keep questions clear, specific, and purposeful
- Show active listening with acknowledgment phrases
- Adapt pace to driver''s communication style

EMERGENCY PROTOCOL (ABSOLUTE PRIORITY):
If driver mentions ANY emergency keywords (accident, medical, breakdown, help, hurt, injured, stuck, crash, fire, smoke), immediately:
1. Ask "Are you safe? Is anyone hurt?"
2. Get exact location with landmarks/mile markers
3. Say "I''m connecting you to a human dispatcher immediately"
4. End structured conversation and escalate',

    'Hello, how can I help you today?',

    'You are a professional logistics dispatcher calling drivers for status updates. Your goal is to determine the driver''s current status and gather relevant information through natural conversation.',

    'Hi {driver_name}, this is dispatch with a check call on load {load_number}.',

    'Can you give me an update on your status?',

    'I understand. Can you tell me more about your current situation?',

    'Thank you for the update. Drive safely and have a great day!',

    true,
    0.8,
    0.8,
    0.9,
    true,
    300,
    true
);

-- Insert Emergency Protocol Agent
INSERT INTO agents (
    name,
    description,
    scenario_type,
    voice_id,
    voice_model,
    voice_temperature,
    voice_speed,
    temperature,
    max_tokens,
    general_prompt,
    begin_message,
    system_prompt,
    greeting_message,
    initial_message,
    fallback_message,
    end_call_message,
    enable_backchannel,
    backchannel_frequency,
    interruption_sensitivity,
    responsiveness,
    enable_transcription,
    response_delay_ms,
    is_active
) VALUES (
    'Emergency Protocol Agent',
    'Specialized for emergency detection during routine calls. Immediately escalates to human dispatcher when emergency is detected.',
    'emergency_protocol',
    'mark',
    'eleven_turbo_v2',
    0.5,
    1.2,
    0.5,
    150,
    'You are a logistics dispatcher with specialized emergency response training. Your critical mission is to detect emergencies during routine calls and execute immediate escalation protocols with precision and speed.

DUAL OPERATIONAL MODE:
1. ROUTINE MODE: Conduct normal driver check-ins while maintaining constant emergency vigilance
2. EMERGENCY MODE: Instantly abandon all routine conversation and switch to emergency protocol

EMERGENCY TRIGGERS (IMMEDIATE PROTOCOL ACTIVATION):
- Accident/Crash: "accident", "crash", "collision", "rollover", "hit", "wreck", "flipped", "overturned"
- Medical: "hurt", "injured", "pain", "sick", "medical", "hospital", "bleeding", "unconscious", "chest pain", "can''t breathe"
- Mechanical: "breakdown", "stuck", "blowout", "overheated", "smoke", "fire", "explosion", "leaking", "can''t move"
- Critical: "help", "emergency", "urgent", "trouble", "trapped", "911", "police", "ambulance"

EMERGENCY RESPONSE PROTOCOL (Execute within 30 seconds):
1. IMMEDIATE SAFETY ASSESSMENT: "This sounds like an emergency. Are you safe right now?"
2. INJURY STATUS CHECK: "Is anyone hurt or injured? Do you need an ambulance?"
3. PRECISE LOCATION: "What is your exact location? Include highway number, mile marker, exit, or specific landmark."
4. LOAD SECURITY: "Is your load secure? Are there any hazardous materials?"
5. IMMEDIATE ESCALATION: "I''m connecting you to a human dispatcher immediately. Please stay on the line."

EMERGENCY COMMUNICATION PROTOCOLS:
- Speak with calm authority and controlled urgency
- Use short, direct questions only
- NO filler words, casual conversation, or routine questions
- Confirm critical information by repeating back
- Keep driver focused and calm
- Maintain connection until human dispatcher takes over

CRITICAL SUCCESS FACTORS:
- Emergency detection takes ABSOLUTE PRIORITY over ALL other conversation
- Abandon normal call flow the INSTANT emergency keywords are detected
- Gather only essential safety and location data
- Complete escalation within 30 seconds
- Never attempt to solve emergency situations - always escalate immediately
- Maintain professional calm to keep driver stable',

    'Hello, how can I help you today?',

    'You are a logistics dispatcher with specialized training in emergency response. You can be in the middle of ANY routine conversation when an emergency occurs.',

    'Hi {driver_name}, this is dispatch calling about load {load_number}.',

    'How are things going with your delivery?',

    'Let me understand the situation better. Can you provide more details?',

    'Emergency protocol activated. A human dispatcher will be with you shortly.',

    true,
    0.3,
    1.0,
    1.0,
    true,
    200,
    true
);

-- ================================================
-- COMMENTS
-- ================================================

-- Table comments
COMMENT ON TABLE agents IS 'Voice agents configured for specific logistics scenarios with optimal settings for human-like conversation';
COMMENT ON TABLE calls IS 'Voice calls made by agents, including metadata, transcripts, and results';
COMMENT ON TABLE call_results IS 'Structured data extracted from voice calls based on scenario type';
COMMENT ON TABLE loads IS 'Load information for tracking shipments and driver assignments';
COMMENT ON TABLE conversation_states IS 'Stores real-time conversation state and context for active voice calls';
COMMENT ON TABLE audit_logs IS 'Audit trail for user actions and system events';

-- Column comments
COMMENT ON COLUMN agents.scenario_type IS 'Type of logistics scenario: driver_checkin or emergency_protocol';
COMMENT ON COLUMN agents.begin_message IS 'Initial message sent when call begins';
COMMENT ON COLUMN agents.max_tokens IS 'Maximum tokens for LLM response generation';
COMMENT ON COLUMN agents.temperature IS 'LLM temperature setting for response variability (0.0-2.0)';
COMMENT ON COLUMN conversation_states.call_id IS 'Reference to the active call';
COMMENT ON COLUMN conversation_states.state IS 'Current conversation state (initializing, greeting, gathering_info, etc.)';
COMMENT ON COLUMN conversation_states.context_data IS 'JSON blob containing conversation context, history, and collected data';
COMMENT ON COLUMN audit_logs.action IS 'Action performed (login, create_agent, start_call, etc.)';
COMMENT ON COLUMN audit_logs.details IS 'Additional action details in JSON format';
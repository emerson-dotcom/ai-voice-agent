# Database Migrations for AI Voice Agent

This folder contains SQL migration files to be executed in the Supabase SQL Editor.

## Files Overview

### 01_initial_schema.sql
Creates the complete database schema including:
- **agents** - Agent configurations and settings
- **agent_states** - Conversation flow states for agents
- **agent_tools** - Tools available to agents in different states
- **calls** - Call records and metadata
- **call_results** - Structured data extracted from calls
- **loads** - Load/shipment information

### 02_seed_data.sql
Inserts sample data including:
- Sample load records
- Pre-configured Driver Check-in Agent
- Pre-configured Emergency Protocol Agent
- Agent states and tools for both scenarios

## How to Run Migrations

1. **Open Supabase Dashboard**
   - Go to your Supabase project dashboard
   - Navigate to the SQL Editor

2. **Run Initial Schema**
   - Copy the entire content of `01_initial_schema.sql`
   - Paste into a new query in Supabase SQL Editor
   - Click "Run" to execute

3. **Run Seed Data**
   - Copy the entire content of `02_seed_data.sql`
   - Paste into a new query in Supabase SQL Editor
   - Click "Run" to execute

## Database Schema Overview

### Core Tables

#### agents
Stores agent configurations including:
- Retell AI integration settings (llm_id, agent_id)
- Voice settings (voice_id, temperature, speed)
- Advanced features (backchannel, interruption sensitivity)
- Scenario type (driver_checkin, emergency_protocol)

#### calls
Records all call attempts and results:
- Links to agent and load information
- Stores Retell AI call data
- Contains transcripts and analysis results
- Tracks call status and timing

#### call_results
Structured data extracted from calls:
- Driver check-in data (status, location, ETA)
- Emergency protocol data (type, safety status, location)
- AI extraction confidence scores

### Relationships

```
agents (1) -> (many) calls
calls (1) -> (1) call_results
agents (1) -> (many) agent_states
agents (1) -> (many) agent_tools
loads (1) -> (many) calls (via load_number)
```

## Security

- Row Level Security (RLS) is enabled on all tables
- Basic policies allow authenticated users full access
- Policies can be refined based on specific auth requirements

## Data Types

### Custom ENUMs
- `call_status`: registered, ongoing, ended, error
- `call_outcome`: in_transit_update, arrival_confirmation, emergency_escalation
- `driver_status`: driving, delayed, arrived, unloading
- `emergency_type`: accident, breakdown, medical, other

## Indexes

Performance indexes are created on:
- Foreign key relationships
- Search fields (call_status, scenario_type)
- Timestamp fields for reporting

## Notes

- All tables use UUID primary keys
- Timestamps are stored with timezone information
- JSONB is used for flexible configuration storage
- Triggers automatically update `updated_at` timestamps
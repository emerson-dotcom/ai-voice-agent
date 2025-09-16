# AI Voice Agent - Application Flow

## Overview
This document outlines the complete application flow for the AI Voice Agent Tool, detailing user interactions, system processes, and data flow between components.

## User Journey Map

### 1. Administrator Login & Dashboard Access
```
[Admin Login] → [Dashboard] → [Configuration/Call Management]
```

### 2. Agent Configuration Flow
```
[Dashboard] → [Agent Config] → [Prompt Editor] → [Voice Settings] → [Save Config]
    ↓
[Test Configuration] → [Preview Settings] → [Deploy to Production]
```

### 3. Call Management Flow
```
[Dashboard] → [New Call] → [Enter Driver Details] → [Start Call] → [Monitor Progress] → [View Results]
```

## Detailed Flow Diagrams

### Agent Configuration Process
1. **Access Configuration Panel**
   - Navigate to "Agent Configuration" from dashboard
   - Select scenario type (Check-in or Emergency)

2. **Define Conversation Logic**
   - Input opening prompts
   - Set conversation branching rules
   - Configure data extraction points

3. **Voice Settings Configuration**
   - Adjust Retell AI parameters:
     - Backchanneling frequency
     - Filler word usage
     - Interruption sensitivity
     - Voice speed and tone

4. **Save and Test**
   - Save configuration to Supabase
   - Run test scenario validation
   - Deploy to active agent pool

### Call Execution Flow
```
[Admin Input] → [System Validation] → [Retell AI Call] → [Real-time Processing] → [Data Extraction] → [Results Display]
```

#### Step-by-Step Call Process:
1. **Pre-Call Setup**
   - Admin enters: Driver name, phone number, load number
   - System validates input format
   - Retrieves relevant agent configuration

2. **Call Initiation**
   - FastAPI triggers Retell AI call
   - System sends context data to voice agent
   - Call status updates in real-time

3. **During Call Processing**
   - Retell AI webhook sends conversation updates
   - FastAPI processes responses in real-time
   - Dynamic conversation flow based on driver responses

4. **Post-Call Processing**
   - Raw transcript received from Retell AI
   - NLP processing extracts structured data
   - Results formatted and stored in database

5. **Results Presentation**
   - Structured data displayed as key-value pairs
   - Full transcript available for review
   - Call metadata (duration, outcome, timestamp)

## System Flow Architecture

### Data Flow Between Components
```
[Next.js Frontend] ↔ [FastAPI Backend] ↔ [Supabase Database]
                            ↕
                     [Retell AI Service]
```

### Real-time Communication Flow
1. **Frontend → Backend**: Call trigger request
2. **Backend → Retell AI**: Initiate voice call
3. **Retell AI → Backend**: Real-time conversation webhooks
4. **Backend → Frontend**: Live call status updates
5. **Backend → Database**: Store conversation data
6. **Database → Frontend**: Retrieve and display results

## Scenario-Specific Flows

### Scenario 1: Driver Check-in Flow
```
[Call Start] → [Open Status Question] → [Driver Response Analysis]
    ↓
[In-Transit Path] OR [Arrival Path]
    ↓
[Collect Specific Data] → [Confirm Information] → [Call End]
```

**Decision Points:**
- Driver status determines conversation branch
- Dynamic questioning based on response type
- Graceful handling of unclear responses

### Scenario 2: Emergency Protocol Flow
```
[Normal Conversation] → [Emergency Trigger Detected] → [Immediate Protocol Switch]
    ↓
[Safety Assessment] → [Information Gathering] → [Human Escalation]
```

**Critical Triggers:**
- Emergency keyword detection
- Immediate conversation pivot
- Structured emergency data collection
- Automatic escalation process

## Error Handling Flows

### Uncooperative Driver Flow
```
[Short Response] → [Probing Question] → [Still Uncooperative?] 
    ↓                                           ↓
[Continue Probing] ← [No]                [Yes] → [Graceful Exit]
```

### Technical Issue Flow
```
[Audio Issue Detected] → [Repeat Request] → [Still Unclear?]
    ↓                                           ↓
[Continue Call] ← [No]                    [Yes] → [Escalate to Human]
```

### Conflicting Information Flow
```
[GPS vs Driver Location Mismatch] → [Non-confrontational Verification] → [Accept Driver Input]
```

## User Interface Flow

### Dashboard Navigation
```
Main Dashboard
├── Agent Configuration
│   ├── Scenario Templates
│   ├── Prompt Editor
│   └── Voice Settings
├── Call Management
│   ├── New Call Form
│   ├── Active Calls Monitor
│   └── Call History
└── Results & Analytics
    ├── Individual Call Results
    ├── Transcript Viewer
    └── Performance Metrics
```

## Integration Points

### External Service Integrations
1. **Retell AI Integration**
   - Webhook endpoints for real-time updates
   - Voice configuration API calls
   - Call initiation and management

2. **Supabase Integration**
   - Configuration storage and retrieval
   - Call data persistence
   - User authentication and authorization

## Security & Validation Flow
1. **Input Validation**: All user inputs validated before processing
2. **Authentication**: Secure admin access to all functions
3. **Data Encryption**: Sensitive call data encrypted in transit and storage
4. **Audit Trail**: All configuration changes and calls logged

## Performance Considerations
- **Real-time Updates**: WebSocket connections for live call monitoring
- **Scalability**: Async processing for multiple concurrent calls
- **Reliability**: Fallback mechanisms for service failures
- **Monitoring**: Health checks and performance metrics tracking

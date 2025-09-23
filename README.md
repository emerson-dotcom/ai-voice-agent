# AI Voice Agent - Logistics Communication Platform

A comprehensive web application that allows non-technical administrators to configure, test, and review calls made by adaptive AI voice agents for logistics operations. Built with NextJS 15, FastAPI, Supabase, and Retell AI.

## 🎯 Project Overview

This platform enables logistics companies to deploy intelligent voice agents that can handle driver check-ins, emergency detection, and structured data collection through natural conversation. The system features an intuitive administrative interface for agent configuration, real-time call triggering, and comprehensive results analysis.

## ✨ Key Features

### Administrative Interface
- **Agent Configuration UI**: Simple interface to define prompts and conversation logic
- **Call Triggering Dashboard**: Enter driver context (name, phone, load number) and start test calls
- **Results Analysis**: View structured data extraction and full call transcripts
- **Real-time Monitoring**: Live call status and transcript viewing

### Advanced Voice Capabilities
- **Human-like Conversation**: Backchannel responses, filler words, interruption sensitivity
- **Dynamic Flow Control**: Adaptive conversation paths based on driver responses
- **Emergency Detection**: Immediate pivot to emergency protocol when needed
- **Structured Data Extraction**: Convert conversations to actionable business data

### Built-in Logistics Scenarios

#### 1. Driver Check-in Agent ("Dispatch")
- **Purpose**: End-to-end driver status conversations
- **Flow**: Determines driver status → adapts questioning dynamically
- **Data Collected**: Status, location, ETA, delays, unloading info, POD acknowledgment

#### 2. Emergency Protocol Agent ("Dispatch")
- **Purpose**: Detects emergencies during routine calls
- **Flow**: Abandons standard conversation → gathers critical info → escalates to human
- **Data Collected**: Emergency type, safety status, location, load security

## 🛠 Technology Stack

### Frontend
- **Next.js 15** - React framework with app router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Radix UI** - Accessible component primitives
- **Supabase Auth** - Authentication and user management

### Backend
- **FastAPI** - Modern Python web framework serving as Retell AI webhook
- **Supabase** - Database and authentication
- **Retell AI** - Voice conversation platform
- **Pydantic** - Data validation and real-time conversation logic

### Infrastructure
- **Supabase** - Database, authentication, real-time features
- **Retell AI** - Voice AI platform with advanced human-like features
- **Row Level Security** - Database-level access control

## 📋 Prerequisites

- **Node.js 18+** and npm
- **Python 3.8+** and pip
- **Supabase Account** - For database and authentication
- **Retell AI Account** - For voice agent functionality
- **Windows Environment** - Project optimized for Windows development

## 🚀 Quick Start

### 1. Environment Setup

**Frontend (.env.local):**
```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_RETELL_API_KEY=your_retell_api_key
```

**Backend (.env):**
```env
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_service_key
RETELL_API_KEY=your_retell_api_key
RETELL_WEBHOOK_SECRET=your_webhook_secret
```

### 2. Database Setup
```bash
# Run migrations in Supabase SQL Editor
# See migrations/README.md for setup instructions
```

### 3. Backend Setup
```cmd
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### 4. Frontend Setup
```cmd
cd frontend
npm install
npm run dev
```

## 🎯 Core Workflows

### Agent Configuration
1. Define conversation prompts and logic through the UI
2. Configure voice settings (backchannel, interruption sensitivity, filler words)
3. Set up scenario-specific data extraction schemas

### Call Testing
1. Enter driver context (name, phone number, load number)
2. Click "Start Test Call" to trigger voice agent
3. Monitor real-time call progress and transcript
4. Review structured data extraction post-call

### Results Analysis
- **Structured Data**: Clean key-value pairs extracted from conversation
- **Full Transcript**: Complete conversation history
- **Call Metrics**: Duration, status, confidence scores
- **Emergency Alerts**: Automatic flagging of safety issues

## 📊 Structured Data Collection

### Driver Check-in Scenario
```json
{
  "call_outcome": "In-Transit Update" | "Arrival Confirmation",
  "driver_status": "Driving" | "Delayed" | "Arrived" | "Unloading",
  "current_location": "I-10 near Indio, CA",
  "eta": "Tomorrow, 8:00 AM",
  "delay_reason": "Heavy Traffic" | "Weather" | "None",
  "unloading_status": "In Door 42" | "Waiting for Lumper" | "N/A",
  "pod_reminder_acknowledged": true
}
```

### Emergency Protocol Scenario
```json
{
  "call_outcome": "Emergency Escalation",
  "emergency_type": "Accident" | "Breakdown" | "Medical" | "Other",
  "safety_status": "Driver confirmed everyone is safe",
  "injury_status": "No injuries reported",
  "emergency_location": "I-15 North, Mile Marker 123",
  "load_secure": true,
  "escalation_status": "Connected to Human Dispatcher"
}
```

## 🏗 Project Structure

```
ai-voice-agent-c0/
├── frontend/                 # NextJS 15 admin interface
│   ├── src/
│   │   ├── app/             # App router pages
│   │   ├── components/      # UI components
│   │   ├── lib/            # Supabase client & utilities
│   │   └── types/          # TypeScript definitions
├── backend/                 # FastAPI webhook & logic
│   ├── app/
│   │   ├── api/            # REST endpoints
│   │   ├── core/           # Configuration & database
│   │   ├── models/         # Data models
│   │   ├── scenarios/      # Logistics scenario logic
│   │   └── services/       # Business logic & Retell integration
├── migrations/             # Supabase database schema
├── docs/                   # Documentation
└── scripts/               # Development utilities
```

## 🔧 Advanced Voice Features

### Human-like Conversation
- **Backchannel Responses**: Automatic "uh-huh", "yeah" during conversation
- **Filler Words**: Natural speech patterns and hesitations
- **Interruption Sensitivity**: Configurable response to user interruptions
- **Dynamic Flow**: Conversation adapts based on driver responses

### Robust Handling
- **Uncooperative Drivers**: Probes for information, knows when to end calls
- **Noisy Environments**: Handles garbled speech, asks for repetition
- **Conflicting Information**: Non-confrontational handling of discrepancies

## 📚 Documentation

- [Database Schema](migrations/README.md) - Complete database structure
- [API Documentation](docs/api.md) - Backend API reference
- [Deployment Guide](docs/deployment.md) - Production setup
- [Project Requirements](project_requirements.md) - Original specifications

## 🎯 Success Metrics

- **Conversation Completion Rate**: Successfully completed driver check-ins
- **Emergency Detection Accuracy**: Proper identification and escalation
- **Data Extraction Quality**: Structured data accuracy and completeness
- **User Experience**: Administrative ease of use and call monitoring

# AI Voice Agent Tool

A comprehensive web application for managing AI-powered voice agents in logistics operations. This system enables non-technical administrators to configure, test, and review calls made by adaptive AI voice agents for driver check-ins and emergency protocols.

## 🚀 Features

### Core Functionality
- **Agent Configuration**: Intuitive interface for configuring voice prompts, conversation flows, and Retell AI settings
- **Call Management**: Initiate, monitor, and manage voice calls in real-time
- **Results Analysis**: View structured data extracted from conversations with full transcripts
- **Emergency Protocol**: Automatic emergency detection and escalation procedures

### Logistics Scenarios
1. **Driver Check-in**: Dynamic conversation flow for status updates, location tracking, and ETA management
2. **Emergency Protocol**: Immediate emergency detection with safety assessment and human escalation

### Advanced Features
- Real-time call monitoring with WebSocket connections
- Intelligent data extraction using OpenAI and rule-based NLP
- Emergency keyword detection and automatic protocol switching
- Comprehensive analytics and reporting
- Edge case handling (uncooperative drivers, technical issues, conflicting information)

## 🏗️ Architecture

### Technology Stack
- **Frontend**: Next.js 15+ with TypeScript, Tailwind CSS, Headless UI
- **Backend**: FastAPI with Python 3.12+, SQLAlchemy, Pydantic
- **Database**: Supabase (PostgreSQL) with real-time subscriptions
- **Voice AI**: Retell AI integration with advanced voice features
- **Real-time**: Socket.IO for live call monitoring and updates
- **NLP**: OpenAI GPT-4 + spaCy for structured data extraction

### Project Structure
```
ai-voice-agent/
├── frontend/                 # Next.js frontend application
│   ├── app/                 # App Router pages
│   ├── components/          # Reusable UI components
│   ├── hooks/              # Custom React hooks
│   ├── lib/                # Utilities and configurations
│   └── types/              # TypeScript type definitions
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── api/            # API route handlers
│   │   ├── core/           # Core functionality
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utility functions
│   ├── tests/              # Test suite
│   └── requirements.txt    # Python dependencies
└── Instructions/           # Project documentation
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.12+
- PostgreSQL (or Supabase account)
- Redis (for background tasks)

### Required API Keys
You'll need accounts and API keys for:
- **Retell AI**: Voice conversation platform
- **OpenAI**: For NLP data extraction
- **Supabase**: Database and authentication

### Backend Setup

1. **Navigate to backend directory**
```bash
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv

# On Windows (PowerShell):
venv\Scripts\Activate.ps1
# Or on Windows (Command Prompt):
venv\Scripts\activate.bat

# On Linux/Mac:
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys and database URL
```

5. **Start the backend server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Configure environment variables**
```bash
cp .env.local.example .env.local
# Edit .env.local with your API endpoints
```

4. **Start the development server**
```bash
npm run dev
```

### Docker Setup (Alternative)

1. **Start with Docker Compose**
```bash
cd backend
docker-compose up -d
```

This will start:
- FastAPI backend on port 8000
- PostgreSQL database on port 5432
- Redis on port 6379

## 📋 Environment Variables

### Backend (.env)
```bash
# Application
DEBUG=True
SECRET_KEY=your-super-secret-key

# Database
DATABASE_URL=postgresql+asyncpg://username:password@localhost/ai_voice_agent

# Retell AI
RETELL_API_KEY=your-retell-ai-api-key
RETELL_BASE_URL=https://api.retellai.com/v2
RETELL_WEBHOOK_SECRET=your-webhook-secret

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-key
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SOCKET_URL=http://localhost:8000
```

## 🎯 Usage Guide

### 1. Agent Configuration
1. Navigate to "Agent Configuration" in the dashboard
2. Click "Create New Agent"
3. Choose scenario type (Check-in or Emergency)
4. Configure conversation prompts and voice settings
5. Deploy the agent to Retell AI

### 2. Making Calls
1. Go to "Call Management"
2. Click "New Call"
3. Enter driver details and select agent configuration
4. Monitor call progress in real-time
5. View results after call completion

### 3. Viewing Results
1. Access "Results & Analytics"
2. View structured data extracted from calls
3. Read full conversation transcripts
4. Export data for further analysis

## 🔧 API Documentation

The backend provides a comprehensive REST API with automatic OpenAPI documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoints
- `POST /api/v1/auth/login` - User authentication
- `GET/POST /api/v1/agents` - Agent configuration management
- `POST /api/v1/calls/initiate` - Start voice calls
- `GET /api/v1/calls/{id}` - Get call details
- `POST /api/v1/webhooks/retell/*` - Retell AI webhooks

## 🧪 Testing

### Backend Testing
```bash
cd backend
pytest tests/ -v
```

### Frontend Testing
```bash
cd frontend
npm test
```

## 🚀 Deployment

### Backend Deployment (Railway/Heroku)
1. Connect your GitHub repository
2. Set environment variables in the platform
3. Deploy from the `backend` directory

### Frontend Deployment (Vercel)
1. Connect your GitHub repository
2. Set build command: `cd frontend && npm run build`
3. Set environment variables
4. Deploy

## 📊 Monitoring

The application includes comprehensive monitoring:
- Real-time call status updates
- Emergency alert notifications
- Performance analytics
- Error tracking and logging

## 🤝 Contributing

This is an assignment project. For production use, consider:
- Implementing comprehensive test coverage
- Adding user management and role-based access
- Setting up CI/CD pipelines
- Implementing proper error handling and monitoring
- Adding rate limiting and security measures

## 📄 License

This project is for educational/assignment purposes. Please check with your institution regarding usage rights.

## 🆘 Support

For issues or questions:
1. Check the API documentation at `/docs`
2. Review the logs for error messages
3. Ensure all environment variables are properly set
4. Verify API keys and external service connectivity

---

**Built for logistics communication excellence with AI-powered voice technology.**

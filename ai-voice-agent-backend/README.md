# AI Voice Agent Tool - Backend

A FastAPI backend application for the AI Voice Agent Tool that handles Retell AI webhooks, manages conversation logic, and provides APIs for the frontend application.

## Features

- **Retell AI Integration**: Webhook handling for call events and transcript updates
- **Dynamic Conversation Logic**: Intelligent processing of call transcripts for logistics scenarios
- **Call Management**: Create, track, and update call records
- **Structured Data Extraction**: Convert raw transcripts into structured logistics data
- **Emergency Detection**: Automatic detection and escalation of emergency situations
- **Real-time Processing**: Live transcript updates and call status tracking

## Technology Stack

- **Framework**: FastAPI with Python 3.8+
- **Database**: Supabase (PostgreSQL)
- **Voice AI**: Retell AI integration
- **HTTP Client**: httpx for async requests
- **Validation**: Pydantic for data validation
- **Logging**: Python logging with structured logs

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Supabase account
- Retell AI account

### Installation

1. Navigate to the backend directory:
```bash
cd ai-voice-agent-backend
```

2. Create and activate virtual environment:
```bash
python -m venv venv

# On Windows
venv\Scripts\Activate.ps1

# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Copy the example file
cp .env.example .env
```

5. Update `.env` with your actual values:
```env
# Supabase Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_service_role_key_here

# Retell AI Configuration
RETELL_API_KEY=your_retell_api_key_here
RETELL_AGENT_ID=your_retell_agent_id_here

# FastAPI Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

6. Run the development server:
```bash
python -m app.main
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:

- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

## Project Structure

```
app/
├── api/                    # API route handlers
│   ├── health.py          # Health check endpoints
│   ├── calls.py           # Call management endpoints
│   └── retell_webhook.py  # Retell AI webhook handlers
├── core/                  # Core configuration and utilities
│   ├── config.py          # Application settings
│   └── database.py        # Database connection
├── models/                # Data models and schemas
│   └── schemas.py         # Pydantic models
├── services/              # Business logic services
│   ├── retell_service.py  # Retell AI integration
│   └── conversation_service.py  # Conversation processing
├── utils/                 # Utility functions
│   └── helpers.py         # Helper functions
└── main.py               # FastAPI application entry point
```

## API Endpoints

### Health Check
- `GET /api/health` - Application health status

### Call Management
- `POST /api/calls/trigger` - Trigger a new call
- `GET /api/calls` - Get all calls
- `GET /api/calls/{call_id}` - Get specific call
- `PUT /api/calls/{call_id}` - Update call record

### Webhooks
- `POST /api/webhook/retell` - Retell AI webhook handler

## Conversation Logic

The backend includes intelligent conversation processing for two main scenarios:

### 1. Routine Driver Check-in
- Detects driver status (Driving, Delayed, Arrived, Unloading)
- Extracts location, ETA, and delay reasons
- Processes unloading status and POD acknowledgments

### 2. Emergency Protocol
- Detects emergency keywords in real-time
- Categorizes emergency types (Accident, Breakdown, Medical, Other)
- Extracts safety status and location information
- Triggers escalation to human dispatcher

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_KEY` | Supabase service role key | Yes |
| `RETELL_API_KEY` | Retell AI API key | Yes |
| `RETELL_AGENT_ID` | Retell AI agent ID | Yes |
| `API_HOST` | API host address | No (default: 0.0.0.0) |
| `API_PORT` | API port | No (default: 8000) |
| `DEBUG` | Debug mode | No (default: True) |
| `ALLOWED_ORIGINS` | CORS allowed origins | No |

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest
```

### Code Quality
```bash
# Install linting tools
pip install black flake8

# Format code
black app/

# Lint code
flake8 app/
```

## Deployment

### Local Development
```bash
python -m app.main
```

### Production
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Logging

The application uses structured logging with the following levels:
- **INFO**: General application flow
- **ERROR**: Error conditions
- **DEBUG**: Detailed debugging information (when DEBUG=True)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is part of the AI Voice Agent Tool system for logistics management.

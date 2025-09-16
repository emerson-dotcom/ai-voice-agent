# AI Voice Agent - Backend Structure

## Architecture Overview

The backend is built using FastAPI and follows a modular, scalable architecture designed to handle real-time voice interactions with Retell AI while maintaining clean separation of concerns.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration and environment variables
│   ├── dependencies.py         # Dependency injection
│   │
│   ├── api/                    # API route handlers
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── agents.py           # Agent configuration endpoints
│   │   ├── calls.py            # Call management endpoints
│   │   └── webhooks.py         # Retell AI webhook endpoints
│   │
│   ├── core/                   # Core business logic
│   │   ├── __init__.py
│   │   ├── security.py         # Authentication and authorization
│   │   ├── conversation.py     # Conversation flow management
│   │   ├── data_extraction.py  # NLP and data processing
│   │   └── retell_client.py    # Retell AI integration
│   │
│   ├── models/                 # Database models and schemas
│   │   ├── __init__.py
│   │   ├── database.py         # Database connection
│   │   ├── agent.py            # Agent configuration models
│   │   ├── call.py             # Call record models
│   │   └── user.py             # User models
│   │
│   ├── schemas/                # Pydantic schemas for API
│   │   ├── __init__.py
│   │   ├── agent.py            # Agent configuration schemas
│   │   ├── call.py             # Call data schemas
│   │   └── webhook.py          # Webhook payload schemas
│   │
│   ├── services/               # Business logic services
│   │   ├── __init__.py
│   │   ├── agent_service.py    # Agent configuration management
│   │   ├── call_service.py     # Call orchestration
│   │   ├── nlp_service.py      # Natural language processing
│   │   └── notification_service.py # Real-time notifications
│   │
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       ├── logger.py           # Logging configuration
│       ├── validators.py       # Input validation
│       └── helpers.py          # Common helper functions
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Test configuration
│   ├── test_api/               # API endpoint tests
│   ├── test_services/          # Service layer tests
│   └── test_utils/             # Utility function tests
│
├── alembic/                    # Database migrations
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
└── docker-compose.yml          # Development environment
```

## Core Components

### 1. FastAPI Application (`main.py`)

```python
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, agents, calls, webhooks
from app.core.security import get_current_user
from app.config import settings

app = FastAPI(
    title="AI Voice Agent API",
    description="Backend API for AI Voice Agent Tool",
    version="1.0.0"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route includes
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(agents.router, prefix="/agents", tags=["agents"], dependencies=[Depends(get_current_user)])
app.include_router(calls.router, prefix="/calls", tags=["calls"], dependencies=[Depends(get_current_user)])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
```

### 2. Database Models

#### Agent Configuration Model (`models/agent.py`)
```python
from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class AgentConfiguration(Base):
    __tablename__ = "agent_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    scenario_type = Column(String)  # "check_in" or "emergency"
    prompts = Column(JSON)
    voice_settings = Column(JSON)
    conversation_flow = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### Call Record Model (`models/call.py`)
```python
class CallRecord(Base):
    __tablename__ = "call_records"
    
    id = Column(Integer, primary_key=True, index=True)
    driver_name = Column(String)
    phone_number = Column(String)
    load_number = Column(String)
    agent_config_id = Column(Integer, ForeignKey("agent_configurations.id"))
    retell_call_id = Column(String, unique=True, index=True)
    status = Column(String)  # "initiated", "in_progress", "completed", "failed"
    raw_transcript = Column(Text)
    structured_data = Column(JSON)
    duration = Column(Integer)  # seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
```

### 3. API Endpoints

#### Agent Configuration API (`api/agents.py`)
```python
from fastapi import APIRouter, Depends, HTTPException
from app.services.agent_service import AgentService
from app.schemas.agent import AgentConfigCreate, AgentConfigResponse

router = APIRouter()

@router.post("/", response_model=AgentConfigResponse)
async def create_agent_config(
    config: AgentConfigCreate,
    agent_service: AgentService = Depends()
):
    """Create new agent configuration"""
    return await agent_service.create_configuration(config)

@router.get("/{config_id}", response_model=AgentConfigResponse)
async def get_agent_config(
    config_id: int,
    agent_service: AgentService = Depends()
):
    """Get agent configuration by ID"""
    return await agent_service.get_configuration(config_id)

@router.put("/{config_id}", response_model=AgentConfigResponse)
async def update_agent_config(
    config_id: int,
    config: AgentConfigCreate,
    agent_service: AgentService = Depends()
):
    """Update agent configuration"""
    return await agent_service.update_configuration(config_id, config)
```

#### Call Management API (`api/calls.py`)
```python
@router.post("/initiate", response_model=CallResponse)
async def initiate_call(
    call_request: CallInitiateRequest,
    call_service: CallService = Depends()
):
    """Initiate a new voice call"""
    return await call_service.initiate_call(call_request)

@router.get("/{call_id}", response_model=CallDetailResponse)
async def get_call_details(
    call_id: int,
    call_service: CallService = Depends()
):
    """Get detailed call information"""
    return await call_service.get_call_details(call_id)

@router.get("/{call_id}/transcript")
async def get_call_transcript(
    call_id: int,
    call_service: CallService = Depends()
):
    """Get call transcript"""
    return await call_service.get_transcript(call_id)
```

#### Retell AI Webhooks (`api/webhooks.py`)
```python
@router.post("/retell/conversation")
async def handle_conversation_webhook(
    payload: RetellConversationWebhook,
    conversation_service: ConversationService = Depends()
):
    """Handle real-time conversation updates from Retell AI"""
    return await conversation_service.process_conversation_update(payload)

@router.post("/retell/call-ended")
async def handle_call_ended_webhook(
    payload: RetellCallEndedWebhook,
    call_service: CallService = Depends()
):
    """Handle call completion from Retell AI"""
    return await call_service.process_call_completion(payload)
```

### 4. Service Layer

#### Call Service (`services/call_service.py`)
```python
class CallService:
    def __init__(self, db: Session, retell_client: RetellClient):
        self.db = db
        self.retell_client = retell_client
    
    async def initiate_call(self, call_request: CallInitiateRequest) -> CallResponse:
        """Initiate a new call with Retell AI"""
        # 1. Validate input data
        # 2. Get agent configuration
        # 3. Create call record
        # 4. Initiate call with Retell AI
        # 5. Return call information
        
        agent_config = self.get_agent_configuration(call_request.agent_config_id)
        
        call_record = CallRecord(
            driver_name=call_request.driver_name,
            phone_number=call_request.phone_number,
            load_number=call_request.load_number,
            agent_config_id=call_request.agent_config_id,
            status="initiated"
        )
        
        retell_response = await self.retell_client.create_call(
            phone_number=call_request.phone_number,
            agent_config=agent_config.retell_config
        )
        
        call_record.retell_call_id = retell_response.call_id
        self.db.add(call_record)
        self.db.commit()
        
        return CallResponse.from_orm(call_record)
```

#### NLP Service (`services/nlp_service.py`)
```python
class NLPService:
    def __init__(self):
        self.emergency_keywords = ["emergency", "accident", "blowout", "medical", "breakdown"]
    
    def extract_structured_data(self, transcript: str, scenario_type: str) -> dict:
        """Extract structured data from conversation transcript"""
        if scenario_type == "check_in":
            return self._extract_checkin_data(transcript)
        elif scenario_type == "emergency":
            return self._extract_emergency_data(transcript)
    
    def detect_emergency_trigger(self, message: str) -> bool:
        """Detect if message contains emergency keywords"""
        return any(keyword in message.lower() for keyword in self.emergency_keywords)
    
    def _extract_checkin_data(self, transcript: str) -> dict:
        """Extract check-in specific data fields"""
        # Implementation for extracting:
        # - call_outcome, driver_status, current_location
        # - eta, delay_reason, unloading_status
        # - pod_reminder_acknowledged
        pass
    
    def _extract_emergency_data(self, transcript: str) -> dict:
        """Extract emergency specific data fields"""
        # Implementation for extracting:
        # - emergency_type, safety_status, injury_status
        # - emergency_location, load_secure, escalation_status
        pass
```

### 5. Retell AI Integration (`core/retell_client.py`)

```python
class RetellClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def create_call(self, phone_number: str, agent_config: dict) -> dict:
        """Create a new call with Retell AI"""
        payload = {
            "phone_number": phone_number,
            "agent_id": agent_config["agent_id"],
            "metadata": agent_config.get("metadata", {})
        }
        
        response = await self.client.post(
            f"{self.base_url}/calls",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload
        )
        
        return response.json()
    
    async def update_agent_config(self, agent_id: str, config: dict) -> dict:
        """Update agent configuration in Retell AI"""
        response = await self.client.patch(
            f"{self.base_url}/agents/{agent_id}",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=config
        )
        
        return response.json()
```

## Database Schema

### Tables Structure

#### agent_configurations
- `id` (Primary Key)
- `name` (String)
- `scenario_type` (Enum: check_in, emergency)
- `prompts` (JSON)
- `voice_settings` (JSON)
- `conversation_flow` (JSON)
- `is_active` (Boolean)
- `created_at`, `updated_at` (Timestamps)

#### call_records
- `id` (Primary Key)
- `driver_name` (String)
- `phone_number` (String)
- `load_number` (String)
- `agent_config_id` (Foreign Key)
- `retell_call_id` (String, Unique)
- `status` (Enum)
- `raw_transcript` (Text)
- `structured_data` (JSON)
- `duration` (Integer)
- `created_at`, `completed_at` (Timestamps)

#### users
- `id` (Primary Key)
- `email` (String, Unique)
- `hashed_password` (String)
- `is_active` (Boolean)
- `created_at` (Timestamp)

## API Documentation

### Authentication
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - User logout

### Agent Management
- `GET /agents` - List all agent configurations
- `POST /agents` - Create new agent configuration
- `GET /agents/{id}` - Get specific agent configuration
- `PUT /agents/{id}` - Update agent configuration
- `DELETE /agents/{id}` - Delete agent configuration

### Call Management
- `POST /calls/initiate` - Start new call
- `GET /calls` - List all calls
- `GET /calls/{id}` - Get call details
- `GET /calls/{id}/transcript` - Get call transcript
- `POST /calls/{id}/cancel` - Cancel active call

### Webhooks
- `POST /webhooks/retell/conversation` - Real-time conversation updates
- `POST /webhooks/retell/call-ended` - Call completion notification

## Environment Configuration

```python
# config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Authentication
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Retell AI
    RETELL_API_KEY: str
    RETELL_BASE_URL: str = "https://api.retellai.com/v2"
    
    # CORS
    ALLOWED_ORIGINS: list = ["http://localhost:3000"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
```

## Error Handling

### Custom Exception Classes
```python
class VoiceAgentException(Exception):
    """Base exception for voice agent errors"""
    pass

class CallInitiationError(VoiceAgentException):
    """Error during call initiation"""
    pass

class DataExtractionError(VoiceAgentException):
    """Error during data extraction"""
    pass

class RetellAPIError(VoiceAgentException):
    """Error communicating with Retell AI"""
    pass
```

### Global Exception Handler
```python
@app.exception_handler(VoiceAgentException)
async def voice_agent_exception_handler(request: Request, exc: VoiceAgentException):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "type": exc.__class__.__name__}
    )
```

## Testing Strategy

### Unit Tests
- Service layer testing
- Utility function testing
- Model validation testing

### Integration Tests
- API endpoint testing
- Database operation testing
- External service integration testing

### End-to-End Tests
- Complete call workflow testing
- Webhook processing testing
- Data extraction accuracy testing

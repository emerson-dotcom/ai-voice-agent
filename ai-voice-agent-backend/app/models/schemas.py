from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class CallStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class CallOutcome(str, Enum):
    IN_TRANSIT_UPDATE = "In-Transit Update"
    ARRIVAL_CONFIRMATION = "Arrival Confirmation"
    EMERGENCY_ESCALATION = "Emergency Escalation"


class DriverStatus(str, Enum):
    DRIVING = "Driving"
    DELAYED = "Delayed"
    ARRIVED = "Arrived"
    UNLOADING = "Unloading"


class EmergencyType(str, Enum):
    ACCIDENT = "Accident"
    BREAKDOWN = "Breakdown"
    MEDICAL = "Medical"
    OTHER = "Other"


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


# Agent Configuration Models
class AgentConfigBase(BaseModel):
    name: str
    description: str
    initial_prompt: str
    emergency_prompt: str
    follow_up_prompts: List[str]
    backchanneling: bool = True
    filler_words: bool = True
    interruption_sensitivity: float = Field(ge=0.0, le=1.0, default=0.5)
    voice_id: str
    speed: float = Field(ge=0.5, le=2.0, default=1.0)
    pitch: float = Field(ge=0.5, le=2.0, default=1.0)


class AgentConfigCreate(AgentConfigBase):
    pass


class AgentConfigUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    initial_prompt: Optional[str] = None
    emergency_prompt: Optional[str] = None
    follow_up_prompts: Optional[List[str]] = None
    backchanneling: Optional[bool] = None
    filler_words: Optional[bool] = None
    interruption_sensitivity: Optional[float] = Field(None, ge=0.0, le=1.0)
    voice_id: Optional[str] = None
    speed: Optional[float] = Field(None, ge=0.5, le=2.0)
    pitch: Optional[float] = Field(None, ge=0.5, le=2.0)
    is_active: Optional[bool] = None


class AgentConfig(AgentConfigBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Call Models
class CallTrigger(BaseModel):
    agent_id: str
    driver_name: str
    phone_number: Optional[str] = None  # Optional for web calls
    load_number: str


class CallResult(BaseModel):
    call_outcome: CallOutcome
    driver_status: Optional[DriverStatus] = None
    current_location: Optional[str] = None
    eta: Optional[str] = None
    delay_reason: Optional[str] = None
    unloading_status: Optional[str] = None
    pod_reminder_acknowledged: Optional[bool] = None
    emergency_type: Optional[EmergencyType] = None
    safety_status: Optional[str] = None
    injury_status: Optional[str] = None
    emergency_location: Optional[str] = None
    load_secure: Optional[bool] = None
    escalation_status: Optional[str] = None


class CallBase(BaseModel):
    agent_id: str
    driver_name: str
    phone_number: str
    load_number: str
    status: CallStatus = CallStatus.PENDING


class CallCreate(CallBase):
    pass


class CallUpdate(BaseModel):
    status: Optional[CallStatus] = None
    transcript: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None


class Call(CallBase):
    id: str
    transcript: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Retell AI Webhook Models
class RetellWebhookEvent(BaseModel):
    event: str
    call_id: str
    agent_id: str
    transcript: Optional[str] = None
    transcript_segments: Optional[List[Dict[str, Any]]] = None
    call_metadata: Optional[Dict[str, Any]] = None


# API Response Models
class APIResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    version: str = "1.0.0"


# User Models
class UserBase(BaseModel):
    email: str
    role: UserRole = UserRole.USER


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None


class User(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    id: str
    email: str
    role: UserRole
    created_at: datetime
    updated_at: datetime

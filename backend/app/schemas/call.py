from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import re


class CallStatus(str, Enum):
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


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


# Structured data schemas for different scenarios
class CheckInData(BaseModel):
    """Structured data for driver check-in scenario"""
    call_outcome: CallOutcome
    driver_status: DriverStatus
    current_location: Optional[str] = None
    eta: Optional[str] = None
    delay_reason: Optional[str] = None
    unloading_status: Optional[str] = None
    pod_reminder_acknowledged: bool = False


class EmergencyData(BaseModel):
    """Structured data for emergency scenario"""
    call_outcome: CallOutcome = CallOutcome.EMERGENCY_ESCALATION
    emergency_type: EmergencyType
    safety_status: Optional[str] = None
    injury_status: Optional[str] = None
    emergency_location: Optional[str] = None
    load_secure: bool = False
    escalation_status: str = "Connected to Human Dispatcher"


class CallInitiateRequest(BaseModel):
    driver_name: str = Field(min_length=2, max_length=100)
    phone_number: str = Field(min_length=10, max_length=20)
    load_number: str = Field(min_length=3, max_length=50)
    agent_config_id: int = Field(gt=0)
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', v)
        
        # Check if it's a valid phone number (10-15 digits)
        if len(digits_only) < 10 or len(digits_only) > 15:
            raise ValueError('Phone number must be between 10-15 digits')
        
        # Format as E.164 if it's a US number (starts with 1 and has 11 digits)
        if len(digits_only) == 11 and digits_only.startswith('1'):
            return f"+{digits_only}"
        elif len(digits_only) == 10:
            return f"+1{digits_only}"
        else:
            return f"+{digits_only}"


class CallResponse(BaseModel):
    id: int
    retell_call_id: Optional[str] = None
    driver_name: str
    phone_number: str
    load_number: str
    agent_config_id: int
    status: CallStatus
    call_outcome: Optional[CallOutcome] = None
    duration: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    extraction_confidence: Optional[float] = None
    conversation_quality_score: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CallDetailResponse(CallResponse):
    """Detailed call response with transcript and structured data"""
    raw_transcript: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    conversation_metadata: Optional[Dict[str, Any]] = None
    agent_config_name: Optional[str] = None
    scenario_type: Optional[str] = None


class CallListResponse(BaseModel):
    """List of calls with pagination"""
    calls: List[CallResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class CallStatusUpdate(BaseModel):
    """Real-time call status update"""
    call_id: int
    status: CallStatus
    duration: Optional[int] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationTurnCreate(BaseModel):
    """Create a new conversation turn"""
    call_id: int
    turn_number: int
    speaker: str = Field(pattern=r'^(agent|driver)$')
    message: str = Field(min_length=1, max_length=5000)
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    intent_detected: Optional[str] = None
    entities_extracted: Optional[Dict[str, Any]] = None
    emergency_trigger_detected: bool = False
    emergency_keywords: Optional[List[str]] = None


class TranscriptResponse(BaseModel):
    """Complete call transcript with turns"""
    call_id: int
    driver_name: str
    load_number: str
    total_duration: Optional[int] = None
    turns: List[Dict[str, Any]]
    structured_data: Optional[Dict[str, Any]] = None
    extraction_confidence: Optional[float] = None

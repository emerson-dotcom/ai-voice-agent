from pydantic import BaseModel, Field, validator, model_validator
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

class CallType(str, Enum):
    WEB_CALL = "web_call"
    PHONE_CALL = "phone_call"


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
    phone_number: Optional[str] = Field(None, max_length=20)
    load_number: str = Field(min_length=3, max_length=50)
    agent_config_id: int = Field(gt=0)
    call_type: CallType = Field(default=CallType.PHONE_CALL, description="Type of call: web_call or phone_call")
    
    @model_validator(mode='after')
    def validate_phone_number(self):
        phone_number = self.phone_number
        call_type = self.call_type
        
        # If call_type is web_call, phone_number is optional
        if call_type == CallType.WEB_CALL:
            # For web calls, phone number is optional
            if not phone_number or phone_number.strip() == "":
                self.phone_number = None
                return self
        else:
            # For phone calls, phone number is required
            if not phone_number or phone_number.strip() == "":
                raise ValueError('Phone number is required for phone calls')
        
        # If phone number is provided, validate it
        if phone_number and phone_number.strip():
            # If already in E.164 format, validate and return as-is
            if phone_number.startswith('+'):
                digits_only = re.sub(r'\D', '', phone_number)
                if len(digits_only) < 10 or len(digits_only) > 15:
                    raise ValueError('Phone number must be between 10-15 digits')
                self.phone_number = phone_number
            else:
                # Remove all non-digit characters for non-E.164 numbers
                digits_only = re.sub(r'\D', '', phone_number)
                
                # Check if it's a valid phone number (10-15 digits)
                if len(digits_only) < 10 or len(digits_only) > 15:
                    raise ValueError('Phone number must be between 10-15 digits')
                
                # Format as E.164 if it's a US number (starts with 1 and has 11 digits)
                if len(digits_only) == 11 and digits_only.startswith('1'):
                    self.phone_number = f"+{digits_only}"
                elif len(digits_only) == 10:
                    self.phone_number = f"+1{digits_only}"
                else:
                    self.phone_number = f"+{digits_only}"
        
        return self


class CallResponse(BaseModel):
    id: int
    retell_call_id: Optional[str] = None
    driver_name: str
    phone_number: str
    load_number: str
    agent_config_id: int
    status: CallStatus
    call_type: Optional[CallType] = None
    call_outcome: Optional[CallOutcome] = None
    duration: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    raw_transcript: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    conversation_metadata: Optional[Dict[str, Any]] = None
    extraction_confidence: Optional[float] = None
    conversation_quality_score: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Add transcript alias for frontend compatibility
    @property
    def transcript(self) -> Optional[str]:
        return self.raw_transcript
    
    # Add analysis alias for frontend compatibility  
    @property
    def analysis(self) -> Optional[Dict[str, Any]]:
        return self.structured_data
    
    # Add web call URL for easy access
    @property
    def web_call_url(self) -> Optional[str]:
        if self.conversation_metadata:
            return self.conversation_metadata.get('web_call_url')
        return None
    
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

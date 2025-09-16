from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List


class RetellCallStartedWebhook(BaseModel):
    """Webhook payload when a call starts"""
    call_id: str
    agent_id: str
    phone_number: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class RetellConversationWebhook(BaseModel):
    """Webhook payload for real-time conversation updates"""
    call_id: str
    agent_id: str
    turn_id: str
    speaker: str = Field(pattern=r'^(agent|user)$')  # Retell uses 'user' for driver
    message: str
    timestamp: datetime
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    intent: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    is_final: bool = True  # Whether this is the final version of the message
    
    # Emergency detection fields
    emergency_detected: Optional[bool] = False
    emergency_keywords: Optional[List[str]] = None
    
    # Audio quality metrics
    audio_quality: Optional[float] = Field(None, ge=0.0, le=1.0)
    background_noise: Optional[bool] = None


class RetellCallEndedWebhook(BaseModel):
    """Webhook payload when a call ends"""
    call_id: str
    agent_id: str
    phone_number: str
    start_time: datetime
    end_time: datetime
    duration: int  # seconds
    end_reason: str  # "completed", "cancelled", "failed", "timeout"
    
    # Call quality metrics
    call_quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    user_satisfaction: Optional[str] = None  # "positive", "neutral", "negative"
    
    # Complete transcript
    transcript: Optional[str] = None
    conversation_turns: Optional[List[Dict[str, Any]]] = None
    
    # Analysis results
    call_summary: Optional[str] = None
    key_points: Optional[List[str]] = None
    sentiment_analysis: Optional[Dict[str, Any]] = None
    
    # Error information
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None


class RetellErrorWebhook(BaseModel):
    """Webhook payload for errors during calls"""
    call_id: str
    agent_id: str
    error_type: str
    error_code: str
    error_message: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class WebhookResponse(BaseModel):
    """Standard response for webhook endpoints"""
    status: str = "success"
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Optional[Dict[str, Any]] = None

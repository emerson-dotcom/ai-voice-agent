from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class ScenarioType(str, Enum):
    CHECK_IN = "check_in"
    EMERGENCY = "emergency"


class VoiceSettings(BaseModel):
    """Retell AI voice configuration"""
    backchanneling: bool = True
    filler_words: bool = True
    interruption_sensitivity: float = Field(ge=0.0, le=1.0, default=0.5)
    voice_speed: float = Field(ge=0.5, le=2.0, default=1.0)
    voice_temperature: float = Field(ge=0.0, le=2.0, default=0.7)
    responsiveness: float = Field(ge=0.0, le=2.0, default=1.0)


class ConversationPrompts(BaseModel):
    """Conversation prompts for different scenarios"""
    opening: str = Field(min_length=10, max_length=1000)
    follow_up: str = Field(min_length=10, max_length=1000)
    closing: str = Field(min_length=10, max_length=500)
    emergency_trigger: Optional[str] = Field(max_length=1000)
    probing_questions: List[str] = Field(default_factory=list)


class ConversationFlow(BaseModel):
    """Dynamic conversation flow configuration"""
    max_turns: int = Field(ge=5, le=50, default=20)
    timeout_seconds: int = Field(ge=30, le=300, default=120)
    retry_attempts: int = Field(ge=1, le=5, default=3)
    emergency_keywords: List[str] = Field(default_factory=lambda: [
        "emergency", "accident", "blowout", "medical", "breakdown", "crash", "injured"
    ])
    data_extraction_points: List[str] = Field(default_factory=list)


class AgentConfigBase(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: Optional[str] = Field(max_length=500)
    scenario_type: ScenarioType
    prompts: ConversationPrompts
    voice_settings: VoiceSettings
    conversation_flow: ConversationFlow


class AgentConfigCreate(AgentConfigBase):
    pass


class AgentConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    scenario_type: Optional[ScenarioType] = None
    prompts: Optional[ConversationPrompts] = None
    voice_settings: Optional[VoiceSettings] = None
    conversation_flow: Optional[ConversationFlow] = None
    is_active: Optional[bool] = None


class AgentConfigResponse(AgentConfigBase):
    id: int
    retell_agent_id: Optional[str] = None
    is_active: bool
    is_deployed: bool
    version: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AgentConfigList(BaseModel):
    """List of agent configurations with pagination"""
    configs: List[AgentConfigResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool

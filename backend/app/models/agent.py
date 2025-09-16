from sqlalchemy import Column, Integer, String, JSON, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class AgentConfiguration(Base):
    __tablename__ = "agent_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text)
    scenario_type = Column(String, nullable=False)  # "check_in" or "emergency"
    
    # Conversation configuration
    prompts = Column(JSON, nullable=False)  # {"opening", "follow_up", "closing", "emergency_trigger"}
    voice_settings = Column(JSON, nullable=False)  # Retell AI voice configuration
    conversation_flow = Column(JSON, nullable=False)  # Dynamic conversation logic
    
    # Retell AI configuration
    retell_agent_id = Column(String, unique=True, index=True)
    retell_config = Column(JSON)  # Complete Retell AI agent configuration
    
    # Status and metadata
    is_active = Column(Boolean, default=True)
    is_deployed = Column(Boolean, default=False)
    version = Column(Integer, default=1)
    
    # Relationships
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship to calls
    calls = relationship("CallRecord", back_populates="agent_config")

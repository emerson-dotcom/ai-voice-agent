from sqlalchemy import Column, Integer, String, JSON, DateTime, Text, ForeignKey, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class CallRecord(Base):
    __tablename__ = "call_records"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Call identification
    retell_call_id = Column(String, unique=True, index=True)
    
    # Driver information
    driver_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    load_number = Column(String, nullable=False)
    
    # Agent configuration used
    agent_config_id = Column(Integer, ForeignKey("agent_configurations.id"), nullable=False)
    
    # Call status and metadata
    status = Column(String, default="initiated")  # initiated, in_progress, completed, failed, cancelled
    call_type = Column(String, default="phone_call")  # web_call, phone_call
    call_outcome = Column(String)  # "In-Transit Update", "Arrival Confirmation", "Emergency Escalation"
    
    # Call data
    duration = Column(Integer)  # seconds
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    
    # Conversation data
    raw_transcript = Column(Text)
    structured_data = Column(JSON)  # Extracted structured data
    conversation_metadata = Column(JSON)  # Additional conversation metadata
    
    # Quality metrics
    extraction_confidence = Column(Float)  # Confidence score for data extraction
    conversation_quality_score = Column(Float)  # Overall conversation quality
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    agent_config = relationship("AgentConfiguration", back_populates="calls")


class ConversationTurn(Base):
    __tablename__ = "conversation_turns"
    
    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("call_records.id"), nullable=False)
    
    # Turn data
    turn_number = Column(Integer, nullable=False)
    speaker = Column(String, nullable=False)  # "agent" or "driver"
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Turn metadata
    confidence_score = Column(Float)
    intent_detected = Column(String)
    entities_extracted = Column(JSON)
    
    # Emergency detection
    emergency_trigger_detected = Column(Boolean, default=False)
    emergency_keywords = Column(JSON)  # Keywords that triggered emergency protocol

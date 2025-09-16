from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.call import CallRecord, ConversationTurn
from app.models.agent import AgentConfiguration
from app.schemas.call import (
    CallInitiateRequest,
    CallResponse,
    CallDetailResponse,
    CallListResponse,
    TranscriptResponse,
    CallStatusUpdate
)
from app.services.call_service import CallService

router = APIRouter()


@router.post("/initiate", response_model=CallResponse, status_code=status.HTTP_201_CREATED)
async def initiate_call(
    call_request: CallInitiateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initiate a new voice call with the driver"""
    call_service = CallService(db)
    return await call_service.initiate_call(call_request)


@router.get("/", response_model=CallListResponse)
async def list_calls(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    driver_name: Optional[str] = Query(None),
    load_number: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all calls with pagination and filtering"""
    call_service = CallService(db)
    return await call_service.list_calls(
        page=page,
        per_page=per_page,
        status_filter=status_filter,
        driver_name=driver_name,
        load_number=load_number
    )


@router.get("/active", response_model=List[CallResponse])
async def get_active_calls(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all currently active calls"""
    result = await db.execute(
        select(CallRecord)
        .where(CallRecord.status.in_(["initiated", "in_progress"]))
        .order_by(CallRecord.created_at.desc())
    )
    active_calls = result.scalars().all()
    
    return [CallResponse.from_orm(call) for call in active_calls]


@router.get("/{call_id}", response_model=CallDetailResponse)
async def get_call_details(
    call_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific call"""
    # Get call with agent config
    result = await db.execute(
        select(CallRecord, AgentConfiguration)
        .join(AgentConfiguration, CallRecord.agent_config_id == AgentConfiguration.id)
        .where(CallRecord.id == call_id)
    )
    call_data = result.first()
    
    if not call_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found"
        )
    
    call, agent_config = call_data
    
    # Create detailed response
    response_data = CallDetailResponse.from_orm(call)
    response_data.agent_config_name = agent_config.name
    response_data.scenario_type = agent_config.scenario_type
    
    return response_data


@router.get("/{call_id}/transcript", response_model=TranscriptResponse)
async def get_call_transcript(
    call_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the complete transcript for a call"""
    # Get call record
    result = await db.execute(
        select(CallRecord).where(CallRecord.id == call_id)
    )
    call = result.scalar_one_or_none()
    
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found"
        )
    
    # Get conversation turns
    result = await db.execute(
        select(ConversationTurn)
        .where(ConversationTurn.call_id == call_id)
        .order_by(ConversationTurn.turn_number)
    )
    turns = result.scalars().all()
    
    # Format turns data
    formatted_turns = [
        {
            "turn_number": turn.turn_number,
            "speaker": turn.speaker,
            "message": turn.message,
            "timestamp": turn.timestamp,
            "confidence_score": turn.confidence_score,
            "intent_detected": turn.intent_detected,
            "entities_extracted": turn.entities_extracted,
            "emergency_trigger_detected": turn.emergency_trigger_detected
        }
        for turn in turns
    ]
    
    return TranscriptResponse(
        call_id=call.id,
        driver_name=call.driver_name,
        load_number=call.load_number,
        total_duration=call.duration,
        turns=formatted_turns,
        structured_data=call.structured_data,
        extraction_confidence=call.extraction_confidence
    )


@router.post("/{call_id}/cancel", response_model=CallResponse)
async def cancel_call(
    call_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel an active call"""
    call_service = CallService(db)
    return await call_service.cancel_call(call_id)


@router.get("/{call_id}/status", response_model=CallStatusUpdate)
async def get_call_status(
    call_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current status of a call"""
    result = await db.execute(
        select(CallRecord).where(CallRecord.id == call_id)
    )
    call = result.scalar_one_or_none()
    
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found"
        )
    
    return CallStatusUpdate(
        call_id=call.id,
        status=call.status,
        duration=call.duration,
        message=call.error_message,
        timestamp=call.updated_at
    )


@router.post("/{call_id}/retry", response_model=CallResponse)
async def retry_failed_call(
    call_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retry a failed call"""
    call_service = CallService(db)
    return await call_service.retry_call(call_id)


@router.get("/analytics/summary", response_model=dict)
async def get_call_analytics(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get call analytics summary for the specified number of days"""
    call_service = CallService(db)
    return await call_service.get_analytics_summary(days)

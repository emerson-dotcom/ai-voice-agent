"""
Call management API endpoints.
Handles call creation, monitoring, and results.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, validator
from app.core.database import supabase_client
from app.api.dependencies import get_current_user
import logging
import uuid
import re
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()


class CallCreate(BaseModel):
    """Call creation model."""
    agent_id: str
    driver_name: str
    driver_phone: Optional[str] = None
    load_number: str
    metadata: dict = {}

    @validator('agent_id')
    def validate_agent_id(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid agent ID format')
        return v

    @validator('driver_name')
    def validate_driver_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Driver name must be at least 2 characters long')
        if len(v) > 100:
            raise ValueError('Driver name must not exceed 100 characters')
        return v.strip()

    @validator('driver_phone')
    def validate_driver_phone(cls, v):
        # Skip validation if phone is None or empty (for web calls)
        if not v:
            return v
        # Basic phone number validation (E.164 format) for traditional calls
        phone_pattern = r'^\+?[1-9]\d{1,14}$'
        if not re.match(phone_pattern, v.replace(' ', '').replace('-', '')):
            raise ValueError('Invalid phone number format. Use international format (+1234567890)')
        return v.strip()

    @validator('load_number')
    def validate_load_number(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Load number must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Load number must not exceed 50 characters')
        return v.strip()


class CallResponse(BaseModel):
    """Call response model."""
    id: str
    retell_call_id: Optional[str] = None
    retell_access_token: Optional[str] = None
    agent_id: str
    agent_version: int
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    load_number: Optional[str] = None
    call_status: str
    start_timestamp: Optional[str] = None
    end_timestamp: Optional[str] = None
    duration_ms: Optional[int] = None
    transcript: Optional[str] = None
    recording_url: Optional[str] = None
    disconnection_reason: Optional[str] = None
    call_analysis: Optional[dict] = None
    metadata: dict = {}
    created_at: str
    updated_at: str


class CallResultResponse(BaseModel):
    """Call result response model."""
    id: str
    call_id: str
    call_outcome: str = None

    # Driver Check-in Fields
    driver_status: str = None
    current_location: str = None
    eta: str = None
    delay_reason: str = None
    unloading_status: str = None
    pod_reminder_acknowledged: bool = None

    # Emergency Protocol Fields
    emergency_type: str = None
    safety_status: str = None
    injury_status: str = None
    emergency_location: str = None
    load_secure: bool = None
    escalation_status: str = None

    custom_analysis_data: dict = {}
    confidence_score: float = None
    extracted_at: str
    extraction_method: str


@router.get("/", response_model=List[CallResponse])
async def list_calls(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    status: Optional[str] = Query(None, description="Filter by call status"),
    limit: int = Query(100, description="Number of calls to return"),
    offset: int = Query(0, description="Number of calls to skip"),
    current_user: dict = Depends(get_current_user)
):
    """List calls with optional filtering."""
    try:
        # Validate parameters
        if limit < 1 or limit > 1000:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
        if offset < 0:
            raise HTTPException(status_code=400, detail="Offset must be non-negative")

        # Validate agent_id if provided
        if agent_id:
            try:
                uuid.UUID(agent_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid agent ID format")

        # Validate status if provided
        valid_statuses = ['created', 'registered', 'ongoing', 'ended', 'error']
        if status and status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Status must be one of: {valid_statuses}")

        calls = await supabase_client.get_calls(
            agent_id=agent_id,
            status=status,
            limit=limit,
            offset=offset
        )

        # Debug: Log what we're returning
        logger.info(f"Returning {len(calls)} calls")
        for call in calls[:3]:  # Log first 3 calls for debugging
            logger.info(f"Call {call.get('id')}: transcript={bool(call.get('transcript'))}, duration={call.get('duration_ms')}, status={call.get('call_status')}")

        return calls
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching calls: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch calls")


@router.get("/{call_id}", response_model=CallResponse)
async def get_call(
    call_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific call by ID."""
    try:
        logger.info(f"Fetching call details for ID: {call_id}")

        # Validate UUID format
        try:
            uuid.UUID(call_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid call ID format")

        call = await supabase_client.get_call_by_id(call_id)
        logger.info(f"Retrieved call from database: {call}")

        if not call:
            raise HTTPException(status_code=404, detail="Call not found")
        return call
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching call {call_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{call_id}/results", response_model=CallResultResponse)
async def get_call_results(
    call_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get structured results for a call."""
    try:
        # Validate UUID format
        try:
            uuid.UUID(call_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid call ID format")

        # Check if call exists
        call = await supabase_client.get_call_by_id(call_id)
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")

        # Get call results
        results = await supabase_client.get_call_results(call_id)
        if not results:
            raise HTTPException(status_code=404, detail="Call results not found")

        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching call results for {call_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch call results")


@router.post("/", response_model=CallResponse)
async def create_call(
    call: CallCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new call and store it in database."""
    try:
        # Verify agent exists and is active
        agent = await supabase_client.get_agent_by_id(call.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        if not agent.get('is_active', True):
            raise HTTPException(status_code=400, detail="Agent is not active")

        # Check for duplicate load numbers in active calls
        active_calls = await supabase_client.get_calls(status='ongoing')
        existing_loads = [c.get('load_number') for c in active_calls if c.get('load_number')]
        if call.load_number in existing_loads:
            raise HTTPException(status_code=409, detail="Load number already has an active call")

        # Validate phone number is not already in an active call (only for traditional calls with phone numbers)
        if call.driver_phone:
            existing_phones = [c.get('driver_phone') for c in active_calls if c.get('driver_phone')]
            if call.driver_phone in existing_phones:
                raise HTTPException(status_code=409, detail="Driver phone number already has an active call")

        # Create call record
        call_dict = call.model_dump()
        call_dict.update({
            "call_status": "created",
            "agent_version": 1,
            "created_by": current_user.get('id')
        })

        created_call = await supabase_client.create_call(call_dict)
        return created_call
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating call: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create call")


@router.post("/{call_id}/end")
async def end_call(
    call_id: str,
    current_user: dict = Depends(get_current_user)
):
    """End an active call."""
    try:
        # Validate UUID format
        try:
            uuid.UUID(call_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid call ID format")

        # Check if call exists
        call = await supabase_client.get_call_by_id(call_id)
        if not call:
            raise HTTPException(status_code=404, detail="Call not found")

        # Check if call is already ended
        if call.get('call_status') in ['ended', 'error']:
            raise HTTPException(status_code=400, detail=f"Call is already {call.get('call_status')}")

        # Check permissions - user can only end their own calls or admin can end any
        user_role = current_user.get('user_metadata', {}).get('role', 'user')
        if user_role != 'admin' and call.get('created_by') != current_user.get('id'):
            raise HTTPException(status_code=403, detail="Insufficient permissions to end this call")

        # Calculate duration if start timestamp exists
        duration_update = {}
        if call.get('start_timestamp'):
            try:
                start_time = datetime.fromisoformat(call['start_timestamp'].replace('Z', '+00:00'))
                end_time = datetime.now()
                duration_ms = int((end_time - start_time).total_seconds() * 1000)
                duration_update['duration_ms'] = duration_ms
            except Exception as e:
                logger.warning(f"Could not calculate call duration: {str(e)}")

        # Update call status to ended
        updated_call = await supabase_client.update_call(call_id, {
            "call_status": "ended",
            "end_timestamp": datetime.now().isoformat(),
            **duration_update
        })

        return {"success": True, "message": "Call ended successfully", "duration_ms": duration_update.get('duration_ms')}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending call {call_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to end call")
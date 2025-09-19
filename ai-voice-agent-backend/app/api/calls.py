from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models.schemas import CallTrigger, Call, CallUpdate, APIResponse
from app.core.database import get_supabase_client
from app.core.auth import get_current_user, get_user_info
from app.services.retell_service import retell_service
from app.services.conversation_service import conversation_service
from app.services.call_polling_service import call_polling_service
from supabase import Client
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/calls/trigger", response_model=APIResponse)
async def trigger_web_call(
    call_data: CallTrigger, 
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Trigger a new web call using Retell AI."""
    try:
        # Create call record in database
        call_record = {
            "agent_id": call_data.agent_id,
            "driver_name": call_data.driver_name,
            "phone_number": call_data.phone_number or "N/A",  # Default for web calls
            "load_number": call_data.load_number,
            "status": "pending",
            "user_id": current_user["id"]  # Associate with current user
        }
        
        result = supabase.table("calls").insert(call_record).execute()
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create call record")
        
        call_id = result.data[0]["id"]
        
        # Get agent data to get retell_agent_id
        agent_result = supabase.table("agents").select("retell_agent_id").eq("id", call_data.agent_id).execute()
        if not agent_result.data or not agent_result.data[0].get("retell_agent_id"):
            raise HTTPException(status_code=400, detail="Agent not found or not configured in Retell AI")
        
        retell_agent_id = agent_result.data[0]["retell_agent_id"]
        
        # Prepare Retell AI web call data
        customer_id = f"driver_{call_data.load_number.replace(' ', '_').replace('-', '_')}" if call_data.load_number else f"driver_{call_id}"
        
        retell_call_data = {
            "agent_id": retell_agent_id,
            "customer_id": customer_id,
            "driver_name": call_data.driver_name,
            "load_number": call_data.load_number,
            "web_call_url": f"http://localhost:3000/call/{call_id}",  # Frontend call page
            "metadata": {
                "call_id": call_id,
                "driver_name": call_data.driver_name,
                "load_number": call_data.load_number
            }
        }
        
        # Add phone_number to metadata if provided (for web calls, this might be optional)
        if call_data.phone_number:
            retell_call_data["phone_number"] = call_data.phone_number
            retell_call_data["metadata"]["phone_number"] = call_data.phone_number
        
        # Create web call with Retell AI using the new method that returns access token
        retell_response = await retell_service.create_web_call_with_access_token(retell_call_data)
        if not retell_response:
            raise HTTPException(status_code=500, detail="Failed to create call with Retell AI")
        
        retell_call_id = retell_response.get("call_id")
        access_token = retell_response.get("access_token")
        call_status = retell_response.get("call_status", "registered")
        
        # Update call record with Retell AI call ID
        supabase.table("calls").update({
            "status": "in_progress",
            "retell_call_id": retell_call_id
        }).eq("id", call_id).execute()
        
        # Start polling for call updates (for localhost development)
        # In production with webhooks, this wouldn't be needed
        import asyncio
        asyncio.create_task(
            call_polling_service.start_polling_for_call(call_id, retell_call_id)
        )
        
        return APIResponse(
            success=True,
            message="Web call triggered successfully",
            data={
                "call_id": call_id, 
                "retell_call_id": retell_call_id,
                "access_token": access_token,
                "call_status": call_status,
                "web_call_url": retell_response.get("web_call_url"),
                "join_url": retell_response.get("join_url"),
                "metadata": retell_response.get("metadata", {}),
                "retell_llm_dynamic_variables": retell_response.get("retell_llm_dynamic_variables", {}),
                "collected_dynamic_variables": retell_response.get("collected_dynamic_variables", {})
            }
        )
        
    except Exception as e:
        logger.error(f"Error triggering call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calls", response_model=APIResponse)
async def get_calls(supabase: Client = Depends(get_supabase_client)):
    """Get all calls."""
    try:
        result = supabase.table("calls").select("*").order("created_at", desc=True).execute()
        return APIResponse(
            success=True,
            message="Calls retrieved successfully",
            data={"calls": result.data or []}
        )
    except Exception as e:
        logger.error(f"Error fetching calls: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calls/{call_id}", response_model=APIResponse)
async def get_call(call_id: str, supabase: Client = Depends(get_supabase_client)):
    """Get a specific call by ID."""
    try:
        result = supabase.table("calls").select("*").eq("id", call_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Call not found")
        return APIResponse(
            success=True,
            message="Call retrieved successfully",
            data=result.data[0]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching call {call_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calls/{call_id}/stats", response_model=APIResponse)
async def get_call_stats(call_id: str, supabase: Client = Depends(get_supabase_client)):
    """Get call statistics from Retell AI by call ID."""
    try:
        # Get call record from database
        result = supabase.table("calls").select("*").eq("id", call_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Call not found")
        
        call_record = result.data[0]
        retell_call_id = call_record.get("retell_call_id")
        
        if not retell_call_id:
            raise HTTPException(status_code=400, detail="Call not associated with Retell AI")
        
        # Get call statistics from Retell AI
        call_stats = await retell_service.get_call(retell_call_id)
        
        if not call_stats:
            raise HTTPException(status_code=500, detail="Failed to retrieve call statistics from Retell AI")
        
        # Extract relevant statistics
        statistics = {
            "call_id": retell_call_id,
            "duration_ms": call_stats.get("duration_ms"),
            "call_cost": call_stats.get("call_cost"),
            "latency": call_stats.get("latency"),
            "disconnection_reason": call_stats.get("disconnection_reason"),
            "call_analysis": call_stats.get("call_analysis"),
            "llm_token_usage": call_stats.get("llm_token_usage"),
            "recording_url": call_stats.get("recording_url"),
            "public_log_url": call_stats.get("public_log_url"),
            "transcript": call_stats.get("transcript"),
            "transcript_object": call_stats.get("transcript_object"),
            "metadata": call_stats.get("metadata"),
            "retell_llm_dynamic_variables": call_stats.get("retell_llm_dynamic_variables"),
            "collected_dynamic_variables": call_stats.get("collected_dynamic_variables")
        }
        
        # Update the call record with the latest statistics
        supabase.table("calls").update({
            "structured_data": {
                **call_record.get("structured_data", {}),
                "call_statistics": statistics
            }
        }).eq("id", call_id).execute()
        
        return APIResponse(
            success=True,
            message="Call statistics retrieved successfully",
            data=statistics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching call statistics for {call_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/calls/{call_id}", response_model=APIResponse)
async def update_call(
    call_id: str, 
    call_update: CallUpdate, 
    supabase: Client = Depends(get_supabase_client)
):
    """Update a call record."""
    try:
        update_data = call_update.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        result = supabase.table("calls").update(update_data).eq("id", call_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Call not found")
        
        return APIResponse(
            success=True,
            message="Call updated successfully",
            data=result.data[0]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating call {call_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

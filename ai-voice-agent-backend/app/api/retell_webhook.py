from fastapi import APIRouter, HTTPException, Depends, Request, Header
from app.models.schemas import RetellWebhookEvent, APIResponse
from app.core.database import get_supabase_client
from app.services.conversation_service import conversation_service
from app.services.retell_service import retell_service
from supabase import Client
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/webhook/retell", response_model=APIResponse)
async def retell_webhook(
    request: Request,
    supabase: Client = Depends(get_supabase_client),
    x_retell_signature: str = Header(None, alias="X-Retell-Signature")
):
    """Handle Retell AI webhook events with signature verification."""
    try:
        # Get raw body for signature verification
        body = await request.body()
        body_str = body.decode('utf-8')
        
        # Verify webhook signature for security
        if x_retell_signature:
            if not retell_service.verify_webhook_signature(body_str, x_retell_signature):
                logger.warning("Invalid webhook signature received")
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse the webhook event
        try:
            event_data = json.loads(body_str)
            event = RetellWebhookEvent(**event_data)
        except Exception as e:
            logger.error(f"Failed to parse webhook event: {e}")
            raise HTTPException(status_code=400, detail="Invalid webhook payload")
        
        logger.info(f"Received Retell webhook: {event.event} for call {event.call_id}")
        
        # Get call record from database
        call_result = supabase.table("calls").select("*").eq("retell_call_id", event.call_id).execute()
        if not call_result.data:
            logger.error(f"Call not found for Retell call ID: {event.call_id}")
            raise HTTPException(status_code=404, detail="Call not found")
        
        call_record = call_result.data[0]
        call_id = call_record["id"]
        
        # Handle different event types
        if event.event == "call_ended":
            await _handle_call_ended(event, call_id, supabase)
        elif event.event == "transcript_updated":
            await _handle_transcript_updated(event, call_id, supabase)
        elif event.event == "call_started":
            await _handle_call_started(event, call_id, supabase)
        elif event.event == "call_analyzed":
            await _handle_call_analyzed(event, call_id, supabase)
        else:
            logger.info(f"Unhandled event type: {event.event}")
        
        return APIResponse(
            success=True,
            message=f"Webhook processed for event: {event.event}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Retell webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _handle_call_ended(event: RetellWebhookEvent, call_id: str, supabase: Client):
    """Handle call ended event."""
    try:
        # Get full call statistics from Retell AI
        call_stats = await retell_service.get_call(event.call_id)
        
        # Get agent configuration for processing
        agent_result = supabase.table("agents").select("*").eq("id", event.agent_id).execute()
        agent_config = agent_result.data[0] if agent_result.data else {}
        
        # Process transcript if available
        structured_data = None
        transcript = event.transcript
        
        # Use transcript from call stats if available (more complete)
        if call_stats and call_stats.get("transcript"):
            transcript = call_stats.get("transcript")
        
        if transcript:
            call_result = conversation_service.process_transcript(
                transcript, 
                agent_config
            )
            structured_data = call_result.dict()
        
        # Prepare update data with call statistics
        update_data = {
            "status": "completed",
            "transcript": transcript,
            "structured_data": structured_data
        }
        
        # Add call statistics if available
        if call_stats:
            # Store call statistics in structured_data
            call_statistics = {
                "duration_ms": call_stats.get("duration_ms"),
                "call_cost": call_stats.get("call_cost"),
                "latency": call_stats.get("latency"),
                "disconnection_reason": call_stats.get("disconnection_reason"),
                "call_analysis": call_stats.get("call_analysis"),
                "llm_token_usage": call_stats.get("llm_token_usage"),
                "recording_url": call_stats.get("recording_url"),
                "public_log_url": call_stats.get("public_log_url")
            }
            
            # Merge call statistics with existing structured_data
            if structured_data:
                structured_data["call_statistics"] = call_statistics
            else:
                structured_data = {"call_statistics": call_statistics}
            
            update_data["structured_data"] = structured_data
            
            logger.info(f"Call {call_id} statistics retrieved: duration={call_stats.get('duration_ms')}ms, cost={call_stats.get('call_cost', {}).get('combined_cost')}")
        
        # Update call record
        supabase.table("calls").update(update_data).eq("id", call_id).execute()
        logger.info(f"Call {call_id} marked as completed with statistics")
        
    except Exception as e:
        logger.error(f"Error handling call ended: {e}")
        # Mark call as failed if processing fails
        supabase.table("calls").update({"status": "failed"}).eq("id", call_id).execute()


async def _handle_transcript_updated(event: RetellWebhookEvent, call_id: str, supabase: Client):
    """Handle transcript updated event."""
    try:
        # Update transcript in real-time
        update_data = {"transcript": event.transcript}
        supabase.table("calls").update(update_data).eq("id", call_id).execute()
        logger.info(f"Transcript updated for call {call_id}")
        
    except Exception as e:
        logger.error(f"Error updating transcript: {e}")


async def _handle_call_started(event: RetellWebhookEvent, call_id: str, supabase: Client):
    """Handle call started event."""
    try:
        # Update call status to in_progress
        update_data = {"status": "in_progress"}
        supabase.table("calls").update(update_data).eq("id", call_id).execute()
        logger.info(f"Call {call_id} marked as in progress")
        
    except Exception as e:
        logger.error(f"Error handling call started: {e}")


async def _handle_call_analyzed(event: RetellWebhookEvent, call_id: str, supabase: Client):
    """Handle call analyzed event."""
    try:
        # This event contains the final analysis and structured data
        if event.call_metadata:
            # Extract structured data from call metadata
            structured_data = event.call_metadata.get("structured_data", {})
            
            # Update call with structured data
            update_data = {
                "structured_data": structured_data,
                "status": "completed"
            }
            supabase.table("calls").update(update_data).eq("id", call_id).execute()
            
            # Also create a call result record
            if structured_data:
                call_result_data = {
                    "call_id": call_id,
                    "call_outcome": structured_data.get("call_outcome", "In-Transit Update"),
                    "driver_status": structured_data.get("driver_status"),
                    "current_location": structured_data.get("current_location"),
                    "eta": structured_data.get("eta"),
                    "delay_reason": structured_data.get("delay_reason"),
                    "unloading_status": structured_data.get("unloading_status"),
                    "pod_reminder_acknowledged": structured_data.get("pod_reminder_acknowledged"),
                    "emergency_type": structured_data.get("emergency_type"),
                    "safety_status": structured_data.get("safety_status"),
                    "injury_status": structured_data.get("injury_status"),
                    "emergency_location": structured_data.get("emergency_location"),
                    "load_secure": structured_data.get("load_secure"),
                    "escalation_status": structured_data.get("escalation_status")
                }
                
                # Remove None values
                call_result_data = {k: v for k, v in call_result_data.items() if v is not None}
                
                supabase.table("call_results").insert(call_result_data).execute()
            
            logger.info(f"Call {call_id} analysis completed and stored")
        
    except Exception as e:
        logger.error(f"Error handling call analyzed: {e}")

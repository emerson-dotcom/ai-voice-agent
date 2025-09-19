"""
Retell AI Webhook Handler for Real-time Conversation Events
"""

import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
import hmac
import hashlib
import time

from app.core.database import get_supabase_client
from app.core.auth import get_current_user
from app.models.schemas import CallUpdate
from app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize conversation service
conversation_service = ConversationService()

@router.post("/webhooks/retell")
async def retell_webhook(
    request: Request,
    supabase = Depends(get_supabase_client)
):
    """
    Handle Retell AI webhook events for real-time conversation processing.
    
    Events handled:
    - call_started: Call begins
    - call_ended: Call ends
    - transcript_updated: Real-time transcript updates
    - function_call: Function calls from the agent
    - error: Error events
    """
    try:
        # Get raw body for signature verification
        body = await request.body()
        
        # Verify webhook signature (if configured)
        signature = request.headers.get("x-retell-signature")
        if signature:
            if not verify_webhook_signature(body, signature):
                logger.warning("Invalid webhook signature")
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse webhook data
        webhook_data = json.loads(body.decode('utf-8'))
        event_type = webhook_data.get("event")
        
        logger.info(f"Received Retell webhook: {event_type}")
        
        # Route to appropriate handler based on event type
        if event_type == "call_started":
            await handle_call_started(webhook_data, supabase)
        elif event_type == "call_ended":
            await handle_call_ended(webhook_data, supabase)
        elif event_type == "transcript_updated":
            await handle_transcript_updated(webhook_data, supabase)
        elif event_type == "function_call":
            await handle_function_call(webhook_data, supabase)
        elif event_type == "error":
            await handle_error(webhook_data, supabase)
        else:
            logger.warning(f"Unknown webhook event type: {event_type}")
        
        return JSONResponse(content={"status": "success"})
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """Verify Retell AI webhook signature."""
    # This would need to be configured with your Retell AI webhook secret
    # For now, we'll skip verification in development
    return True

async def handle_call_started(webhook_data: Dict[str, Any], supabase):
    """Handle call started event."""
    try:
        call_id = webhook_data.get("call_id")
        retell_call_id = webhook_data.get("retell_call_id")
        
        logger.info(f"Call started: {call_id} (Retell: {retell_call_id})")
        
        # Update call status in database
        if call_id:
            supabase.table("calls").update({
                "status": "in_progress",
                "retell_call_id": retell_call_id
            }).eq("id", call_id).execute()
        
    except Exception as e:
        logger.error(f"Error handling call_started: {e}")

async def handle_call_ended(webhook_data: Dict[str, Any], supabase):
    """Handle call ended event."""
    try:
        call_id = webhook_data.get("call_id")
        retell_call_id = webhook_data.get("retell_call_id")
        transcript = webhook_data.get("transcript", "")
        call_metadata = webhook_data.get("metadata", {})
        
        logger.info(f"Call ended: {call_id} (Retell: {retell_call_id})")
        
        # Process the conversation and extract structured data
        structured_data = await conversation_service.process_conversation(
            transcript, call_metadata
        )
        
        # Update call record with results
        if call_id:
            update_data = {
                "status": "completed",
                "transcript": transcript,
                "structured_data": structured_data
            }
            
            supabase.table("calls").update(update_data).eq("id", call_id).execute()
            
            logger.info(f"Call {call_id} completed with structured data: {structured_data}")
        
    except Exception as e:
        logger.error(f"Error handling call_ended: {e}")

async def handle_transcript_updated(webhook_data: Dict[str, Any], supabase):
    """Handle real-time transcript updates."""
    try:
        call_id = webhook_data.get("call_id")
        transcript = webhook_data.get("transcript", "")
        
        # Update transcript in real-time (optional - for live monitoring)
        if call_id:
            supabase.table("calls").update({
                "transcript": transcript
            }).eq("id", call_id).execute()
        
    except Exception as e:
        logger.error(f"Error handling transcript_updated: {e}")

async def handle_function_call(webhook_data: Dict[str, Any], supabase):
    """Handle function calls from the agent."""
    try:
        call_id = webhook_data.get("call_id")
        function_name = webhook_data.get("function_name")
        function_args = webhook_data.get("function_args", {})
        
        logger.info(f"Function call: {function_name} with args: {function_args}")
        
        # Process function call based on function name
        if function_name == "escalate_to_human":
            await handle_escalation(call_id, function_args, supabase)
        elif function_name == "update_driver_status":
            await handle_status_update(call_id, function_args, supabase)
        elif function_name == "log_emergency":
            await handle_emergency_log(call_id, function_args, supabase)
        
    except Exception as e:
        logger.error(f"Error handling function_call: {e}")

async def handle_error(webhook_data: Dict[str, Any], supabase):
    """Handle error events."""
    try:
        call_id = webhook_data.get("call_id")
        error_message = webhook_data.get("error_message", "Unknown error")
        
        logger.error(f"Call error: {call_id} - {error_message}")
        
        # Update call status to failed
        if call_id:
            supabase.table("calls").update({
                "status": "failed",
                "transcript": f"Error: {error_message}"
            }).eq("id", call_id).execute()
        
    except Exception as e:
        logger.error(f"Error handling error event: {e}")

# Function call handlers
async def handle_escalation(call_id: str, args: Dict[str, Any], supabase):
    """Handle escalation to human dispatcher."""
    logger.info(f"Escalating call {call_id} to human dispatcher")
    # Implementation for escalation logic

async def handle_status_update(call_id: str, args: Dict[str, Any], supabase):
    """Handle driver status updates."""
    logger.info(f"Updating driver status for call {call_id}: {args}")
    # Implementation for status update logic

async def handle_emergency_log(call_id: str, args: Dict[str, Any], supabase):
    """Handle emergency logging."""
    logger.info(f"Logging emergency for call {call_id}: {args}")
    # Implementation for emergency logging logic

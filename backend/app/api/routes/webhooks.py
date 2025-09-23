"""
Webhook endpoints for Retell AI integration.
Handles real-time call events and conversation flow.
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
import hashlib
import hmac
import logging
from app.core.config import settings
from app.services.conversation_state_service import conversation_service
from app.services.conversation_flow_service import conversation_flow_service
from app.services.llm_service import llm_service
from app.services.call_service import CallService
from app.services.agent_service import AgentService
from app.services.retell_client import get_retell_client
from app.core.database import supabase_client
from app.models.agent import ScenarioType
from datetime import datetime

logger = logging.getLogger(__name__)
call_service = CallService()
agent_service = AgentService()

router = APIRouter()


class WebhookEvent(BaseModel):
    """Base webhook event model."""
    event: str
    call_id: str
    agent_id: str = None
    data: Dict[str, Any] = {}


@router.post("/retell/call-started")
async def handle_call_started(request: Request):
    """Handle call started webhook from Retell AI."""
    try:
        # Verify webhook signature
        if not await _verify_webhook_signature(request):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

        payload = await request.json()
        call_id = payload.get("call_id")
        agent_id = payload.get("agent_id")

        if not call_id:
            raise HTTPException(status_code=400, detail="Missing call_id")

        # Update call status to ongoing
        await call_service.update_call_status(call_id, "ongoing")

        # Get agent to determine scenario type
        agent = await agent_service.get_agent(agent_id) if agent_id else None
        scenario_type = ScenarioType(agent.get("scenario_type", "driver_checkin")) if agent else ScenarioType.DRIVER_CHECKIN

        # Initialize conversation state
        await conversation_service.initialize_conversation(call_id, agent_id, scenario_type)

        logger.info(f"Call started: {call_id} with agent {agent_id}")
        return {"status": "success", "message": "Call started event processed"}

    except Exception as e:
        logger.error(f"Error handling call started: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retell/call-ended")
async def handle_call_ended(request: Request):
    """Handle call ended webhook from Retell AI."""
    try:
        # Verify webhook signature
        if not await _verify_webhook_signature(request):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

        payload = await request.json()
        call_id = payload.get("call_id")
        transcript = payload.get("transcript", "")
        call_length_ms = payload.get("call_length_ms", 0)

        if not call_id:
            raise HTTPException(status_code=400, detail="Missing call_id")

        # Update call status and store transcript
        await call_service.update_call_status(call_id, "completed")
        await call_service.update_call_transcript(call_id, transcript, call_length_ms)

        # Automatically fetch and store complete call data from Retell
        await _fetch_and_store_complete_call_data(call_id)

        # Trigger post-call analysis
        await _trigger_call_analysis(call_id, transcript)

        # End conversation state
        await conversation_service.end_conversation(call_id)

        logger.info(f"Call ended: {call_id}, duration: {call_length_ms}ms")
        return {"status": "success", "message": "Call ended event processed"}

    except Exception as e:
        logger.error(f"Error handling call ended: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retell/call-analyzed")
async def handle_call_analyzed(request: Request):
    """Handle call analysis completed webhook from Retell AI."""
    try:
        # Verify webhook signature
        if not await _verify_webhook_signature(request):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

        payload = await request.json()
        call_id = payload.get("call_id")
        analysis_data = payload.get("analysis", {})

        if not call_id:
            raise HTTPException(status_code=400, detail="Missing call_id")

        # Store call analysis results
        await call_service.store_call_analysis(call_id, analysis_data)

        logger.info(f"Call analysis completed: {call_id}")
        return {"status": "success", "message": "Call analysis event processed"}

    except Exception as e:
        logger.error(f"Error handling call analyzed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retell/response")
async def handle_llm_response(request: Request):
    """Handle LLM response webhook for real-time conversation flow."""
    try:
        # Verify webhook signature
        if not await _verify_webhook_signature(request):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

        payload = await request.json()
        call_id = payload.get("call_id")
        user_message = payload.get("transcript", "")
        response_id = payload.get("response_id", 0)

        if not call_id:
            logger.warning("Missing call_id in response webhook")
            return _get_default_response(response_id)

        # Process user message and generate response
        response = await conversation_flow_service.process_user_message(
            call_id=call_id,
            user_message=user_message,
            response_id=response_id
        )

        logger.info(f"Generated response for call {call_id}: {response.get('response', '')[:50]}...")
        return response

    except Exception as e:
        logger.error(f"Error handling LLM response: {str(e)}")
        return _get_default_response(payload.get("response_id", 0) if payload else 0)


async def _verify_webhook_signature(request: Request) -> bool:
    """Verify webhook signature from Retell AI."""
    try:
        # For development, skip signature verification
        if settings.ENVIRONMENT == "development":
            return True

        # Get signature from header
        signature = request.headers.get("x-retell-signature")
        if not signature:
            return False

        # Get request body
        body = await request.body()

        # Calculate expected signature
        expected_signature = hmac.new(
            settings.RETELL_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    except Exception as e:
        logger.error(f"Error verifying webhook signature: {str(e)}")
        return False


async def _trigger_call_analysis(call_id: str, transcript: str):
    """Trigger post-call analysis using LLM service."""
    try:
        # Get conversation context to determine scenario type
        context = conversation_service.get_conversation(call_id)
        if not context:
            # Fallback: get from call record
            call = await call_service.get_call(call_id)
            if call and call.get("agent_id"):
                agent = await agent_service.get_agent(call["agent_id"])
                scenario_type = ScenarioType(agent.get("scenario_type", "driver_checkin")) if agent else ScenarioType.DRIVER_CHECKIN
            else:
                scenario_type = ScenarioType.DRIVER_CHECKIN
        else:
            scenario_type = context.scenario_type

        # Extract structured data using LLM
        analysis_result = await llm_service.extract_structured_data(
            transcript=transcript,
            scenario_type=scenario_type,
            context=context.context if context else {}
        )

        # Store analysis results
        await call_service.store_call_analysis(call_id, analysis_result)

        logger.info(f"Analysis completed for call {call_id}")

    except Exception as e:
        logger.error(f"Error triggering call analysis: {str(e)}")


async def _fetch_and_store_complete_call_data(call_id: str):
    """Fetch complete call data from Retell and store in database."""
    try:
        logger.info(f"Fetching complete call data from Retell for call: {call_id}")

        # Find the call in our database
        db_call = await supabase_client.get_call_by_retell_id(call_id)
        if not db_call:
            logger.warning(f"Call {call_id} not found in database")
            return

        # Fetch complete data from Retell
        retell_client = get_retell_client()
        call_data = await retell_client.get_call(call_id)

        if not call_data:
            logger.warning(f"No data returned from Retell for call {call_id}")
            return

        # Prepare update data
        update_data = {}

        # Map Retell fields to database fields
        if call_data.get('transcript'):
            update_data['transcript'] = call_data['transcript']
        if call_data.get('recording_url'):
            update_data['recording_url'] = call_data['recording_url']
        if call_data.get('duration_ms'):
            update_data['duration_ms'] = call_data['duration_ms']
        if call_data.get('start_timestamp'):
            # Convert timestamp from milliseconds to ISO string
            start_dt = datetime.fromtimestamp(call_data['start_timestamp'] / 1000)
            update_data['start_timestamp'] = start_dt.isoformat()
        if call_data.get('end_timestamp'):
            # Convert timestamp from milliseconds to ISO string
            end_dt = datetime.fromtimestamp(call_data['end_timestamp'] / 1000)
            update_data['end_timestamp'] = end_dt.isoformat()
        if call_data.get('disconnection_reason'):
            update_data['disconnection_reason'] = call_data['disconnection_reason']
        if call_data.get('call_analysis'):
            # Convert CallAnalysis object to dict for JSON serialization
            analysis = call_data['call_analysis']
            if hasattr(analysis, '__dict__'):
                update_data['call_analysis'] = analysis.__dict__
            elif hasattr(analysis, 'model_dump'):
                update_data['call_analysis'] = analysis.model_dump()
            elif hasattr(analysis, 'dict'):
                update_data['call_analysis'] = analysis.dict()
            else:
                # Fallback: try to convert to dict
                try:
                    update_data['call_analysis'] = dict(analysis)
                except:
                    # Last resort: convert to string
                    update_data['call_analysis'] = str(analysis)

        # Update call status based on Retell status
        if call_data.get('call_status'):
            # Map Retell statuses to our database statuses
            retell_status = call_data['call_status']
            if retell_status == 'ended':
                update_data['call_status'] = 'ended'
            elif retell_status == 'ongoing':
                update_data['call_status'] = 'ongoing'
            elif retell_status == 'registered':
                update_data['call_status'] = 'registered'
            elif retell_status == 'error':
                update_data['call_status'] = 'error'
            else:
                update_data['call_status'] = retell_status

        # Update database with complete call data
        if update_data:
            await supabase_client.update_call(db_call['id'], update_data)
            logger.info(f"Successfully stored complete call data for {call_id}")
        else:
            logger.info(f"No data to update for call {call_id}")

    except Exception as e:
        logger.error(f"Error fetching and storing complete call data for {call_id}: {str(e)}", exc_info=True)


def _get_default_response(response_id: int) -> Dict[str, Any]:
    """Get default response for error cases - WEB CALL ONLY."""
    return {
        "response": "I understand. Can you tell me more about your current situation?",
        "response_id": response_id,
        "end_call": False  # Keep web call active
    }
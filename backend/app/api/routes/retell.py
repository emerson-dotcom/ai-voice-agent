"""
Retell AI integration API endpoints.
Handles LLM creation, agent management, and voice configuration.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.retell_client import get_retell_client
from app.core.database import supabase_client
from app.api.dependencies import get_current_user
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()


class LLMCreate(BaseModel):
    """LLM creation model."""
    agent_id: str
    general_prompt: str
    begin_message: Optional[str] = None
    model_temperature: Optional[float] = 0.8
    model: Optional[str] = "gpt-4o"


class LLMResponse(BaseModel):
    """LLM response model."""
    llm_id: str
    agent_id: str
    version: int
    is_published: bool
    last_modification_timestamp: int


class AgentCreateRetell(BaseModel):
    """Retell agent creation model."""
    agent_id: str
    llm_id: str
    voice_id: str
    voice_temperature: Optional[float] = 1.0
    voice_speed: Optional[float] = 1.0
    responsiveness: Optional[float] = 1.0
    interruption_sensitivity: Optional[float] = 1.0
    enable_backchannel: Optional[bool] = True
    backchannel_frequency: Optional[float] = 0.8
    backchannel_words: Optional[List[str]] = ["yeah", "uh-huh", "mm-hmm"]
    voice_model: Optional[str] = None
    agent_name: Optional[str] = None


class RetellAgentResponse(BaseModel):
    """Retell agent response model."""
    retell_agent_id: str
    agent_id: str
    version: int
    is_published: bool
    last_modification_timestamp: int


class VoiceResponse(BaseModel):
    """Voice response model."""
    voice_id: str
    voice_name: str
    provider: str
    accent: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[str] = None
    preview_audio_url: Optional[str] = None


@router.post("/llm", response_model=LLMResponse)
async def create_llm(llm_data: LLMCreate):
    """Create a new Retell LLM for an agent."""
    try:
        # Get agent data from database
        agent = await supabase_client.get_agent_by_id(llm_data.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Build LLM configuration
        retell_client = get_retell_client()

        # Prepare agent data with only non-None overrides from API request
        agent_config = {**agent}
        agent_config["general_prompt"] = llm_data.general_prompt
        agent_config["voice_temperature"] = llm_data.model_temperature
        agent_config["model"] = llm_data.model

        # Only override begin_message if explicitly provided in API request
        if llm_data.begin_message is not None:
            agent_config["begin_message"] = llm_data.begin_message

        llm_config = retell_client.build_llm_config(agent_config)

        # Create LLM in Retell
        retell_response = await retell_client.create_retell_llm(llm_config)

        # Update agent with LLM ID
        await supabase_client.update_agent(llm_data.agent_id, {
            "retell_llm_id": retell_response["llm_id"]
        })

        return LLMResponse(
            llm_id=retell_response["llm_id"],
            agent_id=llm_data.agent_id,
            version=retell_response["version"],
            is_published=retell_response["is_published"],
            last_modification_timestamp=retell_response["last_modification_timestamp"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating LLM: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create LLM")


@router.put("/llm/{llm_id}", response_model=LLMResponse)
async def update_llm(llm_id: str, llm_data: LLMCreate):
    """Update an existing Retell LLM."""
    try:
        # Get agent data from database
        agent = await supabase_client.get_agent_by_id(llm_data.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Build LLM configuration
        retell_client = get_retell_client()

        # Prepare agent data with only non-None overrides from API request
        agent_config = {**agent}
        agent_config["general_prompt"] = llm_data.general_prompt
        agent_config["voice_temperature"] = llm_data.model_temperature
        agent_config["model"] = llm_data.model

        # Only override begin_message if explicitly provided in API request
        if llm_data.begin_message is not None:
            agent_config["begin_message"] = llm_data.begin_message

        llm_config = retell_client.build_llm_config(agent_config)

        # Update LLM in Retell
        retell_response = await retell_client.update_retell_llm(llm_id, llm_config)

        return LLMResponse(
            llm_id=retell_response["llm_id"],
            agent_id=llm_data.agent_id,
            version=retell_response["version"],
            is_published=retell_response["is_published"],
            last_modification_timestamp=retell_response["last_modification_timestamp"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating LLM {llm_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update LLM")


@router.delete("/llm/{llm_id}")
async def delete_llm(llm_id: str):
    """Delete a Retell LLM."""
    try:
        # Delete LLM in Retell
        retell_client = get_retell_client()
        success = await retell_client.delete_retell_llm(llm_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete LLM")

        return {"success": True, "message": "LLM deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting LLM {llm_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete LLM")


@router.post("/agent", response_model=RetellAgentResponse)
async def create_retell_agent(agent_data: AgentCreateRetell):
    """Create a new Retell agent."""
    try:
        # Get agent data from database
        agent = await supabase_client.get_agent_by_id(agent_data.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Build agent configuration
        retell_client = get_retell_client()
        agent_config = retell_client.build_agent_config({
            **agent,
            **agent_data.model_dump()
        }, agent_data.llm_id)

        # Create agent in Retell
        retell_response = await retell_client.create_agent(agent_config)

        # Update agent with Retell agent ID
        await supabase_client.update_agent(agent_data.agent_id, {
            "retell_agent_id": retell_response["agent_id"]
        })

        return RetellAgentResponse(
            retell_agent_id=retell_response["agent_id"],
            agent_id=agent_data.agent_id,
            version=retell_response["version"],
            is_published=retell_response["is_published"],
            last_modification_timestamp=retell_response["last_modification_timestamp"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating Retell agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create Retell agent")


@router.put("/agent/{retell_agent_id}", response_model=RetellAgentResponse)
async def update_retell_agent(retell_agent_id: str, agent_data: AgentCreateRetell):
    """Update an existing Retell agent."""
    try:
        # Get agent data from database
        agent = await supabase_client.get_agent_by_id(agent_data.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Build agent configuration
        retell_client = get_retell_client()
        agent_config = retell_client.build_agent_config({
            **agent,
            **agent_data.model_dump()
        }, agent_data.llm_id)

        # Update agent in Retell
        retell_response = await retell_client.update_agent(retell_agent_id, agent_config)

        return RetellAgentResponse(
            retell_agent_id=retell_response["agent_id"],
            agent_id=agent_data.agent_id,
            version=retell_response["version"],
            is_published=retell_response["is_published"],
            last_modification_timestamp=retell_response["last_modification_timestamp"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Retell agent {retell_agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update Retell agent")


@router.delete("/agent/{retell_agent_id}")
async def delete_retell_agent(retell_agent_id: str):
    """Delete a Retell agent."""
    try:
        # Delete agent in Retell
        retell_client = get_retell_client()
        success = await retell_client.delete_agent(retell_agent_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete Retell agent")

        return {"success": True, "message": "Retell agent deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting Retell agent {retell_agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete Retell agent")


@router.get("/call/{retell_call_id}/data")
async def get_retell_call_data(
    retell_call_id: str,
    force_refresh: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Fetch complete call data - from database first, then Retell AI if needed."""
    try:
        logger.info(f"Getting call data for call ID: {retell_call_id}")

        # First, check if we already have complete data in our database
        db_call = await supabase_client.get_call_by_retell_id(retell_call_id)

        if db_call and not force_refresh:
            # Check if we have complete data (transcript means call is complete)
            if db_call.get('transcript') and db_call.get('call_status') in ['ended', 'completed']:
                logger.info(f"Found complete call data in database for {retell_call_id}")
                return {
                    "source": "database",
                    "call_id": db_call.get('retell_call_id'),
                    "transcript": db_call.get('transcript'),
                    "recording_url": db_call.get('recording_url'),
                    "duration_ms": db_call.get('duration_ms'),
                    "start_timestamp": db_call.get('start_timestamp'),
                    "end_timestamp": db_call.get('end_timestamp'),
                    "disconnection_reason": db_call.get('disconnection_reason'),
                    "call_analysis": db_call.get('call_analysis'),
                    "call_status": db_call.get('call_status'),
                    "metadata": db_call.get('metadata', {}),
                    "retell_llm_dynamic_variables": db_call.get('retell_llm_dynamic_variables', {})
                }

        # If no complete data in database, fetch from Retell
        logger.info(f"Fetching fresh call data from Retell for call ID: {retell_call_id}")
        retell_client = get_retell_client()
        call_data = await retell_client.get_call(retell_call_id)
        call_data["source"] = "retell"

        logger.info(f"Successfully retrieved call data from Retell: {call_data.get('call_id')}")
        logger.info(f"Call data keys: {list(call_data.keys())}")
        logger.info(f"Has transcript: {bool(call_data.get('transcript'))}")
        logger.info(f"Call status: {call_data.get('call_status')}")

        # Update our database with the new data if we have the call
        if call_data:
            try:
                # Find the call in our database by retell_call_id
                logger.info(f"Looking for call in database with retell_call_id: {retell_call_id}")
                db_call = await supabase_client.get_call_by_retell_id(retell_call_id)

                if db_call:
                    logger.info(f"Found database call: {db_call['id']}")
                    # Update our database call with the Retell data
                    update_data = {}

                    # Map Retell fields to our database fields
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
                    if call_data.get('call_status'):
                        update_data['call_status'] = call_data['call_status']

                    if update_data:
                        logger.info(f"Updating database with data: {list(update_data.keys())}")
                        try:
                            logger.info(f"Before update - DB call: {db_call}")
                            logger.info(f"Update data: {update_data}")
                            updated_call = await supabase_client.update_call(db_call['id'], update_data)
                            logger.info(f"Successfully updated database call {db_call['id']} with Retell data")
                            logger.info(f"Updated call result: {updated_call}")
                            call_data["database_update_success"] = True
                            call_data["updated_fields"] = list(update_data.keys())
                            call_data["updated_call"] = updated_call  # Return the updated call data
                        except Exception as update_error:
                            logger.error(f"Database update failed for call {db_call['id']}: {str(update_error)}", exc_info=True)
                            call_data["database_update_success"] = False
                            call_data["database_update_error"] = str(update_error)
                    else:
                        logger.info("No update data to apply to database")
                else:
                    logger.warning(f"Call with retell_call_id {retell_call_id} not found in database")

            except Exception as db_error:
                logger.error(f"Failed to update database with Retell data: {str(db_error)}", exc_info=True)
                # Add the error to the response so we can see what's failing
                call_data["database_update_error"] = str(db_error)

        return call_data

    except Exception as e:
        logger.error(f"Error fetching call data from Retell: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch call data: {str(e)}")


@router.get("/llms/compare")
async def compare_llms(current_user: dict = Depends(get_current_user)):
    """Compare LLMs in database with those in Retell AI."""
    try:
        logger.info("Comparing LLMs between database and Retell")

        # Get all agents from database (which contain LLM info)
        db_agents = await supabase_client.get_agents()

        # Get LLMs from Retell
        retell_client = get_retell_client()
        retell_llms = []

        try:
            # Try to list LLMs from Retell
            llms_response = retell_client.client.llm.list()
            retell_llms = [
                {
                    "llm_id": llm.llm_id,
                    "version": llm.version,
                    "is_published": llm.is_published,
                    "last_modification_timestamp": llm.last_modification_timestamp,
                    "general_prompt": getattr(llm, 'general_prompt', None),
                    "model": getattr(llm, 'model', None)
                }
                for llm in llms_response
            ]
        except Exception as e:
            logger.warning(f"Could not fetch LLMs from Retell: {str(e)}")

        # Compare and create report
        db_llm_ids = {agent.get("retell_llm_id"): agent for agent in db_agents if agent.get("retell_llm_id")}
        retell_llm_ids = {llm["llm_id"]: llm for llm in retell_llms}

        comparison = {
            "database_agents_count": len(db_agents),
            "database_agents_with_llm": len(db_llm_ids),
            "retell_llms_count": len(retell_llms),
            "comparison_results": {
                "in_both": [],
                "only_in_database": [],
                "only_in_retell": [],
                "mismatched": []
            }
        }

        # Check which LLMs exist in both
        for llm_id, db_agent in db_llm_ids.items():
            if llm_id in retell_llm_ids:
                retell_llm = retell_llm_ids[llm_id]
                comparison["comparison_results"]["in_both"].append({
                    "llm_id": llm_id,
                    "agent_name": db_agent.get("name"),
                    "agent_id": db_agent.get("id"),
                    "retell_version": retell_llm.get("version"),
                    "retell_published": retell_llm.get("is_published")
                })
            else:
                comparison["comparison_results"]["only_in_database"].append({
                    "llm_id": llm_id,
                    "agent_name": db_agent.get("name"),
                    "agent_id": db_agent.get("id"),
                    "issue": "LLM exists in database but not found in Retell"
                })

        # Check which LLMs exist only in Retell
        for llm_id, retell_llm in retell_llm_ids.items():
            if llm_id not in db_llm_ids:
                comparison["comparison_results"]["only_in_retell"].append({
                    "llm_id": llm_id,
                    "retell_version": retell_llm.get("version"),
                    "retell_model": retell_llm.get("model"),
                    "issue": "LLM exists in Retell but no corresponding agent in database"
                })

        return comparison

    except Exception as e:
        logger.error(f"Error comparing LLMs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to compare LLMs: {str(e)}")


@router.get("/agents/compare")
async def compare_agents(current_user: dict = Depends(get_current_user)):
    """Compare agents in database with those in Retell AI."""
    try:
        logger.info("Comparing agents between database and Retell")

        # Get all agents from database
        db_agents = await supabase_client.get_agents()

        # Get agents from Retell
        retell_client = get_retell_client()
        retell_agents = []

        try:
            # Try to list agents from Retell
            agents_response = retell_client.client.agent.list()
            retell_agents = [
                {
                    "agent_id": agent.agent_id,
                    "version": agent.version,
                    "is_published": agent.is_published,
                    "last_modification_timestamp": agent.last_modification_timestamp,
                    "voice_id": getattr(agent, 'voice_id', None),
                    "response_engine": getattr(agent, 'response_engine', None)
                }
                for agent in agents_response
            ]
        except Exception as e:
            logger.warning(f"Could not fetch agents from Retell: {str(e)}")

        # Compare and create report
        db_agent_ids = {agent.get("retell_agent_id"): agent for agent in db_agents if agent.get("retell_agent_id")}
        retell_agent_ids = {agent["agent_id"]: agent for agent in retell_agents}

        comparison = {
            "database_agents_count": len(db_agents),
            "database_agents_with_retell_id": len(db_agent_ids),
            "retell_agents_count": len(retell_agents),
            "comparison_results": {
                "in_both": [],
                "only_in_database": [],
                "only_in_retell": [],
                "mismatched": []
            }
        }

        # Check which agents exist in both
        for agent_id, db_agent in db_agent_ids.items():
            if agent_id in retell_agent_ids:
                retell_agent = retell_agent_ids[agent_id]
                comparison["comparison_results"]["in_both"].append({
                    "agent_id": agent_id,
                    "db_agent_name": db_agent.get("name"),
                    "db_agent_id": db_agent.get("id"),
                    "retell_version": retell_agent.get("version"),
                    "retell_published": retell_agent.get("is_published"),
                    "voice_match": db_agent.get("voice_id") == retell_agent.get("voice_id")
                })
            else:
                comparison["comparison_results"]["only_in_database"].append({
                    "agent_id": agent_id,
                    "db_agent_name": db_agent.get("name"),
                    "db_agent_id": db_agent.get("id"),
                    "issue": "Agent exists in database but not found in Retell"
                })

        # Check which agents exist only in Retell
        for agent_id, retell_agent in retell_agent_ids.items():
            if agent_id not in db_agent_ids:
                comparison["comparison_results"]["only_in_retell"].append({
                    "agent_id": agent_id,
                    "retell_version": retell_agent.get("version"),
                    "retell_voice_id": retell_agent.get("voice_id"),
                    "issue": "Agent exists in Retell but no corresponding agent in database"
                })

        return comparison

    except Exception as e:
        logger.error(f"Error comparing agents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to compare agents: {str(e)}")


@router.get("/llm/{llm_id}/details")
async def get_llm_details(llm_id: str, current_user: dict = Depends(get_current_user)):
    """Get detailed LLM information from Retell AI."""
    try:
        logger.info(f"Fetching LLM details from Retell for LLM: {llm_id}")

        retell_client = get_retell_client()

        # Get LLM details from Retell
        llm_response = retell_client.client.llm.retrieve(llm_id)

        # Convert to dictionary with all available fields
        llm_details = {
            "llm_id": llm_response.llm_id,
            "version": llm_response.version,
            "is_published": llm_response.is_published,
            "last_modification_timestamp": llm_response.last_modification_timestamp,
            "general_prompt": getattr(llm_response, 'general_prompt', None),
            "model": getattr(llm_response, 'model', None),
            "model_temperature": getattr(llm_response, 'model_temperature', None),
            "begin_message": getattr(llm_response, 'begin_message', None),
            "default_dynamic_variables": getattr(llm_response, 'default_dynamic_variables', None),
            "states": getattr(llm_response, 'states', None),
            "starting_state": getattr(llm_response, 'starting_state', None),
            "general_tools": getattr(llm_response, 'general_tools', None),
            "inbound_dynamic_variables_webhook_url": getattr(llm_response, 'inbound_dynamic_variables_webhook_url', None),
            "outbound_dynamic_variables_webhook_url": getattr(llm_response, 'outbound_dynamic_variables_webhook_url', None)
        }

        # Also get corresponding database agent if it exists
        db_agents = await supabase_client.get_agents()
        corresponding_agent = None
        for agent in db_agents:
            if agent.get("retell_llm_id") == llm_id:
                corresponding_agent = {
                    "agent_id": agent.get("id"),
                    "agent_name": agent.get("name"),
                    "scenario_type": agent.get("scenario_type"),
                    "voice_id": agent.get("voice_id"),
                    "is_active": agent.get("is_active")
                }
                break

        return {
            "retell_llm": llm_details,
            "corresponding_database_agent": corresponding_agent,
            "source": "retell"
        }

    except Exception as e:
        logger.error(f"Error fetching LLM details from Retell: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch LLM details: {str(e)}")


@router.get("/voices", response_model=List[VoiceResponse])
async def list_voices():
    """List available voices from Retell AI."""
    try:
        retell_client = get_retell_client()
        voices = await retell_client.list_voices()
        return voices

    except Exception as e:
        logger.error(f"Error fetching voices: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch voices")


@router.post("/call/web")
async def create_web_call(call_data: dict):
    """Create a new web call with Retell AI."""
    try:
        logger.info(f"Received web call request: {call_data}")

        # Get agent data from database
        agent_id = call_data.get("agent_id")
        if not agent_id:
            raise HTTPException(status_code=400, detail="Agent ID is required")

        agent = await supabase_client.get_agent_by_id(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        logger.info(f"Found agent: {agent.get('name')} with retell_agent_id: {agent.get('retell_agent_id')}")

        if not agent.get("retell_agent_id"):
            raise HTTPException(status_code=400, detail="Agent does not have a Retell agent ID")

        # Get dynamic variables for LLM template substitution
        dynamic_vars = call_data.get("dynamic_variables", {})

        # Create web call configuration with dynamic variables
        call_config = {
            "agent_id": agent["retell_agent_id"],
            "metadata": call_data.get("metadata", {}),
            "retell_llm_dynamic_variables": dynamic_vars
        }

        logger.info(f"Prepared call config: {call_config}")

        # Get retell client and create web call
        retell_client = get_retell_client()
        logger.info("Got retell client, attempting to create web call...")
        retell_response = await retell_client.create_web_call(call_config)

        logger.info(f"Retell response: {retell_response}")
        logger.info(f"Retell call_status: '{retell_response['call_status']}'")

        # Store call record in database
        metadata = call_data.get("metadata", {})
        call_record = {
            "retell_call_id": retell_response["call_id"],
            "retell_access_token": retell_response["access_token"],
            "agent_id": agent_id,
            "agent_version": 1,
            "call_status": retell_response["call_status"],  # Use status from Retell API
            "metadata": metadata,
            "retell_llm_dynamic_variables": call_data.get("dynamic_variables", {}),  # Preserve dynamic variables
            # Extract driver info from metadata
            "driver_name": metadata.get("driver_name"),
            "driver_phone": metadata.get("driver_phone"),
            "load_number": metadata.get("load_number")
        }

        logger.info(f"Call record to be inserted: {call_record}")

        created_call = await supabase_client.create_call(call_record)
        logger.info(f"Created call record: {created_call}")

        return {
            "call_id": created_call["id"],
            "retell_call_id": retell_response["call_id"],
            "access_token": retell_response["access_token"],
            "agent_id": agent_id,
            "call_status": retell_response["call_status"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating web call: {str(e)}", exc_info=True)
        # Return the actual error message for debugging
        raise HTTPException(status_code=500, detail=str(e))
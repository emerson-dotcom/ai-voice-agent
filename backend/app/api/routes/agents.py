"""
Agent management API endpoints.
Handles CRUD operations for voice agents.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, validator
from app.core.database import supabase_client
from app.services.retell_client import get_retell_client
from app.api.dependencies import get_current_user
import logging
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()


class AgentBase(BaseModel):
    """Base agent model for API requests."""
    name: str
    description: Optional[str] = None
    general_prompt: str
    begin_message: Optional[str] = None
    voice_id: str
    voice_model: Optional[str] = None
    voice_temperature: float = 1.0
    voice_speed: float = 1.0
    enable_backchannel: bool = True
    backchannel_frequency: float = 0.8
    backchannel_words: List[str] = ["yeah", "uh-huh", "mm-hmm"]
    interruption_sensitivity: float = 1.0
    responsiveness: float = 1.0
    scenario_type: str


class AgentCreate(AgentBase):
    """Agent creation model."""

    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Agent name must be at least 3 characters long')
        if len(v) > 100:
            raise ValueError('Agent name must not exceed 100 characters')
        return v.strip()

    @validator('general_prompt')
    def validate_prompt(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('General prompt must be at least 10 characters long')
        if len(v) > 5000:
            raise ValueError('General prompt must not exceed 5000 characters')
        return v.strip()

    @validator('voice_temperature')
    def validate_temperature(cls, v):
        if v < 0.1 or v > 2.0:
            raise ValueError('Voice temperature must be between 0.1 and 2.0')
        return v

    @validator('voice_speed')
    def validate_speed(cls, v):
        if v < 0.5 or v > 2.0:
            raise ValueError('Voice speed must be between 0.5 and 2.0')
        return v

    @validator('scenario_type')
    def validate_scenario(cls, v):
        valid_scenarios = ['driver_checkin', 'emergency_protocol', 'custom']
        if v not in valid_scenarios:
            raise ValueError(f'Scenario type must be one of: {valid_scenarios}')
        return v


class AgentUpdate(BaseModel):
    """Agent update model - all fields optional."""
    name: Optional[str] = None
    description: Optional[str] = None
    general_prompt: Optional[str] = None
    begin_message: Optional[str] = None
    voice_id: Optional[str] = None
    voice_model: Optional[str] = None
    voice_temperature: Optional[float] = None
    voice_speed: Optional[float] = None
    enable_backchannel: Optional[bool] = None
    backchannel_frequency: Optional[float] = None
    backchannel_words: Optional[List[str]] = None
    interruption_sensitivity: Optional[float] = None
    responsiveness: Optional[float] = None
    scenario_type: Optional[str] = None
    is_active: Optional[bool] = None


class AgentResponse(AgentBase):
    """Agent response model."""
    id: str
    retell_llm_id: Optional[str] = None
    retell_agent_id: Optional[str] = None
    is_active: bool
    created_at: str
    updated_at: str


@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    scenario_type: Optional[str] = Query(None, description="Filter by scenario type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: dict = Depends(get_current_user)
):
    """List all agents with optional filtering."""
    try:
        agents = await supabase_client.get_agents(
            scenario_type=scenario_type,
            is_active=is_active
        )

        # Clean up agents data to ensure proper types
        cleaned_agents = []
        for agent in agents:
            cleaned_agent = {
                **agent,
                'retell_llm_id': agent.get('retell_llm_id') or None,
                'retell_agent_id': agent.get('retell_agent_id') or None,
                'is_active': bool(agent.get('is_active', True)),
                'created_at': str(agent.get('created_at', '')),
                'updated_at': str(agent.get('updated_at', '')),
                # Ensure begin_message is never None for API response
                'begin_message': agent.get('begin_message') or '',
                'description': agent.get('description') or '',
                'voice_model': agent.get('voice_model') or None
            }
            cleaned_agents.append(cleaned_agent)

        return cleaned_agents
    except Exception as e:
        logger.error(f"Error fetching agents: {str(e)}")
        logger.error(f"Exception details: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch agents")


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific agent by ID."""
    try:
        # Validate UUID format
        try:
            uuid.UUID(agent_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid agent ID format")

        agent = await supabase_client.get_agent_by_id(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch agent")


@router.post("/", response_model=AgentResponse)
async def create_agent(
    agent: AgentCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new agent with Retell LLM and Agent integration."""
    try:
        # Check if agent name already exists
        existing_agents = await supabase_client.get_agents()
        existing_names = [a.get('name', '').lower() for a in existing_agents]
        if agent.name.lower() in existing_names:
            raise HTTPException(status_code=409, detail="Agent with this name already exists")

        # Create agent record in database first
        agent_dict = agent.model_dump()
        agent_dict['created_by'] = current_user.get('id')
        created_agent = await supabase_client.create_agent(agent_dict)

        # Create Retell LLM
        try:
            retell_client = get_retell_client()
            llm_config = retell_client.build_llm_config(created_agent)
            retell_llm = await retell_client.create_retell_llm(llm_config)

            # Create Retell Agent
            agent_config = retell_client.build_agent_config(created_agent, retell_llm["llm_id"])
            retell_agent = await retell_client.create_agent(agent_config)

            # Update agent with Retell IDs
            updated_agent = await supabase_client.update_agent(created_agent["id"], {
                "retell_llm_id": retell_llm["llm_id"],
                "retell_agent_id": retell_agent["agent_id"]
            })

            return updated_agent

        except Exception as retell_error:
            # If Retell creation fails, delete the database agent and return error
            logger.error(f"Failed to create Retell components for agent {created_agent['id']}: {str(retell_error)}")

            # Clean up: delete the database agent since Retell creation failed
            try:
                await supabase_client.delete_agent(created_agent["id"])
                logger.info(f"Cleaned up database agent {created_agent['id']} after Retell failure")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup agent {created_agent['id']}: {str(cleanup_error)}")

            # Return a proper error to the frontend
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create voice agent: {str(retell_error)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create agent")


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    agent: AgentUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing agent and sync with Retell."""
    try:
        # Validate UUID format
        try:
            uuid.UUID(agent_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid agent ID format")

        # Check if agent exists
        existing_agent = await supabase_client.get_agent_by_id(agent_id)
        if not existing_agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Check if user has permission to update this agent
        user_role = current_user.get('user_metadata', {}).get('role', 'user')
        if user_role != 'admin' and existing_agent.get('created_by') != current_user.get('id'):
            raise HTTPException(status_code=403, detail="Insufficient permissions to update this agent")

        # Check for name conflicts if name is being updated
        if agent.name and agent.name != existing_agent.get('name'):
            existing_agents = await supabase_client.get_agents()
            existing_names = [a.get('name', '').lower() for a in existing_agents if a.get('id') != agent_id]
            if agent.name.lower() in existing_names:
                raise HTTPException(status_code=409, detail="Agent with this name already exists")

        # Update agent in database
        update_dict = agent.model_dump(exclude_unset=True)
        updated_agent = await supabase_client.update_agent(agent_id, update_dict)

        if not updated_agent:
            raise HTTPException(status_code=500, detail="Failed to update agent")

        # Update Retell components if they exist
        try:
            retell_client = get_retell_client()
            if updated_agent.get("retell_llm_id"):
                llm_config = retell_client.build_llm_config(updated_agent)
                await retell_client.update_retell_llm(updated_agent["retell_llm_id"], llm_config)

            if updated_agent.get("retell_agent_id") and updated_agent.get("retell_llm_id"):
                agent_config = retell_client.build_agent_config(updated_agent, updated_agent["retell_llm_id"])
                await retell_client.update_agent(updated_agent["retell_agent_id"], agent_config)

        except Exception as retell_error:
            logger.error(f"Failed to update Retell components for agent {agent_id}: {str(retell_error)}")
            # Continue with database update even if Retell sync fails
            updated_agent['_warning'] = "Agent updated but Retell sync failed. Manual sync may be required."

        return updated_agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update agent")


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an agent and its Retell components."""
    try:
        # Validate UUID format
        try:
            uuid.UUID(agent_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid agent ID format")

        # Check if agent exists
        existing_agent = await supabase_client.get_agent_by_id(agent_id)
        if not existing_agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Check permissions - only admins can delete agents
        user_role = current_user.get('user_metadata', {}).get('role', 'user')
        if user_role != 'admin':
            raise HTTPException(status_code=403, detail="Only administrators can delete agents")

        # Check if agent is being used in active calls
        active_calls = await supabase_client.get_calls(agent_id=agent_id, status='ongoing')
        if active_calls:
            raise HTTPException(status_code=409, detail="Cannot delete agent with active calls")

        # Delete Retell components first
        try:
            retell_client = get_retell_client()
            if existing_agent.get("retell_agent_id"):
                await retell_client.delete_agent(existing_agent["retell_agent_id"])

            if existing_agent.get("retell_llm_id"):
                await retell_client.delete_retell_llm(existing_agent["retell_llm_id"])
        except Exception as retell_error:
            logger.error(f"Failed to delete Retell components for agent {agent_id}: {str(retell_error)}")
            # Continue with database deletion even if Retell deletion fails

        # Delete agent from database
        success = await supabase_client.delete_agent(agent_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete agent")

        return {"success": True, "message": "Agent deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete agent")
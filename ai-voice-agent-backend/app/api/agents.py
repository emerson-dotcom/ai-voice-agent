from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models.schemas import AgentConfig, AgentConfigCreate, AgentConfigUpdate, APIResponse
from app.core.database import get_supabase_client
from app.core.auth import get_current_user, get_current_admin_user, get_user_info
from app.services.retell_service import retell_service
from supabase import Client
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/agents", response_model=APIResponse)
async def create_agent(
    agent_data: AgentConfigCreate, 
    current_user: dict = Depends(get_current_admin_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Create a new agent configuration."""
    try:
        # Create agent in database
        db_agent_data = agent_data.dict()
        db_agent_data["user_id"] = current_user["id"]  # Associate with current user
        result = supabase.table("agents").insert(db_agent_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create agent in database")
        
        agent_id = result.data[0]["id"]
        
        # Create agent in Retell AI (both LLM and Agent)
        retell_response = retell_service.create_agent_with_llm(db_agent_data)
        
        if retell_response:
            # Update database with Retell AI information
            update_data = {}
            
            # Add agent ID if available
            if retell_response.get("agent_id"):
                update_data["retell_agent_id"] = retell_response.get("agent_id")
            
            # Note: retell_llm_id column doesn't exist in current schema
            # We'll include it in the response but not store it in the database
            # TODO: Add retell_llm_id column to agents table schema
            
            if update_data:
                supabase.table("agents").update(update_data).eq("id", agent_id).execute()
            
            # Determine success message based on status
            if retell_response.get("status") == "complete":
                message = "Agent created successfully with full Retell AI integration"
                logger.info(f"Agent created successfully with full Retell AI integration: {agent_id}")
            else:
                message = "Agent created with Retell LLM. Agent creation requires upgraded Retell AI account."
                logger.info(f"Agent created with Retell LLM only: {agent_id}")
            
            return APIResponse(
                success=True,
                message=message,
                data={
                    "agent_id": agent_id, 
                    "retell_agent_id": retell_response.get("agent_id"),
                    "retell_llm_id": retell_response.get("llm_id"),  # Include in response but not in DB update
                    "status": retell_response.get("status", "unknown"),
                    "retell_message": retell_response.get("message")
                }
            )
        else:
            # If Retell AI creation fails completely, mark agent as inactive
            supabase.table("agents").update({"is_active": False}).eq("id", agent_id).execute()
            logger.warning(f"Agent created in database but failed in Retell AI: {agent_id}")
            return APIResponse(
                success=True,
                message="Agent created in database but failed in Retell AI",
                data={"agent_id": agent_id}
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents", response_model=APIResponse)
async def get_agents(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Get all agent configurations."""
    try:
        # If user is admin, get all agents; otherwise, get only their own agents
        if current_user["role"] == "admin":
            result = supabase.table("agents").select("*").order("created_at", desc=True).execute()
        else:
            result = supabase.table("agents").select("*").eq("user_id", current_user["id"]).order("created_at", desc=True).execute()
        
        return APIResponse(
            success=True,
            message="Agents retrieved successfully",
            data={"agents": result.data}
        )
    except Exception as e:
        logger.error(f"Error fetching agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}", response_model=APIResponse)
async def get_agent(
    agent_id: str, 
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Get a specific agent by ID."""
    try:
        result = supabase.table("agents").select("*").eq("id", agent_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent = result.data[0]
        
        # Check if user has access to this agent
        if current_user["role"] != "admin" and agent["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return APIResponse(
            success=True,
            message="Agent retrieved successfully",
            data=agent
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/agents/{agent_id}", response_model=APIResponse)
async def update_agent(
    agent_id: str,
    agent_update: AgentConfigUpdate,
    current_user: dict = Depends(get_current_admin_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Update an agent configuration."""
    try:
        # Get current agent data
        current_result = supabase.table("agents").select("*").eq("id", agent_id).execute()
        if not current_result.data:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        current_agent = current_result.data[0]
        
        # Update database
        update_data = agent_update.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        db_result = supabase.table("agents").update(update_data).eq("id", agent_id).execute()
        if not db_result.data:
            raise HTTPException(status_code=500, detail="Failed to update agent in database")
        
        # Update Retell AI if agent has retell_agent_id and retell_llm_id
        if current_agent.get("retell_agent_id") and current_agent.get("retell_llm_id"):
            # Merge current data with updates
            updated_agent = {**current_agent, **update_data}
            
            # Use the comprehensive update method that handles both LLM and Agent
            retell_response = retell_service.update_agent_with_llm(
                current_agent["retell_agent_id"],
                current_agent["retell_llm_id"],
                updated_agent
            )
            
            if retell_response:
                logger.info(f"Retell AI update result: {retell_response.get('status', 'unknown')}")
                if retell_response.get("status") == "complete":
                    logger.info(f"Agent and LLM updated successfully in Retell AI: {agent_id}")
                elif retell_response.get("status") == "llm_only":
                    logger.warning(f"LLM updated but agent update failed in Retell AI: {agent_id}")
            else:
                logger.warning(f"Failed to update agent {agent_id} in Retell AI")
        
        return APIResponse(
            success=True,
            message="Agent updated successfully",
            data=db_result.data[0]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/agents/{agent_id}", response_model=APIResponse)
async def delete_agent(
    agent_id: str, 
    current_user: dict = Depends(get_current_admin_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Delete an agent configuration."""
    try:
        # Get agent data
        result = supabase.table("agents").select("*").eq("id", agent_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent = result.data[0]
        
        # Delete from Retell AI if agent has retell_agent_id and retell_llm_id
        if agent.get("retell_agent_id") and agent.get("retell_llm_id"):
            retell_result = retell_service.delete_agent_with_llm(
                agent["retell_agent_id"],
                agent["retell_llm_id"]
            )
            
            if retell_result.get("status") == "complete":
                logger.info(f"Agent and LLM deleted successfully from Retell AI: {agent_id}")
            elif retell_result.get("status") == "partial":
                logger.warning(f"Partial deletion from Retell AI: {agent_id} - {retell_result.get('message', '')}")
            else:
                logger.warning(f"Failed to delete from Retell AI: {agent_id} - {retell_result.get('message', '')}")
        elif agent.get("retell_agent_id"):
            # Fallback: try to delete just the agent if no LLM ID
            retell_success = retell_service.delete_agent(agent["retell_agent_id"])
            if not retell_success:
                logger.warning(f"Failed to delete agent {agent_id} from Retell AI")
        
        # Delete from database
        supabase.table("agents").delete().eq("id", agent_id).execute()
        
        logger.info(f"Agent deleted successfully: {agent_id}")
        return APIResponse(
            success=True,
            message="Agent deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/{agent_id}/sync-retell", response_model=APIResponse)
async def sync_agent_with_retell(
    agent_id: str, 
    current_user: dict = Depends(get_current_admin_user),
    supabase: Client = Depends(get_supabase_client)
):
    """Sync agent configuration with Retell AI."""
    try:
        # Get agent data
        result = supabase.table("agents").select("*").eq("id", agent_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent = result.data[0]
        
        # Create/update in Retell AI
        retell_config = retell_service.create_agent_config(agent)
        
        if agent.get("retell_agent_id"):
            # Update existing agent
            retell_response = await retell_service.update_agent(agent["retell_agent_id"], retell_config)
            if not retell_response:
                raise HTTPException(status_code=500, detail="Failed to update agent in Retell AI")
        else:
            # Create new agent
            retell_response = await retell_service.create_agent(retell_config)
            if retell_response:
                # Update database with Retell AI agent ID
                supabase.table("agents").update({
                    "retell_agent_id": retell_response.get("agent_id")
                }).eq("id", agent_id).execute()
            else:
                raise HTTPException(status_code=500, detail="Failed to create agent in Retell AI")
        
        return APIResponse(
            success=True,
            message="Agent synced with Retell AI successfully",
            data={"retell_agent_id": retell_response.get("agent_id")}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

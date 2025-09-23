"""
Supabase client configuration and database operations.
Uses Supabase Python client for all database interactions.
"""

from supabase import create_client, Client
from app.core.config import settings
from typing import Optional, Dict, Any, List

class SupabaseClient:
    """Supabase client wrapper for database operations."""

    def __init__(self):
        """Initialize Supabase client."""
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )

    async def get_agents(self, scenario_type: Optional[str] = None, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get agents with optional filtering."""
        query = self.client.table("agents").select("*")

        if scenario_type:
            query = query.eq("scenario_type", scenario_type)
        if is_active is not None:
            query = query.eq("is_active", is_active)

        response = query.execute()
        return response.data

    async def get_agent_by_id(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific agent by ID."""
        response = self.client.table("agents").select("*").eq("id", agent_id).execute()
        return response.data[0] if response.data else None

    async def create_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new agent."""
        response = self.client.table("agents").insert(agent_data).execute()
        return response.data[0]

    async def update_agent(self, agent_id: str, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing agent."""
        response = self.client.table("agents").update(agent_data).eq("id", agent_id).execute()
        return response.data[0] if response.data else None

    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent."""
        response = self.client.table("agents").delete().eq("id", agent_id).execute()
        return len(response.data) > 0

    async def get_calls(self, agent_id: Optional[str] = None, status: Optional[str] = None,
                       limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get calls with optional filtering."""
        query = self.client.table("calls").select("*").order("created_at", desc=True)

        if agent_id:
            query = query.eq("agent_id", agent_id)
        if status:
            query = query.eq("call_status", status)

        query = query.limit(limit).offset(offset)
        response = query.execute()
        return response.data

    async def get_call_by_id(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific call by ID."""
        response = self.client.table("calls").select("*").eq("id", call_id).execute()
        return response.data[0] if response.data else None

    async def get_call_by_retell_id(self, retell_call_id: str) -> Optional[Dict[str, Any]]:
        """Get a call by Retell call ID."""
        response = self.client.table("calls").select("*").eq("retell_call_id", retell_call_id).execute()
        return response.data[0] if response.data else None

    async def create_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new call record."""
        response = self.client.table("calls").insert(call_data).execute()
        return response.data[0]

    async def update_call(self, call_id: str, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing call."""
        response = self.client.table("calls").update(call_data).eq("id", call_id).execute()
        return response.data[0] if response.data else None

    async def update_call_by_retell_id(self, retell_call_id: str, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a call by Retell call ID."""
        response = self.client.table("calls").update(call_data).eq("retell_call_id", retell_call_id).execute()
        return response.data[0] if response.data else None

    async def get_call_results(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get call results for a specific call."""
        response = self.client.table("call_results").select("*").eq("call_id", call_id).execute()
        return response.data[0] if response.data else None

    async def create_call_results(self, results_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create call results."""
        response = self.client.table("call_results").insert(results_data).execute()
        return response.data[0]

    async def update_call_results(self, call_id: str, results_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update call results."""
        response = self.client.table("call_results").update(results_data).eq("call_id", call_id).execute()
        return response.data[0] if response.data else None

    async def get_loads(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get loads."""
        response = self.client.table("loads").select("*").order("created_at", desc=True).limit(limit).offset(offset).execute()
        return response.data

    async def get_load_by_number(self, load_number: str) -> Optional[Dict[str, Any]]:
        """Get a load by load number."""
        response = self.client.table("loads").select("*").eq("load_number", load_number).execute()
        return response.data[0] if response.data else None

    async def get_agent_states(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get agent states for a specific agent."""
        response = self.client.table("agent_states").select("*").eq("agent_id", agent_id).order("name").execute()
        return response.data

    async def get_agent_tools(self, agent_id: str, state_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get agent tools for a specific agent and optionally a specific state."""
        query = self.client.table("agent_tools").select("*").eq("agent_id", agent_id)

        if state_id:
            query = query.eq("state_id", state_id)

        response = query.execute()
        return response.data


# Global Supabase client instance
supabase_client = SupabaseClient()
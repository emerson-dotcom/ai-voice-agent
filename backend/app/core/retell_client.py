from typing import Dict, Any, Optional
import asyncio
from retell import Retell
from app.config import settings


class RetellClient:
    """Client for interacting with Retell AI API"""
    
    def __init__(self, api_key: str, base_url: str = None):
        self.api_key = api_key
        # The official SDK handles the base URL internally
        self.client = Retell(api_key=api_key)

    async def create_agent(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new agent in Retell AI"""
        try:
            response = self.client.agent.create(**config)
            return {"agent_id": response.agent_id, "name": getattr(response, 'name', 'Agent')}
        except Exception as e:
            raise Exception(f"Failed to create agent: {e}")

    async def update_agent(self, agent_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing agent in Retell AI"""
        try:
            response = self.client.agent.update(agent_id=agent_id, **config)
            return {"agent_id": response.agent_id, "name": getattr(response, 'name', 'Agent')}
        except Exception as e:
            raise Exception(f"Failed to update agent: {e}")

    async def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get agent details from Retell AI"""
        try:
            response = self.client.agent.retrieve(agent_id=agent_id)
            return {"agent_id": response.agent_id, "name": getattr(response, 'name', 'Agent')}
        except Exception as e:
            raise Exception(f"Failed to get agent: {e}")

    async def delete_agent(self, agent_id: str) -> Dict[str, Any]:
        """Delete an agent from Retell AI"""
        try:
            self.client.agent.delete(agent_id=agent_id)
            return {"success": True}
        except Exception as e:
            raise Exception(f"Failed to delete agent: {e}")

    async def create_call(
        self,
        phone_number: str,
        agent_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new call with Retell AI"""
        try:
            response = self.client.call.create_phone_call(
                from_number="+1234567890",  # Your Retell phone number
                to_number=phone_number,
                agent_id=agent_id,
                metadata=metadata or {}
            )
            return {"call_id": response.call_id}
        except Exception as e:
            raise Exception(f"Failed to create call: {e}")

    async def get_call(self, call_id: str) -> Dict[str, Any]:
        """Get call details from Retell AI"""
        try:
            response = self.client.call.retrieve(call_id=call_id)
            return {"call_id": response.call_id, "status": getattr(response, 'status', 'unknown')}
        except Exception as e:
            raise Exception(f"Failed to get call: {e}")

    async def end_call(self, call_id: str) -> Dict[str, Any]:
        """End an active call"""
        try:
            # Note: The SDK might not have an end_call method, this may need adjustment
            response = self.client.call.end(call_id=call_id)
            return {"success": True}
        except Exception as e:
            raise Exception(f"Failed to end call: {e}")

    async def create_test_call(
        self,
        phone_number: str,
        agent_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a test call (same as regular call but with test metadata)"""
        test_metadata = {"test_call": True}
        if metadata:
            test_metadata.update(metadata)
        
        return await self.create_call(phone_number, agent_id, test_metadata)

    async def get_call_recording(self, call_id: str) -> Optional[str]:
        """Get call recording URL if available"""
        try:
            response = self.client.call.retrieve(call_id=call_id)
            return getattr(response, 'recording_url', None)
        except Exception:
            return None

    async def list_calls(
        self,
        limit: int = 100,
        offset: int = 0,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """List calls from Retell AI"""
        try:
            response = self.client.call.list(
                limit=limit,
                # Note: SDK might use different parameter names
                **filter_criteria if filter_criteria else {}
            )
            return {"calls": list(response)}
        except Exception as e:
            raise Exception(f"Failed to list calls: {e}")

    # Note: The official SDK handles connection management internally
    # No need for explicit close methods

import httpx
from typing import Dict, Any, Optional
import asyncio
from app.config import settings


class RetellClient:
    """Client for interacting with Retell AI API"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )

    async def create_agent(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new agent in Retell AI"""
        try:
            response = await self.client.post(
                f"{self.base_url}/agent",
                json=config
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"Failed to create agent: {e}")

    async def update_agent(self, agent_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing agent in Retell AI"""
        try:
            response = await self.client.patch(
                f"{self.base_url}/agent/{agent_id}",
                json=config
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"Failed to update agent: {e}")

    async def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get agent details from Retell AI"""
        try:
            response = await self.client.get(f"{self.base_url}/agent/{agent_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"Failed to get agent: {e}")

    async def delete_agent(self, agent_id: str) -> Dict[str, Any]:
        """Delete an agent from Retell AI"""
        try:
            response = await self.client.delete(f"{self.base_url}/agent/{agent_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"Failed to delete agent: {e}")

    async def create_call(
        self,
        phone_number: str,
        agent_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new call with Retell AI"""
        payload = {
            "from_number": "+1234567890",  # Your Retell phone number
            "to_number": phone_number,
            "agent_id": agent_id,
            "metadata": metadata or {}
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/call",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"Failed to create call: {e}")

    async def get_call(self, call_id: str) -> Dict[str, Any]:
        """Get call details from Retell AI"""
        try:
            response = await self.client.get(f"{self.base_url}/call/{call_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"Failed to get call: {e}")

    async def end_call(self, call_id: str) -> Dict[str, Any]:
        """End an active call"""
        try:
            response = await self.client.post(f"{self.base_url}/call/{call_id}/end")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
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
            response = await self.client.get(f"{self.base_url}/call/{call_id}/recording")
            response.raise_for_status()
            data = response.json()
            return data.get("recording_url")
        except httpx.HTTPError:
            return None

    async def list_calls(
        self,
        limit: int = 100,
        offset: int = 0,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """List calls from Retell AI"""
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if filter_criteria:
            params.update(filter_criteria)
        
        try:
            response = await self.client.get(
                f"{self.base_url}/call",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"Failed to list calls: {e}")

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

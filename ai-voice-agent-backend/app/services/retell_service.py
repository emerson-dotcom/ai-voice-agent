import httpx
import logging
import hashlib
import hmac
import json
from typing import Dict, Any, Optional, List
from app.core.config import settings
from retell import Retell

logger = logging.getLogger(__name__)


class RetellService:
    """Service for interacting with Retell AI API using official SDK."""
    
    def __init__(self):
        self.api_key = settings.retell_api_key
        self.client = Retell(api_key=self.api_key)
        self.webhook_secret = settings.retell_api_key  # Using API key as webhook secret
        self.base_url = settings.retell_base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_web_call(self, call_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new web call using Retell AI."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/create-web-call",
                    headers=self.headers,
                    json=call_data,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to create web call: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating web call: {e}")
            return None
    
    async def get_call(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get call details from Retell AI using official SDK."""
        try:
            logger.info(f"Attempting to retrieve call {call_id} using Retell SDK")
            
            # Use the official Retell SDK to retrieve call data
            call_response = self.client.call.retrieve(call_id)
            
            logger.info(f"Call response type: {type(call_response)}")
            
            # Check if response is None
            if call_response is None:
                logger.error(f"Call {call_id} not found or returned None")
                return None
            
            # The Retell SDK returns a response object that can be converted to dict
            # Try different methods to convert to dictionary
            if hasattr(call_response, 'model_dump'):
                # Pydantic v2 style
                result = call_response.model_dump()
                logger.info(f"Converted call response using model_dump()")
                return result
            elif hasattr(call_response, 'dict'):
                # Pydantic v1 style
                result = call_response.dict()
                logger.info(f"Converted call response using dict()")
                return result
            elif hasattr(call_response, '__dict__'):
                # Standard object attributes
                result = call_response.__dict__
                logger.info(f"Converted call response using __dict__")
                return result
            else:
                # If it's already a dict or similar, return as is
                logger.info(f"Returning call response as-is (type: {type(call_response)})")
                return call_response
                
        except Exception as e:
            logger.error(f"Failed to get call {call_id} using Retell SDK: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    async def create_web_call_with_access_token(self, call_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a web call and get access token using Retell AI create-web-call API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/create-web-call",
                    headers=self.headers,
                    json=call_data,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to create web call: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating web call: {e}")
            return None
    
    def update_agent(self, agent_id: str, agent_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update agent configuration in Retell AI using SDK."""
        try:
            # Use the official SDK to update agent (synchronous)
            agent_response = self.client.agent.update(agent_id, **agent_data)
            logger.info(f"Retell Agent updated successfully: {agent_id}")
            return agent_response.model_dump()
        except Exception as e:
            logger.error(f"Failed to update Retell Agent {agent_id}: {e}")
            return None
    
    def create_retell_llm(self, llm_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new Retell LLM Response Engine using SDK."""
        try:
            # Use the official SDK to create LLM (synchronous)
            llm_response = self.client.llm.create(**llm_data)
            logger.info(f"Retell LLM created successfully with ID: {llm_response.llm_id}")
            return llm_response.model_dump()
        except Exception as e:
            logger.error(f"Failed to create Retell LLM: {e}")
            return None

    def update_retell_llm(self, llm_id: str, llm_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a Retell LLM Response Engine using SDK."""
        try:
            # Use the official SDK to update LLM (synchronous)
            llm_response = self.client.llm.update(llm_id, **llm_data)
            logger.info(f"Retell LLM updated successfully: {llm_id}")
            return llm_response.model_dump()
        except Exception as e:
            logger.error(f"Failed to update Retell LLM {llm_id}: {e}")
            return None

    def delete_retell_llm(self, llm_id: str) -> bool:
        """Delete a Retell LLM Response Engine using SDK."""
        try:
            # Use the official SDK to delete LLM (synchronous)
            self.client.llm.delete(llm_id)
            logger.info(f"Retell LLM deleted successfully: {llm_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete Retell LLM {llm_id}: {e}")
            return False

    def get_retell_llm(self, llm_id: str) -> Optional[Dict[str, Any]]:
        """Get a Retell LLM Response Engine using SDK."""
        try:
            # Use the official SDK to get LLM (synchronous)
            llm_response = self.client.llm.get(llm_id)
            logger.info(f"Retrieved Retell LLM: {llm_id}")
            return llm_response.model_dump()
        except Exception as e:
            logger.error(f"Failed to get Retell LLM {llm_id}: {e}")
            return None

    def list_retell_llms(self) -> Optional[List[Dict[str, Any]]]:
        """List all Retell LLM Response Engines using SDK."""
        try:
            # Use the official SDK to list LLMs (synchronous)
            llms_response = self.client.llm.list()
            logger.info(f"Retrieved {len(llms_response)} LLMs from Retell AI")
            return [llm.model_dump() for llm in llms_response]
        except Exception as e:
            logger.error(f"Failed to list Retell LLMs: {e}")
            return None

    def create_agent(self, agent_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new agent in Retell AI using SDK."""
        try:
            # Use the official SDK to create agent (synchronous)
            agent_response = self.client.agent.create(**agent_data)
            logger.info(f"Retell Agent created successfully with ID: {agent_response.agent_id}")
            return agent_response.model_dump()
        except Exception as e:
            logger.error(f"Failed to create Retell Agent: {e}")
            return None
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent details from Retell AI using SDK."""
        try:
            # Use the official SDK to get agent (synchronous)
            agent_response = self.client.agent.get(agent_id)
            logger.info(f"Retrieved Retell Agent: {agent_id}")
            return agent_response.model_dump()
        except Exception as e:
            logger.error(f"Failed to get Retell Agent {agent_id}: {e}")
            return None
    
    def list_agents(self) -> Optional[List[Dict[str, Any]]]:
        """List all agents from Retell AI using SDK."""
        try:
            # Use the official SDK to list agents (synchronous)
            agents_response = self.client.agent.list()
            logger.info(f"Retrieved {len(agents_response)} agents from Retell AI")
            return [agent.model_dump() for agent in agents_response]
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            return None
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent from Retell AI using SDK."""
        try:
            # Use the official SDK to delete agent (synchronous)
            self.client.agent.delete(agent_id)
            logger.info(f"Retell Agent deleted successfully: {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete Retell Agent {agent_id}: {e}")
            return False
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verify webhook signature for security."""
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    def create_web_call_config(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create web call configuration for Retell AI."""
        return {
            "agent_id": call_data.get("agent_id"),
            "customer_id": call_data.get("customer_id", "web_user"),
            "customer_name": call_data.get("driver_name", "Driver"),
            "metadata": call_data.get("metadata", {}),
            "web_call_url": call_data.get("web_call_url"),  # URL to redirect user to
            "allow_agent_override": True,
            "dynamic_variables": {
                "driver_name": call_data.get("driver_name", ""),
                "load_number": call_data.get("load_number", ""),
                "phone_number": call_data.get("phone_number", "")
            }
        }
    
    def create_llm_config(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Retell LLM configuration from our agent data."""
        # Build the main prompt from our agent data
        main_prompt = agent_data.get("initial_prompt", "You are a helpful AI assistant.")
        
        # Add emergency prompt if provided
        emergency_prompt = agent_data.get("emergency_prompt", "")
        if emergency_prompt:
            main_prompt += f"\n\nEmergency Protocol: {emergency_prompt}"
        
        # Add follow-up prompts if provided
        follow_up_prompts = agent_data.get("follow_up_prompts", [])
        if follow_up_prompts:
            main_prompt += "\n\nFollow-up prompts to use when appropriate:"
            for i, prompt in enumerate(follow_up_prompts, 1):
                main_prompt += f"\n{i}. {prompt}"
        
        return {
            "general_prompt": main_prompt,
            "model": "gpt-4.1",  # Use GPT-4.1 as default
            "model_temperature": 0.7,
            "general_tools": [
                {
                    "type": "end_call",
                    "name": "end_call",
                    "description": "End the call when the conversation is complete or if the user requests to end the call."
                }
            ],
            "begin_message": "Hello! I'm calling to check on your delivery status. How are you doing today?",
            "default_dynamic_variables": {
                "driver_name": agent_data.get("driver_name", ""),
                "load_number": agent_data.get("load_number", "")
            }
        }

    def validate_voice_id(self, voice_id: str) -> str:
        """Validate and return a working voice ID."""
        # Map common voice names to actual voice IDs
        voice_mapping = {
            "sarah": "cartesia-Sarah",  # Map sarah to cartesia-Sarah
            "adrian": "11labs-Adrian",  # Map adrian to 11labs-Adrian
            "emma": "cartesia-Emma",    # Map emma to cartesia-Emma
        }
        
        # If the voice_id is in our mapping, use the mapped value
        if voice_id.lower() in voice_mapping:
            return voice_mapping[voice_id.lower()]
        
        # If it's already a valid voice ID format, use it as is
        if "-" in voice_id and any(provider in voice_id for provider in ["11labs", "cartesia", "openai", "playht"]):
            return voice_id
        
        # Default to a known working voice
        return "11labs-Adrian"

    def create_agent_config(self, agent_data: Dict[str, Any], llm_id: str) -> Dict[str, Any]:
        """Create Retell AI agent configuration from our agent data."""
        # Validate and get a working voice ID
        voice_id = self.validate_voice_id(agent_data.get("voice_id", "sarah"))
        
        return {
            "agent_name": agent_data.get("name", "AI Voice Agent"),
            "voice_id": voice_id,
            "voice_speed": agent_data.get("speed", 1.0),
            "interruption_sensitivity": agent_data.get("interruption_sensitivity", 0.5),
            "enable_backchannel": agent_data.get("backchanneling", True),
            "language": "en-US",
            "webhook_url": f"http://{settings.api_host}:{settings.api_port}/api/webhook/retell",
            "response_engine": {
                "type": "retell-llm",
                "llm_id": llm_id
            }
        }

    def create_agent_with_llm(self, agent_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create Retell LLM and attempt to create Agent. Handle partial success gracefully."""
        try:
            # Step 1: Create Retell LLM
            logger.info("Creating Retell LLM...")
            llm_config = self.create_llm_config(agent_data)
            llm_response = self.create_retell_llm(llm_config)
            
            if not llm_response:
                logger.error("Failed to create Retell LLM")
                return None
            
            llm_id = llm_response.get("llm_id")
            if not llm_id:
                logger.error("No llm_id returned from Retell LLM creation")
                return None
            
            logger.info(f"Retell LLM created successfully with ID: {llm_id}")
            
            # Step 2: Attempt to Create Agent with the LLM ID
            logger.info("Attempting to create Retell Agent...")
            agent_config = self.create_agent_config(agent_data, llm_id)
            agent_response = self.create_agent(agent_config)
            
            if agent_response:
                agent_id = agent_response.get("agent_id")
                if agent_id:
                    logger.info(f"Retell Agent created successfully with ID: {agent_id}")
                    return {
                        "llm_id": llm_id,
                        "agent_id": agent_id,
                        "llm_response": llm_response,
                        "agent_response": agent_response,
                        "status": "complete"
                    }
            
            # If agent creation fails, return partial success with LLM only
            logger.warning(f"Retell LLM created but Agent creation failed. LLM ID: {llm_id}")
            return {
                "llm_id": llm_id,
                "agent_id": None,
                "llm_response": llm_response,
                "agent_response": None,
                "status": "llm_only",
                "message": "LLM created successfully, but agent creation failed due to API permissions"
            }
            
        except Exception as e:
            logger.error(f"Unexpected error in create_agent_with_llm: {e}")
            return None

    def update_agent_with_llm(self, agent_id: str, llm_id: str, agent_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update both Retell LLM and Agent. Handle partial success gracefully."""
        try:
            # Step 1: Update Retell LLM if prompt data changed
            logger.info(f"Updating Retell LLM: {llm_id}")
            llm_config = self.create_llm_config(agent_data)
            llm_response = self.update_retell_llm(llm_id, llm_config)
            
            if not llm_response:
                logger.warning(f"Failed to update Retell LLM {llm_id}, continuing with agent update")
            else:
                logger.info(f"Retell LLM updated successfully: {llm_id}")
            
            # Step 2: Update Agent configuration
            logger.info(f"Updating Retell Agent: {agent_id}")
            agent_config = self.create_agent_config(agent_data, llm_id)
            agent_response = self.update_agent(agent_id, agent_config)
            
            if agent_response:
                logger.info(f"Retell Agent updated successfully: {agent_id}")
                return {
                    "llm_id": llm_id,
                    "agent_id": agent_id,
                    "llm_response": llm_response,
                    "agent_response": agent_response,
                    "status": "complete"
                }
            else:
                logger.error(f"Failed to update Retell Agent: {agent_id}")
                return {
                    "llm_id": llm_id,
                    "agent_id": agent_id,
                    "llm_response": llm_response,
                    "agent_response": None,
                    "status": "llm_only",
                    "message": "LLM updated successfully, but agent update failed"
                }
            
        except Exception as e:
            logger.error(f"Unexpected error in update_agent_with_llm: {e}")
            return None

    def delete_agent_with_llm(self, agent_id: str, llm_id: str) -> Dict[str, Any]:
        """Delete both Retell Agent and its associated LLM."""
        try:
            results = {
                "agent_deleted": False,
                "llm_deleted": False,
                "agent_id": agent_id,
                "llm_id": llm_id,
                "errors": []
            }
            
            # Step 1: Delete Agent first
            if agent_id:
                logger.info(f"Deleting Retell Agent: {agent_id}")
                if self.delete_agent(agent_id):
                    results["agent_deleted"] = True
                    logger.info(f"Retell Agent deleted successfully: {agent_id}")
                else:
                    results["errors"].append(f"Failed to delete agent {agent_id}")
            
            # Step 2: Delete LLM
            if llm_id:
                logger.info(f"Deleting Retell LLM: {llm_id}")
                if self.delete_retell_llm(llm_id):
                    results["llm_deleted"] = True
                    logger.info(f"Retell LLM deleted successfully: {llm_id}")
                else:
                    results["errors"].append(f"Failed to delete LLM {llm_id}")
            
            # Determine overall status
            if results["agent_deleted"] and results["llm_deleted"]:
                results["status"] = "complete"
                results["message"] = "Agent and LLM deleted successfully"
            elif results["agent_deleted"] or results["llm_deleted"]:
                results["status"] = "partial"
                results["message"] = "Partial deletion completed with some errors"
            else:
                results["status"] = "failed"
                results["message"] = "Failed to delete agent and LLM"
            
            return results
            
        except Exception as e:
            logger.error(f"Unexpected error in delete_agent_with_llm: {e}")
            return {
                "agent_deleted": False,
                "llm_deleted": False,
                "agent_id": agent_id,
                "llm_id": llm_id,
                "status": "error",
                "message": f"Unexpected error: {str(e)}",
                "errors": [str(e)]
            }


# Global instance
retell_service = RetellService()

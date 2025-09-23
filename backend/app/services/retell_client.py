"""
Retell AI client integration for backend operations.
Handles LLM creation, agent management, and call operations.
"""

from retell import Retell
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.exceptions import RetellException
from app.scenarios.scenario_manager import ScenarioManager
import logging
import asyncio
import time
import httpx
from functools import wraps

logger = logging.getLogger(__name__)

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry failed operations with exponential backoff."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}: {str(e)}")
            raise last_exception
        return wrapper
    return decorator

class RetellClient:
    """Retell AI client wrapper for API operations."""

    def __init__(self):
        """Initialize Retell client."""
        self.client = Retell(api_key=settings.RETELL_API_KEY)

    @retry_on_failure(max_retries=settings.RETELL_MAX_RETRIES)
    async def create_retell_llm(self, llm_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Retell LLM."""
        try:
            # Validate required fields
            required_fields = ['general_prompt', 'model']
            for field in required_fields:
                if field not in llm_config:
                    raise RetellException(f"Missing required field: {field}", status_code=400)

            logger.info(f"Creating Retell LLM with model: {llm_config.get('model')}")
            response = self.client.llm.create(**llm_config)

            result = {
                "llm_id": response.llm_id,
                "version": response.version,
                "is_published": response.is_published,
                "last_modification_timestamp": response.last_modification_timestamp
            }

            logger.info(f"Successfully created Retell LLM: {result['llm_id']}")
            return result

        except RetellException:
            raise
        except Exception as e:
            logger.error(f"Failed to create Retell LLM: {str(e)}")
            raise RetellException(f"Failed to create Retell LLM: {str(e)}", status_code=500)

    @retry_on_failure(max_retries=settings.RETELL_MAX_RETRIES)
    async def update_retell_llm(self, llm_id: str, llm_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing Retell LLM."""
        try:
            if not llm_id:
                raise RetellException("LLM ID is required", status_code=400)

            logger.info(f"Updating Retell LLM: {llm_id}")
            response = self.client.llm.update(llm_id, **llm_config)

            result = {
                "llm_id": response.llm_id,
                "version": response.version,
                "is_published": response.is_published,
                "last_modification_timestamp": response.last_modification_timestamp
            }

            logger.info(f"Successfully updated Retell LLM: {llm_id}")
            return result

        except RetellException:
            raise
        except Exception as e:
            logger.error(f"Failed to update Retell LLM {llm_id}: {str(e)}")
            raise RetellException(f"Failed to update Retell LLM: {str(e)}", status_code=500)

    @retry_on_failure(max_retries=settings.RETELL_MAX_RETRIES)
    async def delete_retell_llm(self, llm_id: str) -> bool:
        """Delete a Retell LLM."""
        try:
            if not llm_id:
                raise RetellException("LLM ID is required", status_code=400)

            logger.info(f"Deleting Retell LLM: {llm_id}")
            self.client.llm.delete(llm_id)
            logger.info(f"Successfully deleted Retell LLM: {llm_id}")
            return True

        except RetellException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete Retell LLM {llm_id}: {str(e)}")
            raise RetellException(f"Failed to delete Retell LLM: {str(e)}", status_code=500)

    async def create_agent(self, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Retell agent using SDK first, then fallback to direct HTTP."""
        try:
            # First try using the SDK
            logger.info(f"Attempting to create agent using SDK with config: {agent_config}")
            response = self.client.agent.create(**agent_config)

            return {
                "agent_id": response.agent_id,
                "version": getattr(response, 'version', None),
                "is_published": getattr(response, 'is_published', None),
                "last_modification_timestamp": getattr(response, 'last_modification_timestamp', None)
            }
        except Exception as sdk_error:
            logger.warning(f"SDK agent creation failed: {sdk_error}, trying direct HTTP call")

            try:
                # Fallback to direct HTTP call with different endpoints
                headers = {
                    "Authorization": f"Bearer {settings.RETELL_API_KEY}",
                    "Content-Type": "application/json"
                }

                endpoints_to_try = [
                    "https://api.retellai.com/agent",  # Try REST-style endpoint
                    "https://api.retellai.com/agents", # Try plural
                    "https://api.retellai.com/create-agent" # Original from docs
                ]

                async with httpx.AsyncClient() as client:
                    for endpoint in endpoints_to_try:
                        logger.info(f"Trying endpoint: {endpoint}")
                        response = await client.post(
                            endpoint,
                            json=agent_config,
                            headers=headers
                        )

                        if response.status_code in [200, 201]:
                            result = response.json()
                            logger.info(f"Success with endpoint {endpoint}: {response.status_code}")
                            return {
                                "agent_id": result.get("agent_id"),
                                "version": result.get("version"),
                                "is_published": result.get("is_published"),
                                "last_modification_timestamp": result.get("last_modification_timestamp")
                            }
                        else:
                            logger.warning(f"Endpoint {endpoint} failed with {response.status_code}: {response.text}")

                # If all endpoints fail
                raise Exception(f"All agent creation endpoints failed. Last response: {response.status_code} - {response.text}")

            except Exception as http_error:
                logger.error(f"Direct HTTP agent creation also failed: {http_error}")
                raise Exception(f"Failed to create Retell agent via both SDK and HTTP: SDK='{sdk_error}', HTTP='{http_error}'")

    async def update_agent(self, agent_id: str, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing Retell agent."""
        try:
            response = self.client.agent.update(agent_id, **agent_config)
            return {
                "agent_id": response.agent_id,
                "version": response.version,
                "is_published": response.is_published,
                "last_modification_timestamp": response.last_modification_timestamp
            }
        except Exception as e:
            raise Exception(f"Failed to update Retell agent: {str(e)}")

    async def delete_agent(self, agent_id: str) -> bool:
        """Delete a Retell agent."""
        try:
            self.client.agent.delete(agent_id)
            return True
        except Exception as e:
            raise Exception(f"Failed to delete Retell agent: {str(e)}")

    async def create_web_call(self, call_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new web call."""
        try:
            logger.info(f"Creating web call with config: {call_config}")

            # Log the exact parameters being sent to Retell
            logger.info(f"Agent ID: {call_config.get('agent_id')}")
            logger.info(f"Metadata: {call_config.get('metadata')}")
            logger.info(f"Dynamic Variables: {call_config.get('retell_llm_dynamic_variables')}")

            response = self.client.call.create_web_call(**call_config)
            logger.info(f"Web call created successfully: {response}")

            # Log the response to see if dynamic variables are reflected
            logger.info(f"Response retell_llm_dynamic_variables: {getattr(response, 'retell_llm_dynamic_variables', 'Not available')}")

            return {
                "call_id": response.call_id,
                "access_token": response.access_token,
                "agent_id": response.agent_id,
                "call_status": response.call_status
            }
        except Exception as e:
            logger.error(f"Detailed web call creation error: {str(e)}, type: {type(e)}, config: {call_config}")
            raise Exception(f"Failed to create web call: {str(e)}")

    async def get_call(self, call_id: str) -> Dict[str, Any]:
        """Get call details from Retell."""
        try:
            response = self.client.call.retrieve(call_id)
            return {
                "call_id": response.call_id,
                "agent_id": response.agent_id,
                "call_status": response.call_status,
                "start_timestamp": response.start_timestamp,
                "end_timestamp": response.end_timestamp,
                "duration_ms": response.duration_ms,
                "transcript": response.transcript,
                "recording_url": response.recording_url,
                "public_log_url": response.public_log_url,
                "disconnection_reason": response.disconnection_reason,
                "call_analysis": response.call_analysis
            }
        except Exception as e:
            raise Exception(f"Failed to get call details: {str(e)}")

    async def list_voices(self) -> List[Dict[str, Any]]:
        """List available voices."""
        try:
            response = self.client.voice.list()
            return [
                {
                    "voice_id": voice.voice_id,
                    "voice_name": voice.voice_name,
                    "provider": voice.provider,
                    "accent": voice.accent,
                    "gender": voice.gender,
                    "age": voice.age,
                    "preview_audio_url": voice.preview_audio_url
                }
                for voice in response
            ]
        except Exception as e:
            raise Exception(f"Failed to list voices: {str(e)}")

    def build_llm_config(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build LLM configuration from agent data using scenario manager."""
        scenario_type = agent_data.get("scenario_type")

        if scenario_type:
            # Use scenario manager for scenario-specific configuration
            return ScenarioManager.build_llm_config(agent_data)

        # Fallback to legacy configuration for non-scenario agents
        config = {
            "general_prompt": agent_data["general_prompt"],
            "model": agent_data.get("model", "gpt-4o"),
            "model_temperature": agent_data.get("voice_temperature", 0.8),
        }

        if agent_data.get("begin_message"):
            config["begin_message"] = agent_data["begin_message"]

        # Add default dynamic variables for template substitution
        config["default_dynamic_variables"] = {
            "driver_name": "Driver",
            "load_number": "N/A"
        }

        # Add states and tools if available
        states = self._build_states_config(agent_data)
        if states:
            config["states"] = states
            config["starting_state"] = states[0]["name"]

        # Add general tools
        config["general_tools"] = self._build_general_tools()

        return config

    def build_agent_config(self, agent_data: Dict[str, Any], llm_id: str) -> Dict[str, Any]:
        """Build agent configuration from agent data using scenario manager."""
        scenario_type = agent_data.get("scenario_type")

        if scenario_type:
            # Use scenario manager for scenario-specific configuration
            return ScenarioManager.build_agent_config(agent_data, llm_id)

        # Fallback to legacy configuration for non-scenario agents
        config = {
            "response_engine": {
                "type": "retell-llm",
                "llm_id": llm_id
            },
            "voice_id": agent_data["voice_id"],
            "voice_temperature": agent_data.get("voice_temperature", 1.0),
            "voice_speed": agent_data.get("voice_speed", 1.0),
            "responsiveness": agent_data.get("responsiveness", 1.0),
            "interruption_sensitivity": agent_data.get("interruption_sensitivity", 1.0),
            "enable_backchannel": agent_data.get("enable_backchannel", True),
            "backchannel_frequency": agent_data.get("backchannel_frequency", 0.8),
            "language": "en-US"
        }

        if agent_data.get("voice_model"):
            config["voice_model"] = agent_data["voice_model"]

        if agent_data.get("backchannel_words"):
            config["backchannel_words"] = agent_data["backchannel_words"]

        if agent_data.get("name"):
            config["agent_name"] = agent_data["name"]

        return config

    def _build_states_config(self, agent_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build states configuration based on scenario type."""
        scenario_type = agent_data.get("scenario_type")

        if scenario_type == "driver_checkin":
            return [
                {
                    "name": "information_collection",
                    "state_prompt": "You are collecting initial information about the driver's status. Ask open-ended questions and listen carefully for emergency indicators.",
                    "edges": [
                        {
                            "destination_state_name": "status_assessment",
                            "description": "Transition when you have basic status information"
                        }
                    ],
                    "tools": []
                },
                {
                    "name": "status_assessment",
                    "state_prompt": "You are assessing the driver's detailed status. Get specific information about location, ETA, and any issues.",
                    "edges": [
                        {
                            "destination_state_name": "details_gathering",
                            "description": "Transition to gather final details"
                        }
                    ],
                    "tools": []
                },
                {
                    "name": "details_gathering",
                    "state_prompt": "You are gathering final details and confirming information before ending the call.",
                    "tools": []
                }
            ]
        elif scenario_type == "emergency_protocol":
            return [
                {
                    "name": "safety_assessment",
                    "state_prompt": "EMERGENCY MODE: Immediately assess safety status. Ask if everyone is safe.",
                    "edges": [
                        {
                            "destination_state_name": "information_gathering",
                            "description": "Transition once safety is confirmed"
                        }
                    ],
                    "tools": []
                },
                {
                    "name": "information_gathering",
                    "state_prompt": "EMERGENCY MODE: Quickly gather essential emergency information - location, type, load status.",
                    "edges": [
                        {
                            "destination_state_name": "escalation",
                            "description": "Transition to escalate to human dispatcher"
                        }
                    ],
                    "tools": []
                },
                {
                    "name": "escalation",
                    "state_prompt": "EMERGENCY MODE: Inform driver you are connecting them to human dispatcher immediately. End the call to allow manual escalation.",
                    "tools": [
                        {
                            "type": "end_call",
                            "name": "end_call_emergency",
                            "description": "End call for emergency escalation to human dispatcher"
                        }
                    ]
                }
            ]

        return []

    def _build_general_tools(self) -> List[Dict[str, Any]]:
        """Build general tools available to all states."""
        return [
            {
                "type": "end_call",
                "name": "end_call",
                "description": "End the call when conversation is complete"
            }
        ]


# Global Retell client instance (lazy initialization)
_retell_client = None

def get_retell_client() -> RetellClient:
    """Get or create the global Retell client instance."""
    global _retell_client
    if _retell_client is None:
        _retell_client = RetellClient()
    return _retell_client

# Note: Use get_retell_client() function for lazy loading
# retell_client = get_retell_client()
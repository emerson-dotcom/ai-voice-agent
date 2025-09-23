"""
Conversation Flow Service
Manages real-time conversation flow and response generation for Retell AI webhooks.
"""

import logging
from typing import Dict, Any, Optional
from app.services.conversation_state_service import conversation_service, ConversationState
from app.services.llm_service import llm_service
from app.services.agent_service import AgentService
from app.services.call_service import CallService
from app.models.agent import ScenarioType

logger = logging.getLogger(__name__)


class ConversationFlowService:
    """Service for managing conversation flow and generating responses."""

    def __init__(self):
        self.agent_service = AgentService()
        self.call_service = CallService()

    async def process_user_message(
        self,
        call_id: str,
        user_message: str,
        response_id: int = 0
    ) -> Dict[str, Any]:
        """Process user message and generate appropriate response."""
        try:
            # Get conversation context
            context = conversation_service.get_conversation(call_id)
            if not context:
                logger.error(f"No conversation context found for call {call_id}")
                return self._get_default_response(response_id)

            # Add user message to history
            context.add_message("user", user_message)

            # Check for emergency detection
            emergency_detected = context.detect_emergency(user_message)
            if emergency_detected and context.state != ConversationState.EMERGENCY_HANDLING:
                return await self._handle_emergency_detection(context, user_message, response_id)

            # Get agent configuration
            agent = await self.agent_service.get_agent(context.agent_id)
            if not agent:
                logger.error(f"Agent not found: {context.agent_id}")
                return self._get_default_response(response_id)

            # Generate contextual response based on current state
            response_data = await self._generate_contextual_response(
                context, user_message, agent, response_id
            )

            # Update conversation state and context
            await self._update_conversation_context(context, user_message, response_data)

            # Add assistant response to history
            context.add_message("assistant", response_data["response"])

            return response_data

        except Exception as e:
            logger.error(f"Error processing user message for call {call_id}: {str(e)}")
            return self._get_default_response(response_id)

    async def _generate_contextual_response(
        self,
        context,
        user_message: str,
        agent: Dict[str, Any],
        response_id: int
    ) -> Dict[str, Any]:
        """Generate contextual response based on conversation state and scenario."""

        # Determine response based on current state
        if context.state == ConversationState.INITIALIZING:
            return await self._handle_initialization(context, agent, response_id)

        elif context.state == ConversationState.GREETING:
            return await self._handle_greeting_response(context, user_message, agent, response_id)

        elif context.state == ConversationState.STATUS_INQUIRY:
            return await self._handle_status_response(context, user_message, agent, response_id)

        elif context.state == ConversationState.GATHERING_INFO:
            return await self._handle_info_gathering(context, user_message, agent, response_id)

        elif context.state == ConversationState.EMERGENCY_HANDLING:
            return await self._handle_emergency_conversation(context, user_message, agent, response_id)

        elif context.state == ConversationState.CLOSING:
            return await self._handle_closing(context, user_message, agent, response_id)

        else:
            # Use LLM for dynamic response generation
            return await self._generate_llm_response(context, user_message, agent, response_id)

    async def _handle_initialization(self, context, agent: Dict[str, Any], response_id: int) -> Dict[str, Any]:
        """Handle conversation initialization."""
        context.update_state(ConversationState.GREETING)

        # Get call details for context
        call_details = await self._get_call_details(context.call_id)
        driver_name = call_details.get('driver_name', 'driver')
        load_number = call_details.get('load_number', 'your load')

        if context.scenario_type == ScenarioType.DRIVER_CHECKIN:
            response_text = f"Hi {driver_name}, this is dispatch with a check call on load {load_number}. Can you give me an update on your status?"
        else:
            response_text = f"Hi {driver_name}, this is dispatch calling about load {load_number}. How are things going?"

        return {
            "response": response_text,
            "response_id": response_id
        }

    async def _handle_greeting_response(self, context, user_message: str, agent: Dict[str, Any], response_id: int) -> Dict[str, Any]:
        """Handle response to greeting."""
        context.update_state(ConversationState.STATUS_INQUIRY)

        # Analyze user response to determine next question
        user_lower = user_message.lower()

        if any(word in user_lower for word in ["arrived", "here", "at", "delivery", "pickup"]):
            context.update_context("likely_arrived", True)
            response_text = "Great! Can you tell me about the unloading process? Are you in a door or waiting?"
        elif any(word in user_lower for word in ["driving", "road", "highway", "miles"]):
            context.update_context("status", "driving")
            response_text = "Got it. What's your current location and estimated arrival time?"
        elif any(word in user_lower for word in ["delayed", "stuck", "traffic", "problem"]):
            context.update_context("status", "delayed")
            response_text = "I understand you're experiencing delays. Can you tell me what's causing the delay and your updated ETA?"
        else:
            response_text = "Can you be more specific about your current status? Are you still driving, have you arrived, or are you experiencing any delays?"

        return {
            "response": response_text,
            "response_id": response_id
        }

    async def _handle_status_response(self, context, user_message: str, agent: Dict[str, Any], response_id: int) -> Dict[str, Any]:
        """Handle status inquiry responses."""
        context.update_state(ConversationState.GATHERING_INFO)

        # Extract information from response
        user_lower = user_message.lower()

        if "arrived" in user_lower or "here" in user_lower:
            context.update_collected_data({
                "driver_status": "Arrived",
                "call_outcome": "Arrival Confirmation"
            })
            response_text = "Perfect. Are you currently unloading or waiting to get into a door? Also, please remember to get your POD signed when you're finished."
        elif any(word in user_lower for word in ["driving", "road", "miles"]):
            context.update_collected_data({
                "driver_status": "Driving",
                "call_outcome": "In-Transit Update"
            })
            response_text = "Thanks for the update. Do you have an estimated arrival time?"
        else:
            # Use LLM for more complex responses
            return await self._generate_llm_response(context, user_message, agent, response_id)

        return {
            "response": response_text,
            "response_id": response_id
        }

    async def _handle_info_gathering(self, context, user_message: str, agent: Dict[str, Any], response_id: int) -> Dict[str, Any]:
        """Handle information gathering phase."""
        # Extract location, time, or other details
        collected_data = {}

        # Simple pattern matching for common responses
        user_lower = user_message.lower()
        if "door" in user_lower:
            collected_data["unloading_status"] = f"In {user_message}"
        elif "waiting" in user_lower:
            collected_data["unloading_status"] = "Waiting for dock assignment"
        elif any(time_word in user_lower for time_word in ["am", "pm", "hour", "minute"]):
            collected_data["eta"] = user_message
        elif any(location_word in user_lower for location_word in ["highway", "i-", "mile", "exit"]):
            collected_data["current_location"] = user_message

        if collected_data:
            context.update_collected_data(collected_data)

        # Determine if we need more information or can close
        if self._has_sufficient_info(context):
            context.update_state(ConversationState.CLOSING)
            response_text = "Thank you for the update. Is there anything else you need assistance with regarding this load?"
        else:
            response_text = "Thanks. Is there anything else I should know about the delivery status or any issues you're experiencing?"

        return {
            "response": response_text,
            "response_id": response_id
        }

    async def _handle_emergency_detection(self, context, user_message: str, response_id: int) -> Dict[str, Any]:
        """Handle emergency detection and immediate response."""
        context.update_state(ConversationState.EMERGENCY_HANDLING)
        context.update_context("emergency_trigger", user_message)

        response_text = "I understand this is an emergency situation. First, are you and anyone else involved safe? Please tell me your exact location."

        return {
            "response": response_text,
            "response_id": response_id
        }

    async def _handle_emergency_conversation(self, context, user_message: str, agent: Dict[str, Any], response_id: int) -> Dict[str, Any]:
        """Handle emergency conversation flow."""
        # Extract emergency information
        user_lower = user_message.lower()

        emergency_data = {}
        if any(word in user_lower for word in ["safe", "okay", "fine"]):
            emergency_data["safety_status"] = "Driver confirmed everyone is safe"
        elif any(word in user_lower for word in ["hurt", "injured", "medical"]):
            emergency_data["injury_status"] = user_message
            emergency_data["safety_status"] = "Injuries reported"

        if any(word in user_lower for word in ["highway", "i-", "mile", "exit", "road"]):
            emergency_data["emergency_location"] = user_message

        if emergency_data:
            context.update_collected_data(emergency_data)

        # Move to escalation
        context.update_state(ConversationState.ESCALATING)
        context.update_collected_data({
            "call_outcome": "Emergency Escalation",
            "escalation_status": "Connecting to Human Dispatcher"
        })

        response_text = "I'm connecting you to a human dispatcher immediately. Please stay on the line and keep yourself safe."

        return {
            "response": response_text,
            "response_id": response_id
        }

    async def _handle_closing(self, context, user_message: str, agent: Dict[str, Any], response_id: int) -> Dict[str, Any]:
        """Handle conversation closing."""
        context.update_state(ConversationState.COMPLETED)

        response_text = "Perfect, thank you for the update. Drive safely and have a great day!"

        return {
            "response": response_text,
            "response_id": response_id
        }

    async def _generate_llm_response(self, context, user_message: str, agent: Dict[str, Any], response_id: int) -> Dict[str, Any]:
        """Generate response using LLM service."""
        try:
            llm_response = await llm_service.generate_conversation_response(
                user_message=user_message,
                conversation_history=context.conversation_history,
                agent_config=agent,
                scenario_type=context.scenario_type,
                current_state=context.state.value
            )

            # Update state if LLM suggests it
            if llm_response.get("next_state"):
                try:
                    new_state = ConversationState(llm_response["next_state"])
                    context.update_state(new_state)
                except ValueError:
                    pass  # Invalid state, keep current

            # Check for emergency detection
            if llm_response.get("emergency_detected"):
                context.emergency_detected = True
                context.update_state(ConversationState.EMERGENCY_DETECTED)

            return {
                "response": llm_response.get("response", "I understand. Can you tell me more?"),
                "response_id": response_id
            }

        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            return self._get_default_response(response_id)

    async def _update_conversation_context(self, context, user_message: str, response_data: Dict[str, Any]):
        """Update conversation context with new information."""
        # Update conversation state in service
        await conversation_service.update_conversation(
            context.call_id,
            state=context.state,
            context=context.context,
            collected_data=context.collected_data
        )

    async def _get_call_details(self, call_id: str) -> Dict[str, Any]:
        """Get call details from database."""
        try:
            call = await self.call_service.get_call(call_id)
            return call if call else {}
        except Exception as e:
            logger.error(f"Error getting call details: {str(e)}")
            return {}

    def _has_sufficient_info(self, context) -> bool:
        """Check if we have sufficient information to close the call."""
        collected = context.collected_data
        if context.scenario_type == ScenarioType.DRIVER_CHECKIN:
            required_fields = ["driver_status", "call_outcome"]
            return all(field in collected for field in required_fields)
        return len(collected) >= 2

    def _get_default_response(self, response_id: int) -> Dict[str, Any]:
        """Get default response for error cases."""
        return {
            "response": "I understand. Can you tell me more about your current situation?",
            "response_id": response_id
        }


# Global conversation flow service instance
conversation_flow_service = ConversationFlowService()
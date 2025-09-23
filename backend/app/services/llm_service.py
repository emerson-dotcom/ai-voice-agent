"""
LLM Service for Structured Data Extraction
Integrates with OpenAI GPT-4 for extracting structured data from call transcripts.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import openai
from app.core.config import settings
from app.models.agent import ScenarioType

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM-based structured data extraction and conversation management."""

    def __init__(self):
        # Initialize OpenAI client
        openai.api_key = settings.OPENAI_API_KEY
        self.model = "gpt-4"
        self.max_tokens = 1000
        self.temperature = 0.1  # Low temperature for consistent extraction

    async def extract_structured_data(
        self,
        transcript: str,
        scenario_type: ScenarioType,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Extract structured data from call transcript using GPT-4."""
        try:
            prompt = self._get_extraction_prompt(scenario_type, transcript, context)

            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt(scenario_type)},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )

            extracted_data = json.loads(response.choices[0].message.content)

            # Add confidence score and metadata
            result = {
                "extracted_data": extracted_data,
                "confidence_score": self._calculate_confidence(extracted_data, transcript),
                "extraction_timestamp": datetime.utcnow().isoformat(),
                "model_used": self.model,
                "scenario_type": scenario_type.value
            }

            logger.info(f"Successfully extracted structured data for scenario {scenario_type}")
            return result

        except Exception as e:
            logger.error(f"Error extracting structured data: {str(e)}")
            return {
                "extracted_data": {},
                "confidence_score": 0.0,
                "error": str(e),
                "extraction_timestamp": datetime.utcnow().isoformat()
            }

    async def generate_conversation_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, Any]],
        agent_config: Dict[str, Any],
        scenario_type: ScenarioType,
        current_state: str
    ) -> Dict[str, Any]:
        """Generate contextual conversation response using GPT-4."""
        try:
            prompt = self._get_conversation_prompt(
                user_message, conversation_history, agent_config, scenario_type, current_state
            )

            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_conversation_system_prompt(agent_config, scenario_type)},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            logger.info(f"Generated conversation response for state {current_state}")
            return result

        except Exception as e:
            logger.error(f"Error generating conversation response: {str(e)}")
            return {
                "response": "I understand. Can you tell me more?",
                "next_state": current_state,
                "emergency_detected": False
            }

    def _get_system_prompt(self, scenario_type: ScenarioType) -> str:
        """Get system prompt for data extraction based on scenario type."""
        if scenario_type == ScenarioType.DRIVER_CHECKIN:
            return """You are an expert data extraction system for logistics driver check-in calls.
            Extract structured data from call transcripts and return valid JSON only.

            Required fields for driver check-in scenario:
            - call_outcome: "In-Transit Update" OR "Arrival Confirmation"
            - driver_status: "Driving" OR "Delayed" OR "Arrived" OR "Unloading"
            - current_location: driver's current location description
            - eta: estimated time of arrival
            - delay_reason: reason for any delays or "None"
            - unloading_status: status of unloading process or "N/A"
            - pod_reminder_acknowledged: true/false if POD reminder was acknowledged

            Only return valid JSON with these exact field names."""

        elif scenario_type == ScenarioType.EMERGENCY_PROTOCOL:
            return """You are an expert data extraction system for emergency logistics calls.
            Extract structured data from emergency call transcripts and return valid JSON only.

            Required fields for emergency scenario:
            - call_outcome: "Emergency Escalation"
            - emergency_type: "Accident" OR "Breakdown" OR "Medical" OR "Other"
            - safety_status: description of safety confirmation
            - injury_status: description of injury status
            - emergency_location: specific location of emergency
            - load_secure: true/false if load is secure
            - escalation_status: "Connected to Human Dispatcher" or current status

            Only return valid JSON with these exact field names."""

        return "Extract structured data from the call transcript and return valid JSON."

    def _get_extraction_prompt(self, scenario_type: ScenarioType, transcript: str, context: Dict[str, Any] = None) -> str:
        """Build extraction prompt with transcript and context."""
        base_prompt = f"""
        Extract structured data from this call transcript:

        TRANSCRIPT:
        {transcript}
        """

        if context:
            base_prompt += f"""

        ADDITIONAL CONTEXT:
        Driver Name: {context.get('driver_name', 'Unknown')}
        Load Number: {context.get('load_number', 'Unknown')}
        """

        if scenario_type == ScenarioType.DRIVER_CHECKIN:
            base_prompt += """

        Focus on extracting information about the driver's current status, location,
        timeline, and any issues or delays. If this appears to be an arrival confirmation,
        extract unloading details.
        """

        elif scenario_type == ScenarioType.EMERGENCY_PROTOCOL:
            base_prompt += """

        This is an emergency call. Focus on extracting safety information, injury status,
        emergency type, location, and escalation details.
        """

        return base_prompt

    def _get_conversation_system_prompt(self, agent_config: Dict[str, Any], scenario_type: ScenarioType) -> str:
        """Get system prompt for conversation generation."""
        base_prompt = f"""You are a professional logistics dispatcher AI making calls to truck drivers.

        Agent Configuration:
        - Voice: {agent_config.get('voice_id', 'default')}
        - Scenario: {scenario_type.value}
        - Temperature: {agent_config.get('temperature', 0.7)}
        - Use backchannel responses: {agent_config.get('enable_backchannel', True)}

        Instructions:
        1. Be professional but friendly
        2. Ask clear, specific questions
        3. If emergency keywords are detected, immediately pivot to emergency protocol
        4. Keep responses concise and natural
        5. Return JSON with 'response', 'next_state', and 'emergency_detected' fields
        """

        if scenario_type == ScenarioType.DRIVER_CHECKIN:
            base_prompt += """

        Driver Check-in Protocol:
        1. Start with open-ended status inquiry
        2. Based on response, ask follow-up questions about location, timing, delays
        3. If driver has arrived, ask about unloading status
        4. Remind about POD (Proof of Delivery) requirements
        """

        elif scenario_type == ScenarioType.EMERGENCY_PROTOCOL:
            base_prompt += """

        Emergency Protocol:
        1. Immediately assess safety status
        2. Gather critical information quickly
        3. Confirm location and nature of emergency
        4. Prepare to escalate to human dispatcher
        """

        return base_prompt

    def _get_conversation_prompt(
        self,
        user_message: str,
        conversation_history: List[Dict[str, Any]],
        agent_config: Dict[str, Any],
        scenario_type: ScenarioType,
        current_state: str
    ) -> str:
        """Build conversation prompt with history and context."""

        history_text = ""
        for msg in conversation_history[-5:]:  # Last 5 messages for context
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            history_text += f"{role}: {content}\n"

        prompt = f"""
        CONVERSATION HISTORY:
        {history_text}

        CURRENT USER MESSAGE:
        {user_message}

        CURRENT STATE: {current_state}

        Generate the next response as a professional dispatcher.
        Check for emergency keywords and set emergency_detected to true if found.
        Determine the next conversation state based on the flow.

        Return JSON format:
        {{
            "response": "your response text",
            "next_state": "next_conversation_state",
            "emergency_detected": false
        }}
        """

        return prompt

    def _calculate_confidence(self, extracted_data: Dict[str, Any], transcript: str) -> float:
        """Calculate confidence score for extracted data."""
        if not extracted_data:
            return 0.0

        # Simple confidence calculation based on data completeness
        total_fields = len(extracted_data)
        filled_fields = len([v for v in extracted_data.values() if v and str(v).strip() != ""])

        base_confidence = filled_fields / total_fields if total_fields > 0 else 0.0

        # Adjust based on transcript length and content quality
        transcript_words = len(transcript.split())
        if transcript_words < 10:
            base_confidence *= 0.5
        elif transcript_words > 50:
            base_confidence = min(base_confidence * 1.1, 1.0)

        return round(base_confidence, 2)


# Global LLM service instance
llm_service = LLMService()
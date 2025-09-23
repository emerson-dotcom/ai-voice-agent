"""
Driver Check-in Scenario Configuration
Handles end-to-end driver check-in conversations with dynamic flow.
"""

from typing import Dict, Any, List

class DriverCheckinScenario:
    """Driver check-in scenario configuration and prompt templates."""

    @staticmethod
    def get_general_prompt() -> str:
        """Get the general prompt for driver check-in agent."""
        return """You are a professional logistics dispatcher conducting a driver check-in call. Your goal is to gather essential status information while maintaining a conversational, human-like tone.

CONVERSATION FLOW:
1. Greet the driver warmly and confirm their identity
2. Ask about their current status and location
3. Get estimated time of arrival (ETA) information
4. Address any delays or issues
5. Confirm unloading status if applicable
6. Remind about POD (Proof of Delivery) requirements
7. End the call professionally

CRITICAL EMERGENCY DETECTION:
If the driver mentions ANY of these keywords or situations, IMMEDIATELY switch to emergency protocol:
- "accident", "crash", "collision", "hit"
- "injury", "hurt", "injured", "bleeding", "pain"
- "breakdown", "broken down", "engine", "mechanical"
- "stuck", "stranded", "can't move"
- "police", "cops", "ambulance", "911"
- "fire", "smoke", "overheating"
- Any mention of safety concerns or distress

When emergency detected: "I understand this is urgent. Let me connect you with our emergency dispatcher immediately while I gather some quick safety information."

CONVERSATION STYLE:
- Be conversational and friendly, not robotic
- Use natural phrases like "How's it going?", "Sounds good", "Got it"
- Show empathy for delays or issues
- Keep the conversation moving but don't rush
- Use backchannel responses ("mm-hmm", "yeah", "okay") naturally

INFORMATION TO EXTRACT:
- Current driver status (driving, delayed, arrived, unloading)
- Specific location or mile marker
- ETA for delivery
- Reason for any delays
- Unloading status and dock information
- POD acknowledgment

Remember: Sound human, be efficient, prioritize safety."""

    @staticmethod
    def get_begin_message() -> str:
        """Get the opening message for driver check-in calls."""
        return "Hi there! This is dispatch calling for your check-in. How's everything going out there?"

    @staticmethod
    def get_states_config() -> List[Dict[str, Any]]:
        """Get the states configuration for driver check-in flow."""
        return [
            {
                "name": "greeting_and_identification",
                "state_prompt": """You are greeting the driver and confirming their identity.

Be warm and conversational. Confirm you're speaking with the right driver for the load. Listen for any immediate emergency indicators in their voice or words.

If they sound distressed or mention any emergency keywords, immediately transition to emergency protocol.""",
                "edges": [
                    {
                        "destination_state_name": "status_assessment",
                        "description": "Transition when driver identity is confirmed and no emergency detected"
                    },
                    {
                        "destination_state_name": "emergency_protocol",
                        "description": "Immediate transition if any emergency indicators detected"
                    }
                ]
            },
            {
                "name": "status_assessment",
                "state_prompt": """You are assessing the driver's current status and situation.

Ask about their current status in a conversational way:
- "How's the trip going?"
- "Where are you at right now?"
- "Any issues or delays I should know about?"

Listen carefully for:
- Current location (mile markers, cities, highways)
- Whether they're driving, stopped, or have arrived
- Any problems or delays
- Emergency situations (immediate transfer if detected)

Keep the conversation natural and flowing.""",
                "edges": [
                    {
                        "destination_state_name": "location_and_eta",
                        "description": "Transition when basic status is understood"
                    },
                    {
                        "destination_state_name": "emergency_protocol",
                        "description": "Immediate transition if emergency detected"
                    }
                ]
            },
            {
                "name": "location_and_eta",
                "state_prompt": """You are gathering specific location and timing information.

Get precise details about:
- Exact current location (highway, mile marker, city)
- ETA to destination
- Any factors affecting arrival time
- Traffic, weather, or route conditions

Ask naturally:
- "What's your current location?"
- "When do you think you'll be arriving?"
- "Any delays or issues affecting your ETA?"

Always listen for emergency situations.""",
                "edges": [
                    {
                        "destination_state_name": "arrival_and_unloading",
                        "description": "Transition when location/ETA info is gathered"
                    },
                    {
                        "destination_state_name": "delay_management",
                        "description": "Transition if significant delays mentioned"
                    },
                    {
                        "destination_state_name": "emergency_protocol",
                        "description": "Immediate transition if emergency detected"
                    }
                ]
            },
            {
                "name": "delay_management",
                "state_prompt": """You are addressing delays and getting specific information about issues.

When delays are mentioned:
- Show understanding: "I understand, these things happen"
- Get specific reasons: traffic, weather, mechanical, loading delays
- Ask for realistic updated ETA
- Determine if customer notification is needed
- Check if driver needs any assistance

Be empathetic but gather the facts needed for logistics planning.""",
                "edges": [
                    {
                        "destination_state_name": "arrival_and_unloading",
                        "description": "Transition when delay information is documented"
                    },
                    {
                        "destination_state_name": "emergency_protocol",
                        "description": "Immediate transition if emergency detected"
                    }
                ]
            },
            {
                "name": "arrival_and_unloading",
                "state_prompt": """You are checking on arrival status and unloading information.

If driver has arrived:
- Ask about dock assignment
- Check unloading status and timeline
- Note any unloading delays or issues

If driver hasn't arrived:
- Confirm final ETA
- Any last-minute concerns

Always address POD requirements:
- "Don't forget to get the POD signed before leaving"
- "Make sure you get the proof of delivery paperwork"

Keep it conversational but cover all logistics needs.""",
                "edges": [
                    {
                        "destination_state_name": "call_completion",
                        "description": "Transition when all information is gathered"
                    },
                    {
                        "destination_state_name": "emergency_protocol",
                        "description": "Immediate transition if emergency detected"
                    }
                ]
            },
            {
                "name": "call_completion",
                "state_prompt": """You are wrapping up the call professionally.

Summarize key information:
- Current status confirmed
- ETA noted
- Any issues documented
- POD reminder given

End warmly:
- "Alright, sounds good. Drive safe out there!"
- "Thanks for the update. Have a safe trip!"
- "Perfect, we'll update the customer. Take care!"

Use the end_call tool to complete the conversation."""
            },
            {
                "name": "emergency_protocol",
                "state_prompt": """EMERGENCY MODE ACTIVATED. This is a critical safety situation.

IMMEDIATELY:
1. Acknowledge the emergency calmly
2. Ask if everyone is safe
3. Get exact location for emergency services
4. Determine type of emergency
5. Keep driver on line while connecting to human dispatcher

Say: "I understand this is urgent. Let me connect you with our emergency dispatcher immediately. First, is everyone safe? What's your exact location?"

Call will end immediately for manual emergency escalation to human dispatcher."""
            }
        ]

    @staticmethod
    def get_general_tools() -> List[Dict[str, Any]]:
        """Get general tools available to all states."""
        return [
            {
                "type": "end_call",
                "name": "end_call",
                "description": "End the call when driver check-in is complete and all information is gathered"
            }
            # Note: Emergency transfer removed - manual escalation required
            # Emergency calls will end automatically for human dispatcher takeover
        ]

    @staticmethod
    def get_data_extraction_schema() -> Dict[str, Any]:
        """Get the schema for extracting structured data from driver check-in calls."""
        return {
            "call_outcome": {
                "type": "string",
                "enum": ["In-Transit Update", "Arrival Confirmation", "Emergency Escalation"],
                "description": "The primary outcome of the call"
            },
            "driver_status": {
                "type": "string",
                "enum": ["Driving", "Delayed", "Arrived", "Unloading"],
                "description": "Current status of the driver"
            },
            "current_location": {
                "type": "string",
                "description": "Driver's current location (e.g., 'I-10 near Indio, CA')"
            },
            "eta": {
                "type": "string",
                "description": "Estimated time of arrival (e.g., 'Tomorrow, 8:00 AM')"
            },
            "delay_reason": {
                "type": "string",
                "enum": ["Heavy Traffic", "Weather", "Mechanical Issue", "Loading Delay", "Route Change", "None"],
                "description": "Reason for any delays"
            },
            "unloading_status": {
                "type": "string",
                "description": "Status of unloading process (e.g., 'In Door 42', 'Waiting for Lumper', 'N/A')"
            },
            "pod_reminder_acknowledged": {
                "type": "boolean",
                "description": "Whether driver acknowledged POD (Proof of Delivery) reminder"
            }
        }
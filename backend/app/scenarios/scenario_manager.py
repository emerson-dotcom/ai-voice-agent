"""
Scenario Manager
Manages logistics scenarios and provides configuration for different call types.
"""

from typing import Dict, Any, List, Optional
from .driver_checkin import DriverCheckinScenario
from .emergency_protocol import EmergencyProtocolScenario

class ScenarioManager:
    """Manages logistics scenarios and provides unified configuration interface."""

    SCENARIOS = {
        "driver_checkin": DriverCheckinScenario,
        "emergency_protocol": EmergencyProtocolScenario
    }

    @classmethod
    def get_scenario_config(cls, scenario_type: str) -> Dict[str, Any]:
        """Get complete configuration for a scenario type."""
        if scenario_type not in cls.SCENARIOS:
            raise ValueError(f"Unknown scenario type: {scenario_type}")

        scenario_class = cls.SCENARIOS[scenario_type]

        return {
            "general_prompt": scenario_class.get_general_prompt(),
            "begin_message": scenario_class.get_begin_message(),
            "states": scenario_class.get_states_config(),
            "general_tools": scenario_class.get_general_tools(),
            "data_extraction_schema": scenario_class.get_data_extraction_schema()
        }

    @classmethod
    def build_llm_config(cls, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build LLM configuration with scenario-specific prompts and states."""
        scenario_type = agent_data.get("scenario_type")
        if not scenario_type:
            raise ValueError("Agent must have a scenario_type")

        scenario_config = cls.get_scenario_config(scenario_type)

        # Base LLM configuration
        llm_config = {
            "general_prompt": scenario_config["general_prompt"],
            "model": agent_data.get("model", "gpt-4o"),
            "model_temperature": agent_data.get("voice_temperature", 0.8),
        }

        # Add begin message - prioritize agent's custom begin_message over scenario default
        if agent_data.get("begin_message"):
            # Use the agent's custom begin_message from database
            llm_config["begin_message"] = agent_data["begin_message"]
        elif scenario_config.get("begin_message"):
            # Fallback to scenario default if no custom message set
            llm_config["begin_message"] = scenario_config["begin_message"]

        # Add default dynamic variables for template substitution
        llm_config["default_dynamic_variables"] = {
            "driver_name": "Driver",
            "load_number": "N/A"
        }

        # Add states configuration
        if scenario_config.get("states"):
            llm_config["states"] = scenario_config["states"]
            # Set starting state to first state
            llm_config["starting_state"] = scenario_config["states"][0]["name"]

        # Add general tools
        if scenario_config.get("general_tools"):
            llm_config["general_tools"] = scenario_config["general_tools"]

        return llm_config

    @classmethod
    def build_agent_config(cls, agent_data: Dict[str, Any], llm_id: str) -> Dict[str, Any]:
        """Build agent configuration with scenario-specific settings."""
        scenario_type = agent_data.get("scenario_type")

        # Base agent configuration
        agent_config = {
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

        # Scenario-specific adjustments
        if scenario_type == "emergency_protocol":
            # Emergency protocol needs highest responsiveness and interruption sensitivity (max 1.0 for Retell API)
            agent_config["responsiveness"] = 1.0
            agent_config["interruption_sensitivity"] = 1.0
            agent_config["backchannel_frequency"] = min(agent_config["backchannel_frequency"], 0.6)  # Less backchannel during emergencies

        elif scenario_type == "driver_checkin":
            # Driver check-in benefits from natural conversation flow
            agent_config["backchannel_frequency"] = max(agent_config["backchannel_frequency"], 0.8)

        # Add optional fields
        if agent_data.get("voice_model"):
            agent_config["voice_model"] = agent_data["voice_model"]

        if agent_data.get("backchannel_words"):
            agent_config["backchannel_words"] = agent_data["backchannel_words"]

        if agent_data.get("name"):
            agent_config["agent_name"] = agent_data["name"]

        return agent_config

    @classmethod
    def get_data_extraction_prompt(cls, scenario_type: str, transcript: str) -> str:
        """Generate data extraction prompt for post-call analysis."""
        if scenario_type not in cls.SCENARIOS:
            raise ValueError(f"Unknown scenario type: {scenario_type}")

        scenario_config = cls.get_scenario_config(scenario_type)
        schema = scenario_config["data_extraction_schema"]

        prompt = f"""Extract structured data from this logistics call transcript.

SCENARIO: {scenario_type.replace('_', ' ').title()}

TRANSCRIPT:
{transcript}

EXTRACT THE FOLLOWING DATA in JSON format:

"""

        for field, config in schema.items():
            prompt += f"- {field}: {config.get('description', 'No description')}"
            if config.get('enum'):
                prompt += f" (Options: {', '.join(config['enum'])})"
            prompt += f" [{config['type']}]\n"

        prompt += """
INSTRUCTIONS:
- Extract only information explicitly mentioned in the transcript
- Use null for missing information
- Be accurate - don't infer information not clearly stated
- For enums, use exact values from the options list
- Provide confidence level (0.0-1.0) for extracted data

Return valid JSON only."""

        return prompt

    @classmethod
    def list_available_scenarios(cls) -> List[Dict[str, str]]:
        """List all available scenario types with descriptions."""
        return [
            {
                "type": "driver_checkin",
                "name": "Driver Check-in Agent",
                "description": "Handles end-to-end driver check-in conversations with dynamic flow based on driver status"
            },
            {
                "type": "emergency_protocol",
                "name": "Emergency Protocol Agent",
                "description": "Detects emergencies during routine calls and immediately escalates to human dispatcher"
            }
        ]

    @classmethod
    def validate_scenario_agent_data(cls, scenario_type: str, agent_data: Dict[str, Any]) -> List[str]:
        """Validate agent data for specific scenario requirements."""
        errors = []

        if scenario_type not in cls.SCENARIOS:
            errors.append(f"Unknown scenario type: {scenario_type}")
            return errors

        # Common required fields
        required_fields = ["name", "general_prompt", "voice_id", "scenario_type"]
        for field in required_fields:
            if not agent_data.get(field):
                errors.append(f"Missing required field: {field}")

        # Scenario-specific validation
        if scenario_type == "emergency_protocol":
            # Emergency protocol should have high responsiveness
            if agent_data.get("responsiveness", 1.0) < 1.0:
                errors.append("Emergency protocol agents should have responsiveness >= 1.0")

        elif scenario_type == "driver_checkin":
            # Driver check-in should have balanced settings
            if agent_data.get("backchannel_frequency", 0.8) < 0.5:
                errors.append("Driver check-in agents should have backchannel_frequency >= 0.5 for natural conversation")

        return errors
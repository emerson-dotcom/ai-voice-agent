"""
Scenarios API endpoints.
Handles scenario configuration and management.
"""

from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.scenarios.scenario_manager import ScenarioManager
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class ScenarioInfo(BaseModel):
    """Scenario information model."""
    type: str
    name: str
    description: str


class ScenarioConfig(BaseModel):
    """Scenario configuration model."""
    type: str
    general_prompt: str
    begin_message: str
    states: List[dict]
    general_tools: List[dict]
    data_extraction_schema: dict


@router.get("/", response_model=List[ScenarioInfo])
async def list_scenarios():
    """List all available logistics scenarios."""
    try:
        scenarios = ScenarioManager.list_available_scenarios()
        return scenarios
    except Exception as e:
        logger.error(f"Error listing scenarios: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list scenarios")


@router.get("/{scenario_type}", response_model=ScenarioConfig)
async def get_scenario_config(scenario_type: str):
    """Get configuration for a specific scenario type."""
    try:
        config = ScenarioManager.get_scenario_config(scenario_type)
        return {
            "type": scenario_type,
            **config
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting scenario config for {scenario_type}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get scenario configuration")


@router.post("/{scenario_type}/validate")
async def validate_agent_for_scenario(scenario_type: str, agent_data: dict):
    """Validate agent data for specific scenario requirements."""
    try:
        errors = ScenarioManager.validate_scenario_agent_data(scenario_type, agent_data)

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "scenario_type": scenario_type
        }
    except Exception as e:
        logger.error(f"Error validating agent for scenario {scenario_type}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to validate agent data")


@router.post("/{scenario_type}/extract-data")
async def extract_data_from_transcript(scenario_type: str, transcript_data: dict):
    """Generate data extraction prompt for post-call analysis."""
    try:
        transcript = transcript_data.get("transcript", "")
        if not transcript:
            raise HTTPException(status_code=400, detail="Transcript is required")

        extraction_prompt = ScenarioManager.get_data_extraction_prompt(scenario_type, transcript)

        return {
            "scenario_type": scenario_type,
            "extraction_prompt": extraction_prompt,
            "schema": ScenarioManager.get_scenario_config(scenario_type)["data_extraction_schema"]
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating extraction prompt for {scenario_type}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate extraction prompt")
"""
Post-call analysis service for extracting structured data from call transcripts.
"""

import json
import logging
from typing import Dict, Any, Optional
from app.scenarios.scenario_manager import ScenarioManager
from app.core.database import supabase_client
from app.services.llm_service import llm_service
from app.models.agent import ScenarioType

logger = logging.getLogger(__name__)


class AnalysisService:
    """Service for analyzing call transcripts and extracting structured data."""

    @staticmethod
    async def analyze_call_transcript(call_id: str, transcript: str, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze call transcript and extract structured data based on scenario.

        Args:
            call_id: The call ID
            transcript: The call transcript
            agent_data: Agent configuration data including scenario_type

        Returns:
            Dict containing extracted structured data
        """
        try:
            scenario_type = agent_data.get("scenario_type")
            if not scenario_type:
                logger.warning(f"No scenario type found for call {call_id}, skipping analysis")
                return {"error": "No scenario type specified"}

            # Convert string scenario type to enum
            scenario_enum = ScenarioType(scenario_type)

            # Use real LLM service for data extraction
            extraction_result = await llm_service.extract_structured_data(
                transcript=transcript,
                scenario_type=scenario_enum,
                context={"call_id": call_id, "agent_data": agent_data}
            )

            extracted_data = extraction_result.get("extracted_data", {})
            confidence_score = extraction_result.get("confidence_score", 0.0)

            # Store analysis results
            analysis_data = {
                "call_id": call_id,
                "scenario_type": scenario_type,
                "extraction_method": "llm_analysis",
                "confidence_score": confidence_score,
                "custom_analysis_data": extracted_data,
                "extraction_metadata": {
                    "model_used": extraction_result.get("model_used", "gpt-4"),
                    "extraction_timestamp": extraction_result.get("extraction_timestamp"),
                    "error": extraction_result.get("error")
                },
                **{k: v for k, v in extracted_data.items() if k not in ["confidence_score", "error"]}
            }

            # Save to database
            await supabase_client.create_call_results(analysis_data)

            logger.info(f"Analysis completed for call {call_id} with scenario {scenario_type}")
            return analysis_data

        except Exception as e:
            logger.error(f"Error analyzing call {call_id}: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    def _simulate_data_extraction(scenario_type: str, transcript: str) -> Dict[str, Any]:
        """
        Simulate LLM-based data extraction from transcript.
        In production, this would make an actual LLM API call.
        """

        # Basic keyword-based extraction for demonstration
        transcript_lower = transcript.lower()

        if scenario_type == "driver_checkin":
            return AnalysisService._extract_driver_checkin_data(transcript_lower)
        elif scenario_type == "emergency_protocol":
            return AnalysisService._extract_emergency_data(transcript_lower)
        else:
            return {"error": f"Unknown scenario type: {scenario_type}"}

    @staticmethod
    def _extract_driver_checkin_data(transcript: str) -> Dict[str, Any]:
        """Extract driver check-in specific data from transcript."""
        data = {
            "confidence_score": 0.8
        }

        # Determine call outcome
        if any(word in transcript for word in ["arrived", "here", "dock", "unloading"]):
            data["call_outcome"] = "Arrival Confirmation"
        else:
            data["call_outcome"] = "In-Transit Update"

        # Driver status
        if "arrived" in transcript or "here" in transcript:
            data["driver_status"] = "Arrived"
        elif any(word in transcript for word in ["delay", "behind", "late", "stuck"]):
            data["driver_status"] = "Delayed"
        elif "unload" in transcript:
            data["driver_status"] = "Unloading"
        else:
            data["driver_status"] = "Driving"

        # Location extraction (simplified)
        if "i-" in transcript or "interstate" in transcript:
            # Try to extract highway information
            words = transcript.split()
            for i, word in enumerate(words):
                if word.startswith("i-") and i < len(words) - 1:
                    data["current_location"] = f"{word.upper()} near {words[i+1] if i+1 < len(words) else 'unknown'}"
                    break
        elif "mile" in transcript:
            data["current_location"] = "Highway location (mile marker mentioned)"
        else:
            data["current_location"] = "Location discussed but not clearly specified"

        # ETA extraction
        if any(word in transcript for word in ["hour", "minutes", "tomorrow", "morning", "afternoon"]):
            if "hour" in transcript:
                data["eta"] = "Within a few hours"
            elif "tomorrow" in transcript:
                data["eta"] = "Tomorrow"
            else:
                data["eta"] = "ETA provided"
        else:
            data["eta"] = "No specific ETA given"

        # Delay reasons
        if "traffic" in transcript:
            data["delay_reason"] = "Heavy Traffic"
        elif "weather" in transcript:
            data["delay_reason"] = "Weather"
        elif "mechanical" in transcript or "engine" in transcript:
            data["delay_reason"] = "Mechanical Issue"
        elif "load" in transcript and "delay" in transcript:
            data["delay_reason"] = "Loading Delay"
        else:
            data["delay_reason"] = "None"

        # Unloading status
        if "dock" in transcript:
            data["unloading_status"] = "At dock (specific door mentioned)" if any(char.isdigit() for char in transcript) else "At dock"
        elif "wait" in transcript and "lumper" in transcript:
            data["unloading_status"] = "Waiting for Lumper"
        elif "unload" in transcript:
            data["unloading_status"] = "Unloading in progress"
        else:
            data["unloading_status"] = "N/A"

        # POD reminder
        data["pod_reminder_acknowledged"] = "pod" in transcript or "proof" in transcript or "delivery" in transcript

        return data

    @staticmethod
    def _extract_emergency_data(transcript: str) -> Dict[str, Any]:
        """Extract emergency protocol specific data from transcript."""
        data = {
            "confidence_score": 0.9  # Higher confidence for emergency detection
        }

        # Emergency keywords
        emergency_keywords = [
            "accident", "crash", "collision", "hit", "injury", "hurt", "breakdown",
            "stuck", "stranded", "police", "ambulance", "fire", "smoke", "emergency"
        ]

        emergency_detected = any(keyword in transcript for keyword in emergency_keywords)

        if emergency_detected:
            data["call_outcome"] = "Emergency Escalation"
        else:
            data["call_outcome"] = "Routine Logistics"

        # Emergency type
        if any(word in transcript for word in ["accident", "crash", "collision", "hit"]):
            data["emergency_type"] = "Accident"
        elif any(word in transcript for word in ["breakdown", "engine", "mechanical"]):
            data["emergency_type"] = "Breakdown"
        elif any(word in transcript for word in ["injury", "hurt", "medical", "ambulance"]):
            data["emergency_type"] = "Medical"
        elif any(word in transcript for word in ["weather", "tornado", "hurricane", "flood"]):
            data["emergency_type"] = "Weather"
        elif emergency_detected:
            data["emergency_type"] = "Other"
        else:
            data["emergency_type"] = "None"

        # Safety status
        if "safe" in transcript and "everyone" in transcript:
            data["safety_status"] = "Driver confirmed everyone is safe"
        elif "safe" in transcript:
            data["safety_status"] = "Driver reported being safe"
        elif emergency_detected:
            data["safety_status"] = "Safety status unclear - emergency situation"
        else:
            data["safety_status"] = "No safety concerns reported"

        # Injury status
        if "no injur" in transcript or ("no" in transcript and "hurt" in transcript):
            data["injury_status"] = "No injuries reported"
        elif any(word in transcript for word in ["injury", "hurt", "bleeding", "pain"]):
            data["injury_status"] = "Injuries reported or suspected"
        else:
            data["injury_status"] = "Injury status not discussed"

        # Emergency location
        if emergency_detected and ("i-" in transcript or "mile" in transcript or "highway" in transcript):
            data["emergency_location"] = "Highway location provided"
        elif emergency_detected:
            data["emergency_location"] = "Emergency location discussed"
        else:
            data["emergency_location"] = "N/A - no emergency"

        # Load security
        if "load" in transcript and ("secure" in transcript or "safe" in transcript):
            data["load_secure"] = True
        elif "load" in transcript and any(word in transcript for word in ["damage", "spill", "lost"]):
            data["load_secure"] = False
        else:
            data["load_secure"] = None

        # Escalation status
        if emergency_detected:
            if "dispatcher" in transcript or "transfer" in transcript:
                data["escalation_status"] = "Connected to Human Dispatcher"
            else:
                data["escalation_status"] = "Emergency Services Notified"
        else:
            data["escalation_status"] = "No Escalation Needed"

        # Emergency services
        data["emergency_services_called"] = "911" in transcript or "emergency" in transcript

        return data

    @staticmethod
    async def get_call_analysis(call_id: str) -> Optional[Dict[str, Any]]:
        """Get existing analysis for a call."""
        try:
            return await supabase_client.get_call_results(call_id)
        except Exception as e:
            logger.error(f"Error retrieving call analysis for {call_id}: {str(e)}")
            return None

    @staticmethod
    async def reanalyze_call(call_id: str) -> Dict[str, Any]:
        """Re-analyze a call with updated logic."""
        try:
            # Get call data
            call = await supabase_client.get_call_by_id(call_id)
            if not call:
                raise ValueError("Call not found")

            # Get agent data
            agent = await supabase_client.get_agent_by_id(call["agent_id"])
            if not agent:
                raise ValueError("Agent not found")

            # Re-analyze
            transcript = call.get("transcript", "")
            if not transcript:
                raise ValueError("No transcript available for analysis")

            return await AnalysisService.analyze_call_transcript(call_id, transcript, agent)

        except Exception as e:
            logger.error(f"Error re-analyzing call {call_id}: {str(e)}")
            return {"error": str(e)}
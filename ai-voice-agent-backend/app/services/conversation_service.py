"""
Conversation Service for Dynamic AI Voice Agent Logic
"""

import json
import logging
import re
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)

class ConversationScenario(Enum):
    """Available conversation scenarios."""
    DISPATCH_CHECKIN = "dispatch_checkin"
    EMERGENCY_PROTOCOL = "emergency_protocol"

class DriverStatus(Enum):
    """Driver status options."""
    MID_TRANSIT = "mid_transit"
    ARRIVED = "arrived"
    DELAYED = "delayed"
    EMERGENCY = "emergency"

class CallOutcome(Enum):
    """Call outcome options."""
    SUCCESSFUL = "successful"
    FAILED = "failed"
    ESCALATED = "escalated"
    INCOMPLETE = "incomplete"

class ConversationService:
    """Service for processing dynamic conversation logic."""
    
    def __init__(self):
        self.emergency_keywords = [
            "emergency", "accident", "crash", "injury", "hurt", "bleeding",
            "stuck", "broken down", "can't move", "urgent", "help", "danger"
        ]
        
        self.uncooperative_indicators = [
            "don't want to talk", "not answering", "refusing", "hanging up",
            "being difficult", "uncooperative", "rude", "angry"
        ]
        
        self.noise_indicators = [
            "can't hear", "unclear", "garbled", "static", "noise",
            "background noise", "cutting out", "breaking up"
        ]

    async def process_conversation(
        self, 
        transcript: str, 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a conversation transcript and extract structured data.
        
        Args:
            transcript: Full conversation transcript
            metadata: Call metadata including scenario type
            
        Returns:
            Structured data extracted from the conversation
        """
        try:
            # Determine conversation scenario
            scenario = self._detect_scenario(transcript, metadata)
            
            # Process based on scenario
            if scenario == ConversationScenario.EMERGENCY_PROTOCOL:
                return await self._process_emergency_conversation(transcript, metadata)
            else:
                return await self._process_dispatch_conversation(transcript, metadata)
                
        except Exception as e:
            logger.error(f"Error processing conversation: {e}")
            return {
                "call_outcome": CallOutcome.FAILED.value,
                "error": str(e),
                "scenario": "unknown"
            }

    def _detect_scenario(self, transcript: str, metadata: Dict[str, Any]) -> ConversationScenario:
        """Detect the conversation scenario based on transcript and metadata."""
        transcript_lower = transcript.lower()
        
        # Check for emergency keywords
        for keyword in self.emergency_keywords:
            if keyword in transcript_lower:
                return ConversationScenario.EMERGENCY_PROTOCOL
        
        # Check metadata for scenario hint
        if metadata.get("scenario") == "emergency":
            return ConversationScenario.EMERGENCY_PROTOCOL
        
        # Default to dispatch checkin
        return ConversationScenario.DISPATCH_CHECKIN

    async def _process_dispatch_conversation(
        self, 
        transcript: str, 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process dispatch check-in conversation."""
        try:
            # Extract basic information
            driver_name = self._extract_driver_name(transcript)
            load_number = self._extract_load_number(transcript)
            
            # Determine driver status
            driver_status = self._determine_driver_status(transcript)
            
            # Extract location information
            current_location = self._extract_location(transcript)
            eta = self._extract_eta(transcript)
            
            # Check for delays
            delay_reason = self._extract_delay_reason(transcript)
            
            # Check unloading status
            unloading_status = self._extract_unloading_status(transcript)
            
            # Check POD acknowledgment
            pod_acknowledged = self._extract_pod_acknowledgment(transcript)
            
            # Determine call outcome
            call_outcome = self._determine_call_outcome(transcript, driver_status)
            
            # Check for special cases
            special_cases = self._detect_special_cases(transcript)
            
            return {
                "call_outcome": call_outcome.value,
                "driver_status": driver_status.value,
                "current_location": current_location,
                "eta": eta,
                "delay_reason": delay_reason,
                "unloading_status": unloading_status,
                "pod_reminder_acknowledged": pod_acknowledged,
                "special_cases": special_cases,
                "scenario": ConversationScenario.DISPATCH_CHECKIN.value,
                "driver_name": driver_name,
                "load_number": load_number
            }
            
        except Exception as e:
            logger.error(f"Error processing dispatch conversation: {e}")
            return {
                "call_outcome": CallOutcome.FAILED.value,
                "error": str(e),
                "scenario": ConversationScenario.DISPATCH_CHECKIN.value
            }

    async def _process_emergency_conversation(
        self, 
        transcript: str, 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process emergency protocol conversation."""
        try:
            # Extract emergency information
            emergency_type = self._extract_emergency_type(transcript)
            safety_status = self._extract_safety_status(transcript)
            injury_status = self._extract_injury_status(transcript)
            emergency_location = self._extract_emergency_location(transcript)
            load_secure = self._extract_load_security(transcript)
            
            # Determine escalation status
            escalation_status = self._determine_escalation_status(transcript)
            
            return {
                "call_outcome": CallOutcome.ESCALATED.value,
                "emergency_type": emergency_type,
                "safety_status": safety_status,
                "injury_status": injury_status,
                "emergency_location": emergency_location,
                "load_secure": load_secure,
                "escalation_status": escalation_status,
                "scenario": ConversationScenario.EMERGENCY_PROTOCOL.value
            }
            
        except Exception as e:
            logger.error(f"Error processing emergency conversation: {e}")
            return {
                "call_outcome": CallOutcome.FAILED.value,
                "error": str(e),
                "scenario": ConversationScenario.EMERGENCY_PROTOCOL.value
            }

    def _extract_driver_name(self, transcript: str) -> Optional[str]:
        """Extract driver name from transcript."""
        # Look for patterns like "This is [name]" or "I'm [name]"
        patterns = [
            r"this is (\w+)",
            r"i'm (\w+)",
            r"i am (\w+)",
            r"my name is (\w+)",
            r"driver (\w+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, transcript.lower())
            if match:
                return match.group(1).title()
        
        return None

    def _extract_load_number(self, transcript: str) -> Optional[str]:
        """Extract load number from transcript."""
        # Look for load number patterns
        patterns = [
            r"load (\w+)",
            r"load number (\w+)",
            r"shipment (\w+)",
            r"delivery (\w+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, transcript.lower())
            if match:
                return match.group(1).upper()
        
        return None

    def _determine_driver_status(self, transcript: str) -> DriverStatus:
        """Determine driver status from transcript."""
        transcript_lower = transcript.lower()
        
        if any(word in transcript_lower for word in ["arrived", "here", "delivered", "completed"]):
            return DriverStatus.ARRIVED
        elif any(word in transcript_lower for word in ["delayed", "late", "behind", "stuck"]):
            return DriverStatus.DELAYED
        elif any(word in transcript_lower for word in self.emergency_keywords):
            return DriverStatus.EMERGENCY
        else:
            return DriverStatus.MID_TRANSIT

    def _extract_location(self, transcript: str) -> Optional[str]:
        """Extract current location from transcript."""
        # Look for location patterns
        patterns = [
            r"at (\w+ \w+)",
            r"in (\w+ \w+)",
            r"near (\w+ \w+)",
            r"location is (\w+ \w+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, transcript.lower())
            if match:
                return match.group(1).title()
        
        return None

    def _extract_eta(self, transcript: str) -> Optional[str]:
        """Extract ETA from transcript."""
        # Look for time patterns
        patterns = [
            r"(\d+) minutes",
            r"(\d+) mins",
            r"in (\d+) minutes",
            r"about (\d+) minutes",
            r"(\d+):(\d+)",
            r"(\d+) o'clock"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, transcript.lower())
            if match:
                return match.group(0)
        
        return None

    def _extract_delay_reason(self, transcript: str) -> Optional[str]:
        """Extract delay reason from transcript."""
        transcript_lower = transcript.lower()
        
        delay_reasons = [
            "traffic", "construction", "weather", "accident", "breakdown",
            "loading", "unloading", "paperwork", "customs", "detour"
        ]
        
        for reason in delay_reasons:
            if reason in transcript_lower:
                return reason.title()
        
        return None

    def _extract_unloading_status(self, transcript: str) -> Optional[str]:
        """Extract unloading status from transcript."""
        transcript_lower = transcript.lower()
        
        if any(word in transcript_lower for word in ["unloaded", "delivered", "completed"]):
            return "Completed"
        elif any(word in transcript_lower for word in ["unloading", "delivering"]):
            return "In Progress"
        elif any(word in transcript_lower for word in ["waiting", "scheduled"]):
            return "Scheduled"
        else:
            return None

    def _extract_pod_acknowledgment(self, transcript: str) -> bool:
        """Extract POD acknowledgment from transcript."""
        transcript_lower = transcript.lower()
        
        positive_responses = ["yes", "acknowledged", "understood", "got it", "will do"]
        
        return any(response in transcript_lower for response in positive_responses)

    def _determine_call_outcome(self, transcript: str, driver_status: DriverStatus) -> CallOutcome:
        """Determine overall call outcome."""
        transcript_lower = transcript.lower()
        
        if any(word in transcript_lower for word in self.uncooperative_indicators):
            return CallOutcome.INCOMPLETE
        elif driver_status == DriverStatus.EMERGENCY:
            return CallOutcome.ESCALATED
        elif any(word in transcript_lower for word in ["completed", "done", "finished"]):
            return CallOutcome.SUCCESSFUL
        else:
            return CallOutcome.SUCCESSFUL

    def _detect_special_cases(self, transcript: str) -> List[str]:
        """Detect special cases in the conversation."""
        special_cases = []
        transcript_lower = transcript.lower()
        
        if any(word in transcript_lower for word in self.uncooperative_indicators):
            special_cases.append("uncooperative_driver")
        
        if any(word in transcript_lower for word in self.noise_indicators):
            special_cases.append("noisy_environment")
        
        if "gps" in transcript_lower and "location" in transcript_lower:
            special_cases.append("conflicting_location_data")
        
        return special_cases

    # Emergency-specific extraction methods
    def _extract_emergency_type(self, transcript: str) -> Optional[str]:
        """Extract emergency type from transcript."""
        transcript_lower = transcript.lower()
        
        emergency_types = {
            "accident": ["accident", "crash", "collision"],
            "breakdown": ["broken down", "not working", "mechanical"],
            "medical": ["hurt", "injured", "bleeding", "pain"],
            "weather": ["storm", "flood", "snow", "ice"],
            "traffic": ["stuck", "blocked", "detour"]
        }
        
        for emergency_type, keywords in emergency_types.items():
            if any(keyword in transcript_lower for keyword in keywords):
                return emergency_type.title()
        
        return "Unknown"

    def _extract_safety_status(self, transcript: str) -> Optional[str]:
        """Extract safety status from transcript."""
        transcript_lower = transcript.lower()
        
        if any(word in transcript_lower for word in ["safe", "okay", "fine", "alright"]):
            return "Safe"
        elif any(word in transcript_lower for word in ["danger", "unsafe", "risk"]):
            return "At Risk"
        else:
            return "Unknown"

    def _extract_injury_status(self, transcript: str) -> Optional[str]:
        """Extract injury status from transcript."""
        transcript_lower = transcript.lower()
        
        if any(word in transcript_lower for word in ["hurt", "injured", "bleeding", "pain"]):
            return "Injured"
        elif any(word in transcript_lower for word in ["fine", "okay", "not hurt"]):
            return "Not Injured"
        else:
            return "Unknown"

    def _extract_emergency_location(self, transcript: str) -> Optional[str]:
        """Extract emergency location from transcript."""
        return self._extract_location(transcript)

    def _extract_load_security(self, transcript: str) -> Optional[bool]:
        """Extract load security status from transcript."""
        transcript_lower = transcript.lower()
        
        if any(word in transcript_lower for word in ["secure", "safe", "tied down"]):
            return True
        elif any(word in transcript_lower for word in ["loose", "falling", "unsafe"]):
            return False
        else:
            return None

    def _determine_escalation_status(self, transcript: str) -> str:
        """Determine escalation status."""
        transcript_lower = transcript.lower()
        
        if any(word in transcript_lower for word in ["escalated", "transferred", "human"]):
            return "Escalated to Human"
        else:
            return "AI Handled"

# Global instance
conversation_service = ConversationService()
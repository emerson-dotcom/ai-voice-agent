from typing import Dict, Any, List, Optional
import re
import json
from datetime import datetime
import openai
from app.config import settings


class NLPService:
    """Natural Language Processing service for extracting structured data from conversations"""
    
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        
        # Emergency keywords for detection
        self.emergency_keywords = [
            "emergency", "accident", "crash", "collision", "blowout", "breakdown",
            "medical", "injured", "hurt", "sick", "hospital", "ambulance",
            "fire", "smoke", "explosion", "leak", "hazmat", "dangerous",
            "stuck", "stranded", "disabled", "mechanical", "engine", "flat tire",
            "help", "urgent", "critical", "serious", "problem", "trouble"
        ]
        
        # Location extraction patterns
        self.location_patterns = [
            r'(?:mile marker|mm)\s*(\d+)',
            r'(?:exit|off)\s*(\d+)',
            r'I-(\d+)',
            r'Highway\s*(\d+)',
            r'Route\s*(\d+)',
            r'([A-Z][a-z]+),?\s*([A-Z]{2})',  # City, State
        ]

    async def extract_structured_data(
        self,
        transcript: str,
        scenario_type: str
    ) -> Dict[str, Any]:
        """Extract structured data from conversation transcript"""
        try:
            if scenario_type == "check_in":
                return await self._extract_checkin_data(transcript)
            elif scenario_type == "emergency":
                return await self._extract_emergency_data(transcript)
            else:
                return {"error": "Unknown scenario type", "confidence_score": 0.0}
                
        except Exception as e:
            print(f"Error in NLP extraction: {e}")
            return {
                "error": str(e),
                "confidence_score": 0.0,
                "extraction_method": "failed"
            }

    async def _extract_checkin_data(self, transcript: str) -> Dict[str, Any]:
        """Extract check-in specific data fields"""
        # Use OpenAI for primary extraction
        openai_result = await self._openai_extract_checkin(transcript)
        
        # Use rule-based extraction as backup
        rule_based_result = self._rule_based_extract_checkin(transcript)
        
        # Combine results with confidence weighting
        final_result = self._combine_extraction_results(
            openai_result,
            rule_based_result,
            "check_in"
        )
        
        return final_result

    async def _extract_emergency_data(self, transcript: str) -> Dict[str, Any]:
        """Extract emergency specific data fields"""
        # Use OpenAI for primary extraction
        openai_result = await self._openai_extract_emergency(transcript)
        
        # Use rule-based extraction as backup
        rule_based_result = self._rule_based_extract_emergency(transcript)
        
        # Combine results
        final_result = self._combine_extraction_results(
            openai_result,
            rule_based_result,
            "emergency"
        )
        
        return final_result

    async def _openai_extract_checkin(self, transcript: str) -> Dict[str, Any]:
        """Use OpenAI to extract check-in data"""
        prompt = f"""
        Extract structured data from this truck driver check-in conversation transcript:

        {transcript}

        Extract the following information and return as JSON:
        - call_outcome: "In-Transit Update" OR "Arrival Confirmation"
        - driver_status: "Driving" OR "Delayed" OR "Arrived" OR "Unloading"
        - current_location: specific location mentioned (string or null)
        - eta: estimated time of arrival (string or null)
        - delay_reason: reason for any delays (string or null)
        - unloading_status: unloading details (string or null)
        - pod_reminder_acknowledged: did driver acknowledge POD requirements? (boolean)

        Return ONLY the JSON object with these exact field names. If information is not available, use null.
        """
        
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured data from logistics conversations. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Clean up the response to ensure it's valid JSON
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            
            result = json.loads(result_text)
            result["extraction_method"] = "openai"
            result["confidence_score"] = 0.9  # High confidence for GPT-4
            
            return result
            
        except Exception as e:
            print(f"OpenAI extraction failed: {e}")
            return {
                "extraction_method": "openai_failed",
                "confidence_score": 0.0,
                "error": str(e)
            }

    async def _openai_extract_emergency(self, transcript: str) -> Dict[str, Any]:
        """Use OpenAI to extract emergency data"""
        prompt = f"""
        Extract structured data from this emergency truck driver conversation transcript:

        {transcript}

        Extract the following information and return as JSON:
        - call_outcome: "Emergency Escalation" (always for emergency)
        - emergency_type: "Accident" OR "Breakdown" OR "Medical" OR "Other"
        - safety_status: driver's safety confirmation (string or null)
        - injury_status: injury information (string or null)
        - emergency_location: specific emergency location (string or null)
        - load_secure: is the load secure? (boolean)
        - escalation_status: "Connected to Human Dispatcher" (standard response)

        Return ONLY the JSON object with these exact field names. If information is not available, use null.
        """
        
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured data from emergency logistics conversations. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Clean up the response
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            
            result = json.loads(result_text)
            result["extraction_method"] = "openai"
            result["confidence_score"] = 0.9
            
            return result
            
        except Exception as e:
            print(f"OpenAI emergency extraction failed: {e}")
            return {
                "extraction_method": "openai_failed",
                "confidence_score": 0.0,
                "error": str(e)
            }

    def _rule_based_extract_checkin(self, transcript: str) -> Dict[str, Any]:
        """Rule-based extraction for check-in data"""
        transcript_lower = transcript.lower()
        
        # Determine call outcome
        call_outcome = None
        if any(word in transcript_lower for word in ["arrived", "here", "at the dock", "at destination"]):
            call_outcome = "Arrival Confirmation"
        elif any(word in transcript_lower for word in ["driving", "on the road", "en route", "traveling"]):
            call_outcome = "In-Transit Update"
        
        # Determine driver status
        driver_status = None
        if any(word in transcript_lower for word in ["driving", "on the road"]):
            driver_status = "Driving"
        elif any(word in transcript_lower for word in ["delayed", "late", "behind", "stuck"]):
            driver_status = "Delayed"
        elif any(word in transcript_lower for word in ["arrived", "here", "at the"]):
            driver_status = "Arrived"
        elif any(word in transcript_lower for word in ["unloading", "offloading", "door"]):
            driver_status = "Unloading"
        
        # Extract location
        current_location = self._extract_location(transcript)
        
        # Extract ETA
        eta = self._extract_eta(transcript)
        
        # Extract delay reason
        delay_reason = self._extract_delay_reason(transcript)
        
        # POD acknowledgment
        pod_acknowledged = any(word in transcript_lower for word in ["pod", "proof of delivery", "paperwork", "documents"])
        
        return {
            "call_outcome": call_outcome,
            "driver_status": driver_status,
            "current_location": current_location,
            "eta": eta,
            "delay_reason": delay_reason,
            "unloading_status": None,
            "pod_reminder_acknowledged": pod_acknowledged,
            "extraction_method": "rule_based",
            "confidence_score": 0.6
        }

    def _rule_based_extract_emergency(self, transcript: str) -> Dict[str, Any]:
        """Rule-based extraction for emergency data"""
        transcript_lower = transcript.lower()
        
        # Emergency type detection
        emergency_type = "Other"
        if any(word in transcript_lower for word in ["accident", "crash", "collision"]):
            emergency_type = "Accident"
        elif any(word in transcript_lower for word in ["breakdown", "mechanical", "engine", "blowout"]):
            emergency_type = "Breakdown"
        elif any(word in transcript_lower for word in ["medical", "injured", "hurt", "sick"]):
            emergency_type = "Medical"
        
        # Safety status
        safety_status = None
        if any(phrase in transcript_lower for phrase in ["everyone is safe", "we're safe", "no injuries"]):
            safety_status = "Everyone is safe"
        elif any(phrase in transcript_lower for phrase in ["someone is hurt", "injured", "need ambulance"]):
            safety_status = "Injuries reported"
        
        # Injury status
        injury_status = "No injuries reported"
        if any(word in transcript_lower for word in ["injured", "hurt", "bleeding", "unconscious"]):
            injury_status = "Injuries reported"
        
        # Load security
        load_secure = True
        if any(phrase in transcript_lower for phrase in ["load shifted", "cargo damaged", "spilled"]):
            load_secure = False
        
        # Emergency location
        emergency_location = self._extract_location(transcript)
        
        return {
            "call_outcome": "Emergency Escalation",
            "emergency_type": emergency_type,
            "safety_status": safety_status,
            "injury_status": injury_status,
            "emergency_location": emergency_location,
            "load_secure": load_secure,
            "escalation_status": "Connected to Human Dispatcher",
            "extraction_method": "rule_based",
            "confidence_score": 0.7
        }

    def _extract_location(self, transcript: str) -> Optional[str]:
        """Extract location information from transcript"""
        # Look for common location patterns
        for pattern in self.location_patterns:
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                return match.group(0)
        
        # Look for common location phrases
        location_phrases = [
            r'at\s+([^,.!?]+)',
            r'near\s+([^,.!?]+)',
            r'on\s+([^,.!?]+)',
            r'in\s+([^,.!?]+)'
        ]
        
        for pattern in location_phrases:
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                if len(location) > 3 and len(location) < 100:  # Reasonable length
                    return location
        
        return None

    def _extract_eta(self, transcript: str) -> Optional[str]:
        """Extract ETA information from transcript"""
        eta_patterns = [
            r'(\d+)\s*(?:hours?|hrs?)',
            r'(\d+)\s*(?:minutes?|mins?)',
            r'(?:around|about|approximately)\s*(\d+(?::\d+)?)',
            r'(\d{1,2}:\d{2})',
            r'tomorrow\s*(?:at\s*)?(\d+(?::\d+)?)?',
            r'tonight\s*(?:at\s*)?(\d+(?::\d+)?)?'
        ]
        
        for pattern in eta_patterns:
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None

    def _extract_delay_reason(self, transcript: str) -> Optional[str]:
        """Extract delay reason from transcript"""
        delay_keywords = {
            "traffic": ["traffic", "congestion", "jam"],
            "weather": ["weather", "rain", "snow", "fog", "storm"],
            "mechanical": ["mechanical", "breakdown", "engine", "tire"],
            "loading": ["loading", "waiting", "dock", "appointment"],
            "other": ["delayed", "late", "behind"]
        }
        
        transcript_lower = transcript.lower()
        
        for reason, keywords in delay_keywords.items():
            if any(keyword in transcript_lower for keyword in keywords):
                return reason.title()
        
        return None

    def detect_emergency_trigger(self, message: str) -> bool:
        """Detect if message contains emergency keywords"""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.emergency_keywords)

    def extract_emergency_keywords(self, message: str) -> List[str]:
        """Extract specific emergency keywords from message"""
        message_lower = message.lower()
        found_keywords = []
        
        for keyword in self.emergency_keywords:
            if keyword in message_lower:
                found_keywords.append(keyword)
        
        return found_keywords

    def _combine_extraction_results(
        self,
        openai_result: Dict[str, Any],
        rule_based_result: Dict[str, Any],
        scenario_type: str
    ) -> Dict[str, Any]:
        """Combine OpenAI and rule-based extraction results"""
        # If OpenAI worked well, use it primarily
        if openai_result.get("confidence_score", 0) > 0.8:
            combined = openai_result.copy()
            
            # Fill in any missing values with rule-based results
            for key, value in rule_based_result.items():
                if key not in ["extraction_method", "confidence_score"] and not combined.get(key):
                    combined[key] = value
            
            combined["extraction_method"] = "openai_primary"
            
        else:
            # Use rule-based as primary with OpenAI backup
            combined = rule_based_result.copy()
            
            # Fill in missing values from OpenAI if available
            for key, value in openai_result.items():
                if key not in ["extraction_method", "confidence_score", "error"] and not combined.get(key):
                    combined[key] = value
            
            combined["extraction_method"] = "rule_based_primary"
            combined["confidence_score"] = min(0.8, combined.get("confidence_score", 0.6))
        
        # Add metadata
        combined["extracted_at"] = datetime.utcnow().isoformat()
        combined["scenario_type"] = scenario_type
        
        return combined

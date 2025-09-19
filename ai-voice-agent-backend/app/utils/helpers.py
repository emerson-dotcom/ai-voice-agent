import logging
from typing import Any, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def format_phone_number(phone: str) -> str:
    """Format phone number for Retell AI."""
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone))
    
    # Add +1 if it's a 10-digit US number
    if len(digits) == 10:
        return f"+1{digits}"
    elif len(digits) == 11 and digits.startswith('1'):
        return f"+{digits}"
    else:
        return f"+{digits}"


def validate_phone_number(phone: str) -> bool:
    """Validate phone number format."""
    digits = ''.join(filter(str.isdigit, phone))
    return len(digits) >= 10 and len(digits) <= 15


def sanitize_transcript(transcript: str) -> str:
    """Sanitize transcript text."""
    if not transcript:
        return ""
    
    # Remove extra whitespace and normalize
    return " ".join(transcript.split())


def extract_keywords(text: str, keywords: list) -> list:
    """Extract keywords from text."""
    text_lower = text.lower()
    found_keywords = []
    
    for keyword in keywords:
        if keyword.lower() in text_lower:
            found_keywords.append(keyword)
    
    return found_keywords


def create_response(success: bool, message: str = "", data: Any = None) -> Dict[str, Any]:
    """Create standardized API response."""
    response = {
        "success": success,
        "timestamp": datetime.now().isoformat()
    }
    
    if message:
        response["message"] = message
    
    if data is not None:
        response["data"] = data
    
    return response


def log_api_call(endpoint: str, method: str, user_id: Optional[str] = None, **kwargs):
    """Log API call for monitoring."""
    log_data = {
        "endpoint": endpoint,
        "method": method,
        "timestamp": datetime.now().isoformat()
    }
    
    if user_id:
        log_data["user_id"] = user_id
    
    log_data.update(kwargs)
    
    logger.info(f"API Call: {method} {endpoint}", extra=log_data)

"""
Call Polling Service for Localhost Development
Since webhooks can't reach localhost, we'll poll Retell AI for call updates
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from app.core.database import get_supabase_client
from app.services.retell_service import retell_service
from app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)

class CallPollingService:
    """Service for polling Retell AI for call status updates."""
    
    def __init__(self):
        self.conversation_service = ConversationService()
        self.polling_interval = 10  # seconds
        self.max_polling_duration = 1800  # 30 minutes max
        
    async def start_polling_for_call(self, call_id: str, retell_call_id: str):
        """
        Start polling for a specific call.
        
        Args:
            call_id: Internal call ID
            retell_call_id: Retell AI call ID
        """
        logger.info(f"Starting polling for call {call_id} (Retell: {retell_call_id})")
        
        start_time = datetime.now()
        
        while True:
            try:
                # Check if we've exceeded max polling time
                if datetime.now() - start_time > timedelta(seconds=self.max_polling_duration):
                    logger.warning(f"Polling timeout for call {call_id}")
                    await self._handle_polling_timeout(call_id)
                    break
                
                # Get call status from Retell AI
                call_status = await self._get_retell_call_status(retell_call_id)
                
                if call_status:
                    # Process the call status update
                    await self._process_call_status_update(call_id, call_status)
                    
                    # If call is completed or failed, stop polling
                    if call_status.get("status") in ["completed", "failed"]:
                        logger.info(f"Call {call_id} finished with status: {call_status.get('status')}")
                        break
                
                # Wait before next poll
                await asyncio.sleep(self.polling_interval)
                
            except Exception as e:
                logger.error(f"Error polling call {call_id}: {e}")
                await asyncio.sleep(self.polling_interval)
    
    async def _get_retell_call_status(self, retell_call_id: str) -> Optional[Dict[str, Any]]:
        """Get call status from Retell AI."""
        try:
            # Use the Retell AI API to get call status
            # This would call: retell_service.get_call_status(retell_call_id)
            # For now, return None to indicate no status available
            logger.info(f"Getting call status for {retell_call_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting Retell call status: {e}")
            return None
    
    async def _process_call_status_update(self, call_id: str, call_status: Dict[str, Any]):
        """Process a call status update."""
        try:
            supabase = get_supabase_client()
            
            status = call_status.get("status")
            transcript = call_status.get("transcript", "")
            metadata = call_status.get("metadata", {})
            
            if status == "completed":
                # Process completed call
                structured_data = await self.conversation_service.process_completed_call(
                    call_id, transcript, metadata
                )
                
                # Update call record
                supabase.table("calls").update({
                    "status": "completed",
                    "transcript": transcript,
                    "structured_data": structured_data,
                    "updated_at": datetime.now().isoformat()
                }).eq("id", call_id).execute()
                
                logger.info(f"Call {call_id} completed successfully")
                
            elif status == "failed":
                # Process failed call
                error_message = call_status.get("error", "Unknown error")
                
                supabase.table("calls").update({
                    "status": "failed",
                    "transcript": f"Call failed: {error_message}"
                }).eq("id", call_id).execute()
                
                logger.warning(f"Call {call_id} failed: {error_message}")
                
            else:
                # Update transcript for in-progress calls
                supabase.table("calls").update({
                    "transcript": transcript
                }).eq("id", call_id).execute()
                
        except Exception as e:
            logger.error(f"Error processing call status update: {e}")
    
    async def _handle_polling_timeout(self, call_id: str):
        """Handle polling timeout."""
        try:
            supabase = get_supabase_client()
            
            supabase.table("calls").update({
                "status": "failed",
                "transcript": "Call polling timeout - no response from Retell AI"
            }).eq("id", call_id).execute()
            
            logger.warning(f"Call {call_id} timed out during polling")
            
        except Exception as e:
            logger.error(f"Error handling polling timeout: {e}")

# Global instance
call_polling_service = CallPollingService()
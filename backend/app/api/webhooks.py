from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import hashlib
import hmac
import json

from app.core.database import get_db
from app.models.call import CallRecord
from app.schemas.webhook import (
    RetellConversationWebhook,
    RetellCallEndedWebhook,
    RetellCallStartedWebhook
)
from app.services.call_service import CallService
from app.services.conversation_service import ConversationService
from app.config import settings

router = APIRouter()


def verify_retell_signature(
    payload: bytes,
    signature: str,
    secret: str
) -> bool:
    """Verify Retell AI webhook signature"""
    if not signature:
        return False
    
    try:
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Remove 'sha256=' prefix if present
        if signature.startswith('sha256='):
            signature = signature[7:]
            
        return hmac.compare_digest(expected_signature, signature)
    except Exception:
        return False


async def verify_webhook_signature(
    request: Request,
    x_retell_signature: Optional[str] = Header(None)
) -> bytes:
    """Dependency to verify webhook signature"""
    payload = await request.body()
    
    # Skip signature verification in development
    if settings.DEBUG:
        return payload
    
    if not x_retell_signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing signature header"
        )
    
    if not verify_retell_signature(
        payload,
        x_retell_signature,
        settings.RETELL_WEBHOOK_SECRET
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )
    
    return payload


@router.post("/retell/call-started")
async def handle_call_started(
    payload: RetellCallStartedWebhook,
    db: AsyncSession = Depends(get_db),
    verified_payload: bytes = Depends(verify_webhook_signature)
):
    """Handle call started webhook from Retell AI"""
    try:
        # Find the call record by Retell call ID
        result = await db.execute(
            select(CallRecord).where(CallRecord.retell_call_id == payload.call_id)
        )
        call = result.scalar_one_or_none()
        
        if not call:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Call record not found"
            )
        
        # Update call status and start time
        call.status = "in_progress"
        call.start_time = payload.timestamp
        
        await db.commit()
        await db.refresh(call)
        
        # Notify frontend via Socket.IO
        from app.main import sio
        await sio.emit(
            "call_status_update",
            {
                "call_id": call.id,
                "status": "in_progress",
                "message": "Call started successfully",
                "timestamp": payload.timestamp.isoformat()
            },
            room=f"call_{call.id}"
        )
        
        return {"status": "success", "message": "Call started event processed"}
        
    except Exception as e:
        print(f"Error processing call started webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing webhook"
        )


@router.post("/retell/conversation")
async def handle_conversation_update(
    payload: RetellConversationWebhook,
    db: AsyncSession = Depends(get_db),
    verified_payload: bytes = Depends(verify_webhook_signature)
):
    """Handle real-time conversation updates from Retell AI"""
    try:
        conversation_service = ConversationService(db)
        await conversation_service.process_conversation_update(payload)
        
        return {"status": "success", "message": "Conversation update processed"}
        
    except Exception as e:
        print(f"Error processing conversation webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing conversation update"
        )


@router.post("/retell/call-ended")
async def handle_call_ended(
    payload: RetellCallEndedWebhook,
    db: AsyncSession = Depends(get_db),
    verified_payload: bytes = Depends(verify_webhook_signature)
):
    """Handle call completion webhook from Retell AI"""
    try:
        call_service = CallService(db)
        await call_service.process_call_completion(payload)
        
        return {"status": "success", "message": "Call ended event processed"}
        
    except Exception as e:
        print(f"Error processing call ended webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing call completion"
        )


@router.post("/retell/call-analysis")
async def handle_call_analysis(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    verified_payload: bytes = Depends(verify_webhook_signature)
):
    """Handle call analysis webhook from Retell AI (if available)"""
    try:
        # This would handle any additional analysis data from Retell AI
        call_id = payload.get("call_id")
        analysis_data = payload.get("analysis", {})
        
        if not call_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing call_id in payload"
            )
        
        # Find call record
        result = await db.execute(
            select(CallRecord).where(CallRecord.retell_call_id == call_id)
        )
        call = result.scalar_one_or_none()
        
        if call:
            # Update conversation metadata with analysis
            if not call.conversation_metadata:
                call.conversation_metadata = {}
            
            call.conversation_metadata.update({
                "retell_analysis": analysis_data,
                "analysis_timestamp": payload.get("timestamp")
            })
            
            await db.commit()
        
        return {"status": "success", "message": "Call analysis processed"}
        
    except Exception as e:
        print(f"Error processing call analysis webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing call analysis"
        )


@router.get("/health")
async def webhook_health_check():
    """Health check endpoint for webhook service"""
    return {"status": "healthy", "service": "webhook-handler"}

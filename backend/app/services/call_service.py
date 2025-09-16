from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from app.models.call import CallRecord, ConversationTurn
from app.models.agent import AgentConfiguration
from app.schemas.call import (
    CallInitiateRequest,
    CallResponse,
    CallListResponse,
    CallStatus
)
from app.schemas.webhook import RetellCallEndedWebhook
from app.core.retell_client import RetellClient
from app.services.nlp_service import NLPService
from app.config import settings


class CallService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.retell_client = RetellClient(
            api_key=settings.RETELL_API_KEY,
            base_url=settings.RETELL_BASE_URL
        )
        self.nlp_service = NLPService()

    async def initiate_call(self, call_request: CallInitiateRequest) -> CallResponse:
        """Initiate a new voice call with the driver"""
        # Get agent configuration
        result = await self.db.execute(
            select(AgentConfiguration).where(
                and_(
                    AgentConfiguration.id == call_request.agent_config_id,
                    AgentConfiguration.is_active == True,
                    AgentConfiguration.is_deployed == True
                )
            )
        )
        agent_config = result.scalar_one_or_none()
        
        if not agent_config or not agent_config.retell_agent_id:
            raise ValueError("Agent configuration not found or not deployed")
        
        # Create call record
        call_record = CallRecord(
            driver_name=call_request.driver_name,
            phone_number=call_request.phone_number,
            load_number=call_request.load_number,
            agent_config_id=call_request.agent_config_id,
            status=CallStatus.INITIATED
        )
        
        self.db.add(call_record)
        await self.db.commit()
        await self.db.refresh(call_record)
        
        try:
            # Initiate call with Retell AI
            call_metadata = {
                "call_record_id": call_record.id,
                "driver_name": call_request.driver_name,
                "load_number": call_request.load_number,
                "scenario_type": agent_config.scenario_type
            }
            
            retell_response = await self.retell_client.create_call(
                phone_number=call_request.phone_number,
                agent_id=agent_config.retell_agent_id,
                metadata=call_metadata
            )
            
            # Update call record with Retell call ID
            call_record.retell_call_id = retell_response.get("call_id")
            call_record.status = CallStatus.INITIATED
            
            await self.db.commit()
            await self.db.refresh(call_record)
            
            # Notify frontend via Socket.IO
            from app.main import sio
            await sio.emit(
                "call_initiated",
                {
                    "call_id": call_record.id,
                    "driver_name": call_request.driver_name,
                    "phone_number": call_request.phone_number,
                    "load_number": call_request.load_number,
                    "status": "initiated"
                },
                room=f"call_{call_record.id}"
            )
            
            return CallResponse.from_orm(call_record)
            
        except Exception as e:
            # Update call record with error
            call_record.status = CallStatus.FAILED
            call_record.error_message = str(e)
            await self.db.commit()
            
            raise ValueError(f"Failed to initiate call: {str(e)}")

    async def list_calls(
        self,
        page: int = 1,
        per_page: int = 10,
        status_filter: Optional[str] = None,
        driver_name: Optional[str] = None,
        load_number: Optional[str] = None
    ) -> CallListResponse:
        """List calls with pagination and filtering"""
        query = select(CallRecord)
        
        # Apply filters
        filters = []
        if status_filter:
            filters.append(CallRecord.status == status_filter)
        if driver_name:
            filters.append(CallRecord.driver_name.ilike(f"%{driver_name}%"))
        if load_number:
            filters.append(CallRecord.load_number.ilike(f"%{load_number}%"))
        
        if filters:
            query = query.where(and_(*filters))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page).order_by(desc(CallRecord.created_at))
        
        result = await self.db.execute(query)
        calls = result.scalars().all()
        
        return CallListResponse(
            calls=[CallResponse.from_orm(call) for call in calls],
            total=total,
            page=page,
            per_page=per_page,
            has_next=offset + per_page < total,
            has_prev=page > 1
        )

    async def cancel_call(self, call_id: int) -> CallResponse:
        """Cancel an active call"""
        result = await self.db.execute(
            select(CallRecord).where(CallRecord.id == call_id)
        )
        call = result.scalar_one_or_none()
        
        if not call:
            raise ValueError("Call not found")
        
        if call.status not in [CallStatus.INITIATED, CallStatus.IN_PROGRESS]:
            raise ValueError("Call cannot be cancelled in current status")
        
        try:
            # End call in Retell AI if it has a Retell call ID
            if call.retell_call_id:
                await self.retell_client.end_call(call.retell_call_id)
            
            # Update call status
            call.status = CallStatus.CANCELLED
            call.end_time = datetime.utcnow()
            
            if call.start_time:
                call.duration = int((call.end_time - call.start_time).total_seconds())
            
            await self.db.commit()
            await self.db.refresh(call)
            
            # Notify frontend
            from app.main import sio
            await sio.emit(
                "call_status_update",
                {
                    "call_id": call.id,
                    "status": "cancelled",
                    "message": "Call cancelled by user"
                },
                room=f"call_{call.id}"
            )
            
            return CallResponse.from_orm(call)
            
        except Exception as e:
            raise ValueError(f"Failed to cancel call: {str(e)}")

    async def retry_call(self, call_id: int) -> CallResponse:
        """Retry a failed call"""
        result = await self.db.execute(
            select(CallRecord).where(CallRecord.id == call_id)
        )
        call = result.scalar_one_or_none()
        
        if not call:
            raise ValueError("Call not found")
        
        if call.status != CallStatus.FAILED:
            raise ValueError("Only failed calls can be retried")
        
        # Check retry limit
        if call.retry_count >= 3:
            raise ValueError("Maximum retry attempts exceeded")
        
        # Get agent configuration
        result = await self.db.execute(
            select(AgentConfiguration).where(AgentConfiguration.id == call.agent_config_id)
        )
        agent_config = result.scalar_one_or_none()
        
        if not agent_config or not agent_config.retell_agent_id:
            raise ValueError("Agent configuration not available")
        
        try:
            # Increment retry count
            call.retry_count += 1
            call.status = CallStatus.INITIATED
            call.error_message = None
            call.retell_call_id = None
            
            # Retry call with Retell AI
            call_metadata = {
                "call_record_id": call.id,
                "driver_name": call.driver_name,
                "load_number": call.load_number,
                "scenario_type": agent_config.scenario_type,
                "retry_attempt": call.retry_count
            }
            
            retell_response = await self.retell_client.create_call(
                phone_number=call.phone_number,
                agent_id=agent_config.retell_agent_id,
                metadata=call_metadata
            )
            
            call.retell_call_id = retell_response.get("call_id")
            
            await self.db.commit()
            await self.db.refresh(call)
            
            return CallResponse.from_orm(call)
            
        except Exception as e:
            call.status = CallStatus.FAILED
            call.error_message = f"Retry failed: {str(e)}"
            await self.db.commit()
            
            raise ValueError(f"Failed to retry call: {str(e)}")

    async def process_call_completion(self, payload: RetellCallEndedWebhook) -> None:
        """Process call completion webhook from Retell AI"""
        # Find call record
        result = await self.db.execute(
            select(CallRecord).where(CallRecord.retell_call_id == payload.call_id)
        )
        call = result.scalar_one_or_none()
        
        if not call:
            print(f"Call record not found for Retell call ID: {payload.call_id}")
            return
        
        try:
            # Update call record
            call.status = CallStatus.COMPLETED if payload.end_reason == "completed" else CallStatus.FAILED
            call.end_time = payload.end_time
            call.duration = payload.duration
            call.raw_transcript = payload.transcript
            call.conversation_quality_score = payload.call_quality_score
            
            if payload.error_message:
                call.error_message = payload.error_message
            
            # Process conversation turns if available
            if payload.conversation_turns:
                await self._process_conversation_turns(call.id, payload.conversation_turns)
            
            # Extract structured data from transcript
            if call.raw_transcript:
                agent_config = await self._get_agent_config(call.agent_config_id)
                if agent_config:
                    structured_data = await self.nlp_service.extract_structured_data(
                        call.raw_transcript,
                        agent_config.scenario_type
                    )
                    call.structured_data = structured_data
                    call.extraction_confidence = structured_data.get("confidence_score", 0.0)
                    
                    # Set call outcome based on extracted data
                    call.call_outcome = structured_data.get("call_outcome")
            
            await self.db.commit()
            await self.db.refresh(call)
            
            # Notify frontend
            from app.main import sio
            await sio.emit(
                "call_completed",
                {
                    "call_id": call.id,
                    "status": call.status,
                    "duration": call.duration,
                    "call_outcome": call.call_outcome,
                    "structured_data": call.structured_data
                },
                room=f"call_{call.id}"
            )
            
        except Exception as e:
            print(f"Error processing call completion: {e}")
            call.status = CallStatus.FAILED
            call.error_message = f"Post-processing failed: {str(e)}"
            await self.db.commit()

    async def get_analytics_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get call analytics summary for the specified number of days"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total calls
        total_result = await self.db.execute(
            select(func.count(CallRecord.id))
            .where(CallRecord.created_at >= start_date)
        )
        total_calls = total_result.scalar()
        
        # Completed calls
        completed_result = await self.db.execute(
            select(func.count(CallRecord.id))
            .where(
                and_(
                    CallRecord.created_at >= start_date,
                    CallRecord.status == CallStatus.COMPLETED
                )
            )
        )
        completed_calls = completed_result.scalar()
        
        # Failed calls
        failed_result = await self.db.execute(
            select(func.count(CallRecord.id))
            .where(
                and_(
                    CallRecord.created_at >= start_date,
                    CallRecord.status == CallStatus.FAILED
                )
            )
        )
        failed_calls = failed_result.scalar()
        
        # Average duration
        avg_duration_result = await self.db.execute(
            select(func.avg(CallRecord.duration))
            .where(
                and_(
                    CallRecord.created_at >= start_date,
                    CallRecord.duration.isnot(None)
                )
            )
        )
        avg_duration = avg_duration_result.scalar() or 0
        
        # Success rate
        success_rate = (completed_calls / total_calls * 100) if total_calls > 0 else 0
        
        # Call outcomes distribution
        outcomes_result = await self.db.execute(
            select(CallRecord.call_outcome, func.count(CallRecord.id))
            .where(
                and_(
                    CallRecord.created_at >= start_date,
                    CallRecord.call_outcome.isnot(None)
                )
            )
            .group_by(CallRecord.call_outcome)
        )
        outcomes = dict(outcomes_result.fetchall())
        
        return {
            "period_days": days,
            "total_calls": total_calls,
            "completed_calls": completed_calls,
            "failed_calls": failed_calls,
            "success_rate": round(success_rate, 2),
            "average_duration_seconds": round(avg_duration, 2),
            "call_outcomes": outcomes,
            "generated_at": datetime.utcnow().isoformat()
        }

    async def _get_agent_config(self, config_id: int) -> Optional[AgentConfiguration]:
        """Get agent configuration by ID"""
        result = await self.db.execute(
            select(AgentConfiguration).where(AgentConfiguration.id == config_id)
        )
        return result.scalar_one_or_none()

    async def _process_conversation_turns(
        self,
        call_id: int,
        turns: List[Dict[str, Any]]
    ) -> None:
        """Process and store conversation turns"""
        for i, turn_data in enumerate(turns):
            turn = ConversationTurn(
                call_id=call_id,
                turn_number=i + 1,
                speaker="agent" if turn_data.get("speaker") == "agent" else "driver",
                message=turn_data.get("message", ""),
                confidence_score=turn_data.get("confidence"),
                intent_detected=turn_data.get("intent"),
                entities_extracted=turn_data.get("entities"),
                emergency_trigger_detected=turn_data.get("emergency_detected", False),
                emergency_keywords=turn_data.get("emergency_keywords")
            )
            
            self.db.add(turn)
        
        await self.db.commit()

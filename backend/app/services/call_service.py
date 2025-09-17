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
    CallStatus,
    CallType
)
from app.schemas.webhook import RetellCallEndedWebhook
from retell import Retell
from app.services.nlp_service import NLPService
from app.config import settings


class CallService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.retell_client = Retell(api_key=settings.RETELL_API_KEY)
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
            phone_number=call_request.phone_number or "",  # Handle None phone number for web calls
            load_number=call_request.load_number,
            agent_config_id=call_request.agent_config_id,
            status=CallStatus.INITIATED,
            call_type=call_request.call_type.value
        )
        
        self.db.add(call_record)
        await self.db.commit()
        await self.db.refresh(call_record)
        
        try:
            # Initiate call with Retell AI
            call_metadata = {
                "call_record_id": str(call_record.id),  # Convert to string for Retell API
                "driver_name": call_request.driver_name,
                "load_number": call_request.load_number,
                "scenario_type": agent_config.scenario_type
            }
            
            if settings.RETELL_MOCK_MODE:
                # Mock call creation for development/testing
                import uuid
                mock_retell_call_id = f"retell_call_{uuid.uuid4().hex[:8]}"
                call_record.retell_call_id = mock_retell_call_id
                call_record.status = CallStatus.INITIATED
                print(f"🧪 Mock call created: {mock_retell_call_id}")
                
                # Start background task to simulate call progression
                import asyncio
                from app.main import sio
                asyncio.create_task(self._simple_mock_simulation(call_record.id, sio))
            else:
                # Real Retell AI call creation using SDK
                try:
                    if call_request.call_type == CallType.WEB_CALL:
                        # Create web call
                        retell_response = self.retell_client.call.create_web_call(
                            agent_id=agent_config.retell_agent_id,
                            retell_llm_dynamic_variables=call_metadata
                        )
                        call_record.retell_call_id = retell_response.call_id
                        call_record.status = CallStatus.INITIATED
                        
                        # Store the access token for web call URL
                        if not call_record.conversation_metadata:
                            call_record.conversation_metadata = {}
                        call_record.conversation_metadata['access_token'] = retell_response.access_token
                        # Retell webcalls use a custom frontend implementation
                        # The URL should point to your own webcall page with the access token
                        call_record.conversation_metadata['web_call_url'] = f"http://localhost:3000/webcall/{retell_response.access_token}"
                        
                        print(f"🌐 Web call created: {call_record.retell_call_id}")
                        print(f"🔗 Web Call URL: {call_record.conversation_metadata['web_call_url']}")
                        
                    else:  # PHONE_CALL
                        # Create phone call
                        # Remove + prefix from phone numbers for Retell API
                        from_number = settings.RETELL_PHONE_NUMBER.lstrip('+')
                        to_number = (call_request.phone_number or "").lstrip('+')
                        
                        if not to_number:
                            raise ValueError("Phone number is required for phone calls")
                        
                        retell_response = self.retell_client.call.create_phone_call(
                            from_number=from_number,
                            to_number=to_number,
                            override_agent_id=agent_config.retell_agent_id,
                            retell_llm_dynamic_variables=call_metadata
                        )
                        call_record.retell_call_id = retell_response.call_id
                        call_record.status = CallStatus.INITIATED
                        
                        print(f"📞 Phone call created: {call_record.retell_call_id}")
                        print(f"📱 From: {from_number} → To: {to_number}")
                    
                    # Start background task to poll call status (for localhost development)
                    import asyncio
                    asyncio.create_task(self._poll_call_status(call_record.id, call_record.retell_call_id))
                    
                except Exception as e:
                    print(f"❌ Retell API call failed: {e}")
                    raise
            
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
            # End call in Retell AI if not in mock mode
            if call.retell_call_id:
                if settings.RETELL_MOCK_MODE:
                    print(f"🧪 Mock: Ending Retell call {call.retell_call_id}")
                else:
                    try:
                        # Use SDK to end the call
                        self.retell_client.call.end_call(call_id=call.retell_call_id)
                        print(f"📞 Real Retell call ended: {call.retell_call_id}")
                    except Exception as e:
                        print(f"❌ Failed to end Retell call: {e}")
                        # Continue with local cancellation even if Retell fails
            
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


    async def _simple_mock_simulation(self, call_id: int, sio):
        """Intelligent mock call simulation that generates realistic results based on agent configuration"""
        import asyncio
        import random
        from datetime import datetime, timezone
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal
        import json
        
        try:
            print(f"🧪 Starting intelligent mock simulation for call {call_id}")
            
            # Get call details and agent configuration
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    text("""SELECT c.driver_name, c.load_number, c.phone_number, 
                                   a.scenario_type, a.name, a.prompts 
                            FROM call_records c 
                            JOIN agent_configurations a ON c.agent_config_id = a.id 
                            WHERE c.id = :call_id"""),
                    {"call_id": call_id}
                )
                row = result.fetchone()
                if not row:
                    raise Exception("Call or agent configuration not found")
                    
                driver_name, load_number, phone_number, scenario_type, agent_name, prompts = row
                prompts = json.loads(prompts) if isinstance(prompts, str) else prompts
            
            # Wait and update to in_progress
            await asyncio.sleep(8)
            async with AsyncSessionLocal() as db:
                await db.execute(
                    text("UPDATE call_records SET status = 'in_progress', start_time = :start_time WHERE id = :call_id"),
                    {"start_time": datetime.now(timezone.utc), "call_id": call_id}
                )
                await db.commit()
                print(f"🧪 Call {call_id} set to in_progress")
            
            # Generate realistic transcript and structured data based on scenario
            transcript_parts, structured_data, call_outcome = self._generate_scenario_content(
                scenario_type, driver_name, load_number, prompts
            )
            
            full_transcript = ""
            for i, part in enumerate(transcript_parts):
                await asyncio.sleep(random.uniform(3, 7))  # Variable timing for realism
                full_transcript += part + "\n"
                
                # Update transcript progressively
                async with AsyncSessionLocal() as db:
                    await db.execute(
                        text("UPDATE call_records SET raw_transcript = :transcript WHERE id = :call_id"),
                        {"transcript": full_transcript, "call_id": call_id}
                    )
                    await db.commit()
                    print(f"🧪 Updated transcript for call {call_id}, part {i+1}/{len(transcript_parts)}")
            
            # Complete the call
            await asyncio.sleep(3)
            end_time = datetime.now(timezone.utc)
            
            async with AsyncSessionLocal() as db:
                # Get start time for duration calculation
                result = await db.execute(
                    text("SELECT start_time FROM call_records WHERE id = :call_id"),
                    {"call_id": call_id}
                )
                row = result.fetchone()
                start_time = row[0] if row else end_time
                duration = int((end_time - start_time).total_seconds())
                
                # Complete the call with scenario-appropriate data
                await db.execute(
                    text("""UPDATE call_records SET 
                           status = 'completed',
                           end_time = :end_time,
                           duration = :duration,
                           call_outcome = :call_outcome,
                           structured_data = :structured_data,
                           extraction_confidence = :confidence
                           WHERE id = :call_id"""),
                    {
                        "end_time": end_time,
                        "duration": duration,
                        "call_outcome": call_outcome,
                        "structured_data": json.dumps(structured_data),
                        "confidence": random.uniform(0.85, 0.98),  # High confidence for mock
                        "call_id": call_id
                    }
                )
                await db.commit()
                print(f"🧪 Call {call_id} completed successfully with {duration} seconds duration")
                print(f"🎯 Scenario: {scenario_type}, Outcome: {call_outcome}")
                
        except Exception as e:
            print(f"❌ Mock simulation error for call {call_id}: {e}")
            import traceback
            traceback.print_exc()
            
            # Mark as failed
            try:
                async with AsyncSessionLocal() as db:
                    await db.execute(
                        text("UPDATE call_records SET status = 'failed', error_message = :error WHERE id = :call_id"),
                        {"error": str(e), "call_id": call_id}
                    )
                    await db.commit()
            except Exception as inner_e:
                print(f"❌ Failed to mark call as failed: {inner_e}")
    
    def _generate_scenario_content(self, scenario_type: str, driver_name: str, load_number: str, prompts: dict):
        """Generate realistic transcript and structured data based on scenario type"""
        import random
        from datetime import datetime, timedelta
        
        # Get current time for realistic timestamps
        now = datetime.now()
        
        if scenario_type == "check_in":
            return self._generate_checkin_scenario(driver_name, load_number, now)
        elif scenario_type == "emergency":
            return self._generate_emergency_scenario(driver_name, load_number, now)
        else:
            # Default to check_in if scenario type is unknown
            return self._generate_checkin_scenario(driver_name, load_number, now)
    
    def _generate_checkin_scenario(self, driver_name: str, load_number: str, now: datetime):
        """Generate check-in scenario content"""
        import random
        
        # Randomize scenario outcome
        scenarios = [
            "on_time_delivery",
            "delayed_traffic", 
            "arrived_early",
            "minor_delay"
        ]
        
        scenario = random.choice(scenarios)
        
        if scenario == "on_time_delivery":
            eta_minutes = random.randint(30, 90)
            location = random.choice([
                "I-95 near Exit 42", "Highway 287, Mile Marker 23", "Route 80 approaching Exit 15",
                "I-75 South, just passed Exit 67", "Highway 101, about 15 miles out"
            ])
            
            transcript_parts = [
                f"[{now.strftime('%H:%M:%S')}] Agent: Hi {driver_name}, this is dispatch calling about load {load_number}. How's everything going?",
                f"[{(now + timedelta(seconds=5)).strftime('%H:%M:%S')}] Driver: Hey there! Everything's going great. I'm making good time.",
                f"[{(now + timedelta(seconds=10)).strftime('%H:%M:%S')}] Agent: Excellent! Can you give me your current location and ETA?",
                f"[{(now + timedelta(seconds=15)).strftime('%H:%M:%S')}] Driver: I'm currently on {location}, about {eta_minutes} minutes out from delivery.",
                f"[{(now + timedelta(seconds=20)).strftime('%H:%M:%S')}] Agent: Perfect timing! Any issues with the load or route?",
                f"[{(now + timedelta(seconds=25)).strftime('%H:%M:%S')}] Driver: Nope, load is secure and route has been smooth. No problems at all.",
                f"[{(now + timedelta(seconds=30)).strftime('%H:%M:%S')}] Agent: Great to hear! Remember to get your proof of delivery signed. Drive safe!",
                f"[{(now + timedelta(seconds=35)).strftime('%H:%M:%S')}] Driver: Will do. Thanks for checking in!"
            ]
            
            structured_data = {
                "call_outcome": "In-Transit Update",
                "driver_status": "Driving",
                "current_location": location,
                "eta": f"{eta_minutes} minutes",
                "delay_reason": None,
                "unloading_status": None,
                "pod_reminder_acknowledged": True,
                "load_secure": True,
                "route_issues": None
            }
            
            return transcript_parts, structured_data, "In-Transit Update"
            
        elif scenario == "arrived_early":
            transcript_parts = [
                f"[{now.strftime('%H:%M:%S')}] Agent: Hi {driver_name}, dispatch calling about load {load_number}. What's your status?",
                f"[{(now + timedelta(seconds=5)).strftime('%H:%M:%S')}] Driver: Hey! Actually, I just arrived at the delivery location about 20 minutes ago.",
                f"[{(now + timedelta(seconds=10)).strftime('%H:%M:%S')}] Agent: That's great! You made excellent time. Are you unloading now?",
                f"[{(now + timedelta(seconds=15)).strftime('%H:%M:%S')}] Driver: Yeah, they're getting me set up at dock 7. Should have everything off in about an hour.",
                f"[{(now + timedelta(seconds=20)).strftime('%H:%M:%S')}] Agent: Perfect! Make sure to get that BOL signed and send us the POD when you're done.",
                f"[{(now + timedelta(seconds=25)).strftime('%H:%M:%S')}] Driver: Absolutely, I'll scan and send it as soon as I'm finished unloading.",
                f"[{(now + timedelta(seconds=30)).strftime('%H:%M:%S')}] Agent: Excellent work {driver_name}. Thanks for the update!"
            ]
            
            structured_data = {
                "call_outcome": "Arrival Confirmation",
                "driver_status": "Unloading",
                "current_location": "Customer facility - Dock 7",
                "eta": "Arrived early",
                "delay_reason": None,
                "unloading_status": "In progress, estimated 1 hour",
                "pod_reminder_acknowledged": True,
                "load_secure": True,
                "route_issues": None
            }
            
            return transcript_parts, structured_data, "Arrival Confirmation"
            
        elif scenario == "delayed_traffic":
            delay_minutes = random.randint(20, 60)
            location = random.choice([
                "I-95 in heavy traffic", "Highway 287 construction zone", "Route 80 accident backup",
                "I-75 South, traffic jam", "Highway 101, road work delays"
            ])
            
            transcript_parts = [
                f"[{now.strftime('%H:%M:%S')}] Agent: Hi {driver_name}, checking in on load {load_number}. How are things going?",
                f"[{(now + timedelta(seconds=5)).strftime('%H:%M:%S')}] Driver: Hey, running into some delays here. Traffic is pretty backed up.",
                f"[{(now + timedelta(seconds=10)).strftime('%H:%M:%S')}] Agent: I see. What's your current location and what's causing the delay?",
                f"[{(now + timedelta(seconds=15)).strftime('%H:%M:%S')}] Driver: I'm stuck on {location}. Looks like I'll be about {delay_minutes} minutes behind schedule.",
                f"[{(now + timedelta(seconds=20)).strftime('%H:%M:%S')}] Agent: No problem, these things happen. Is the load still secure?",
                f"[{(now + timedelta(seconds=25)).strftime('%H:%M:%S')}] Driver: Yeah, everything's fine with the load. Just this traffic situation.",
                f"[{(now + timedelta(seconds=30)).strftime('%H:%M:%S')}] Agent: Understood. I'll update the customer about the delay. Keep us posted if anything changes.",
                f"[{(now + timedelta(seconds=35)).strftime('%H:%M:%S')}] Driver: Will do. Should start moving again soon hopefully."
            ]
            
            structured_data = {
                "call_outcome": "In-Transit Update",
                "driver_status": "Delayed",
                "current_location": location,
                "eta": f"Delayed by {delay_minutes} minutes",
                "delay_reason": "Heavy traffic",
                "unloading_status": None,
                "pod_reminder_acknowledged": False,
                "load_secure": True,
                "route_issues": "Traffic backup"
            }
            
            return transcript_parts, structured_data, "In-Transit Update"
        
        # Default case
        return self._generate_checkin_scenario(driver_name, load_number, now)
    
    def _generate_emergency_scenario(self, driver_name: str, load_number: str, now: datetime):
        """Generate emergency scenario content"""
        import random
        
        emergency_types = ["breakdown", "accident", "medical"]
        emergency_type = random.choice(emergency_types)
        
        if emergency_type == "breakdown":
            location = random.choice([
                "I-95 shoulder near Mile Marker 45", "Highway 287 rest stop", "Route 80 Exit 12 ramp",
                "I-75 South emergency lane", "Highway 101 truck stop"
            ])
            
            transcript_parts = [
                f"[{now.strftime('%H:%M:%S')}] Agent: Hi {driver_name}, this is dispatch. How can I help you?",
                f"[{(now + timedelta(seconds=5)).strftime('%H:%M:%S')}] Driver: Hey, I've got a problem. My truck just broke down and I'm stuck on the side of the road.",
                f"[{(now + timedelta(seconds=10)).strftime('%H:%M:%S')}] Agent: I'm sorry to hear that. Are you in a safe location? What's your exact position?",
                f"[{(now + timedelta(seconds=15)).strftime('%H:%M:%S')}] Driver: Yeah, I'm safely pulled over on {location}. Engine just died on me.",
                f"[{(now + timedelta(seconds=20)).strftime('%H:%M:%S')}] Agent: Is the load secure? Are you injured at all?",
                f"[{(now + timedelta(seconds=25)).strftime('%H:%M:%S')}] Driver: Load is fine, all strapped down properly. I'm okay, just frustrated.",
                f"[{(now + timedelta(seconds=30)).strftime('%H:%M:%S')}] Agent: I understand. I'm going to connect you with our emergency dispatch team right now. Stay on the line.",
                f"[{(now + timedelta(seconds=35)).strftime('%H:%M:%S')}] Driver: Okay, thanks. I'll wait here."
            ]
            
            structured_data = {
                "call_outcome": "Emergency Escalation",
                "emergency_type": "Breakdown",
                "safety_status": "Driver safe, truck disabled",
                "injury_status": "No injuries reported",
                "emergency_location": location,
                "load_secure": True,
                "escalation_status": "Connected to Human Dispatcher"
            }
            
            return transcript_parts, structured_data, "Emergency Escalation"
            
        elif emergency_type == "accident":
            transcript_parts = [
                f"[{now.strftime('%H:%M:%S')}] Agent: Hi {driver_name}, this is dispatch about load {load_number}.",
                f"[{(now + timedelta(seconds=5)).strftime('%H:%M:%S')}] Driver: Thank God you called! I just had an accident. I think I'm okay but the truck is damaged.",
                f"[{(now + timedelta(seconds=10)).strftime('%H:%M:%S')}] Agent: I'm connecting you to emergency services immediately. Are you hurt? Is anyone else involved?",
                f"[{(now + timedelta(seconds=15)).strftime('%H:%M:%S')}] Driver: I'm shaken up but I think I'm okay. It was just me, slid off in the rain.",
                f"[{(now + timedelta(seconds=20)).strftime('%H:%M:%S')}] Agent: Stay calm. What's your exact location? Is the load secure?",
                f"[{(now + timedelta(seconds=25)).strftime('%H:%M:%S')}] Driver: I'm on Highway 95 near Exit 23. The load shifted but the trailer didn't tip.",
                f"[{(now + timedelta(seconds=30)).strftime('%H:%M:%S')}] Agent: Emergency services and our safety team are being dispatched now. Do not move until help arrives.",
                f"[{(now + timedelta(seconds=35)).strftime('%H:%M:%S')}] Driver: Okay, I'll stay put. Thank you."
            ]
            
            structured_data = {
                "call_outcome": "Emergency Escalation",
                "emergency_type": "Accident",
                "safety_status": "Driver conscious, possible minor injuries",
                "injury_status": "Driver reports feeling okay but shaken",
                "emergency_location": "Highway 95 near Exit 23",
                "load_secure": False,
                "escalation_status": "Emergency services dispatched"
            }
            
            return transcript_parts, structured_data, "Emergency Escalation"
        
        # Default emergency case
        return self._generate_emergency_scenario(driver_name, load_number, now)
    
    async def _poll_call_status(self, call_id: int, retell_call_id: str):
        """Poll Retell API for call status updates (for localhost development)"""
        import asyncio
        from datetime import datetime, timezone
        from sqlalchemy import text
        from app.core.database import AsyncSessionLocal
        
        try:
            print(f"🔄 Starting status polling for call {call_id} (Retell: {retell_call_id})")
            
            # Poll every 5 seconds for up to 10 minutes
            max_polls = 120  # 10 minutes
            poll_count = 0
            
            while poll_count < max_polls:
                await asyncio.sleep(5)  # Wait 5 seconds
                poll_count += 1
                
                try:
                    # Get call status from Retell
                    call_info = self.retell_client.call.retrieve(retell_call_id)
                    current_status = call_info.call_status
                    
                    print(f"📊 Poll {poll_count}: Call {retell_call_id} status = {current_status}")
                    
                    # Update database based on status
                    async with AsyncSessionLocal() as db:
                        if current_status == "ongoing":
                            await db.execute(
                                text("UPDATE call_records SET status = 'in_progress', start_time = :start_time WHERE id = :call_id AND status = 'initiated'"),
                                {"start_time": datetime.now(timezone.utc), "call_id": call_id}
                            )
                            await db.commit()
                            print(f"✅ Call {call_id} updated to in_progress")
                            
                            # Notify frontend
                            from app.main import sio
                            await sio.emit("call_status_update", {
                                "call_id": call_id,
                                "status": "in_progress",
                                "message": "Call started"
                            })
                            
                        elif current_status in ["completed", "ended"]:
                            # Call completed - get transcript and analysis
                            transcript = getattr(call_info, 'transcript', None)
                            duration = getattr(call_info, 'duration_ms', 0)
                            
                            await db.execute(
                                text("""UPDATE call_records SET 
                                       status = 'completed',
                                       end_time = :end_time,
                                       duration = :duration,
                                       raw_transcript = :transcript
                                       WHERE id = :call_id"""),
                                {
                                    "end_time": datetime.now(timezone.utc),
                                    "duration": duration // 1000 if duration else 0,  # Convert ms to seconds
                                    "transcript": transcript,
                                    "call_id": call_id
                                }
                            )
                            await db.commit()
                            print(f"✅ Call {call_id} completed successfully")
                            
                            # Notify frontend
                            from app.main import sio
                            await sio.emit("call_status_update", {
                                "call_id": call_id,
                                "status": "completed",
                                "message": "Call completed",
                                "transcript": transcript,
                                "duration": duration // 1000 if duration else 0
                            })
                            
                            break  # Stop polling
                            
                        elif current_status in ["error", "failed"]:
                            await db.execute(
                                text("UPDATE call_records SET status = 'failed', error_message = 'Call failed on Retell' WHERE id = :call_id"),
                                {"call_id": call_id}
                            )
                            await db.commit()
                            print(f"❌ Call {call_id} failed")
                            
                            # Notify frontend
                            from app.main import sio
                            await sio.emit("call_status_update", {
                                "call_id": call_id,
                                "status": "failed",
                                "message": "Call failed"
                            })
                            
                            break  # Stop polling
                            
                except Exception as poll_error:
                    print(f"⚠️ Poll error for call {call_id}: {poll_error}")
                    continue  # Continue polling despite errors
            
            print(f"🔚 Finished polling for call {call_id} after {poll_count} attempts")
            
        except Exception as e:
            print(f"❌ Status polling error for call {call_id}: {e}")
            import traceback
            traceback.print_exc()

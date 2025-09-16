from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List
from datetime import datetime

from app.models.call import CallRecord, ConversationTurn
from app.schemas.webhook import RetellConversationWebhook
from app.services.nlp_service import NLPService


class ConversationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.nlp_service = NLPService()

    async def process_conversation_update(self, payload: RetellConversationWebhook) -> None:
        """Process real-time conversation updates from Retell AI"""
        # Find call record
        result = await self.db.execute(
            select(CallRecord).where(CallRecord.retell_call_id == payload.call_id)
        )
        call = result.scalar_one_or_none()
        
        if not call:
            print(f"Call record not found for Retell call ID: {payload.call_id}")
            return
        
        try:
            # Only process final messages to avoid duplicates
            if not payload.is_final:
                return
            
            # Get current turn count
            turn_count_result = await self.db.execute(
                select(func.count(ConversationTurn.id))
                .where(ConversationTurn.call_id == call.id)
            )
            current_turn_count = turn_count_result.scalar()
            
            # Map Retell's 'user' to 'driver'
            speaker = "driver" if payload.speaker == "user" else "agent"
            
            # Check for emergency triggers
            emergency_detected = False
            emergency_keywords = []
            
            if speaker == "driver":
                emergency_detected = self.nlp_service.detect_emergency_trigger(payload.message)
                if emergency_detected:
                    emergency_keywords = self.nlp_service.extract_emergency_keywords(payload.message)
            
            # Create conversation turn
            turn = ConversationTurn(
                call_id=call.id,
                turn_number=current_turn_count + 1,
                speaker=speaker,
                message=payload.message,
                confidence_score=payload.confidence,
                intent_detected=payload.intent,
                entities_extracted=payload.entities,
                emergency_trigger_detected=emergency_detected,
                emergency_keywords=emergency_keywords
            )
            
            self.db.add(turn)
            await self.db.commit()
            
            # If emergency detected, notify immediately
            if emergency_detected:
                await self._handle_emergency_detection(call, turn, emergency_keywords)
            
            # Send real-time update to frontend
            from app.main import sio
            await sio.emit(
                "conversation_update",
                {
                    "call_id": call.id,
                    "turn_number": turn.turn_number,
                    "speaker": speaker,
                    "message": payload.message,
                    "timestamp": payload.timestamp.isoformat(),
                    "emergency_detected": emergency_detected,
                    "emergency_keywords": emergency_keywords
                },
                room=f"call_{call.id}"
            )
            
            # Update call status if needed
            if call.status == "initiated":
                call.status = "in_progress"
                if not call.start_time:
                    call.start_time = payload.timestamp
                await self.db.commit()
                
                # Notify status change
                await sio.emit(
                    "call_status_update",
                    {
                        "call_id": call.id,
                        "status": "in_progress",
                        "message": "Conversation started"
                    },
                    room=f"call_{call.id}"
                )
            
        except Exception as e:
            print(f"Error processing conversation update: {e}")

    async def _handle_emergency_detection(
        self,
        call: CallRecord,
        turn: ConversationTurn,
        emergency_keywords: List[str]
    ) -> None:
        """Handle emergency detection during conversation"""
        try:
            # Update call record to mark emergency
            if not call.conversation_metadata:
                call.conversation_metadata = {}
            
            call.conversation_metadata.update({
                "emergency_detected": True,
                "emergency_detected_at": turn.timestamp.isoformat(),
                "emergency_turn": turn.turn_number,
                "emergency_keywords": emergency_keywords
            })
            
            await self.db.commit()
            
            # Send emergency alert to frontend
            from app.main import sio
            await sio.emit(
                "emergency_detected",
                {
                    "call_id": call.id,
                    "driver_name": call.driver_name,
                    "load_number": call.load_number,
                    "phone_number": call.phone_number,
                    "emergency_keywords": emergency_keywords,
                    "message": turn.message,
                    "detected_at": turn.timestamp.isoformat()
                },
                room="emergency_alerts"  # Global emergency room
            )
            
            # Also send to specific call room
            await sio.emit(
                "emergency_protocol_activated",
                {
                    "call_id": call.id,
                    "message": "Emergency protocol activated - gathering critical information",
                    "keywords_detected": emergency_keywords
                },
                room=f"call_{call.id}"
            )
            
        except Exception as e:
            print(f"Error handling emergency detection: {e}")

    async def get_conversation_summary(self, call_id: int) -> Dict[str, Any]:
        """Get a summary of the conversation"""
        # Get all turns for the call
        result = await self.db.execute(
            select(ConversationTurn)
            .where(ConversationTurn.call_id == call_id)
            .order_by(ConversationTurn.turn_number)
        )
        turns = result.scalars().all()
        
        if not turns:
            return {"summary": "No conversation data available"}
        
        # Basic statistics
        total_turns = len(turns)
        agent_turns = len([t for t in turns if t.speaker == "agent"])
        driver_turns = len([t for t in turns if t.speaker == "driver"])
        emergency_turns = len([t for t in turns if t.emergency_trigger_detected])
        
        # Average confidence score
        confidence_scores = [t.confidence_score for t in turns if t.confidence_score is not None]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # Detected intents
        intents = [t.intent_detected for t in turns if t.intent_detected]
        unique_intents = list(set(intents))
        
        # Emergency keywords if any
        all_emergency_keywords = []
        for turn in turns:
            if turn.emergency_keywords:
                all_emergency_keywords.extend(turn.emergency_keywords)
        
        # Conversation timeline
        timeline = [
            {
                "turn": turn.turn_number,
                "speaker": turn.speaker,
                "message": turn.message[:100] + "..." if len(turn.message) > 100 else turn.message,
                "timestamp": turn.timestamp.isoformat(),
                "emergency_detected": turn.emergency_trigger_detected
            }
            for turn in turns
        ]
        
        return {
            "call_id": call_id,
            "total_turns": total_turns,
            "agent_turns": agent_turns,
            "driver_turns": driver_turns,
            "emergency_turns": emergency_turns,
            "average_confidence": round(avg_confidence, 2),
            "detected_intents": unique_intents,
            "emergency_keywords": list(set(all_emergency_keywords)),
            "conversation_timeline": timeline,
            "generated_at": datetime.utcnow().isoformat()
        }

    async def analyze_conversation_quality(self, call_id: int) -> Dict[str, Any]:
        """Analyze the quality of the conversation"""
        result = await self.db.execute(
            select(ConversationTurn)
            .where(ConversationTurn.call_id == call_id)
            .order_by(ConversationTurn.turn_number)
        )
        turns = result.scalars().all()
        
        if not turns:
            return {"quality_score": 0, "analysis": "No conversation data available"}
        
        # Quality metrics
        quality_metrics = {
            "total_turns": len(turns),
            "avg_message_length": 0,
            "confidence_distribution": {"high": 0, "medium": 0, "low": 0},
            "conversation_flow_score": 0,
            "emergency_handling_score": 0 if not any(t.emergency_trigger_detected for t in turns) else None
        }
        
        # Calculate average message length
        message_lengths = [len(turn.message) for turn in turns]
        quality_metrics["avg_message_length"] = sum(message_lengths) / len(message_lengths)
        
        # Confidence distribution
        for turn in turns:
            if turn.confidence_score is not None:
                if turn.confidence_score >= 0.8:
                    quality_metrics["confidence_distribution"]["high"] += 1
                elif turn.confidence_score >= 0.6:
                    quality_metrics["confidence_distribution"]["medium"] += 1
                else:
                    quality_metrics["confidence_distribution"]["low"] += 1
        
        # Calculate overall quality score (0-100)
        total_confidence_turns = sum(quality_metrics["confidence_distribution"].values())
        if total_confidence_turns > 0:
            confidence_score = (
                quality_metrics["confidence_distribution"]["high"] * 1.0 +
                quality_metrics["confidence_distribution"]["medium"] * 0.7 +
                quality_metrics["confidence_distribution"]["low"] * 0.3
            ) / total_confidence_turns
        else:
            confidence_score = 0.5
        
        # Flow score based on turn alternation
        flow_score = self._calculate_flow_score(turns)
        
        # Overall quality score
        overall_score = (confidence_score * 0.6 + flow_score * 0.4) * 100
        
        return {
            "call_id": call_id,
            "overall_quality_score": round(overall_score, 2),
            "metrics": quality_metrics,
            "recommendations": self._generate_quality_recommendations(quality_metrics, turns),
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def _calculate_flow_score(self, turns: List[ConversationTurn]) -> float:
        """Calculate conversation flow score based on turn alternation"""
        if len(turns) < 2:
            return 1.0
        
        alternations = 0
        for i in range(1, len(turns)):
            if turns[i].speaker != turns[i-1].speaker:
                alternations += 1
        
        # Good flow should have mostly alternating speakers
        max_alternations = len(turns) - 1
        return alternations / max_alternations if max_alternations > 0 else 0

    def _generate_quality_recommendations(
        self,
        metrics: Dict[str, Any],
        turns: List[ConversationTurn]
    ) -> List[str]:
        """Generate recommendations for improving conversation quality"""
        recommendations = []
        
        # Low confidence recommendations
        low_confidence_ratio = metrics["confidence_distribution"]["low"] / metrics["total_turns"]
        if low_confidence_ratio > 0.3:
            recommendations.append("Consider improving audio quality or reducing background noise")
        
        # Short conversation recommendations
        if metrics["total_turns"] < 6:
            recommendations.append("Conversation may be too short - consider more thorough information gathering")
        
        # Long conversation recommendations
        if metrics["total_turns"] > 30:
            recommendations.append("Conversation may be too long - consider more direct questioning")
        
        # Message length recommendations
        if metrics["avg_message_length"] < 20:
            recommendations.append("Driver responses are very short - may need more probing questions")
        
        # Emergency handling
        emergency_turns = [t for t in turns if t.emergency_trigger_detected]
        if emergency_turns and len(turns) - emergency_turns[0].turn_number > 10:
            recommendations.append("Emergency was detected but conversation continued too long - ensure quick escalation")
        
        return recommendations

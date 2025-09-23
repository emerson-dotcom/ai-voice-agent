"""
Conversation State Management Service
Tracks conversation flow, context, and state transitions for real-time calls.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from app.core.database import supabase_client
from app.models.agent import ScenarioType

logger = logging.getLogger(__name__)


class ConversationState(str, Enum):
    """Conversation state enum for tracking call flow."""
    INITIALIZING = "initializing"
    GREETING = "greeting"
    STATUS_INQUIRY = "status_inquiry"
    GATHERING_INFO = "gathering_info"
    EMERGENCY_DETECTED = "emergency_detected"
    EMERGENCY_HANDLING = "emergency_handling"
    ESCALATING = "escalating"
    CLOSING = "closing"
    COMPLETED = "completed"


class ConversationContext:
    """Manages conversation context and state for a single call."""

    def __init__(self, call_id: str, agent_id: str, scenario_type: ScenarioType):
        self.call_id = call_id
        self.agent_id = agent_id
        self.scenario_type = scenario_type
        self.state = ConversationState.INITIALIZING
        self.context = {}
        self.collected_data = {}
        self.conversation_history = []
        self.emergency_detected = False
        self.turn_count = 0
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_state(self, new_state: ConversationState):
        """Update conversation state and timestamp."""
        self.state = new_state
        self.updated_at = datetime.utcnow()
        logger.info(f"Call {self.call_id} state updated to {new_state}")

    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """Add a message to conversation history."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "turn": self.turn_count,
            "metadata": metadata or {}
        }
        self.conversation_history.append(message)
        self.turn_count += 1

    def update_context(self, key: str, value: Any):
        """Update conversation context."""
        self.context[key] = value
        self.updated_at = datetime.utcnow()

    def update_collected_data(self, data: Dict[str, Any]):
        """Update collected structured data."""
        self.collected_data.update(data)
        self.updated_at = datetime.utcnow()

    def detect_emergency(self, text: str) -> bool:
        """Detect emergency keywords in conversation."""
        emergency_keywords = [
            "emergency", "accident", "crash", "breakdown", "medical",
            "hurt", "injured", "hospital", "police", "fire", "ambulance",
            "help", "stuck", "blowout", "rollover", "collision"
        ]

        text_lower = text.lower()
        for keyword in emergency_keywords:
            if keyword in text_lower:
                self.emergency_detected = True
                self.update_state(ConversationState.EMERGENCY_DETECTED)
                logger.warning(f"Emergency detected in call {self.call_id}: {keyword}")
                return True

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for storage."""
        return {
            "call_id": self.call_id,
            "agent_id": self.agent_id,
            "scenario_type": self.scenario_type.value if isinstance(self.scenario_type, ScenarioType) else str(self.scenario_type),
            "state": self.state.value,
            "context": self.context,
            "collected_data": self.collected_data,
            "conversation_history": self.conversation_history,
            "emergency_detected": self.emergency_detected,
            "turn_count": self.turn_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class ConversationStateService:
    """Service for managing conversation states across all active calls."""

    def __init__(self):
        self.active_conversations: Dict[str, ConversationContext] = {}

    async def initialize_conversation(self, call_id: str, agent_id: str, scenario_type: ScenarioType) -> ConversationContext:
        """Initialize a new conversation context."""
        try:
            context = ConversationContext(call_id, agent_id, scenario_type)
            self.active_conversations[call_id] = context

            # Store initial state in database
            await self._save_conversation_state(context)

            logger.info(f"Initialized conversation for call {call_id} with agent {agent_id}")
            return context

        except Exception as e:
            logger.error(f"Error initializing conversation {call_id}: {str(e)}")
            raise

    def get_conversation(self, call_id: str) -> Optional[ConversationContext]:
        """Get conversation context by call ID."""
        return self.active_conversations.get(call_id)

    async def update_conversation(self, call_id: str, **updates) -> bool:
        """Update conversation context with new data."""
        try:
            context = self.get_conversation(call_id)
            if not context:
                logger.warning(f"Conversation not found for call {call_id}")
                return False

            # Update context fields
            for key, value in updates.items():
                if hasattr(context, key):
                    setattr(context, key, value)
                else:
                    context.update_context(key, value)

            context.updated_at = datetime.utcnow()

            # Save to database
            await self._save_conversation_state(context)

            return True

        except Exception as e:
            logger.error(f"Error updating conversation {call_id}: {str(e)}")
            return False

    async def end_conversation(self, call_id: str) -> bool:
        """End a conversation and clean up."""
        try:
            context = self.get_conversation(call_id)
            if context:
                context.update_state(ConversationState.COMPLETED)
                await self._save_conversation_state(context)

                # Remove from active conversations
                del self.active_conversations[call_id]

                logger.info(f"Ended conversation for call {call_id}")

            return True

        except Exception as e:
            logger.error(f"Error ending conversation {call_id}: {str(e)}")
            return False

    async def _save_conversation_state(self, context: ConversationContext):
        """Save conversation state to database."""
        try:
            # Store in conversation_states table
            state_data = {
                "call_id": context.call_id,
                "agent_id": context.agent_id,
                "state": context.state.value,
                "context_data": context.to_dict(),
                "updated_at": context.updated_at.isoformat()
            }

            # Upsert conversation state
            supabase_client.client.table('conversation_states').upsert(
                state_data,
                on_conflict='call_id'
            ).execute()

        except Exception as e:
            logger.error(f"Error saving conversation state for {context.call_id}: {str(e)}")
            raise

    async def get_conversation_history(self, call_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a call."""
        try:
            response = supabase_client.client.table('conversation_states').select('context_data').eq('call_id', call_id).execute()

            if response.data:
                context_data = response.data[0]['context_data']
                return context_data.get('conversation_history', [])

            return []

        except Exception as e:
            logger.error(f"Error retrieving conversation history for {call_id}: {str(e)}")
            return []


# Global conversation state service instance
conversation_service = ConversationStateService()
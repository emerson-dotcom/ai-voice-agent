from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Optional, Dict, Any
from datetime import datetime

from app.models.agent import AgentConfiguration
from app.schemas.agent import (
    AgentConfigCreate,
    AgentConfigUpdate,
    AgentConfigResponse,
    AgentConfigList
)
from app.core.retell_client import RetellClient
from app.config import settings


class AgentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.retell_client = RetellClient(
            api_key=settings.RETELL_API_KEY,
            base_url=settings.RETELL_BASE_URL
        )

    async def list_configurations(
        self,
        page: int = 1,
        per_page: int = 10,
        scenario_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> AgentConfigList:
        """List agent configurations with pagination and filtering"""
        query = select(AgentConfiguration)
        
        # Apply filters
        filters = []
        if scenario_type:
            filters.append(AgentConfiguration.scenario_type == scenario_type)
        if is_active is not None:
            filters.append(AgentConfiguration.is_active == is_active)
        
        if filters:
            query = query.where(and_(*filters))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page).order_by(AgentConfiguration.created_at.desc())
        
        result = await self.db.execute(query)
        configs = result.scalars().all()
        
        return AgentConfigList(
            configs=[AgentConfigResponse.from_orm(config) for config in configs],
            total=total,
            page=page,
            per_page=per_page,
            has_next=offset + per_page < total,
            has_prev=page > 1
        )

    async def create_configuration(
        self,
        config_data: AgentConfigCreate,
        created_by: int
    ) -> AgentConfigResponse:
        """Create a new agent configuration"""
        # Create database record
        db_config = AgentConfiguration(
            name=config_data.name,
            description=config_data.description,
            scenario_type=config_data.scenario_type,
            prompts=config_data.prompts.dict(),
            voice_settings=config_data.voice_settings.dict(),
            conversation_flow=config_data.conversation_flow.dict(),
            created_by=created_by
        )
        
        self.db.add(db_config)
        await self.db.commit()
        await self.db.refresh(db_config)
        
        return AgentConfigResponse.from_orm(db_config)

    async def update_configuration(
        self,
        config_id: int,
        config_update: AgentConfigUpdate
    ) -> AgentConfigResponse:
        """Update an existing agent configuration"""
        result = await self.db.execute(
            select(AgentConfiguration).where(AgentConfiguration.id == config_id)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            raise ValueError("Agent configuration not found")
        
        # Update fields
        update_data = config_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(config, field):
                if field in ['prompts', 'voice_settings', 'conversation_flow'] and value:
                    setattr(config, field, value.dict() if hasattr(value, 'dict') else value)
                else:
                    setattr(config, field, value)
        
        config.updated_at = datetime.utcnow()
        config.version += 1
        
        await self.db.commit()
        await self.db.refresh(config)
        
        return AgentConfigResponse.from_orm(config)

    async def deploy_configuration(self, config_id: int) -> AgentConfigResponse:
        """Deploy agent configuration to Retell AI"""
        result = await self.db.execute(
            select(AgentConfiguration).where(AgentConfiguration.id == config_id)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            raise ValueError("Agent configuration not found")
        
        # Prepare Retell AI configuration
        retell_config = self._prepare_retell_config(config)
        
        try:
            if config.retell_agent_id:
                # Update existing agent
                response = await self.retell_client.update_agent(
                    config.retell_agent_id,
                    retell_config
                )
            else:
                # Create new agent
                response = await self.retell_client.create_agent(retell_config)
                config.retell_agent_id = response.get("agent_id")
            
            # Update deployment status
            config.retell_config = retell_config
            config.is_deployed = True
            config.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(config)
            
            return AgentConfigResponse.from_orm(config)
            
        except Exception as e:
            raise ValueError(f"Failed to deploy to Retell AI: {str(e)}")

    async def test_configuration(
        self,
        config_id: int,
        test_phone: str
    ) -> Dict[str, Any]:
        """Test agent configuration with a test call"""
        result = await self.db.execute(
            select(AgentConfiguration).where(AgentConfiguration.id == config_id)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            raise ValueError("Agent configuration not found")
        
        if not config.is_deployed or not config.retell_agent_id:
            raise ValueError("Configuration must be deployed before testing")
        
        try:
            # Initiate test call through Retell AI
            test_call_response = await self.retell_client.create_test_call(
                phone_number=test_phone,
                agent_id=config.retell_agent_id,
                metadata={"test_call": True, "config_id": config_id}
            )
            
            return {
                "status": "test_initiated",
                "test_call_id": test_call_response.get("call_id"),
                "message": "Test call initiated successfully"
            }
            
        except Exception as e:
            raise ValueError(f"Failed to initiate test call: {str(e)}")

    def _prepare_retell_config(self, config: AgentConfiguration) -> Dict[str, Any]:
        """Prepare configuration for Retell AI deployment"""
        prompts = config.prompts
        voice_settings = config.voice_settings
        conversation_flow = config.conversation_flow
        
        # Build the system prompt based on scenario type
        if config.scenario_type == "check_in":
            system_prompt = self._build_checkin_prompt(prompts, conversation_flow)
        elif config.scenario_type == "emergency":
            system_prompt = self._build_emergency_prompt(prompts, conversation_flow)
        else:
            system_prompt = prompts.get("opening", "")
        
        return {
            "agent_name": config.name,
            "voice_id": "default",  # Use Retell's default voice
            "language": "en-US",
            "response_engine": {
                "type": "retell-llm",
                "llm_id": "gpt-4",
                "system_prompt": system_prompt,
                "temperature": voice_settings.get("voice_temperature", 0.7),
                "max_tokens": 200
            },
            "voice_configuration": {
                "speed": voice_settings.get("voice_speed", 1.0),
                "responsiveness": voice_settings.get("responsiveness", 1.0),
                "interruption_sensitivity": voice_settings.get("interruption_sensitivity", 0.5),
                "enable_backchannel": voice_settings.get("backchanneling", True),
                "enable_filler_words": voice_settings.get("filler_words", True)
            },
            "webhook_url": f"{settings.RETELL_BASE_URL}/api/v1/webhooks/retell",
            "begin_message": prompts.get("opening", "Hello, this is dispatch calling."),
            "end_call_after_silence_ms": conversation_flow.get("timeout_seconds", 120) * 1000
        }

    def _build_checkin_prompt(self, prompts: Dict, flow: Dict) -> str:
        """Build system prompt for check-in scenario"""
        return f"""
You are a professional dispatch agent calling a truck driver for a status check. Your goal is to collect specific information about their current status and location.

CONVERSATION FLOW:
1. Start with: "{prompts.get('opening', 'Hi, this is dispatch with a check call. Can you give me an update on your status?')}"
2. Based on their response, determine if they are:
   - Still driving (in-transit)
   - Delayed
   - Arrived at destination
   - Currently unloading

3. Collect the following information:
   - Current location
   - ETA if still driving
   - Reason for any delays
   - Unloading status if arrived
   - Confirm they understand POD requirements

EMERGENCY KEYWORDS: {', '.join(flow.get('emergency_keywords', []))}
If you hear any emergency keywords, immediately switch to emergency protocol and ask about safety.

CONVERSATION RULES:
- Keep responses short and professional
- Ask one question at a time
- If driver gives short answers, probe for more details
- Maximum {flow.get('max_turns', 20)} conversation turns
- End call politely if driver becomes uncooperative

Remember: Extract structured data for: call_outcome, driver_status, current_location, eta, delay_reason, unloading_status, pod_reminder_acknowledged
"""

    def _build_emergency_prompt(self, prompts: Dict, flow: Dict) -> str:
        """Build system prompt for emergency scenario"""
        return f"""
You are a professional dispatch agent. This conversation may involve emergency situations that require immediate attention.

EMERGENCY PROTOCOL:
If you detect emergency keywords ({', '.join(flow.get('emergency_keywords', []))}), immediately:
1. Ask "Are you and any passengers safe?"
2. Get exact location
3. Determine emergency type (accident, breakdown, medical, other)
4. Check if load is secure
5. Inform them you're connecting to human dispatcher

NORMAL CONVERSATION:
Start with: "{prompts.get('opening', 'Hi, this is dispatch calling for a status update.')}"

EMERGENCY KEYWORDS: {', '.join(flow.get('emergency_keywords', []))}

CONVERSATION RULES:
- Safety is the top priority
- Get clear, specific information
- Stay calm and professional
- If emergency detected, gather critical info quickly
- Always end emergency calls by confirming human dispatcher connection

Remember: Extract structured data for emergencies: call_outcome, emergency_type, safety_status, injury_status, emergency_location, load_secure, escalation_status
"""

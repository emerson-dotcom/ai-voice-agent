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
from retell import Retell
from app.config import settings


class AgentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.retell_client = Retell(api_key=settings.RETELL_API_KEY)
        self._cached_llm_id = None

    def _get_or_create_llm(self) -> str:
        """Get existing LLM or create a new one dynamically"""
        if self._cached_llm_id:
            return self._cached_llm_id
        
        # Check if a specific LLM ID is configured
        if settings.RETELL_DEFAULT_LLM_ID:
            print(f"🔧 Using configured LLM: {settings.RETELL_DEFAULT_LLM_ID}")
            self._cached_llm_id = settings.RETELL_DEFAULT_LLM_ID
            return self._cached_llm_id
            
        try:
            # First, try to get existing LLMs
            llms = self.retell_client.llm.list()
            
            if llms and len(llms) > 0:
                # Use the first available LLM
                self._cached_llm_id = llms[0].llm_id
                print(f"🔍 Using existing LLM: {self._cached_llm_id}")
                return self._cached_llm_id
            elif settings.RETELL_AUTO_CREATE_LLM:
                # Create a new LLM if none exist and auto-creation is enabled
                print("🆕 Creating new LLM for agent deployment...")
                new_llm = self.retell_client.llm.create(
                    general_prompt="You are a professional dispatcher assistant helping with driver check-ins and logistics communication. Be polite, efficient, and gather the required information systematically.",
                    general_tools=[],
                    model="gpt-4o",
                    begin_message="Hi! I'm calling to check on your delivery status. This will just take a moment."
                )
                self._cached_llm_id = new_llm.llm_id
                print(f"✅ Created new LLM: {self._cached_llm_id}")
                return self._cached_llm_id
            else:
                raise Exception("No LLMs found and auto-creation is disabled")
                
        except Exception as e:
            print(f"❌ Error managing LLM: {e}")
            # Fallback to the current working LLM ID if everything fails
            fallback_llm = "llm_fa38454870dd949bffe1927ab9c1"  # Current working LLM
            print(f"⚠️  Using fallback LLM: {fallback_llm}")
            self._cached_llm_id = fallback_llm
            return fallback_llm

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
            if settings.RETELL_MOCK_MODE:
                # Mock deployment for development/testing
                if config.retell_agent_id:
                    mock_agent_id = config.retell_agent_id
                else:
                    import uuid
                    mock_agent_id = f"agent_{uuid.uuid4().hex[:8]}"
                    config.retell_agent_id = mock_agent_id
                print(f"🧪 Mock agent deployment: {mock_agent_id}")
            else:
                # Real Retell AI agent deployment using SDK
                llm_id = self._get_or_create_llm()
                print(f"🔧 Using LLM ID: {llm_id}")
                
                if config.retell_agent_id:
                    # Try to update existing agent first
                    print(f"🔄 Attempting to update existing agent: {config.retell_agent_id}")
                    try:
                        response = self.retell_client.agent.update(
                            agent_id=config.retell_agent_id,
                            agent_name=retell_config.get("agent_name"),
                            voice_id=retell_config["voice_id"],
                            language=retell_config.get("language", "en-US"),
                            response_engine={
                                "type": "retell-llm",
                                "llm_id": llm_id
                            },
                            webhook_url="http://localhost:8000/api/v1/webhooks/retell/call-ended"
                        )
                        print(f"✅ Agent updated successfully: {response.agent_id}")
                    except Exception as update_error:
                        print(f"❌ Update failed: {update_error}")
                        print(f"🔍 Checking if agent {config.retell_agent_id} still exists...")
                        
                        # Check if agent exists, if not create new one
                        try:
                            existing_agent = self.retell_client.agent.retrieve(config.retell_agent_id)
                            print(f"⚠️ Agent exists but update failed. Keeping existing agent: {existing_agent.agent_id}")
                            # Don't create a new agent, just keep the existing one
                        except Exception:
                            print(f"🆕 Agent no longer exists. Creating new agent...")
                            response = self.retell_client.agent.create(
                                agent_name=retell_config.get("agent_name"),
                                voice_id=retell_config["voice_id"],
                                language=retell_config.get("language", "en-US"),
                                response_engine={
                                    "type": "retell-llm",
                                    "llm_id": llm_id
                                },
                                webhook_url="http://localhost:8000/api/v1/webhooks/retell/call-ended"
                            )
                            config.retell_agent_id = response.agent_id
                            print(f"✅ New agent created: {response.agent_id}")
                else:
                    # No agent ID, create new agent
                    print(f"🆕 No agent ID found. Creating new agent...")
                    response = self.retell_client.agent.create(
                        agent_name=retell_config.get("agent_name"),
                        voice_id=retell_config["voice_id"],
                        language=retell_config.get("language", "en-US"),
                        response_engine={
                            "type": "retell-llm",
                            "llm_id": llm_id
                        },
                        webhook_url="http://localhost:8000/api/v1/webhooks/retell/call-ended"
                    )
                    config.retell_agent_id = response.agent_id
                    print(f"✅ New agent created: {response.agent_id}")
            
            # Configure phone number with the deployed agent
            if not settings.RETELL_MOCK_MODE:
                try:
                    # Remove + prefix if present for phone number update
                    phone_number = settings.RETELL_PHONE_NUMBER.lstrip('+')
                    print(f"📞 Configuring phone number {phone_number} with agent {config.retell_agent_id}...")
                    phone_response = self.retell_client.phone_number.update(
                        phone_number=phone_number,
                        outbound_agent_id=config.retell_agent_id
                    )
                    print(f"✅ Phone number {phone_number} configured with agent {config.retell_agent_id}")
                except Exception as phone_error:
                    print(f"⚠️ Phone configuration failed: {phone_error}")
                    # Don't fail the deployment if phone config fails
            
            # Update deployment status
            config.retell_config = retell_config
            config.is_deployed = True
            config.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(config)
            
            return AgentConfigResponse.from_orm(config)
            
        except Exception as e:
            raise ValueError(f"Failed to deploy to Retell AI: {str(e)}")

    async def pause_configuration(self, config_id: int) -> AgentConfigResponse:
        """Pause/undeploy agent configuration"""
        result = await self.db.execute(
            select(AgentConfiguration).where(AgentConfiguration.id == config_id)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            raise ValueError("Agent configuration not found")
        
        # Remove phone number configuration when pausing
        if not settings.RETELL_MOCK_MODE and config.retell_agent_id:
            try:
                print(f"📞 Removing phone number configuration for paused agent...")
                # Note: We could set outbound_agent_id to None, but Retell might require a valid agent
                # So we'll just log this for now and let the phone number keep its current config
                print(f"⚠️ Phone number {settings.RETELL_PHONE_NUMBER} still configured with agent {config.retell_agent_id}")
                print("💡 Consider manually updating phone number if deploying a different agent")
            except Exception as phone_error:
                print(f"⚠️ Phone cleanup warning: {phone_error}")
        
        # Update deployment status to paused
        config.is_deployed = False
        config.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(config)
        
        return AgentConfigResponse.from_orm(config)

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
            if settings.RETELL_MOCK_MODE:
                # Mock test call for development/testing
                import uuid
                mock_call_id = f"test_call_{uuid.uuid4().hex[:8]}"
                print(f"🧪 Mock test call created: {mock_call_id}")
                
                return {
                    "status": "test_initiated",
                    "test_call_id": mock_call_id,
                    "message": f"Mock test call initiated successfully to {test_phone}",
                    "agent_name": config.name,
                    "scenario_type": config.scenario_type
                }
            else:
                # Real Retell AI test call using SDK
                try:
                    test_call_response = self.retell_client.call.create_phone_call(
                        from_number=settings.RETELL_PHONE_NUMBER,
                        to_number=test_phone,
                        override_agent_id=config.retell_agent_id,
                        retell_llm_dynamic_variables={"test_call": True, "config_id": str(config_id)}
                    )
                    
                    return {
                        "status": "test_initiated",
                        "test_call_id": test_call_response.call_id,
                        "message": f"Real test call initiated successfully to {test_phone}",
                        "agent_name": config.name,
                        "scenario_type": config.scenario_type
                    }
                except Exception as e:
                    print(f"❌ Retell test call failed: {e}")
                    raise
            
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
        
        # Configuration for Retell SDK
        return {
            "agent_name": config.name,
            "voice_id": "cartesia-Adam",  # Use a valid Retell voice ID
            "language": "en-US"
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

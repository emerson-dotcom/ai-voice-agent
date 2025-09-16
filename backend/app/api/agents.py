from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.agent import AgentConfiguration
from app.schemas.agent import (
    AgentConfigCreate,
    AgentConfigUpdate,
    AgentConfigResponse,
    AgentConfigList
)
from app.services.agent_service import AgentService

router = APIRouter()


@router.get("/", response_model=AgentConfigList)
async def list_agent_configs(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    scenario_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all agent configurations with pagination and filtering"""
    agent_service = AgentService(db)
    return await agent_service.list_configurations(
        page=page,
        per_page=per_page,
        scenario_type=scenario_type,
        is_active=is_active
    )


@router.post("/", response_model=AgentConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_agent_config(
    config: AgentConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new agent configuration"""
    agent_service = AgentService(db)
    return await agent_service.create_configuration(config, current_user.id)


@router.get("/{config_id}", response_model=AgentConfigResponse)
async def get_agent_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get agent configuration by ID"""
    result = await db.execute(
        select(AgentConfiguration).where(AgentConfiguration.id == config_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent configuration not found"
        )
    
    return config


@router.put("/{config_id}", response_model=AgentConfigResponse)
async def update_agent_config(
    config_id: int,
    config_update: AgentConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update agent configuration"""
    agent_service = AgentService(db)
    return await agent_service.update_configuration(config_id, config_update)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete agent configuration"""
    result = await db.execute(
        select(AgentConfiguration).where(AgentConfiguration.id == config_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent configuration not found"
        )
    
    await db.delete(config)
    await db.commit()


@router.post("/{config_id}/deploy", response_model=AgentConfigResponse)
async def deploy_agent_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deploy agent configuration to Retell AI"""
    agent_service = AgentService(db)
    return await agent_service.deploy_configuration(config_id)


@router.post("/{config_id}/test", response_model=dict)
async def test_agent_config(
    config_id: int,
    test_phone: str = Query(..., description="Phone number for test call"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test agent configuration with a test call"""
    agent_service = AgentService(db)
    return await agent_service.test_configuration(config_id, test_phone)


@router.get("/{config_id}/calls", response_model=List[dict])
async def get_config_calls(
    config_id: int,
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent calls for this agent configuration"""
    # Verify config exists
    result = await db.execute(
        select(AgentConfiguration).where(AgentConfiguration.id == config_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent configuration not found"
        )
    
    # Get recent calls for this config
    from app.models.call import CallRecord
    result = await db.execute(
        select(CallRecord)
        .where(CallRecord.agent_config_id == config_id)
        .order_by(CallRecord.created_at.desc())
        .limit(limit)
    )
    calls = result.scalars().all()
    
    return [
        {
            "id": call.id,
            "driver_name": call.driver_name,
            "phone_number": call.phone_number,
            "load_number": call.load_number,
            "status": call.status,
            "call_outcome": call.call_outcome,
            "duration": call.duration,
            "created_at": call.created_at
        }
        for call in calls
    ]

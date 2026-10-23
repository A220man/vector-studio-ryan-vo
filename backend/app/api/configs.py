from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json

from app.core.database import get_db
from app.core.models import AgentConfig, User
from app.api.auth import get_current_user_dependency


router = APIRouter(prefix="/configs", tags=["configs"])


class ConfigCreate(BaseModel):
    name: str
    description: str = ""
    config_data: str


class ConfigUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config_data: Optional[str] = None


class ConfigResponse(BaseModel):
    id: int
    name: str
    description: str
    config_data: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ConfigListResponse(BaseModel):
    items: list[ConfigResponse]
    total: int
    page: int
    limit: int


@router.get("", response_model=ConfigListResponse)
async def list_configs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """List agent configurations for the current user."""
    query = db.query(AgentConfig).filter(AgentConfig.user_id == current_user.id)
    
    if search:
        query = query.filter(AgentConfig.name.ilike(f"%{search}%"))
    
    total = query.count()
    configs = query.order_by(AgentConfig.updated_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    return ConfigListResponse(
        items=[ConfigResponse.model_validate(c) for c in configs],
        total=total,
        page=page,
        limit=limit,
    )


@router.post("", response_model=ConfigResponse, status_code=201)
async def create_config(
    data: ConfigCreate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Create a new agent configuration."""
    # Validate JSON
    try:
        json.loads(data.config_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in config_data")
    
    config = AgentConfig(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        config_data=data.config_data,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return ConfigResponse.model_validate(config)


@router.get("/{config_id}", response_model=ConfigResponse)
async def get_config(
    config_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Get a specific agent configuration."""
    config = db.query(AgentConfig).filter(
        AgentConfig.id == config_id,
        AgentConfig.user_id == current_user.id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return ConfigResponse.model_validate(config)


@router.put("/{config_id}", response_model=ConfigResponse)
async def update_config(
    config_id: int,
    data: ConfigUpdate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Update an agent configuration."""
    config = db.query(AgentConfig).filter(
        AgentConfig.id == config_id,
        AgentConfig.user_id == current_user.id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    if data.name is not None:
        config.name = data.name
    if data.description is not None:
        config.description = data.description
    if data.config_data is not None:
        try:
            json.loads(data.config_data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in config_data")
        config.config_data = data.config_data
    
    db.commit()
    db.refresh(config)
    return ConfigResponse.model_validate(config)


@router.delete("/{config_id}", status_code=204)
async def delete_config(
    config_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Delete an agent configuration."""
    config = db.query(AgentConfig).filter(
        AgentConfig.id == config_id,
        AgentConfig.user_id == current_user.id
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    db.delete(config)
    db.commit()
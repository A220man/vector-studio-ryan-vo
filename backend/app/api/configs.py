from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
import json

from app.core.database import get_db
from app.core.models import AgentConfig, User
from app.api.auth import get_current_user_dependency
from app.core.hook_validation import validate_hook_schema

router = APIRouter(prefix="/configs", tags=["configs"])


class ConfigCreate(BaseModel):
    name: str
    description: str = ""
    config_data: str

    @field_validator('config_data')
    @classmethod
    def validate_config_data(cls, v: str) -> str:
        try:
            json.loads(v)
        except json.JSONDecodeError as e:
            raise ValueError(f"config_data must be valid JSON: {e}")
        errors = validate_hook_schema(v)
        if errors:
            raise ValueError("; ".join(errors))
        return v


class ConfigUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config_data: Optional[str] = None

    @field_validator('config_data')
    @classmethod
    def validate_config_data(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                json.loads(v)
            except json.JSONDecodeError as e:
                raise ValueError(f"config_data must be valid JSON: {e}")
            errors = validate_hook_schema(v)
            if errors:
                raise ValueError("; ".join(errors))
        return v


class ConfigResponse(BaseModel):
    id: int
    name: str
    description: str
    config_data: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


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


class HookSchema(BaseModel):
    """Schema definition for an agent hook configuration."""

    name: str
    description: str = ""
    event: str  # e.g., on_start, on_end, on_error, on_success, on_step, on_step_end
    config: dict  # JSON hook configuration

    model_config = ConfigDict(from_attributes=True)

    @field_validator("event")
    @classmethod
    def validate_event(cls, v: str) -> str:
        valid = {
            "on_start",
            "on_end",
            "on_error",
            "on_success",
            "on_step",
            "on_step_end",
        }
        if v not in valid:
            raise ValueError(
                f"Invalid hook event: {v}. Valid events: {', '.join(sorted(valid))}"
            )
        return v

    @field_validator("config")
    @classmethod
    def validate_config_no_crlf(cls, v: dict) -> dict:
        # Check for CRLF in the config JSON string representation
        raw = json.dumps(v, ensure_ascii=False)
        if "\r\n" in raw:
            raise ValueError("Hook config contains CRLF line endings")
        return v


class HookSchemaListResponse(BaseModel):
    items: list[HookSchema]


@router.post("/{config_id}/validate", response_model=dict)
async def validate_hook_config(
    config_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
):
    """Validate a hook schema for compliance.

    Checks CRLF line endings, valid hook event names,
    and reports actionable validation errors.
    """
    config = db.query(AgentConfig).filter(
        AgentConfig.id == config_id,
        AgentConfig.user_id == current_user.id,
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    try:
        schema = json.loads(config.config_data)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400, detail=f"Invalid JSON in config_data: {exc}"
        )

    errors = validate_hook_schema(schema)
    return {
        "config_id": config.id,
        "config_name": config.name,
        "valid": len(errors) == 0,
        "errors": errors,
    }

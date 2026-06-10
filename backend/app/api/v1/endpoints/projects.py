"""
Projects API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
import structlog

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_admin
from app.db.models.user import User
from app.db.models.project import Project
from app.db.models.api_key import APIKey
from app.core.security import generate_api_key, mask_sensitive_data
from app.schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    APIKeyCreate, APIKeyResponse, APIKeyCreateResponse,
    PaginatedResponse
)

logger = structlog.get_logger()
router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = Project(
        name=project_data.name,
        description=project_data.description,
        environment=project_data.environment,
        owner_id=current_user.id,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    logger.info("Project created", project_id=str(project.id), user=current_user.username)
    return project


@router.get("", response_model=PaginatedResponse)
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role in ["admin", "superadmin"]:
        query = select(Project)
        count_q = select(func.count(Project.id))
    else:
        query = select(Project).where(Project.owner_id == current_user.id)
        count_q = select(func.count(Project.id)).where(Project.owner_id == current_user.id)

    total = (await db.execute(count_q)).scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(desc(Project.created_at)).offset(offset).limit(page_size))
    projects = result.scalars().all()

    return {
        "items": [ProjectResponse.model_validate(p) for p in projects],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if current_user.role not in ["admin", "superadmin"] and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    update_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if current_user.role not in ["admin", "superadmin"] and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    for field, value in update_data.model_dump(exclude_none=True).items():
        setattr(project, field, value)
    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if current_user.role not in ["admin", "superadmin"] and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    await db.delete(project)
    await db.commit()
    return {"message": "Project deleted"}


# ===== API Keys =====

@router.post("/{project_id}/api-keys", response_model=APIKeyCreateResponse, status_code=201)
async def create_api_key(
    project_id: str,
    key_data: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if current_user.role not in ["admin", "superadmin"] and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    plain_key, hashed_key = generate_api_key()
    api_key = APIKey(
        name=key_data.name,
        key_prefix=plain_key[:12],
        key_hash=hashed_key,
        user_id=current_user.id,
        project_id=project.id,
        description=key_data.description,
        permissions=key_data.permissions,
        expires_at=key_data.expires_at,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    logger.info("API key created", key_id=str(api_key.id), project=project_id)
    return {**APIKeyResponse.model_validate(api_key).model_dump(), "plain_key": plain_key}


@router.get("/{project_id}/api-keys", response_model=list)
async def list_api_keys(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(APIKey).where(APIKey.project_id == project_id)
    )
    keys = result.scalars().all()
    return [APIKeyResponse.model_validate(k) for k in keys]


@router.delete("/{project_id}/api-keys/{key_id}")
async def revoke_api_key(
    project_id: str,
    key_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.project_id == project_id)
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    key.is_active = False
    await db.commit()
    return {"message": "API key revoked"}

"""
Prompt & Response Logging API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from typing import Optional, List
from datetime import datetime, timezone
import structlog

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_user_or_api_key
from app.db.models.user import User
from app.db.models.prompt_log import PromptLog
from app.db.models.project import Project
from app.schemas import TrackRequest, PromptLogResponse, PaginatedResponse
from app.security.detector import SecurityDetector
from app.monitoring.cost_calculator import CostCalculator

logger = structlog.get_logger()
router = APIRouter(prefix="/logs", tags=["Logs"])

security_detector = SecurityDetector()
cost_calculator = CostCalculator()


@router.post("/track", status_code=201)
async def track_request(
    track_data: TrackRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_api_key),
):
    """Ingest an LLM request/response for monitoring"""
    # Verify project access
    result = await db.execute(
        select(Project).where(Project.id == track_data.project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or access denied")
    # Check access
    if current_user.role not in ["admin", "superadmin"] and project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Calculate cost if not provided
    cost = track_data.cost
    if cost == 0.0 and track_data.total_tokens > 0:
        cost = cost_calculator.calculate(
            model=track_data.model,
            provider=track_data.provider,
            prompt_tokens=track_data.prompt_tokens,
            completion_tokens=track_data.completion_tokens,
        )

    # Run security detection on prompt
    injection_score = 0.0
    toxicity_score = 0.0
    is_flagged = False
    flag_reason = None

    try:
        security_result = await security_detector.analyze(
            prompt=track_data.prompt,
            response=track_data.response,
        )
        injection_score = security_result.get("injection_score", 0.0)
        toxicity_score = security_result.get("toxicity_score", 0.0)
        is_flagged = security_result.get("is_flagged", False)
        flag_reason = security_result.get("flag_reason")
    except Exception as e:
        logger.warning("Security detection failed", error=str(e))

    # Create prompt log
    log = PromptLog(
        project_id=project.id,
        user_id=current_user.id,
        session_id=track_data.session_id,
        system_prompt=track_data.system_prompt,
        user_prompt=track_data.prompt,
        response_text=track_data.response,
        model_name=track_data.model,
        provider=track_data.provider,
        prompt_tokens=track_data.prompt_tokens,
        completion_tokens=track_data.completion_tokens,
        total_tokens=track_data.total_tokens,
        estimated_cost=cost,
        latency_ms=track_data.latency_ms,
        status=track_data.status,
        error_type=track_data.error_type,
        error_message=track_data.error_message,
        injection_score=injection_score,
        toxicity_score=toxicity_score,
        is_flagged=is_flagged,
        flag_reason=flag_reason,
        tags=track_data.tags,
        extra_metadata=track_data.extra_metadata,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)

    logger.info(
        "Request tracked",
        log_id=str(log.id),
        model=track_data.model,
        tokens=track_data.total_tokens,
        cost=cost,
    )

    return {"log_id": str(log.id), "status": "tracked", "flagged": is_flagged}


@router.get("/", response_model=PaginatedResponse)
async def list_logs(
    project_id: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    model_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    is_flagged: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List prompt logs with filtering and pagination"""
    query = select(PromptLog)
    count_query = select(func.count(PromptLog.id))

    # Filter by user's projects unless admin
    if current_user.role not in ["admin", "superadmin"]:
        user_project_ids = select(Project.id).where(Project.owner_id == current_user.id)
        query = query.where(PromptLog.project_id.in_(user_project_ids))
        count_query = count_query.where(PromptLog.project_id.in_(user_project_ids))

    # Apply filters
    if project_id:
        query = query.where(PromptLog.project_id == project_id)
        count_query = count_query.where(PromptLog.project_id == project_id)
    if provider:
        query = query.where(PromptLog.provider == provider)
        count_query = count_query.where(PromptLog.provider == provider)
    if model_name:
        query = query.where(PromptLog.model_name == model_name)
        count_query = count_query.where(PromptLog.model_name == model_name)
    if status:
        query = query.where(PromptLog.status == status)
        count_query = count_query.where(PromptLog.status == status)
    if is_flagged is not None:
        query = query.where(PromptLog.is_flagged == is_flagged)
        count_query = count_query.where(PromptLog.is_flagged == is_flagged)
    if search:
        search_filter = or_(
            PromptLog.user_prompt.ilike(f"%{search}%"),
            PromptLog.response_text.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    if start_date:
        query = query.where(PromptLog.created_at >= start_date)
        count_query = count_query.where(PromptLog.created_at >= start_date)
    if end_date:
        query = query.where(PromptLog.created_at <= end_date)
        count_query = count_query.where(PromptLog.created_at <= end_date)

    # Count total
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(desc(PromptLog.created_at)).offset(offset).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "items": [PromptLogResponse.model_validate(log) for log in logs],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/{log_id}", response_model=PromptLogResponse)
async def get_log(
    log_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific prompt log by ID"""
    result = await db.execute(select(PromptLog).where(PromptLog.id == log_id))
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(status_code=404, detail="Log not found")

    # Verify access
    if current_user.role not in ["admin", "superadmin"]:
        proj_result = await db.execute(
            select(Project).where(
                Project.id == log.project_id,
                Project.owner_id == current_user.id
            )
        )
        if not proj_result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Access denied")

    return log


@router.delete("/{log_id}")
async def delete_log(
    log_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a prompt log"""
    result = await db.execute(select(PromptLog).where(PromptLog.id == log_id))
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(status_code=404, detail="Log not found")

    await db.delete(log)
    await db.commit()
    return {"message": "Log deleted"}

"""
Alerts API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from typing import Optional
from datetime import datetime, timezone, timedelta
import structlog

from app.core.database import get_db
from app.core.deps import get_current_user
from app.db.models.user import User
from app.db.models.security import Alert, UserFeedback, SecurityEvent
from app.db.models.prompt_log import PromptLog
from app.schemas import AlertCreate, AlertResponse, FeedbackCreate, FeedbackResponse, SecurityEventResponse, PaginatedResponse

logger = structlog.get_logger()

# Alerts router
alerts_router = APIRouter(prefix="/alerts", tags=["Alerts"])

@alerts_router.post("", response_model=AlertResponse, status_code=201)
async def create_alert(
    alert_data: AlertCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = Alert(
        project_id=alert_data.project_id,
        alert_type=alert_data.alert_type,
        severity=alert_data.severity,
        title=alert_data.title,
        message=alert_data.message,
        threshold_value=alert_data.threshold_value,
        notification_channels=alert_data.notification_channels,
        email_recipients=alert_data.email_recipients,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@alerts_router.get("", response_model=PaginatedResponse)
async def list_alerts(
    project_id: Optional[str] = Query(None),
    is_triggered: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Alert)
    count_q = select(func.count(Alert.id))
    
    if project_id:
        query = query.where(Alert.project_id == project_id)
        count_q = count_q.where(Alert.project_id == project_id)
    if is_triggered is not None:
        query = query.where(Alert.is_triggered == is_triggered)
        count_q = count_q.where(Alert.is_triggered == is_triggered)
    
    total = (await db.execute(count_q)).scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(desc(Alert.created_at)).offset(offset).limit(page_size))
    
    return {
        "items": [AlertResponse.model_validate(a) for a in result.scalars().all()],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@alerts_router.put("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_acknowledged = True
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Alert acknowledged"}


@alerts_router.delete("/{alert_id}")
async def delete_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.delete(alert)
    await db.commit()
    return {"message": "Alert deleted"}


# Feedback router
feedback_router = APIRouter(prefix="/feedback", tags=["Feedback"])

@feedback_router.post("", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    feedback_data: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify log exists
    result = await db.execute(select(PromptLog).where(PromptLog.id == feedback_data.prompt_log_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Log not found")
    
    feedback = UserFeedback(
        prompt_log_id=feedback_data.prompt_log_id,
        user_id=current_user.id,
        rating=feedback_data.rating,
        comment=feedback_data.comment,
        thumbs_up=feedback_data.thumbs_up,
        categories=feedback_data.categories,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return feedback


@feedback_router.get("/stats")
async def get_feedback_stats(
    project_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(
            func.avg(UserFeedback.rating).label("avg_rating"),
            func.count(UserFeedback.id).label("total"),
            func.count(UserFeedback.id).filter(UserFeedback.thumbs_up == True).label("thumbs_up"),
        )
    )
    row = result.fetchone()
    
    return {
        "avg_rating": round(float(row.avg_rating or 0), 2),
        "total_feedback": int(row.total or 0),
        "thumbs_up_count": int(row.thumbs_up or 0),
        "approval_rate": round((row.thumbs_up or 0) / (row.total or 1), 2),
    }


# Security router
security_router = APIRouter(prefix="/security", tags=["Security"])

@security_router.get("/events", response_model=PaginatedResponse)
async def list_security_events(
    project_id: Optional[str] = Query(None),
    threat_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(SecurityEvent)
    count_q = select(func.count(SecurityEvent.id))
    
    if project_id:
        query = query.where(SecurityEvent.project_id == project_id)
        count_q = count_q.where(SecurityEvent.project_id == project_id)
    if threat_type:
        query = query.where(SecurityEvent.threat_type == threat_type)
        count_q = count_q.where(SecurityEvent.threat_type == threat_type)
    
    total = (await db.execute(count_q)).scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(desc(SecurityEvent.created_at)).offset(offset).limit(page_size))
    
    return {
        "items": [SecurityEventResponse.model_validate(e) for e in result.scalars().all()],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@security_router.get("/stats")
async def get_security_stats(
    project_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    since = datetime.now(timezone.utc) - timedelta(days=30)
    
    result = await db.execute(
        select(
            SecurityEvent.threat_type,
            func.count(SecurityEvent.id).label("count"),
            func.avg(SecurityEvent.threat_score).label("avg_score"),
        )
        .where(SecurityEvent.created_at >= since)
        .group_by(SecurityEvent.threat_type)
    )
    
    breakdown = [
        {"threat_type": row[0], "count": row[1], "avg_score": round(float(row[2] or 0), 3)}
        for row in result.fetchall()
    ]
    
    total_threats = sum(b["count"] for b in breakdown)
    
    return {
        "total_threats_30d": total_threats,
        "breakdown": breakdown,
        "risk_level": "high" if total_threats > 100 else "medium" if total_threats > 20 else "low",
    }


# Users router (admin)
users_router = APIRouter(prefix="/users", tags=["Users"])

@users_router.get("")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.db.models.user import User as UserModel
    from app.schemas import UserResponse
    
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    count_r = await db.execute(select(func.count(UserModel.id)))
    total = count_r.scalar_one()
    
    offset = (page - 1) * page_size
    result = await db.execute(
        select(UserModel).order_by(desc(UserModel.created_at)).offset(offset).limit(page_size)
    )
    users = result.scalars().all()
    
    return {
        "items": [UserResponse.model_validate(u) for u in users],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@users_router.put("/{user_id}/role")
async def update_user_role(
    user_id: str,
    role_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.db.models.user import User as UserModel
    
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role = role_data.get("role", user.role)
    await db.commit()
    return {"message": "Role updated"}


@users_router.put("/{user_id}/status")
async def toggle_user_status(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.db.models.user import User as UserModel
    
    if current_user.role not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = not user.is_active
    await db.commit()
    return {"message": f"User {'activated' if user.is_active else 'deactivated'}"}

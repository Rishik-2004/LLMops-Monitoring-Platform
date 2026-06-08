"""
Analytics API endpoints
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, text, case
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import structlog

from app.core.database import get_db
from app.core.deps import get_current_user
from app.db.models.user import User
from app.db.models.prompt_log import PromptLog
from app.db.models.project import Project
from app.db.models.security import UserFeedback, Evaluation
from app.schemas import AnalyticsOverview

logger = structlog.get_logger()
router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_user_project_filter(current_user: User):
    """Return project IDs accessible to user"""
    if current_user.role in ["admin", "superadmin"]:
        return None
    return select(Project.id).where(Project.owner_id == current_user.id)


@router.get("/overview", response_model=AnalyticsOverview)
async def get_overview(
    project_id: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get analytics overview metrics"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
    yesterday = today - timedelta(days=1)

    base_filter = [PromptLog.created_at >= since]
    project_ids = get_user_project_filter(current_user)
    if project_ids is not None:
        base_filter.append(PromptLog.project_id.in_(project_ids))
    if project_id:
        base_filter.append(PromptLog.project_id == project_id)

    # Total requests
    r = await db.execute(select(func.count(PromptLog.id)).where(*base_filter))
    total_requests = r.scalar_one() or 0

    # Total cost
    r = await db.execute(select(func.sum(PromptLog.estimated_cost)).where(*base_filter))
    total_cost = float(r.scalar_one() or 0)

    # Total tokens
    r = await db.execute(select(func.sum(PromptLog.total_tokens)).where(*base_filter))
    total_tokens = int(r.scalar_one() or 0)

    # Avg latency
    r = await db.execute(select(func.avg(PromptLog.latency_ms)).where(*base_filter))
    avg_latency = float(r.scalar_one() or 0)

    # Error rate
    error_filter = base_filter + [PromptLog.status == "error"]
    r = await db.execute(select(func.count(PromptLog.id)).where(*error_filter))
    error_count = r.scalar_one() or 0
    error_rate = (error_count / total_requests) if total_requests > 0 else 0.0

    # Hallucination rate
    hall_filter = base_filter + [PromptLog.hallucination_score.isnot(None)]
    r = await db.execute(select(func.avg(PromptLog.hallucination_score)).where(*hall_filter))
    hallucination_rate = float(r.scalar_one() or 0)

    # Satisfaction score
    r = await db.execute(select(func.avg(UserFeedback.rating)))
    satisfaction_score = float(r.scalar_one() or 0)

    # Today's stats
    today_filter = base_filter + [PromptLog.created_at >= today]
    r = await db.execute(select(func.count(PromptLog.id)).where(*today_filter))
    requests_today = r.scalar_one() or 0
    r = await db.execute(select(func.sum(PromptLog.estimated_cost)).where(*today_filter))
    cost_today = float(r.scalar_one() or 0)

    # Yesterday's stats for change %
    yesterday_filter = base_filter + [
        PromptLog.created_at >= yesterday,
        PromptLog.created_at < today,
    ]
    r = await db.execute(select(func.count(PromptLog.id)).where(*yesterday_filter))
    requests_yesterday = r.scalar_one() or 0
    r = await db.execute(select(func.sum(PromptLog.estimated_cost)).where(*yesterday_filter))
    cost_yesterday = float(r.scalar_one() or 0)

    def pct_change(current, previous):
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 2)

    # Active projects
    r = await db.execute(
        select(func.count(func.distinct(PromptLog.project_id))).where(*base_filter)
    )
    active_projects = r.scalar_one() or 0

    # Active users
    r = await db.execute(
        select(func.count(func.distinct(PromptLog.user_id))).where(*base_filter)
    )
    active_users = r.scalar_one() or 0

    return {
        "total_requests": total_requests,
        "active_projects": active_projects,
        "active_users": active_users,
        "total_cost": round(total_cost, 4),
        "total_tokens": total_tokens,
        "avg_latency_ms": round(avg_latency, 2),
        "error_rate": round(error_rate, 4),
        "hallucination_rate": round(hallucination_rate, 4),
        "satisfaction_score": round(satisfaction_score, 2),
        "requests_today": requests_today,
        "cost_today": round(cost_today, 4),
        "cost_change_pct": pct_change(cost_today, cost_yesterday),
        "requests_change_pct": pct_change(requests_today, requests_yesterday),
    }


@router.get("/timeseries")
async def get_timeseries(
    metric: str = Query("requests", enum=["requests", "tokens", "cost", "latency", "errors"]),
    granularity: str = Query("day", enum=["hour", "day", "week"]),
    days: int = Query(30, ge=1, le=90),
    project_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get time series data for charts"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    trunc_map = {"hour": "hour", "day": "day", "week": "week"}
    trunc = trunc_map.get(granularity, "day")

    metric_col = {
        "requests": "COUNT(*)",
        "tokens": "SUM(total_tokens)",
        "cost": "SUM(estimated_cost)",
        "latency": "AVG(latency_ms)",
        "errors": "SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END)",
    }.get(metric, "COUNT(*)")

    # Build parameterized query - trunc and metric_col come from safe enums above
    project_filter_sql = ""
    params: dict = {"since": since}

    project_ids = get_user_project_filter(current_user)
    if project_ids is not None:
        project_filter_sql += " AND project_id IN (SELECT id FROM projects WHERE owner_id = :owner_id)"
        params["owner_id"] = current_user.id
    if project_id:
        project_filter_sql += " AND project_id = :project_id"
        params["project_id"] = project_id

    query = text(f"""
        SELECT 
            DATE_TRUNC('{trunc}', created_at) as ts,
            {metric_col} as value
        FROM prompt_logs
        WHERE created_at >= :since{project_filter_sql}
        GROUP BY ts
        ORDER BY ts
    """)

    result = await db.execute(query, params)
    rows = result.fetchall()

    return [
        {"timestamp": row[0].isoformat() if row[0] else None, "value": float(row[1] or 0)}
        for row in rows
    ]


@router.get("/models")
async def get_model_stats(
    days: int = Query(30, ge=1, le=90),
    project_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get per-model analytics"""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    base_filter = [PromptLog.created_at >= since]
    project_ids = get_user_project_filter(current_user)
    if project_ids is not None:
        base_filter.append(PromptLog.project_id.in_(project_ids))
    if project_id:
        base_filter.append(PromptLog.project_id == project_id)

    result = await db.execute(
        select(
            PromptLog.model_name,
            PromptLog.provider,
            func.count(PromptLog.id).label("total_requests"),
            func.avg(PromptLog.latency_ms).label("avg_latency"),
            func.sum(PromptLog.estimated_cost).label("total_cost"),
            func.avg(PromptLog.estimated_cost).label("avg_cost"),
            func.sum(PromptLog.total_tokens).label("total_tokens"),
            func.sum(
                case((PromptLog.status == "error", 1), else_=0)
            ).label("error_count"),
        )
        .where(*base_filter)
        .group_by(PromptLog.model_name, PromptLog.provider)
        .order_by(desc("total_requests"))
    )
    rows = result.all()

    return [
        {
            "model_name": row.model_name,
            "provider": row.provider,
            "total_requests": row.total_requests,
            "avg_latency_ms": round(float(row.avg_latency or 0), 2),
            "total_cost": round(float(row.total_cost or 0), 4),
            "avg_cost": round(float(row.avg_cost or 0), 6),
            "total_tokens": int(row.total_tokens or 0),
            "error_rate": round((row.error_count or 0) / row.total_requests, 4) if row.total_requests else 0,
        }
        for row in rows
    ]


@router.get("/latency/percentiles")
async def get_latency_percentiles(
    project_id: Optional[str] = Query(None),
    days: int = Query(7),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get latency percentile metrics (P50, P95, P99)"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    params: dict = {"since": since}
    project_filter_sql = ""
    if project_id:
        project_filter_sql = " AND project_id = :project_id"
        params["project_id"] = project_id

    query = text(f"""
        SELECT 
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY latency_ms) as p50,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95,
            PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY latency_ms) as p99,
            MIN(latency_ms) as min_latency,
            MAX(latency_ms) as max_latency,
            AVG(latency_ms) as avg_latency
        FROM prompt_logs
        WHERE created_at >= :since AND latency_ms IS NOT NULL{project_filter_sql}
    """)
    
    result = await db.execute(query, params)
    row = result.fetchone()
    
    if not row:
        return {"p50": 0, "p95": 0, "p99": 0, "min": 0, "max": 0, "avg": 0}

    return {
        "p50": round(float(row[0] or 0), 2),
        "p95": round(float(row[1] or 0), 2),
        "p99": round(float(row[2] or 0), 2),
        "min": round(float(row[3] or 0), 2),
        "max": round(float(row[4] or 0), 2),
        "avg": round(float(row[5] or 0), 2),
    }


@router.get("/costs/forecast")
async def get_cost_forecast(
    project_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get cost forecast for the next 7 days"""
    # Get last 30 days of daily costs
    since = datetime.now(timezone.utc) - timedelta(days=30)
    
    params: dict = {"since": since}
    project_filter_sql = ""
    if project_id:
        project_filter_sql = " AND project_id = :project_id"
        params["project_id"] = project_id

    query = text(f"""
        SELECT 
            DATE_TRUNC('day', created_at) as day,
            SUM(estimated_cost) as daily_cost
        FROM prompt_logs
        WHERE created_at >= :since{project_filter_sql}
        GROUP BY day
        ORDER BY day
    """)
    
    result = await db.execute(query, params)
    rows = result.fetchall()
    
    if not rows:
        return {"historical": [], "forecast": [], "avg_daily_cost": 0}

    historical = [{"date": row[0].isoformat(), "cost": float(row[1])} for row in rows]
    avg_daily = sum(r["cost"] for r in historical) / len(historical)
    
    # Simple linear projection
    forecast = []
    last_date = rows[-1][0]
    for i in range(1, 8):
        forecast_date = last_date + timedelta(days=i)
        forecast.append({
            "date": forecast_date.isoformat(),
            "projected_cost": round(avg_daily * (1 + 0.02 * i), 4),  # 2% daily growth assumption
        })

    return {
        "historical": historical,
        "forecast": forecast,
        "avg_daily_cost": round(avg_daily, 4),
        "projected_monthly": round(avg_daily * 30, 2),
    }

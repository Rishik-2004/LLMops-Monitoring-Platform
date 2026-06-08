"""
Pydantic schemas for all API endpoints
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
import enum


# ===== Auth Schemas =====

class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None
    password: str = Field(..., min_length=8)

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v):
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username must be alphanumeric")
        return v.lower()


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


# ===== User Schemas =====

class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    full_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None


class UserRoleUpdate(BaseModel):
    role: str


# ===== Project Schemas =====

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    environment: str = "development"


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    environment: Optional[str] = None
    status: Optional[str] = None


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    environment: str
    status: str
    owner_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== API Key Schemas =====

class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    project_id: Optional[UUID] = None
    permissions: str = "read,write"
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    description: Optional[str]
    permissions: str
    is_active: bool
    last_used_at: Optional[datetime]
    usage_count: int
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyCreateResponse(APIKeyResponse):
    plain_key: str  # Only returned on creation


# ===== Prompt Log Schemas =====

class TrackRequest(BaseModel):
    """SDK tracking request"""
    project_id: str
    prompt: str
    response: str
    model: str
    provider: str = "groq"
    system_prompt: Optional[str] = None
    session_id: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    latency_ms: float = 0.0
    status: str = "success"
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
    extra_metadata: Optional[Dict[str, Any]] = None


class PromptLogResponse(BaseModel):
    id: UUID
    project_id: UUID
    session_id: Optional[str]
    system_prompt: Optional[str]
    user_prompt: str
    response_text: Optional[str]
    model_name: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    latency_ms: Optional[float]
    status: str
    error_type: Optional[str]
    error_message: Optional[str]
    injection_score: float
    toxicity_score: float
    is_flagged: bool
    hallucination_score: Optional[float]
    faithfulness_score: Optional[float]
    relevance_score: Optional[float]
    tags: Optional[Union[Dict[str, Any], List[Any]]]
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Analytics Schemas =====

class AnalyticsOverview(BaseModel):
    total_requests: int
    active_projects: int
    active_users: int
    total_cost: float
    total_tokens: int
    avg_latency_ms: float
    error_rate: float
    hallucination_rate: float
    satisfaction_score: float
    requests_today: int
    cost_today: float
    cost_change_pct: float
    requests_change_pct: float


class TimeSeriesPoint(BaseModel):
    timestamp: str
    value: float
    label: Optional[str] = None


class ModelComparison(BaseModel):
    model_name: str
    provider: str
    total_requests: int
    avg_latency_ms: float
    avg_cost: float
    error_rate: float
    hallucination_rate: Optional[float]


# ===== Evaluation Schemas =====

class EvaluationCreate(BaseModel):
    project_id: UUID
    prompt_log_id: Optional[UUID] = None
    prompt: str
    response: str
    context: Optional[str] = None
    ground_truth: Optional[str] = None
    run_ragas: bool = True
    run_deepeval: bool = True


class EvaluationResponse(BaseModel):
    id: UUID
    project_id: UUID
    prompt_log_id: Optional[UUID]
    faithfulness: Optional[float]
    answer_relevancy: Optional[float]
    context_precision: Optional[float]
    context_recall: Optional[float]
    hallucination_rate: Optional[float]
    answer_correctness: Optional[float]
    toxicity_score: Optional[float]
    overall_quality_score: Optional[float]
    evaluation_model: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Alert Schemas =====

class AlertCreate(BaseModel):
    project_id: UUID
    alert_type: str
    severity: str = "medium"
    title: str
    message: str
    threshold_value: Optional[float] = None
    notification_channels: List[str] = ["in_app"]
    email_recipients: Optional[List[str]] = None


class AlertResponse(BaseModel):
    id: UUID
    project_id: UUID
    alert_type: str
    severity: str
    title: str
    message: str
    threshold_value: Optional[float]
    actual_value: Optional[float]
    is_active: bool
    is_triggered: bool
    is_acknowledged: bool
    triggered_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Feedback Schemas =====

class FeedbackCreate(BaseModel):
    prompt_log_id: UUID
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    thumbs_up: Optional[bool] = None
    categories: Optional[List[str]] = None


class FeedbackResponse(BaseModel):
    id: UUID
    prompt_log_id: UUID
    user_id: UUID
    rating: int
    comment: Optional[str]
    thumbs_up: Optional[bool]
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Security Schemas =====

class SecurityEventResponse(BaseModel):
    id: UUID
    project_id: UUID
    threat_type: str
    threat_score: float
    detection_reason: Optional[str]
    prompt_snippet: Optional[str]
    is_blocked: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Copilot Schemas =====

class CopilotMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None


class CopilotRequest(BaseModel):
    question: str
    project_id: Optional[str] = None
    conversation_history: Optional[List[CopilotMessage]] = []


class CopilotResponse(BaseModel):
    answer: str
    sources: Optional[List[str]] = None
    tool_calls: Optional[List[Dict]] = None
    reasoning_steps: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    confidence: Optional[float] = None


# ===== Pagination =====

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

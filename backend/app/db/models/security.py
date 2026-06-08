"""
Security Event model
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Float, JSON, Enum as SAEnum, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class ThreatType(str, enum.Enum):
    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK = "jailbreak"
    SYSTEM_PROMPT_EXTRACTION = "system_prompt_extraction"
    ROLE_OVERRIDE = "role_override"
    TOXICITY = "toxicity"
    DATA_EXFILTRATION = "data_exfiltration"
    UNKNOWN = "unknown"


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_log_id = Column(UUID(as_uuid=True), ForeignKey("prompt_logs.id"), nullable=True)
    project_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    threat_type = Column(SAEnum(ThreatType), nullable=False, index=True)
    threat_score = Column(Float, nullable=False)
    detection_reason = Column(Text, nullable=True)
    prompt_snippet = Column(Text, nullable=True)
    is_blocked = Column(Boolean, default=False)
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    prompt_log = relationship("PromptLog", back_populates="security_events")


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    prompt_log_id = Column(UUID(as_uuid=True), ForeignKey("prompt_logs.id"), nullable=True)

    # RAGAS Metrics
    faithfulness = Column(Float, nullable=True)
    answer_relevancy = Column(Float, nullable=True)
    context_precision = Column(Float, nullable=True)
    context_recall = Column(Float, nullable=True)
    hallucination_rate = Column(Float, nullable=True)

    # DeepEval Metrics
    answer_correctness = Column(Float, nullable=True)
    toxicity_score = Column(Float, nullable=True)
    bias_score = Column(Float, nullable=True)
    coherence_score = Column(Float, nullable=True)

    # Composite
    overall_quality_score = Column(Float, nullable=True)
    evaluation_model = Column(String(100), nullable=True)
    evaluator = Column(String(100), default="automated")
    notes = Column(Text, nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="evaluations")


class AlertType(str, enum.Enum):
    COST_THRESHOLD = "cost_threshold"
    LATENCY_SPIKE = "latency_spike"
    ERROR_RATE = "error_rate"
    HALLUCINATION_RATE = "hallucination_rate"
    SECURITY_THREAT = "security_threat"
    TOKEN_LIMIT = "token_limit"


class AlertSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    alert_type = Column(SAEnum(AlertType), nullable=False, index=True)
    severity = Column(SAEnum(AlertSeverity), default=AlertSeverity.MEDIUM)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    threshold_value = Column(Float, nullable=True)
    actual_value = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    is_triggered = Column(Boolean, default=False)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(UUID(as_uuid=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    notification_channels = Column(JSON, default=["in_app"])
    email_recipients = Column(JSON, nullable=True)
    triggered_at = Column(DateTime(timezone=True), nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="alerts")


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_log_id = Column(UUID(as_uuid=True), ForeignKey("prompt_logs.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    thumbs_up = Column(Boolean, nullable=True)
    categories = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    prompt_log = relationship("PromptLog", back_populates="feedback")
    user = relationship("User", back_populates="feedback")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    status = Column(String(50), default="success")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="audit_logs")

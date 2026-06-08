"""
Prompt Log and Response Log models
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Float, Integer, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class PromptLog(Base):
    __tablename__ = "prompt_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    session_id = Column(String(255), nullable=True, index=True)
    trace_id = Column(String(255), nullable=True, index=True)

    # Prompt content
    system_prompt = Column(Text, nullable=True)
    user_prompt = Column(Text, nullable=False)
    full_prompt = Column(Text, nullable=True)

    # Model info
    model_name = Column(String(100), nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)

    # Response
    response_text = Column(Text, nullable=True)
    finish_reason = Column(String(50), nullable=True)

    # Tokens
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)

    # Cost
    estimated_cost = Column(Float, default=0.0)

    # Latency
    latency_ms = Column(Float, nullable=True)
    request_start = Column(DateTime(timezone=True), nullable=True)
    request_end = Column(DateTime(timezone=True), nullable=True)

    # Status
    status = Column(String(50), default="success", index=True)
    error_type = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    http_status_code = Column(Integer, nullable=True)

    # Security scores
    injection_score = Column(Float, default=0.0)
    toxicity_score = Column(Float, default=0.0)
    is_flagged = Column(Boolean, default=False, index=True)
    flag_reason = Column(String(500), nullable=True)

    # Evaluation scores
    hallucination_score = Column(Float, nullable=True)
    faithfulness_score = Column(Float, nullable=True)
    relevance_score = Column(Float, nullable=True)

    # Metadata
    tags = Column(JSON, nullable=True)
    extra_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    project = relationship("Project", back_populates="prompt_logs")
    feedback = relationship("UserFeedback", back_populates="prompt_log", uselist=False)
    security_events = relationship("SecurityEvent", back_populates="prompt_log")

    __table_args__ = (
        Index("ix_prompt_logs_project_created", "project_id", "created_at"),
        Index("ix_prompt_logs_provider_model", "provider", "model_name"),
    )

    def __repr__(self):
        return f"<PromptLog {self.id} - {self.model_name}>"

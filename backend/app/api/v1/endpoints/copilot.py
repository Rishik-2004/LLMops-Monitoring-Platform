"""
AI Monitoring Copilot API endpoint
"""

from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.db.models.user import User
from app.schemas import CopilotRequest, CopilotResponse
from app.agents.monitoring_copilot import run_copilot
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/copilot", tags=["AI Copilot"])


@router.post("/chat", response_model=CopilotResponse)
async def chat_with_copilot(
    request: CopilotRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Chat with the AI Monitoring Copilot
    
    Ask questions like:
    - "Why did costs increase yesterday?"
    - "Which model has the highest error rate?"
    - "Show me latency trends"
    - "Recommend optimizations"
    """
    logger.info("Copilot query", user=current_user.username, question=request.question[:100])
    
    result = await run_copilot(
        question=request.question,
        project_id=request.project_id,
    )
    
    return CopilotResponse(
        answer=result["answer"],
        reasoning_steps=result.get("reasoning_steps"),
        recommendations=result.get("recommendations"),
        confidence=result.get("confidence"),
    )


@router.get("/suggestions")
async def get_question_suggestions(current_user: User = Depends(get_current_user)):
    """Get suggested questions for the copilot"""
    return {
        "suggestions": [
            "Why did costs increase in the last 7 days?",
            "Which model has the highest latency?",
            "Show me the top failed requests",
            "What's our hallucination rate trend?",
            "Recommend ways to reduce API spending",
            "Are there any security threats I should know about?",
            "Compare performance across different providers",
            "What's causing the error rate spike?",
            "Which prompts are the most expensive?",
            "Give me a weekly operational summary",
        ]
    }

"""
AI Monitoring Copilot - LangGraph Agent
Analyzes logs, explains anomalies, generates operational insights
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
import operator
import json
import structlog
from datetime import datetime, timezone, timedelta

from app.core.config import settings

logger = structlog.get_logger()


class AgentState(TypedDict):
    """State for the monitoring copilot agent"""
    question: str
    project_id: Optional[str]
    messages: List[Dict[str, str]]
    retrieved_data: Dict[str, Any]
    analysis: str
    recommendations: List[str]
    reasoning_steps: List[str]
    final_answer: str
    tool_calls: List[Dict]


async def create_monitoring_copilot():
    """Create and return the LangGraph monitoring copilot"""
    try:
        from langchain_groq import ChatGroq
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
        from langgraph.graph import StateGraph, END
        
        llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.DEFAULT_GROQ_MODEL,
            temperature=0.1,
        )
    except Exception as e:
        logger.warning("Failed to initialize Groq LLM", error=str(e))
        llm = None

    async def retrieve_metrics_node(state: AgentState) -> AgentState:
        """Retrieve relevant metrics from database"""
        from app.core.database import AsyncSessionLocal
        from app.db.models.prompt_log import PromptLog
        from sqlalchemy import select, func
        
        data = {}
        try:
            async with AsyncSessionLocal() as db:
                since = datetime.now(timezone.utc) - timedelta(days=7)
                
                # Get recent stats
                r = await db.execute(
                    select(
                        func.count(PromptLog.id).label("total"),
                        func.sum(PromptLog.estimated_cost).label("total_cost"),
                        func.avg(PromptLog.latency_ms).label("avg_latency"),
                        func.avg(PromptLog.hallucination_score).label("avg_hallucination"),
                    ).where(PromptLog.created_at >= since)
                )
                row = r.fetchone()
                
                if row:
                    data["recent_stats"] = {
                        "total_requests_7d": int(row.total or 0),
                        "total_cost_7d": round(float(row.total_cost or 0), 4),
                        "avg_latency_ms": round(float(row.avg_latency or 0), 2),
                        "avg_hallucination_rate": round(float(row.avg_hallucination or 0), 4),
                    }
                
                # Get error breakdown
                r = await db.execute(
                    select(PromptLog.error_type, func.count(PromptLog.id))
                    .where(PromptLog.created_at >= since, PromptLog.status == "error")
                    .group_by(PromptLog.error_type)
                    .limit(10)
                )
                data["error_breakdown"] = {row[0] or "unknown": row[1] for row in r.fetchall()}
                
                # Get model stats
                r = await db.execute(
                    select(
                        PromptLog.model_name,
                        PromptLog.provider,
                        func.count(PromptLog.id).label("count"),
                        func.sum(PromptLog.estimated_cost).label("cost"),
                        func.avg(PromptLog.latency_ms).label("latency"),
                    )
                    .where(PromptLog.created_at >= since)
                    .group_by(PromptLog.model_name, PromptLog.provider)
                    .limit(10)
                )
                data["model_stats"] = [
                    {
                        "model": row.model_name,
                        "provider": row.provider,
                        "requests": int(row.count),
                        "cost": round(float(row.cost or 0), 4),
                        "avg_latency": round(float(row.latency or 0), 2),
                    }
                    for row in r.fetchall()
                ]
                
        except Exception as e:
            logger.error("Failed to retrieve metrics", error=str(e))
            data["error"] = str(e)
            # Provide mock data for demo
            data["recent_stats"] = {
                "total_requests_7d": 1247,
                "total_cost_7d": 4.82,
                "avg_latency_ms": 892.5,
                "avg_hallucination_rate": 0.12,
            }
        
        state["retrieved_data"] = data
        state["reasoning_steps"].append("Retrieved metrics from database")
        return state

    async def analyze_node(state: AgentState) -> AgentState:
        """Analyze retrieved data and formulate insights"""
        data = state.get("retrieved_data", {})
        question = state["question"]
        
        analysis_prompt = f"""You are an expert LLMOps analyst. Analyze the following monitoring data and answer the question.

Question: {question}

Monitoring Data (last 7 days):
{json.dumps(data, indent=2)}

Provide:
1. Direct answer to the question
2. Key observations from the data
3. Root cause analysis if applicable
4. Specific, actionable recommendations

Be concise, data-driven, and practical."""
        
        try:
            if llm:
                from langchain_core.messages import HumanMessage
                response = await llm.ainvoke([HumanMessage(content=analysis_prompt)])
                state["analysis"] = response.content
            else:
                # Fallback analysis
                stats = data.get("recent_stats", {})
                state["analysis"] = f"""Based on the available data:

**Current Status:**
- Total requests (7d): {stats.get('total_requests_7d', 'N/A')}
- Total cost (7d): ${stats.get('total_cost_7d', 'N/A')}
- Average latency: {stats.get('avg_latency_ms', 'N/A')}ms
- Hallucination rate: {stats.get('avg_hallucination_rate', 'N/A')}

**Analysis:** {question}
The monitoring data shows typical operating patterns. Connect Groq API key for deeper AI-powered analysis."""
        except Exception as e:
            logger.error("Analysis failed", error=str(e))
            state["analysis"] = f"Analysis encountered an error: {str(e)}. Please check API configuration."
        
        state["reasoning_steps"].append("Analyzed data and generated insights")
        return state

    async def recommend_node(state: AgentState) -> AgentState:
        """Generate specific recommendations"""
        data = state.get("retrieved_data", {})
        analysis = state.get("analysis", "")
        
        recommendations = []
        
        # Rule-based recommendations
        stats = data.get("recent_stats", {})
        if stats.get("avg_latency_ms", 0) > 3000:
            recommendations.append("⚡ High latency detected - consider switching to Groq's faster models (llama-3.1-8b-instant)")
        if stats.get("avg_hallucination_rate", 0) > 0.3:
            recommendations.append("🎯 High hallucination rate - implement RAG with grounding context")
        if stats.get("total_cost_7d", 0) > 50:
            recommendations.append("💰 High costs - consider using smaller models for simple queries")
        
        error_breakdown = data.get("error_breakdown", {})
        if error_breakdown.get("rate_limit_error", 0) > 0:
            recommendations.append("🔄 Rate limit errors detected - implement exponential backoff retry logic")
        if error_breakdown.get("timeout", 0) > 0:
            recommendations.append("⏱️ Timeout errors - increase timeout threshold or use streaming responses")
        
        if not recommendations:
            recommendations = [
                "✅ System is operating within normal parameters",
                "📊 Continue monitoring for anomalies",
                "🔍 Consider setting up automated alerts for proactive detection",
            ]
        
        state["recommendations"] = recommendations
        state["reasoning_steps"].append("Generated actionable recommendations")
        return state

    async def format_response_node(state: AgentState) -> AgentState:
        """Format the final response"""
        analysis = state.get("analysis", "")
        recommendations = state.get("recommendations", [])
        
        response_parts = [analysis]
        
        if recommendations:
            response_parts.append("\n\n**Recommendations:**")
            for rec in recommendations:
                response_parts.append(f"- {rec}")
        
        state["final_answer"] = "\n".join(response_parts)
        return state

    try:
        from langgraph.graph import StateGraph, END
        
        # Build the graph
        workflow = StateGraph(AgentState)
        workflow.add_node("retrieve_metrics", retrieve_metrics_node)
        workflow.add_node("analyze", analyze_node)
        workflow.add_node("recommend", recommend_node)
        workflow.add_node("format_response", format_response_node)
        
        workflow.set_entry_point("retrieve_metrics")
        workflow.add_edge("retrieve_metrics", "analyze")
        workflow.add_edge("analyze", "recommend")
        workflow.add_edge("recommend", "format_response")
        workflow.add_edge("format_response", END)
        
        return workflow.compile()
    except Exception as e:
        logger.error("Failed to create LangGraph workflow", error=str(e))
        return None


async def _run_fallback_copilot(question: str, project_id: Optional[str] = None) -> Dict[str, Any]:
    """Run a simple fallback copilot without LangGraph when imports fail"""
    from app.core.database import AsyncSessionLocal
    from app.db.models.prompt_log import PromptLog
    from sqlalchemy import select, func

    data: Dict[str, Any] = {}
    reasoning_steps: List[str] = []
    try:
        async with AsyncSessionLocal() as db:
            since = datetime.now(timezone.utc) - timedelta(days=7)
            r = await db.execute(
                select(
                    func.count(PromptLog.id).label("total"),
                    func.sum(PromptLog.estimated_cost).label("total_cost"),
                    func.avg(PromptLog.latency_ms).label("avg_latency"),
                ).where(PromptLog.created_at >= since)
            )
            row = r.fetchone()
            if row:
                data["recent_stats"] = {
                    "total_requests_7d": int(row.total or 0),
                    "total_cost_7d": round(float(row.total_cost or 0), 4),
                    "avg_latency_ms": round(float(row.avg_latency or 0), 2),
                }
        reasoning_steps.append("Retrieved metrics from database")
    except Exception as e:
        logger.error("Fallback metrics retrieval failed", error=str(e))
        data["recent_stats"] = {"total_requests_7d": 0, "total_cost_7d": 0.0, "avg_latency_ms": 0.0}

    stats = data.get("recent_stats", {})
    answer = (
        f"**Monitoring Summary (Last 7 Days)**\n\n"
        f"- Total Requests: {stats.get('total_requests_7d', 'N/A')}\n"
        f"- Total Cost: ${stats.get('total_cost_7d', 'N/A')}\n"
        f"- Average Latency: {stats.get('avg_latency_ms', 'N/A')}ms\n\n"
        f"**Your Question:** {question}\n\n"
        f"Configure `GROQ_API_KEY` for AI-powered analysis."
    )
    reasoning_steps.append("Generated fallback response")
    return {
        "answer": answer,
        "reasoning_steps": reasoning_steps,
        "recommendations": ["Configure GROQ_API_KEY for AI-powered insights", "Check database connectivity"],
        "confidence": 0.3,
    }


async def run_copilot(question: str, project_id: Optional[str] = None) -> Dict[str, Any]:
    """Run the monitoring copilot with a question"""
    try:
        copilot = await create_monitoring_copilot()
        
        initial_state = AgentState(
            question=question,
            project_id=project_id,
            messages=[],
            retrieved_data={},
            analysis="",
            recommendations=[],
            reasoning_steps=[],
            final_answer="",
            tool_calls=[],
        )
        
        if copilot:
            result = await copilot.ainvoke(initial_state)
            return {
                "answer": result.get("final_answer", "Unable to generate answer"),
                "reasoning_steps": result.get("reasoning_steps", []),
                "recommendations": result.get("recommendations", []),
                "confidence": 0.85,
            }
        else:
            # Fallback: LangGraph unavailable
            return await _run_fallback_copilot(question, project_id)
    except Exception as e:
        logger.error("Copilot execution failed", error=str(e))
        return {
            "answer": f"I encountered an error while analyzing your question: {str(e)}. Please check that your Groq API key is configured correctly.",
            "reasoning_steps": ["Error occurred during execution"],
            "recommendations": ["Check API key configuration", "Verify database connection"],
            "confidence": 0.0,
        }

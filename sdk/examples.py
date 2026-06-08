"""
LLMOps SDK Usage Examples
"""

# ── Basic Usage ────────────────────────────────────────────────────────────────
from llmops_sdk import LLMOpsMonitor

monitor = LLMOpsMonitor(
    api_key="llm_your_api_key_here",
    project_id="your-project-uuid",
    base_url="https://your-backend.railway.app/api/v1",
)

# Simple tracking
monitor.track(
    prompt="Explain quantum computing in simple terms",
    response="Quantum computing uses quantum bits (qubits)...",
    model="llama-3.3-70b-versatile",
    provider="groq",
    tokens=1250,
    cost=0.000738,
    latency_ms=892,
)

# ── Context Manager (auto-tracks latency) ─────────────────────────────────────
from groq import Groq

groq_client = Groq(api_key="gsk_your_groq_key")

with monitor.trace(
    prompt="What is machine learning?",
    model="llama-3.3-70b-versatile",
    provider="groq",
    session_id="session_abc123",
) as ctx:
    result = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "What is machine learning?"}],
    )
    ctx.set_response(result.choices[0].message.content)
    ctx.set_tokens(
        total=result.usage.total_tokens,
        prompt=result.usage.prompt_tokens,
        completion=result.usage.completion_tokens,
    )

# ── Auto-Wrapping Groq Client ──────────────────────────────────────────────────
tracked_groq = monitor.groq_wrapper(groq_client, model="llama-3.3-70b-versatile")

# All calls auto-tracked
response = tracked_groq.chat.completions.create(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"},
    ],
    model="llama-3.3-70b-versatile",
)

# ── Error Tracking ─────────────────────────────────────────────────────────────
try:
    # Some LLM call
    raise TimeoutError("Request timed out after 30s")
except TimeoutError as e:
    monitor.track_error(
        prompt="Complex reasoning task...",
        model="llama-3.3-70b-versatile",
        provider="groq",
        error_type="TimeoutError",
        error_message=str(e),
        latency_ms=30000,
    )

# ── With Tags and Metadata ─────────────────────────────────────────────────────
monitor.track(
    prompt="Summarize this document...",
    response="The document discusses...",
    model="gemini-1.5-flash",
    provider="gemini",
    tokens=3400,
    cost=0.000255,
    latency_ms=1240,
    tags={"use_case": "summarization", "environment": "production"},
    metadata={"document_id": "doc_123", "user_tier": "premium"},
)

# ── REST API Direct Usage ──────────────────────────────────────────────────────
# POST /api/v1/logs/track
# Headers: X-API-Key: llm_your_api_key
# Body:
# {
#   "project_id": "uuid",
#   "prompt": "User message",
#   "response": "LLM response",
#   "model": "llama-3.3-70b-versatile",
#   "provider": "groq",
#   "prompt_tokens": 100,
#   "completion_tokens": 200,
#   "total_tokens": 300,
#   "cost": 0.000177,
#   "latency_ms": 450
# }

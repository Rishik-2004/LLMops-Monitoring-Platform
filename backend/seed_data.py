"""
Seed script: populates the database with realistic sample LLM usage data
for dashboard demonstration. Run once after startup.

Usage: python seed_data.py
"""

import asyncio
import random
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import select
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

from app.db.models.user import User
from app.db.models.prompt_log import PromptLog
from app.db.models.project import Project, ProjectEnvironment
from app.core.database import Base

# ── Sample data pools ────────────────────────────────────────────────────────

MODELS = [
    {"provider": "groq",      "model": "llama-3.3-70b-versatile", "cost_per_1k": 0.00059},
    {"provider": "groq",      "model": "llama-3.1-8b-instant",    "cost_per_1k": 0.00005},
    {"provider": "groq",      "model": "mixtral-8x7b-32768",      "cost_per_1k": 0.00027},
    {"provider": "openai",    "model": "gpt-4o",                   "cost_per_1k": 0.005},
    {"provider": "openai",    "model": "gpt-4o-mini",              "cost_per_1k": 0.00015},
    {"provider": "anthropic", "model": "claude-3-5-sonnet-20241022","cost_per_1k": 0.003},
    {"provider": "gemini",    "model": "gemini-1.5-pro",           "cost_per_1k": 0.00125},
    {"provider": "gemini",    "model": "gemini-1.5-flash",         "cost_per_1k": 0.000075},
]

PROMPTS = [
    ("Summarize the following document in 3 bullet points.", "Here are 3 key bullet points from the document: • The system achieved 98% uptime. • Cost was reduced by 40%. • User satisfaction improved significantly."),
    ("Translate this text to French: Hello, how are you?", "Bonjour, comment allez-vous?"),
    ("Write a Python function to reverse a string.", "def reverse_string(s): return s[::-1]"),
    ("What is machine learning?", "Machine learning is a branch of AI that enables systems to learn from data without being explicitly programmed."),
    ("Generate a product description for a smartwatch.", "Introducing the UltraWatch Pro – your ultimate fitness and productivity companion with 7-day battery life and advanced health monitoring."),
    ("Explain quantum computing to a 10-year-old.", "Imagine a magical coin that can be heads AND tails at the same time until you look at it. Quantum computers use particles like that!"),
    ("List 5 best practices for REST API design.", "1. Use nouns in endpoints 2. Versioning (/v1/) 3. Proper HTTP methods 4. Consistent error responses 5. Authentication on all routes"),
    ("What are the GDPR data privacy requirements?", "GDPR requires lawful basis for processing, data minimization, purpose limitation, storage limits, and breach notification within 72 hours."),
    ("Debug this SQL query: SELECT * form users", "There's a typo – 'form' should be 'FROM'. Corrected: SELECT * FROM users"),
    ("Analyze the sentiment of: The product was terrible", "Sentiment: Negative (confidence: 0.97). The phrase 'terrible' strongly indicates dissatisfaction."),
]

SYSTEM_PROMPTS = [
    "You are a helpful AI assistant.",
    "You are an expert software engineer.",
    "You are a data analyst specializing in LLM metrics.",
    "You are a customer support agent.",
    None,
]

TAGS = [
    ["production", "chatbot"],
    ["staging", "summarization"],
    ["production", "code-gen"],
    ["dev", "translation"],
    ["production", "analysis"],
]


def rand_datetime(days_ago_max: int = 30) -> datetime:
    offset = random.uniform(0, days_ago_max * 24 * 3600)
    return datetime.now(timezone.utc) - timedelta(seconds=offset)


async def seed():
    # asyncpg doesn't support sslmode in URL — strip it and pass ssl via connect_args
    db_url = DATABASE_URL
    for param in ["?sslmode=require", "&sslmode=require"]:
        db_url = db_url.replace(param, "")
    engine = create_async_engine(
        db_url,
        echo=False,
        connect_args={"ssl": "require"},
    )

    async with AsyncSession(engine) as session:
        # ── Get admin user ────────────────────────────────────────────────────
        result = await session.execute(select(User).where(User.email == "admin@llmops.dev"))
        admin = result.scalar_one_or_none()
        if not admin:
            print("[ERROR] Admin user not found. Run the server first to seed the admin.")
            return

        # ── Get or create a demo project ──────────────────────────────────────
        result = await session.execute(select(Project).where(Project.name == "Demo Project"))
        project = result.scalar_one_or_none()
        if not project:
            project = Project(
                name="Demo Project",
                description="Auto-generated demo project for dashboard testing",
                owner_id=admin.id,
                environment=ProjectEnvironment.PRODUCTION,
            )
            session.add(project)
            await session.flush()
            print(f"[OK] Created project: {project.name}")
        else:
            print(f"[INFO] Using existing project: {project.name}")

        # ── Seed prompt logs ──────────────────────────────────────────────────
        NUM_LOGS = 200
        logs = []

        for i in range(NUM_LOGS):
            model_info = random.choices(
                MODELS,
                weights=[30, 15, 10, 8, 12, 8, 10, 7],  # groq models more common
                k=1,
            )[0]

            prompt_pair = random.choice(PROMPTS)
            prompt_tokens = random.randint(20, 300)
            completion_tokens = random.randint(30, 500)
            total_tokens = prompt_tokens + completion_tokens
            cost = (total_tokens / 1000) * model_info["cost_per_1k"]
            latency_ms = random.gauss(850, 300)
            latency_ms = max(150, min(5000, latency_ms))

            # ~5% error rate
            status = random.choices(["success", "error", "timeout"], weights=[93, 4, 3])[0]
            is_flagged = random.random() < 0.04  # ~4% flagged
            injection_score = random.uniform(0.7, 0.95) if is_flagged else random.uniform(0.0, 0.15)
            toxicity_score = random.uniform(0.6, 0.9) if is_flagged else random.uniform(0.0, 0.1)

            hallucination = random.uniform(0.05, 0.35)
            faithfulness = random.uniform(0.7, 0.99)
            relevance = random.uniform(0.65, 0.99)

            ts = rand_datetime(days_ago_max=30)

            log = PromptLog(
                project_id=project.id,
                user_id=admin.id,
                session_id=f"sess_{uuid.uuid4().hex[:8]}",
                trace_id=f"trace_{uuid.uuid4().hex[:12]}",
                system_prompt=random.choice(SYSTEM_PROMPTS),
                user_prompt=prompt_pair[0],
                response_text=prompt_pair[1] if status == "success" else None,
                model_name=model_info["model"],
                provider=model_info["provider"],
                finish_reason="stop" if status == "success" else "error",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens if status == "success" else 0,
                total_tokens=total_tokens if status == "success" else prompt_tokens,
                estimated_cost=round(cost, 6),
                latency_ms=round(latency_ms, 2),
                request_start=ts,
                request_end=ts + timedelta(milliseconds=latency_ms),
                status=status,
                error_type="RateLimitError" if status == "error" else None,
                http_status_code=200 if status == "success" else (429 if status == "error" else 408),
                injection_score=round(injection_score, 4),
                toxicity_score=round(toxicity_score, 4),
                is_flagged=is_flagged,
                flag_reason="Potential prompt injection detected" if is_flagged else None,
                hallucination_score=round(hallucination, 4),
                faithfulness_score=round(faithfulness, 4),
                relevance_score=round(relevance, 4),
                tags=random.choice(TAGS),
                created_at=ts,
            )
            logs.append(log)

        session.add_all(logs)
        await session.commit()
        print(f"[DONE] Seeded {NUM_LOGS} prompt logs across {len(MODELS)} models")
        print(f"Refresh your dashboard at http://localhost:3000/dashboard")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())

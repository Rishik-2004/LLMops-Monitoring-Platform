# 🚀 LLMOps Monitoring Platform

> **Enterprise-Grade LLM Observability & Monitoring Platform**  
> Monitor, evaluate, and optimize your AI applications with production-grade observability.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?style=flat&logo=next.js)](https://nextjs.org)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=flat&logo=typescript)](https://typescriptlang.org)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Deployment](#deployment)
- [SDK Usage](#sdk-usage)
- [API Documentation](#api-documentation)
- [Environment Variables](#environment-variables)

---

## Overview

LLMOps Platform is a centralized monitoring solution for AI/ML teams to track, evaluate, and optimize their LLM applications in production. It provides real-time observability similar to LangSmith, Langfuse, and Arize AI.

**Perfect for:**
- AI teams monitoring production LLM applications
- Cost optimization and budget management
- Quality assurance and hallucination detection
- Security threat monitoring (prompt injection, jailbreaks)
- Multi-model benchmarking and comparison

---

## ✨ Features

### 🔍 Monitoring & Observability
- **Real-time request tracking** — prompts, responses, tokens, costs, latency
- **OpenTelemetry integration** — distributed tracing across your stack
- **Error monitoring** — failures, timeouts, rate limits with stack traces
- **Provider comparison** — side-by-side Groq, Gemini, OpenAI, Anthropic metrics

### 🤖 AI Monitoring Copilot (LangGraph Agent)
- **Natural language queries** — ask questions about your platform in plain English
- **Root cause analysis** — automatically explains anomalies and spikes
- **Operational recommendations** — AI-generated optimization suggestions
- **Tool calling** — retrieves live metrics, analyzes trends, generates reports

### 📊 Analytics Dashboard
- **9 overview KPIs** — requests, costs, latency, errors, hallucinations, satisfaction
- **Time-series charts** — requests, costs, latency trends with forecasting
- **Model benchmarks** — ranked leaderboard with composite performance scores
- **Cost forecasting** — 7-day projection with daily breakdown

### 🛡️ Security Layer
- **Prompt injection detection** — 20+ regex patterns + heuristics
- **Jailbreak detection** — role override, instruction bypass, DAN mode
- **Toxicity analysis** — content safety scoring
- **Security dashboard** — threat breakdown, risk levels, event timeline

### ⚗️ Evaluation Engine
- **RAGAS metrics** — faithfulness, answer relevancy, context precision/recall
- **DeepEval metrics** — answer correctness, toxicity, bias, coherence
- **Hallucination rate** — automatic detection and trending
- **Quality scoring** — composite overall quality score per request

### 🔔 Alert System
- **Configurable thresholds** — cost, latency, error rate, hallucination rate
- **Multi-channel delivery** — in-app notifications + email
- **Severity levels** — low/medium/high/critical
- **Acknowledge workflow** — track resolution

### 🗂️ Project Management
- **Multi-project support** — isolated monitoring per application
- **API key management** — generate, rotate, revoke with RBAC
- **Environment separation** — dev/staging/production

### 🔐 Authentication & RBAC
- **JWT + Refresh tokens** — secure stateless authentication
- **4 role levels** — superadmin, admin, developer, viewer
- **API key auth** — for SDK/programmatic access
- **Audit logging** — all actions tracked

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 15, TypeScript, Tailwind CSS, ShadCN UI, Recharts, React Query |
| **Backend** | FastAPI, Python 3.12, SQLAlchemy (async), Pydantic v2 |
| **Database** | PostgreSQL (Neon) |
| **Cache** | Redis (Upstash/Railway) |
| **Vector DB** | ChromaDB |
| **LLM Primary** | Groq SDK (LLaMA 3.3 70B) |
| **LLM Secondary** | Gemini API |
| **Agent Framework** | LangGraph |
| **RAG Framework** | LangChain |
| **Evaluation** | RAGAS, DeepEval |
| **Monitoring** | OpenTelemetry |
| **Deployment** | Vercel (FE), Railway (BE), Neon (DB) |

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 15)                  │
│  Dashboard │ Logs │ Analytics │ Copilot │ Security        │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/REST
┌──────────────────────▼──────────────────────────────────┐
│                 BACKEND (FastAPI)                         │
│                                                           │
│  Auth API │ Logs API │ Analytics │ Copilot │ Evaluations  │
│                                                           │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │  LangGraph  │  │   LangChain  │  │  RAGAS/DeepEval │  │
│  │   Copilot   │  │  RAG Pipeline│  │    Evaluator    │  │
│  └─────────────┘  └──────────────┘  └─────────────────┘  │
│                                                           │
│  ┌─────────────────────┐  ┌───────────────────────────┐  │
│  │  Security Detector  │  │   Cost Calculator         │  │
│  │  (Injection/Tox)    │  │   (All Providers)         │  │
│  └─────────────────────┘  └───────────────────────────┘  │
└──────┬──────────┬─────────────┬────────────────────────┘
       │          │             │
┌──────▼──┐  ┌────▼────┐  ┌────▼────┐
│  Neon   │  │  Redis  │  │ChromaDB │
│ Postgres│  │  Cache  │  │ Vector  │
└─────────┘  └─────────┘  └─────────┘
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker & Docker Compose (recommended)
- PostgreSQL (or Neon account)
- Redis
- Groq API key (free at console.groq.com)

### 1. Clone & Setup

```bash
git clone https://github.com/yourname/llmops-platform
cd llmops-platform
```

### 2. Backend Setup

```bash
cd backend
cp .env.example .env
# Edit .env with your API keys and database URL

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend
cp .env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

npm install
npm run dev
```

### 4. Or use Docker Compose

```bash
# From project root
cp backend/.env.example backend/.env
# Edit backend/.env

docker-compose up --build
```

**Access:**
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

**Default credentials:** `admin@llmops.dev` / `Admin@1234`

---

## 🚀 Deployment

### Backend → Railway

1. Create a Railway project
2. Connect your repo
3. Set environment variables from `backend/.env.example`
4. Railway auto-detects the Dockerfile

### Frontend → Vercel

```bash
cd frontend
npx vercel --prod
# Set NEXT_PUBLIC_API_URL to your Railway backend URL
```

### Database → Neon

1. Create a Neon account at neon.tech
2. Create a project and copy the connection string
3. Set `DATABASE_URL=postgresql+asyncpg://...` in backend `.env`

---

## 🔧 SDK Usage

```bash
pip install llmops-sdk
```

```python
from llmops_sdk import LLMOpsMonitor

monitor = LLMOpsMonitor(
    api_key="llm_your_api_key",
    project_id="your-project-id",
    base_url="https://your-backend.railway.app/api/v1"
)

# Simple tracking
monitor.track(
    prompt="What is quantum computing?",
    response="Quantum computing uses qubits...",
    model="llama-3.3-70b-versatile",
    provider="groq",
    tokens=1250,
    cost=0.000738,
    latency_ms=892
)

# Auto-track with context manager
with monitor.trace(prompt="Hello", model="llama-3.3-70b-versatile") as ctx:
    response = groq_client.chat.completions.create(...)
    ctx.set_response(response.choices[0].message.content)
    ctx.set_tokens(total=response.usage.total_tokens)

# Auto-wrap Groq client
tracked_groq = monitor.groq_wrapper(groq_client)
response = tracked_groq.chat.completions.create(  # auto-tracked!
    messages=[{"role": "user", "content": "Hi!"}],
    model="llama-3.3-70b-versatile"
)
```

---

## 📚 API Documentation

Full OpenAPI docs available at `/docs` when running.

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register user |
| POST | `/api/v1/auth/login` | Login → JWT tokens |
| POST | `/api/v1/logs/track` | Ingest LLM request (SDK) |
| GET | `/api/v1/analytics/overview` | Dashboard KPIs |
| GET | `/api/v1/analytics/timeseries` | Time-series charts |
| GET | `/api/v1/analytics/models` | Per-model stats |
| POST | `/api/v1/copilot/chat` | AI Copilot query |
| POST | `/api/v1/evaluations/` | Run RAGAS+DeepEval |
| GET | `/api/v1/security/events` | Security events |
| GET | `/api/v1/security/stats` | Threat dashboard |
| POST | `/api/v1/alerts/` | Create alert |
| POST | `/api/v1/feedback/` | Submit rating |

---

## 🔑 Environment Variables

### Backend

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection (asyncpg) | ✅ |
| `REDIS_URL` | Redis connection URL | ✅ |
| `SECRET_KEY` | JWT signing secret (64+ chars) | ✅ |
| `GROQ_API_KEY` | Groq API key | ✅ |
| `GEMINI_API_KEY` | Gemini API key | Optional |
| `ALLOWED_ORIGINS` | CORS origins JSON array | ✅ |

### Frontend

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | ✅ |

---

## 📁 Project Structure

```
llmops-platform/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry
│   │   ├── core/                # Config, DB, security, deps
│   │   ├── api/v1/endpoints/    # All API routes
│   │   ├── db/models/           # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── agents/              # LangGraph copilot
│   │   ├── rag/                 # ChromaDB + LangChain
│   │   ├── evaluation/          # RAGAS + DeepEval
│   │   ├── security/            # Injection/toxicity detection
│   │   └── monitoring/          # Cost calculator, telemetry
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js 15 App Router
│   │   │   ├── auth/            # Login/register pages
│   │   │   └── dashboard/       # All dashboard pages
│   │   ├── components/          # Reusable components
│   │   ├── lib/                 # API client, utilities
│   │   └── store/               # Zustand state
│   └── package.json
├── sdk/
│   ├── llmops_sdk/              # Python SDK
│   └── examples.py
├── docker-compose.yml
└── README.md
```

---

## 🎓 Resume Description

**LLMOps Monitoring Platform** | Full-Stack GenAI Capstone Project  
*Python · FastAPI · Next.js · PostgreSQL · Redis · ChromaDB · LangGraph · RAGAS*

Built a production-grade LLM observability platform from scratch with:
- **FastAPI backend** with async SQLAlchemy, JWT auth, RBAC, rate limiting
- **Next.js 15 frontend** with real-time analytics dashboard (Recharts)
- **LangGraph AI Copilot** agent that analyzes monitoring data and generates insights
- **RAG pipeline** using ChromaDB + LangChain for semantic knowledge base search
- **RAGAS + DeepEval** evaluation pipeline for hallucination and quality scoring
- **Security layer** detecting prompt injection and jailbreak attempts
- **Python SDK** with auto-tracking, context managers, and Groq wrapper
- Deployed on **Vercel + Railway + Neon** with Docker containerization

---

## 📄 License

MIT License — free for commercial and personal use.

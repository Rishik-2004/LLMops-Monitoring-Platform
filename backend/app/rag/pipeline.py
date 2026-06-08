"""
RAG Pipeline - ChromaDB + LangChain for knowledge base search
"""

import os
import structlog
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = structlog.get_logger()


MONITORING_DOCS = [
    {
        "id": "doc_001",
        "title": "LLM Token Usage Best Practices",
        "content": """Token usage optimization is critical for controlling LLM API costs. 
        Strategies include: prompt compression using summarization, few-shot example selection, 
        context window management, and model selection based on task complexity. 
        Use smaller models (llama-3.1-8b) for simple classification tasks and larger models 
        (llama-3.3-70b) only for complex reasoning. Track token usage per project and set budget alerts.""",
        "category": "cost_optimization",
    },
    {
        "id": "doc_002", 
        "title": "Hallucination Detection and Mitigation",
        "content": """Hallucination in LLMs occurs when models generate factually incorrect information. 
        Detection methods include: faithfulness scoring using RAGAS, factual consistency checking, 
        retrieval-augmented generation (RAG) to ground responses in source documents.
        Mitigation strategies: use RAG pipelines, implement fact-checking layers, 
        add uncertainty quantification, use chain-of-thought prompting for reasoning transparency.
        Set hallucination rate thresholds and alert when exceeded (recommended: alert at >15% rate).""",
        "category": "quality",
    },
    {
        "id": "doc_003",
        "title": "Prompt Injection Defense",
        "content": """Prompt injection attacks attempt to override system instructions or extract sensitive data.
        Types include: direct injection (malicious content in user input), indirect injection (via external data),
        jailbreak attempts, and system prompt extraction.
        Defense strategies: input validation and sanitization, prompt hardening with defensive instructions,
        output monitoring for sensitive data leakage, rate limiting suspicious requests,
        and using a separate safety classification layer before processing.""",
        "category": "security",
    },
    {
        "id": "doc_004",
        "title": "Latency Optimization for LLM APIs",
        "content": """LLM API latency can be optimized through multiple strategies:
        1. Model selection: Groq provides ultra-low latency inference (typically <500ms for 70B models)
        2. Streaming responses: use streaming to improve perceived latency
        3. Caching: implement semantic caching for similar queries
        4. Request batching: batch similar requests where possible
        5. Async processing: use async patterns for non-blocking calls
        Monitor P95 and P99 latency, not just averages. Set alerts at P95 > 3000ms.""",
        "category": "performance",
    },
    {
        "id": "doc_005",
        "title": "Cost Management for LLM Applications",
        "content": """LLM API costs scale with token usage. Cost optimization strategies:
        1. Model routing: use smaller, cheaper models for simple tasks
        2. Prompt optimization: reduce prompt length without losing quality
        3. Response caching: cache identical or similar queries
        4. Budget alerts: set daily and monthly cost alerts
        5. Usage analytics: identify high-cost prompts and optimize them
        6. Batch processing: use batch APIs where available for 50% cost reduction
        Track cost per request, per model, per project, and per user.""",
        "category": "cost",
    },
    {
        "id": "doc_006",
        "title": "LLM Evaluation Metrics Guide",
        "content": """Key evaluation metrics for LLM applications:
        RAGAS Metrics: Faithfulness (factual consistency), Answer Relevancy, Context Precision, Context Recall
        DeepEval Metrics: Answer Correctness, Toxicity, Bias, Coherence, Hallucination
        Performance Metrics: Latency (P50/P95/P99), Throughput (requests/sec), Error Rate, Availability
        Business Metrics: User satisfaction score, Task completion rate, Cost efficiency
        Run evaluations on a sample of production traffic (5-10%) and on dedicated test sets.
        Track metric trends over time to detect model degradation.""",
        "category": "evaluation",
    },
    {
        "id": "doc_007",
        "title": "Alert Configuration Guide",
        "content": """Configure alerts to proactively detect issues:
        Cost Alerts: daily budget >$10, monthly budget >$100, cost per request >$0.01
        Latency Alerts: P95 >3000ms, P99 >5000ms
        Error Rate Alerts: error rate >5% in 5-minute window
        Hallucination Alerts: rate >15% in last 100 requests
        Security Alerts: prompt injection score >0.7, toxicity score >0.6
        Availability Alerts: success rate <95%
        Configure notification channels: email, Slack, PagerDuty, webhooks.
        Use escalation policies for critical alerts.""",
        "category": "alerting",
    },
    {
        "id": "doc_008",
        "title": "Model Benchmarking and Selection",
        "content": """Model selection should be based on benchmarking across key dimensions:
        Speed: Groq Llama-3.3-70b is typically the fastest for large models
        Cost: Groq and Gemini Flash are most cost-efficient
        Quality: Evaluated on task-specific benchmarks (coding, reasoning, instruction-following)
        Safety: Toxicity, bias, harmful content generation rates
        Context Length: For long documents, use models with 128K+ context
        Benchmarking methodology: use consistent test sets, measure across multiple runs,
        include real-world task distribution. Update benchmarks quarterly.""",
        "category": "models",
    },
]


class RAGPipeline:
    """RAG pipeline for monitoring knowledge base"""
    
    def __init__(self):
        self.collection = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize ChromaDB and load documents"""
        if self._initialized:
            return
        
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            
            client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIRECTORY,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            
            self.collection = client.get_or_create_collection(
                name="monitoring_knowledge_base",
                metadata={"description": "LLMOps monitoring documentation"},
            )
            
            # Check if already populated
            if self.collection.count() < len(MONITORING_DOCS):
                await self._populate_knowledge_base()
            
            self._initialized = True
            logger.info("RAG pipeline initialized", doc_count=self.collection.count())
            
        except Exception as e:
            logger.warning("ChromaDB initialization failed", error=str(e))
            self._initialized = False
    
    async def _populate_knowledge_base(self):
        """Load monitoring documentation into ChromaDB"""
        if not self.collection:
            return
        
        # Clear and reload
        existing_ids = [doc["id"] for doc in MONITORING_DOCS]
        try:
            self.collection.delete(ids=existing_ids)
        except Exception:
            pass
        
        self.collection.add(
            ids=[doc["id"] for doc in MONITORING_DOCS],
            documents=[doc["content"] for doc in MONITORING_DOCS],
            metadatas=[{"title": doc["title"], "category": doc["category"]} for doc in MONITORING_DOCS],
        )
        
        logger.info("Knowledge base populated", count=len(MONITORING_DOCS))
    
    async def search(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Semantic search in knowledge base"""
        if not self._initialized:
            await self.initialize()
        
        if not self.collection:
            return self._fallback_search(query)
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results, self.collection.count()),
            )
            
            docs = []
            for i, (doc_id, document, metadata, distance) in enumerate(zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )):
                docs.append({
                    "id": doc_id,
                    "content": document,
                    "title": metadata.get("title", ""),
                    "category": metadata.get("category", ""),
                    "relevance_score": round(1 - distance, 4),
                })
            
            return docs
        except Exception as e:
            logger.error("RAG search failed", error=str(e))
            return self._fallback_search(query)
    
    def _fallback_search(self, query: str) -> List[Dict[str, Any]]:
        """Keyword-based fallback search"""
        query_lower = query.lower()
        results = []
        
        for doc in MONITORING_DOCS:
            score = 0
            if any(word in doc["content"].lower() for word in query_lower.split()):
                score += 0.5
            if any(word in doc["title"].lower() for word in query_lower.split()):
                score += 0.3
            if doc["category"] in query_lower:
                score += 0.2
            
            if score > 0:
                results.append({**doc, "relevance_score": round(score, 4)})
        
        return sorted(results, key=lambda x: x["relevance_score"], reverse=True)[:3]


# Singleton instance
rag_pipeline = RAGPipeline()

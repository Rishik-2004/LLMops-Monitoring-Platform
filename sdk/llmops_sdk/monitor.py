"""
LLMOps Monitoring SDK
Lightweight Python client for tracking LLM requests
"""

import time
import httpx
import asyncio
import threading
import queue
import logging
from typing import Optional, Dict, Any, Callable
from functools import wraps
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict

__version__ = "1.0.0"
logger = logging.getLogger("llmops_sdk")


@dataclass
class TrackPayload:
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
    metadata: Optional[Dict[str, Any]] = None


class LLMOpsMonitor:
    """
    LLMOps Monitoring SDK Client
    
    Usage:
        monitor = LLMOpsMonitor(
            api_key="llm_your_api_key",
            project_id="your-project-id",
            base_url="https://your-llmops-backend.railway.app"
        )
        
        # Simple tracking
        monitor.track(
            prompt="What is the capital of France?",
            response="The capital of France is Paris.",
            model="llama-3.3-70b-versatile",
            provider="groq",
            tokens=150,
            cost=0.00009,
            latency_ms=342
        )
        
        # Context manager (auto-tracks latency)
        with monitor.trace(prompt="Hello", model="llama-3.3-70b") as ctx:
            response = groq_client.chat(...)
            ctx.set_response(response.choices[0].message.content)
            ctx.set_tokens(response.usage.total_tokens)
    """

    def __init__(
        self,
        api_key: str,
        project_id: str,
        base_url: str = "http://localhost:8000/api/v1",
        async_mode: bool = True,
        batch_size: int = 10,
        flush_interval: float = 5.0,
        timeout: float = 10.0,
        debug: bool = False,
    ):
        self.api_key = api_key
        self.project_id = project_id
        self.base_url = base_url.rstrip("/")
        self.async_mode = async_mode
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.timeout = timeout
        
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        
        self._queue: queue.Queue = queue.Queue()
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"X-API-Key": self.api_key},
            timeout=self.timeout,
        )
        
        if async_mode:
            self._start_background_worker()

    def _start_background_worker(self):
        """Start background thread for async batched sending"""
        self._worker_thread = threading.Thread(
            target=self._worker_loop, daemon=True
        )
        self._worker_thread.start()

    def _worker_loop(self):
        """Background worker that flushes the queue periodically"""
        batch = []
        last_flush = time.time()

        while True:
            try:
                item = self._queue.get(timeout=0.1)
                batch.append(item)
                if len(batch) >= self.batch_size:
                    self._send_batch(batch)
                    batch = []
                    last_flush = time.time()
            except queue.Empty:
                if batch and (time.time() - last_flush) >= self.flush_interval:
                    self._send_batch(batch)
                    batch = []
                    last_flush = time.time()

    def _send_batch(self, batch: list):
        """Send a batch of tracking events"""
        for payload in batch:
            try:
                self._send_single(payload)
            except Exception as e:
                logger.debug(f"Failed to send tracking event: {e}")

    def _send_single(self, payload: TrackPayload):
        """Send a single tracking event to the API"""
        data = asdict(payload)
        data = {k: v for k, v in data.items() if v is not None}
        
        response = self._client.post("/logs/track", json=data)
        response.raise_for_status()
        logger.debug(f"Tracked: {response.json()}")

    def track(
        self,
        prompt: str,
        response: str,
        model: str,
        provider: str = "groq",
        system_prompt: Optional[str] = None,
        session_id: Optional[str] = None,
        tokens: int = 0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        cost: float = 0.0,
        latency_ms: float = 0.0,
        status: str = "success",
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Track an LLM request/response pair.
        
        Args:
            prompt: The user prompt sent to the LLM
            response: The LLM's response
            model: Model name (e.g. "llama-3.3-70b-versatile")
            provider: Provider name (groq, gemini, openai, anthropic)
            tokens: Total tokens used (shorthand for total_tokens)
            cost: Estimated cost in USD
            latency_ms: Response latency in milliseconds
            
        Returns:
            log_id if sync mode, None if async
        """
        payload = TrackPayload(
            project_id=self.project_id,
            prompt=prompt,
            response=response,
            model=model,
            provider=provider,
            system_prompt=system_prompt,
            session_id=session_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=tokens or prompt_tokens + completion_tokens,
            cost=cost,
            latency_ms=latency_ms,
            status=status,
            error_type=error_type,
            error_message=error_message,
            tags=tags,
            metadata=metadata,
        )
        
        if self.async_mode:
            self._queue.put(payload)
            return None
        else:
            try:
                self._send_single(payload)
            except Exception as e:
                logger.warning(f"Tracking failed: {e}")
            return None

    def track_error(
        self,
        prompt: str,
        model: str,
        provider: str,
        error_type: str,
        error_message: str,
        latency_ms: float = 0.0,
    ):
        """Track a failed LLM request"""
        self.track(
            prompt=prompt,
            response="",
            model=model,
            provider=provider,
            latency_ms=latency_ms,
            status="error",
            error_type=error_type,
            error_message=error_message,
        )

    def trace(self, prompt: str, model: str, provider: str = "groq", **kwargs):
        """Context manager for automatic latency tracking"""
        return TraceContext(self, prompt=prompt, model=model, provider=provider, **kwargs)

    def groq_wrapper(self, client, model: str = "llama-3.3-70b-versatile"):
        """Wrap Groq client to auto-track all calls"""
        return GroqWrapper(client, self, model)

    def flush(self):
        """Flush all pending events synchronously"""
        while not self._queue.empty():
            try:
                item = self._queue.get_nowait()
                self._send_single(item)
            except Exception as e:
                logger.debug(f"Flush error: {e}")

    def __del__(self):
        try:
            self.flush()
            self._client.close()
        except Exception:
            pass


class TraceContext:
    """Context manager for automatic latency and error tracking"""

    def __init__(self, monitor: LLMOpsMonitor, prompt: str, model: str, provider: str, **kwargs):
        self.monitor = monitor
        self.prompt = prompt
        self.model = model
        self.provider = provider
        self.kwargs = kwargs
        self._response = ""
        self._tokens = 0
        self._prompt_tokens = 0
        self._completion_tokens = 0
        self._cost = 0.0
        self._start = 0.0

    def __enter__(self):
        self._start = time.time()
        return self

    def set_response(self, response: str):
        self._response = response

    def set_tokens(self, total: int = 0, prompt: int = 0, completion: int = 0):
        self._tokens = total
        self._prompt_tokens = prompt
        self._completion_tokens = completion

    def set_cost(self, cost: float):
        self._cost = cost

    def __exit__(self, exc_type, exc_val, exc_tb):
        latency_ms = (time.time() - self._start) * 1000
        
        if exc_type:
            self.monitor.track_error(
                prompt=self.prompt,
                model=self.model,
                provider=self.provider,
                error_type=exc_type.__name__,
                error_message=str(exc_val),
                latency_ms=latency_ms,
            )
        else:
            self.monitor.track(
                prompt=self.prompt,
                response=self._response,
                model=self.model,
                provider=self.provider,
                tokens=self._tokens,
                prompt_tokens=self._prompt_tokens,
                completion_tokens=self._completion_tokens,
                cost=self._cost,
                latency_ms=latency_ms,
                **self.kwargs,
            )
        return False  # Don't suppress exceptions


class GroqWrapper:
    """Auto-tracking wrapper around Groq client"""

    def __init__(self, client, monitor: LLMOpsMonitor, default_model: str):
        self._client = client
        self._monitor = monitor
        self._default_model = default_model

    @property
    def chat(self):
        return self

    @property
    def completions(self):
        return self

    def create(self, messages: list, model: Optional[str] = None, **kwargs):
        """Wrapped chat.completions.create with auto-tracking"""
        model = model or self._default_model
        prompt = "\n".join(
            f"{m['role']}: {m['content']}" for m in messages if m["role"] == "user"
        )
        system = next((m["content"] for m in messages if m["role"] == "system"), None)

        start = time.time()
        try:
            result = self._client.chat.completions.create(
                messages=messages, model=model, **kwargs
            )
            latency_ms = (time.time() - start) * 1000
            
            response_text = result.choices[0].message.content if result.choices else ""
            usage = result.usage if hasattr(result, "usage") else None
            
            self._monitor.track(
                prompt=prompt,
                response=response_text,
                model=model,
                provider="groq",
                system_prompt=system,
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                tokens=usage.total_tokens if usage else 0,
                latency_ms=latency_ms,
            )
            return result
        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            self._monitor.track_error(
                prompt=prompt,
                model=model,
                provider="groq",
                error_type=type(e).__name__,
                error_message=str(e),
                latency_ms=latency_ms,
            )
            raise


def monitor(
    api_key: str,
    project_id: str,
    base_url: str = "http://localhost:8000/api/v1",
) -> LLMOpsMonitor:
    """Convenience factory to create a monitor instance"""
    return LLMOpsMonitor(api_key=api_key, project_id=project_id, base_url=base_url)

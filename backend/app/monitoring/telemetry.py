"""
OpenTelemetry instrumentation setup
"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    FASTAPI_INSTRUMENTATION_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    FastAPIInstrumentor = None
    FASTAPI_INSTRUMENTATION_AVAILABLE = False
import structlog

from app.core.config import settings

logger = structlog.get_logger()


def setup_telemetry():
    """Initialize OpenTelemetry tracing"""
    resource = Resource.create({
        "service.name": settings.OTEL_SERVICE_NAME,
        "service.version": settings.APP_VERSION,
        "deployment.environment": settings.ENVIRONMENT,
    })
    
    provider = TracerProvider(resource=resource)
    
    # Export to console in debug mode
    if settings.DEBUG:
        provider.add_span_processor(
            BatchSpanProcessor(ConsoleSpanExporter())
        )
    
    # Export to OTLP endpoint if configured
    if settings.OTEL_EXPORTER_ENDPOINT:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            otlp_exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_ENDPOINT)
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logger.info("OTLP exporter configured", endpoint=settings.OTEL_EXPORTER_ENDPOINT)
        except Exception as e:
            logger.warning("Failed to setup OTLP exporter", error=str(e))
    
    trace.set_tracer_provider(provider)
    logger.info("OpenTelemetry initialized", service=settings.OTEL_SERVICE_NAME)


def get_tracer(name: str = "llmops"):
    """Get a tracer instance"""
    return trace.get_tracer(name)


class LLMSpanRecorder:
    """Record LLM call spans for distributed tracing"""
    
    def __init__(self):
        self.tracer = get_tracer()
    
    def record_llm_call(self, model: str, provider: str, tokens: int, cost: float, latency_ms: float):
        """Record an LLM call as a span"""
        with self.tracer.start_as_current_span("llm.completion") as span:
            span.set_attribute("llm.model", model)
            span.set_attribute("llm.provider", provider)
            span.set_attribute("llm.tokens.total", tokens)
            span.set_attribute("llm.cost.usd", cost)
            span.set_attribute("llm.latency.ms", latency_ms)

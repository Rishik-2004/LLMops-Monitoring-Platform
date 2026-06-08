"""
LLM Cost Calculator - pricing per model/provider
"""

from typing import Optional


# Pricing in USD per 1M tokens (as of 2024)
MODEL_PRICING = {
    # Groq models
    "groq": {
        "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
        "llama-3.1-70b-versatile": {"input": 0.59, "output": 0.79},
        "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
        "llama3-8b-8192": {"input": 0.05, "output": 0.08},
        "llama3-70b-8192": {"input": 0.59, "output": 0.79},
        "mixtral-8x7b-32768": {"input": 0.24, "output": 0.24},
        "gemma-7b-it": {"input": 0.07, "output": 0.07},
        "gemma2-9b-it": {"input": 0.20, "output": 0.20},
    },
    # Gemini models
    "gemini": {
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
        "gemini-1.5-flash-8b": {"input": 0.0375, "output": 0.15},
        "gemini-1.5-pro": {"input": 3.50, "output": 10.50},
        "gemini-2.0-flash-exp": {"input": 0.075, "output": 0.30},
    },
    # OpenAI models
    "openai": {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    },
    # Anthropic models
    "anthropic": {
        "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
        "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
        "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
    },
}


class CostCalculator:
    """Calculate estimated costs for LLM API calls"""

    def calculate(
        self,
        model: str,
        provider: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """Calculate cost in USD"""
        provider = provider.lower()
        model = model.lower()
        
        provider_pricing = MODEL_PRICING.get(provider, {})
        model_pricing = provider_pricing.get(model)
        
        if not model_pricing:
            # Try to find a partial match
            for m_name, m_pricing in provider_pricing.items():
                if model in m_name or m_name in model:
                    model_pricing = m_pricing
                    break
        
        if not model_pricing:
            # Default fallback pricing
            model_pricing = {"input": 0.50, "output": 1.50}
        
        input_cost = (prompt_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * model_pricing["output"]
        
        return round(input_cost + output_cost, 8)

    def get_pricing_table(self) -> dict:
        """Get full pricing table"""
        return MODEL_PRICING

    def estimate_batch_cost(
        self,
        model: str,
        provider: str,
        requests: int,
        avg_prompt_tokens: int = 500,
        avg_completion_tokens: int = 200,
    ) -> dict:
        """Estimate cost for a batch of requests"""
        per_request = self.calculate(model, provider, avg_prompt_tokens, avg_completion_tokens)
        total = per_request * requests
        return {
            "per_request": round(per_request, 8),
            "total": round(total, 4),
            "daily_at_rate": round(total, 4),
            "monthly_estimate": round(total * 30, 2),
        }

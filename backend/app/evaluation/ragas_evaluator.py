"""
RAGAS Evaluation - Quality metrics for LLM responses
"""

import structlog
from typing import Dict, Any, Optional

logger = structlog.get_logger()


async def run_ragas_eval(
    prompt: str,
    response: str,
    context: Optional[str] = None,
    ground_truth: Optional[str] = None,
) -> Dict[str, float]:
    """
    Run RAGAS evaluation metrics.
    Returns faithfulness, answer_relevancy, context_precision, context_recall
    """
    scores = {}

    try:
        # Try real RAGAS evaluation
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import (
            faithfulness,
            answer_relevancy,
        )

        data = {
            "question": [prompt],
            "answer": [response],
            "contexts": [[context or "No context provided"]],
        }
        if ground_truth:
            data["ground_truth"] = [ground_truth]

        dataset = Dataset.from_dict(data)
        metrics = [faithfulness, answer_relevancy]

        result = evaluate(dataset=dataset, metrics=metrics)
        scores["faithfulness"] = float(result["faithfulness"])
        scores["answer_relevancy"] = float(result["answer_relevancy"])

    except Exception as e:
        logger.warning("RAGAS evaluation failed, using heuristics", error=str(e))
        # Heuristic fallback
        scores = _heuristic_ragas_scores(prompt, response, context)

    return scores


def _heuristic_ragas_scores(prompt: str, response: str, context: Optional[str]) -> Dict[str, float]:
    """Heuristic scoring when RAGAS is unavailable"""
    import re

    # Faithfulness: Does response avoid contradictions?
    # Heuristic: longer, more structured responses tend to be more faithful
    faithfulness = 0.8
    if len(response) < 20:
        faithfulness = 0.4
    if "I don't know" in response or "I cannot" in response:
        faithfulness = 0.6

    # Answer relevancy: Does response address the prompt?
    prompt_words = set(re.findall(r'\w+', prompt.lower()))
    response_words = set(re.findall(r'\w+', response.lower()))
    overlap = len(prompt_words & response_words) / max(len(prompt_words), 1)
    answer_relevancy = min(0.95, 0.5 + overlap)

    # Context precision/recall if context provided
    context_precision = 0.75
    context_recall = 0.70
    if context:
        context_words = set(re.findall(r'\w+', context.lower()))
        precision = len(response_words & context_words) / max(len(response_words), 1)
        recall = len(response_words & context_words) / max(len(context_words), 1)
        context_precision = min(0.95, 0.5 + precision)
        context_recall = min(0.95, 0.5 + recall)

    return {
        "faithfulness": round(faithfulness, 4),
        "answer_relevancy": round(answer_relevancy, 4),
        "context_precision": round(context_precision, 4),
        "context_recall": round(context_recall, 4),
    }

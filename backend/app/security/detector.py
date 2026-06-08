"""
Security detection: prompt injection, toxicity, jailbreak detection
"""

import re
import structlog
from typing import Dict, Any
from app.core.config import settings

logger = structlog.get_logger()


# Injection patterns
INJECTION_PATTERNS = [
    r"ignore (all |previous |prior )?instructions",
    r"disregard (all |your |previous )?instructions",
    r"forget (all |your |previous )?instructions",
    r"you are now",
    r"new (role|persona|character|instructions)",
    r"pretend (you are|to be)",
    r"act as (a |an |if you are)",
    r"roleplay as",
    r"simulate being",
    r"jailbreak",
    r"DAN (mode|prompt)",
    r"developer mode",
    r"bypass (your |all )?(filters|restrictions|safety)",
    r"override (your |all )?(rules|guidelines|safety)",
    r"reveal (your |the )?(system prompt|instructions|prompt)",
    r"print (your |the )?(system prompt|instructions)",
    r"what (is|are) (your |the )?(system prompt|instructions)",
    r"sudo ",
    r"--[a-z]+",  # command-line style injection
    r"<\|.*?\|>",  # token injection
    r"\{.*?system.*?\}",  # template injection
]

# Toxicity patterns (simplified - production would use a model)
TOXICITY_PATTERNS = [
    r"\b(hate|kill|murder|harm|attack|destroy|rape|assault)\b",
    r"\b(racist|sexist|bigot|slur)\b",
    r"\b(bomb|weapon|explosive|poison|drug synthesis)\b",
    r"\b(suicide|self-harm|self harm)\b",
]

# Compiled patterns
_injection_compiled = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]
_toxicity_compiled = [re.compile(p, re.IGNORECASE) for p in TOXICITY_PATTERNS]


class SecurityDetector:
    """Analyze prompts and responses for security threats"""

    async def analyze(self, prompt: str, response: str = "") -> Dict[str, Any]:
        """Run all security checks and return scores"""
        injection_score = self._detect_injection(prompt)
        toxicity_score = self._detect_toxicity(prompt + " " + response)
        
        is_flagged = (
            injection_score >= settings.INJECTION_THRESHOLD
            or toxicity_score >= settings.TOXICITY_THRESHOLD
        )
        
        flag_reason = None
        if is_flagged:
            reasons = []
            if injection_score >= settings.INJECTION_THRESHOLD:
                reasons.append(f"Potential prompt injection (score: {injection_score:.2f})")
            if toxicity_score >= settings.TOXICITY_THRESHOLD:
                reasons.append(f"Toxic content detected (score: {toxicity_score:.2f})")
            flag_reason = "; ".join(reasons)

        result = {
            "injection_score": round(injection_score, 3),
            "toxicity_score": round(toxicity_score, 3),
            "is_flagged": is_flagged,
            "flag_reason": flag_reason,
            "threat_type": self._classify_threat(injection_score, toxicity_score),
        }
        
        if is_flagged:
            logger.warning("Security threat detected", **result)
        
        return result

    def _detect_injection(self, text: str) -> float:
        """Detect prompt injection attempts, return score 0-1"""
        if not text:
            return 0.0
        
        matches = 0
        for pattern in _injection_compiled:
            if pattern.search(text):
                matches += 1
        
        # Score based on number of pattern matches
        score = min(1.0, matches * 0.25)
        
        # Additional heuristics
        if len(text) > 5000:  # Very long prompts suspicious
            score = min(1.0, score + 0.1)
        
        # Check for system-level language
        if any(kw in text.lower() for kw in ["system:", "[system]", "###instruction", "<<sys>>"]):
            score = min(1.0, score + 0.3)
        
        return score

    def _detect_toxicity(self, text: str) -> float:
        """Detect toxic content, return score 0-1"""
        if not text:
            return 0.0
        
        matches = 0
        for pattern in _toxicity_compiled:
            if pattern.search(text):
                matches += 1
        
        return min(1.0, matches * 0.3)

    def _classify_threat(self, injection_score: float, toxicity_score: float) -> str:
        """Classify the type of threat"""
        if injection_score > 0.7:
            return "prompt_injection"
        elif injection_score > 0.4:
            return "jailbreak"
        elif toxicity_score > 0.6:
            return "toxicity"
        elif injection_score > 0.2 or toxicity_score > 0.2:
            return "suspicious"
        return "clean"

    def get_injection_details(self, text: str) -> Dict[str, Any]:
        """Get detailed injection analysis"""
        matched_patterns = []
        for i, pattern in enumerate(_injection_compiled):
            if pattern.search(text):
                matched_patterns.append(INJECTION_PATTERNS[i])
        
        return {
            "matched_patterns": matched_patterns,
            "match_count": len(matched_patterns),
            "score": self._detect_injection(text),
        }

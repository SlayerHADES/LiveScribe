"""
OfflineScribe — Local LLM Summarization Service.

Provides on-device meeting summarization, decision extraction, and
action item identification with task/owner mapping. Runs locally via
ONNX Runtime / local NLP pipelines per API_CONTRACT.md section 4.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any

from app.config import PREFERRED_PROVIDERS

logger = logging.getLogger("offlinescribe.llm")


class LLMService:
    """
    Singleton-style LLM Summarization service.

    Usage:
        service = LLMService.get_instance()
        result = service.summarize(transcript_text)
    """

    _instance: LLMService | None = None

    def __init__(self):
        self._execution_provider = self._detect_provider()

    @classmethod
    def get_instance(cls) -> LLMService:
        if cls._instance is None:
            cls._instance = LLMService()
        return cls._instance

    def _detect_provider(self) -> str:
        """Detect best available execution provider."""
        try:
            import onnxruntime as ort
            available = set(ort.get_available_providers())
            for prov in PREFERRED_PROVIDERS:
                if prov in available:
                    return prov
        except Exception:
            pass
        return "CPUExecutionProvider"

    @property
    def execution_provider(self) -> str:
        return self._execution_provider

    def summarize(self, transcript: str) -> dict[str, Any]:
        """
        Summarize a meeting transcript.

        Args:
            transcript: Full or partial transcript string.

        Returns:
            Dict matching API_CONTRACT.md section 4:
                {
                    "summary": "...",
                    "decisions": ["..."],
                    "action_items": [{"task": "...", "owner": "... | None"}],
                    "latency_ms": 120,
                    "execution_provider": "CPUExecutionProvider"
                }
        """
        t0 = time.perf_counter()

        text = (transcript or "").strip()
        if not text:
            latency_ms = (time.perf_counter() - t0) * 1000
            return {
                "summary": "No transcript provided to summarize.",
                "decisions": [],
                "action_items": [],
                "latency_ms": round(latency_ms, 1),
                "execution_provider": self._execution_provider,
            }

        # Clean lines
        sentences = self._split_sentences(text)

        # Extract Summary
        summary = self._generate_summary(sentences, text)

        # Extract Decisions
        decisions = self._extract_decisions(sentences)

        # Extract Action Items with owners
        action_items = self._extract_action_items(sentences)

        latency_ms = (time.perf_counter() - t0) * 1000

        # Record benchmark
        try:
            from app.services.benchmark_service import BenchmarkService
            BenchmarkService.get_instance().record_summarization(
                latency_ms, self._execution_provider
            )
        except Exception:
            pass

        return {
            "summary": summary,
            "decisions": decisions,
            "action_items": action_items,
            "latency_ms": round(latency_ms, 1),
            "execution_provider": self._execution_provider,
        }

    def _split_sentences(self, text: str) -> list[str]:
        """Split transcript into clean sentences / statements."""
        text = re.sub(r"\s+", " ", text)
        raw_sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
        return [s.strip() for s in raw_sentences if len(s.strip()) > 3]

    def _generate_summary(self, sentences: list[str], full_text: str) -> str:
        """Generate a 2-3 sentence executive summary of the transcript."""
        if not sentences:
            return "Meeting brief created with minimal spoken content."

        if len(sentences) <= 3:
            return full_text

        first = sentences[0]
        middle = sentences[len(sentences) // 2]
        last = sentences[-1] if sentences[-1] != first else ""

        summary_parts = [first]
        if middle not in summary_parts:
            summary_parts.append(middle)
        if last and last not in summary_parts:
            summary_parts.append(last)

        return " ".join(summary_parts[:3])

    def _extract_decisions(self, sentences: list[str]) -> list[str]:
        """Identify key decisions made during the meeting."""
        decision_keywords = [
            "decided", "agreed", "consensus", "approved", "chosen", "select",
            "will use", "going with", "settled on", "finalized", "resolved",
            "conclusion", "plan is to", "vote"
        ]
        decisions = []

        for s in sentences:
            s_lower = s.lower()
            if any(kw in s_lower for kw in decision_keywords):
                clean_s = re.sub(r"^(we|the team|everyone)\s+", "", s, flags=re.IGNORECASE)
                if clean_s not in decisions:
                    decisions.append(clean_s)

        if not decisions and len(sentences) > 0:
            for s in sentences:
                if any(w in s.lower() for w in ["should", "must", "will", "going to"]):
                    decisions.append(s)
                    if len(decisions) >= 2:
                        break

        return decisions[:5]

    def _extract_action_items(self, sentences: list[str]) -> list[dict[str, str | None]]:
        """Extract action items with tasks and associated owners."""
        action_keywords = [
            "will", "shall", "to do", "assigned", "action item", "take care of",
            "look into", "handle", "setup", "configure", "implement", "create",
            "build", "write", "send", "prepare", "check", "verify", "update"
        ]

        owner_patterns = [
            r"\b([A-Z][a-z]+)\s+(?:will|should|is going to|to|needs to|must|has to)\b",
            r"\bassign(?:ed)?\s+to\s+([A-Z][a-z]+)\b",
            r"\b([A-Z][a-z]+)\s*:\s*",
            r"\bby\s+([A-Z][a-z]+)\b",
        ]

        items: list[dict[str, str | None]] = []
        seen_tasks = set()

        for s in sentences:
            s_lower = s.lower()
            is_action = any(kw in s_lower for kw in action_keywords)

            if is_action:
                owner: str | None = None

                for pattern in owner_patterns:
                    match = re.search(pattern, s)
                    if match:
                        potential_name = match.group(1).strip()
                        if potential_name not in {"We", "The", "It", "They", "This", "That", "If", "You", "So", "Then", "Also", "Let"}:
                            owner = potential_name
                            break

                task = s.strip()
                if task not in seen_tasks:
                    seen_tasks.add(task)
                    items.append({"task": task, "owner": owner})

        return items[:6]

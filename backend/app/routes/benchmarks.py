"""
OfflineScribe — Benchmark Panel API route.

Endpoint:
    GET /api/benchmarks

Per API_CONTRACT.md section 6:
    Response:
    {
      "transcription": [
        { "chunk_id": 14, "latency_ms": 312, "provider": "CPUExecutionProvider" }
      ],
      "summarization": [
        { "call_id": 1, "latency_ms": 1840, "provider": "CPUExecutionProvider" }
      ],
      "system": {
        "cpu_usage_pct": 12.5,
        "memory_mb": 450.2
      }
    }
"""

import logging
from typing import Any

from fastapi import APIRouter

from app.services.benchmark_service import BenchmarkService

logger = logging.getLogger("offlinescribe.benchmarks_route")

router = APIRouter()


@router.get("/api/benchmarks")
async def get_benchmarks() -> dict[str, Any]:
    """
    Returns real-time transcription and summarization latency metrics and system stats.
    """
    benchmarks = BenchmarkService.get_instance()
    return benchmarks.get_summary()

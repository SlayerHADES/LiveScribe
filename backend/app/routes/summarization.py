"""
OfflineScribe — Meeting Summarization API route.

Endpoint:
    POST /api/summarize

Per API_CONTRACT.md section 4:
    Request:  {"transcript": "..."}
    Response: {
        "summary": "...",
        "decisions": [...],
        "action_items": [{"task": "...", "owner": "... | null"}],
        "latency_ms": 1840,
        "execution_provider": "QNNExecutionProvider"
    }
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.llm_service import LLMService

logger = logging.getLogger("offlinescribe.summarization")

router = APIRouter()


class SummarizeRequest(BaseModel):
    transcript: str


class ActionItem(BaseModel):
    task: str
    owner: str | None = None


class SummarizeResponse(BaseModel):
    summary: str
    decisions: list[str]
    action_items: list[ActionItem]
    latency_ms: float
    execution_provider: str


@router.post("/api/summarize", response_model=SummarizeResponse)
async def summarize_transcript(request: SummarizeRequest) -> dict[str, Any]:
    """
    On-demand AI meeting summarization endpoint.

    Takes full or partial transcript, produces summary, decisions, and action items.
    """
    logger.info("Received summarization request (%d chars)", len(request.transcript or ""))

    try:
        service = LLMService.get_instance()
        result = service.summarize(request.transcript)
        return result
    except Exception as e:
        logger.error("Summarization endpoint failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Summarization error: {str(e)}",
        )

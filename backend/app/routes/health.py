"""
OfflineScribe — Health & NPU status routes.

Endpoints:
    GET /api/health      → { status, npu_provider }
    GET /api/npu-status  → { execution_provider, npu_confirmed, fallback_to_cpu }

Response shapes follow docs/API_CONTRACT.md sections 1 & 2 exactly.
"""

from fastapi import APIRouter

from app.services.npu_service import get_npu_status

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check():
    """Basic liveness check + which provider is active."""
    status = get_npu_status()
    return {
        "status": "ok",
        "npu_provider": status["execution_provider"],
    }


@router.get("/npu-status")
async def npu_status():
    """
    Detailed NPU verification endpoint.
    Used by the frontend to show a red/green NPU indicator.
    """
    status = get_npu_status()
    return {
        "execution_provider": status["execution_provider"],
        "npu_confirmed": status["npu_confirmed"],
        "fallback_to_cpu": status["fallback_to_cpu"],
    }

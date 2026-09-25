"""
OfflineScribe — OS Network Status route.

Endpoint:
    GET /api/network-status

Per API_CONTRACT.md section 5:
    Response: { "online": false }
"""

import logging
import socket

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger("offlinescribe.network")

router = APIRouter()


class NetworkStatusResponse(BaseModel):
    online: bool


def check_internet_connection(timeout: float = 1.0) -> bool:
    """
    Check real OS-level network connectivity by attempting a quick socket connection.

    Uses Cloudflare DNS (1.1.1.1:53) or Google DNS (8.8.8.8:53).
    """
    for host, port in [("1.1.1.1", 53), ("8.8.8.8", 53)]:
        try:
            s = socket.create_connection((host, port), timeout=timeout)
            s.close()
            return True
        except OSError:
            continue
    return False


@router.get("/api/network-status", response_model=NetworkStatusResponse)
async def get_network_status() -> dict[str, bool]:
    """
    Returns real OS-level internet connectivity status.
    """
    is_online = check_internet_connection(timeout=0.8)
    return {"online": is_online}

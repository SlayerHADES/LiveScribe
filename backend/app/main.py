"""
OfflineScribe — FastAPI application entry point.

Registers all route modules and configures CORS for the Vite dev server.
Start with:  uvicorn app.main:app --reload --port 8000
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import FRONTEND_ORIGIN
from app.routes import health

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-28s │ %(levelname)-5s │ %(message)s",
    datefmt="%H:%M:%S",
)

# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="OfflineScribe",
    description="Offline meeting transcription & summarization — on-device Whisper + LLM via Snapdragon NPU.",
    version="0.1.0",
)

# ─── CORS (allow Vite dev server) ────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routes ──────────────────────────────────────────────────────────────────
app.include_router(health.router)


@app.on_event("startup")
async def startup_event():
    """Log provider status at startup so it's visible in the console."""
    from app.services.npu_service import get_npu_status

    status = get_npu_status()
    provider = status["execution_provider"]
    npu_ok = status["npu_confirmed"]

    if npu_ok:
        logging.getLogger("offlinescribe").info(
            f"✅ NPU confirmed — using {provider}"
        )
    else:
        logging.getLogger("offlinescribe").warning(
            f"⚠️  NPU not available — falling back to {provider}"
        )

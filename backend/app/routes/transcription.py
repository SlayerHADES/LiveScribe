"""
OfflineScribe — Live transcription WebSocket route.

Endpoint:
    WS /ws/transcribe

Client sends raw audio chunks (binary, ~5s each, float32 PCM at 16 kHz).
Server responds with JSON messages per API_CONTRACT.md section 3:
    - {"type": "transcript_chunk", "text": ..., "chunk_id": ..., "latency_ms": ..., "execution_provider": ...}
    - {"type": "silence", "chunk_id": ...}
"""

import logging
import traceback

import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.whisper_service import WhisperService

logger = logging.getLogger("offlinescribe.transcription")

router = APIRouter()


@router.websocket("/ws/transcribe")
async def transcribe_stream(websocket: WebSocket):
    """
    Live transcription WebSocket endpoint.

    Protocol:
        1. Client connects
        2. Server sends a ready message
        3. Client sends binary audio chunks (float32 PCM, 16kHz, ~5s each)
        4. Server responds with transcript_chunk or silence JSON for each chunk
        5. Client disconnects when done
    """
    await websocket.accept()
    logger.info("WebSocket client connected for transcription")

    # Get the Whisper service (lazy-loads model on first use)
    whisper = WhisperService.get_instance()

    # Send a ready signal so the frontend knows we're good to go
    try:
        if not whisper.is_loaded():
            await websocket.send_json({
                "type": "status",
                "message": "Loading Whisper model, please wait...",
            })
            whisper.load()

        await websocket.send_json({
            "type": "status",
            "message": "ready",
            "execution_provider": whisper.active_provider,
        })
    except Exception as e:
        logger.error("Failed to initialize Whisper: %s", e)
        await websocket.send_json({
            "type": "error",
            "message": f"Failed to load Whisper model: {e}",
        })
        await websocket.close()
        return

    # Main transcription loop
    try:
        while True:
            # Receive binary audio data (float32 PCM at 16kHz)
            data = await websocket.receive_bytes()

            if len(data) == 0:
                continue

            # Convert bytes to numpy float32 array
            try:
                audio = np.frombuffer(data, dtype=np.float32).copy()
            except Exception:
                logger.warning("Failed to parse audio chunk, skipping")
                continue

            # Transcribe the chunk
            try:
                result = whisper.transcribe(audio)
                await websocket.send_json(result)
            except Exception as e:
                logger.error("Transcription error: %s\n%s", e, traceback.format_exc())
                await websocket.send_json({
                    "type": "error",
                    "message": f"Transcription error: {str(e)}",
                })

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error("WebSocket error: %s", e)
    finally:
        logger.info(
            "Session ended — %d chunks processed",
            whisper.chunk_counter,
        )

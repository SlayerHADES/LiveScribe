"""
OfflineScribe — Whisper transcription service.

Loads a pre-exported Whisper ONNX model and provides chunk-by-chunk
transcription. Runs inference through ONNX Runtime with the configured
execution provider (QNN on Snapdragon, CPU elsewhere).
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import numpy as np

from app.config import BASE_DIR, PREFERRED_PROVIDERS

logger = logging.getLogger("offlinescribe.whisper")

# ─── Constants ───────────────────────────────────────────────────────────────

MODEL_DIR = BASE_DIR / "models" / "whisper-base-onnx"
SAMPLE_RATE = 16_000  # Whisper expects 16 kHz mono audio

# Phrases Whisper outputs for silence / no speech — we detect these
# and return a "silence" message instead of empty transcript text.
SILENCE_MARKERS = frozenset({
    "",
    " ",
    "...",
    "[BLANK_AUDIO]",
    "(blank audio)",
    "[ Silence ]",
    "[silence]",
    "(silence)",
    "Thank you.",            # Whisper hallucinates this on silence
    " Thank you.",
    "Thanks for watching!",
    " Thanks for watching!",
    "you",
    " you",
    "You",
    " You",
})


class WhisperService:
    """
    Singleton-style Whisper transcription service.

    Usage:
        service = WhisperService.get_instance()
        result = service.transcribe(audio_float32_16khz)
    """

    _instance: WhisperService | None = None

    def __init__(self):
        self.model = None
        self.processor = None
        self.chunk_counter = 0
        self._active_provider: str = "unknown"
        self._loaded = False

    @classmethod
    def get_instance(cls) -> WhisperService:
        if cls._instance is None:
            cls._instance = WhisperService()
        return cls._instance

    def is_loaded(self) -> bool:
        return self._loaded

    def load(self) -> None:
        """Load the ONNX Whisper model. Call once at startup or on first use."""
        if self._loaded:
            return

        model_path = str(MODEL_DIR)
        if not MODEL_DIR.exists() or not (MODEL_DIR / "config.json").exists():
            raise FileNotFoundError(
                f"Whisper ONNX model not found at {model_path}. "
                f"Run: python scripts/download_models.py"
            )

        logger.info("Loading Whisper ONNX model from %s ...", model_path)
        t0 = time.time()

        from optimum.onnxruntime import ORTModelForSpeechSeq2Seq
        from transformers import WhisperProcessor

        # Determine which provider to use
        provider = self._pick_provider()

        self.processor = WhisperProcessor.from_pretrained(model_path)

        try:
            self.model = ORTModelForSpeechSeq2Seq.from_pretrained(
                model_path,
                provider=provider,
            )
        except Exception:
            # If requested provider fails, fall back to CPU
            logger.warning(
                "Failed to load with %s, falling back to CPUExecutionProvider",
                provider,
            )
            self.model = ORTModelForSpeechSeq2Seq.from_pretrained(
                model_path,
                provider="CPUExecutionProvider",
            )

        # Detect the actual active provider
        try:
            self._active_provider = self.model.encoder.session.get_providers()[0]
        except Exception:
            self._active_provider = "CPUExecutionProvider"

        elapsed = time.time() - t0
        logger.info(
            "Whisper model loaded in %.1fs — provider: %s",
            elapsed,
            self._active_provider,
        )
        self._loaded = True

    def _pick_provider(self) -> str:
        """Pick the best available execution provider."""
        import onnxruntime as ort

        available = set(ort.get_available_providers())
        for prov in PREFERRED_PROVIDERS:
            if prov in available:
                return prov
        return "CPUExecutionProvider"

    @property
    def active_provider(self) -> str:
        return self._active_provider

    def transcribe(self, audio: np.ndarray) -> dict[str, Any]:
        """
        Transcribe a chunk of audio.

        Args:
            audio: float32 numpy array of 16 kHz mono PCM audio.

        Returns:
            Dict matching API_CONTRACT.md section 3:
              - {"type": "transcript_chunk", "text": ..., "chunk_id": ...,
                 "latency_ms": ..., "execution_provider": ...}
              - {"type": "silence", "chunk_id": ...}
        """
        if not self._loaded:
            self.load()

        self.chunk_counter += 1
        chunk_id = self.chunk_counter

        # Ensure audio is the right format
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        # Normalize if needed (some recordings are int16-scaled)
        if np.max(np.abs(audio)) > 1.5:
            audio = audio / 32768.0

        # Skip very short chunks (< 0.5s)
        if len(audio) < SAMPLE_RATE * 0.5:
            logger.debug("Chunk %d too short (%d samples), treating as silence", chunk_id, len(audio))
            return {"type": "silence", "chunk_id": chunk_id}

        # Preprocess
        inputs = self.processor(
            audio,
            sampling_rate=SAMPLE_RATE,
            return_tensors="pt",
        )

        # Run inference
        t0 = time.perf_counter()
        predicted_ids = self.model.generate(
            **inputs,
            max_new_tokens=128,
            language="en",
            task="transcribe",
        )
        latency_ms = (time.perf_counter() - t0) * 1000

        # Decode
        text = self.processor.batch_decode(
            predicted_ids, skip_special_tokens=True
        )[0].strip()

        logger.info(
            "Chunk %d | %.0f ms | %s | '%s'",
            chunk_id,
            latency_ms,
            self._active_provider,
            text[:80],
        )

        # Record benchmark
        try:
            from app.services.benchmark_service import BenchmarkService
            BenchmarkService.get_instance().record_transcription(
                chunk_id, latency_ms, self._active_provider
            )
        except Exception:
            pass

        # Check for silence / hallucinated non-speech
        if text in SILENCE_MARKERS or len(text) < 2:
            return {"type": "silence", "chunk_id": chunk_id}

        return {
            "type": "transcript_chunk",
            "text": text,
            "chunk_id": chunk_id,
            "latency_ms": round(latency_ms, 1),
            "execution_provider": self._active_provider,
        }

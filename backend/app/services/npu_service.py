"""
OfflineScribe — NPU service.

Manages ONNX Runtime session creation and execution-provider detection.
Provides helper functions used by the health/status routes and by
verify_npu.py to confirm whether the QNN (Hexagon NPU) execution provider
is active or whether inference fell back to CPU.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import numpy as np
import onnxruntime as ort

from app.config import PREFERRED_PROVIDERS, QNN_PROVIDER_OPTIONS

logger = logging.getLogger("offlinescribe.npu")

# ─── Provider detection ──────────────────────────────────────────────────────

def get_available_providers() -> list[str]:
    """Return the list of execution providers compiled into this ORT build."""
    return ort.get_available_providers()


def _build_provider_list() -> list[tuple[str, dict[str, Any]]]:
    """
    Build the (provider_name, options) pairs ONNX Runtime expects.
    Only includes providers that are actually available in this build.
    """
    available = set(get_available_providers())
    result: list[tuple[str, dict[str, Any]]] = []
    for prov in PREFERRED_PROVIDERS:
        if prov in available:
            opts = QNN_PROVIDER_OPTIONS if prov == "QNNExecutionProvider" else {}
            result.append((prov, opts))
    # Always ensure CPU is present as ultimate fallback
    if "CPUExecutionProvider" not in {p for p, _ in result}:
        result.append(("CPUExecutionProvider", {}))
    return result


# ─── Tiny test model (in-memory ONNX graph: Z = X + Y) ──────────────────────

def _make_add_model_bytes() -> bytes:
    """
    Programmatically create a minimal ONNX model that computes Z = X + Y.
    Uses the `onnx` helper library for correct protobuf generation.
    This avoids needing a model file on disk just to verify the provider works.
    """
    from onnx import TensorProto, helper

    X = helper.make_tensor_value_info("X", TensorProto.FLOAT, [1, 4])
    Y = helper.make_tensor_value_info("Y", TensorProto.FLOAT, [1, 4])
    Z = helper.make_tensor_value_info("Z", TensorProto.FLOAT, [1, 4])

    add_node = helper.make_node("Add", inputs=["X", "Y"], outputs=["Z"])
    graph = helper.make_graph([add_node], "add_test", [X, Y], [Z])
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)])
    model.ir_version = 8
    return model.SerializeToString()


# ─── Inference test ──────────────────────────────────────────────────────────

def run_test_inference() -> dict[str, Any]:
    """
    Run a single Add inference and report which provider actually executed it.

    Returns a dict with:
        - execution_provider: str    — the provider that ran the inference
        - npu_confirmed: bool        — True only if QNNExecutionProvider was used
        - fallback_to_cpu: bool      — True if we fell back to CPU
        - latency_ms: float          — wall-clock inference time
        - output_correct: bool       — whether the Add result is numerically correct
        - error: str | None          — error message if something went wrong
    """
    try:
        model_bytes = _make_add_model_bytes()
        providers = _build_provider_list()

        sess = ort.InferenceSession(
            model_bytes,
            providers=[p for p, _ in providers],
            provider_options=[o for _, o in providers],
        )

        active_provider = sess.get_providers()[0]  # first = the one actually used

        x = np.array([[1.0, 2.0, 3.0, 4.0]], dtype=np.float32)
        y = np.array([[10.0, 20.0, 30.0, 40.0]], dtype=np.float32)
        expected = x + y

        t0 = time.perf_counter()
        result = sess.run(None, {"X": x, "Y": y})
        latency_ms = (time.perf_counter() - t0) * 1000

        output_correct = np.allclose(result[0], expected)
        npu_confirmed = active_provider == "QNNExecutionProvider"

        return {
            "execution_provider": active_provider,
            "npu_confirmed": npu_confirmed,
            "fallback_to_cpu": not npu_confirmed,
            "latency_ms": round(latency_ms, 2),
            "output_correct": output_correct,
            "error": None,
        }

    except Exception as exc:
        logger.exception("NPU test inference failed")
        return {
            "execution_provider": "unknown",
            "npu_confirmed": False,
            "fallback_to_cpu": True,
            "latency_ms": 0,
            "output_correct": False,
            "error": str(exc),
        }


# ─── Cached singleton ────────────────────────────────────────────────────────

_cached_status: dict[str, Any] | None = None


def get_npu_status(*, force_refresh: bool = False) -> dict[str, Any]:
    """
    Return NPU status, cached after first call unless force_refresh is True.
    """
    global _cached_status
    if _cached_status is None or force_refresh:
        _cached_status = run_test_inference()
    return _cached_status

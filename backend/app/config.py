"""
OfflineScribe — Application configuration.

Centralizes model paths, execution provider preferences, and server settings.
On Snapdragon ARM64 devices, QNNExecutionProvider targets the Hexagon NPU.
On other platforms, falls back to CPUExecutionProvider.
"""

import platform
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"

# ─── Execution provider preference ────────────────────────────────────────────
# Ordered list: ONNX Runtime tries the first available provider.
# QNNExecutionProvider is only available on ARM64 Windows with onnxruntime-qnn.
PREFERRED_PROVIDERS = ["QNNExecutionProvider", "CPUExecutionProvider"]

# QNN provider options — backend_path tells QNN which accelerator to target.
# QnnHtp.dll = Hexagon Tensor Processor (NPU), QnnCpu.dll = CPU reference impl.
QNN_PROVIDER_OPTIONS = {
    "backend_path": "QnnHtp.dll",
}

# ─── Architecture detection ──────────────────────────────────────────────────
MACHINE = platform.machine().lower()
IS_ARM64 = MACHINE in ("aarch64", "arm64")

# ─── Server ──────────────────────────────────────────────────────────────────
BACKEND_HOST = "0.0.0.0"
BACKEND_PORT = 8000
FRONTEND_ORIGIN = "http://localhost:5173"

#!/usr/bin/env python3
"""
verify_npu.py -- Standalone NPU verification script.

Run this BEFORE any other development to confirm that the QNN (Hexagon NPU)
execution provider is working on this machine.

Usage:
    python backend/verify_npu.py

Exit codes:
    0  -- QNNExecutionProvider is active (NPU confirmed)
    1  -- Fell back to CPU or error (NOT ready for competition)

On a non-Snapdragon machine (e.g. AMD/Intel x86), this will always report
CPUExecutionProvider -- that's expected and correct.  The QNN provider only
works on ARM64 Windows with a Qualcomm Hexagon NPU.
"""

import platform
import struct
import sys
import os
import io

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Ensure the backend package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.npu_service import get_available_providers, run_test_inference


def main() -> int:
    print("=" * 64)
    print("  OfflineScribe -- NPU Verification")
    print("=" * 64)
    print()

    # -- Step 1: Architecture check
    machine = platform.machine()
    bits = struct.calcsize("P") * 8
    py_version = sys.version.split()[0]

    print(f"  Python version : {py_version}")
    print(f"  Architecture   : {machine} ({bits}-bit)")
    print(f"  Executable     : {sys.executable}")
    print()

    is_arm64 = machine.lower() in ("aarch64", "arm64")
    if is_arm64:
        print("  [OK] ARM64-native Python detected -- NPU access is possible")
    else:
        print(f"  [WARN] {machine} detected -- this is NOT an ARM64 Snapdragon device.")
        print("         QNNExecutionProvider will NOT be available.")
        print("         (Expected if developing on a non-Snapdragon machine.)")
    print()

    # -- Step 2: Available providers
    providers = get_available_providers()
    print("  Available ONNX Runtime providers:")
    for p in providers:
        marker = " >>>" if p == "QNNExecutionProvider" else "    "
        print(f"  {marker} {p}")
    print()

    has_qnn = "QNNExecutionProvider" in providers
    if has_qnn:
        print("  [OK] QNNExecutionProvider is available in this ORT build")
    else:
        print("  [MISSING] QNNExecutionProvider NOT found in this ORT build")
        if is_arm64:
            print("            -> Install it: pip install onnxruntime-qnn")
    print()

    # -- Step 3: Test inference
    print("  Running test inference (Z = X + Y) ...")
    result = run_test_inference()
    print()

    if result["error"]:
        print(f"  [ERROR] Inference error: {result['error']}")
        print()
        print("=" * 64)
        print("  RESULT: FAIL -- could not run test inference")
        print("=" * 64)
        return 1

    provider = result["execution_provider"]
    correct = result["output_correct"]
    latency = result["latency_ms"]
    npu_ok = result["npu_confirmed"]

    print(f"  Execution provider : {provider}")
    print(f"  Output correct     : {'Yes' if correct else 'No'}")
    print(f"  Inference latency  : {latency:.2f} ms")
    print()

    if npu_ok:
        print("=" * 64)
        print("  [PASS] QNNExecutionProvider (Hexagon NPU) confirmed!")
        print("         Ready to proceed to Phase 2.")
        print("=" * 64)
        return 0
    else:
        print("=" * 64)
        print(f"  [CPU FALLBACK] Using {provider}")
        if not is_arm64:
            print("  This is expected on a non-Snapdragon machine.")
            print("  On a Snapdragon X Elite/Plus, this should show QNNExecutionProvider.")
        else:
            print("  On ARM64 but QNN failed -- debug onnxruntime-qnn installation.")
        print("=" * 64)
        return 1


if __name__ == "__main__":
    sys.exit(main())

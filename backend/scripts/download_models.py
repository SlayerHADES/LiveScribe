#!/usr/bin/env python3
"""
download_models.py — Download and export Whisper model to ONNX format.

Usage:
    python scripts/download_models.py

This script:
  1. Downloads openai/whisper-base from HuggingFace
  2. Exports it to ONNX format (encoder + decoder)
  3. Saves the ONNX model + processor to backend/models/whisper-base-onnx/

The export step requires PyTorch (CPU-only is fine).
After export, inference uses only ONNX Runtime — no PyTorch needed.
"""

import os
import sys
import time

# Ensure backend package is importable
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

MODEL_ID = "openai/whisper-base"
SAVE_DIR = os.path.join(BACKEND_DIR, "models", "whisper-base-onnx")


def main():
    print("=" * 64)
    print("  OfflineScribe — Model Download & ONNX Export")
    print("=" * 64)
    print()

    if os.path.exists(os.path.join(SAVE_DIR, "config.json")):
        print(f"  Model already exported at: {SAVE_DIR}")
        print("  To re-export, delete that directory and run again.")
        print()

        # Verify it loads
        print("  Verifying model loads correctly...")
        try:
            from optimum.onnxruntime import ORTModelForSpeechSeq2Seq
            model = ORTModelForSpeechSeq2Seq.from_pretrained(SAVE_DIR)
            provider = model.encoder.session.get_providers()[0]
            print(f"  [OK] Model loaded, using provider: {provider}")
        except Exception as e:
            print(f"  [ERROR] Failed to load: {e}")
            return 1
        return 0

    print(f"  Model: {MODEL_ID}")
    print(f"  Output: {SAVE_DIR}")
    print()

    # Step 1: Export to ONNX
    print("  [1/3] Loading model and exporting to ONNX...")
    print("        (This downloads ~300MB and takes 1-3 minutes)")
    print()

    t0 = time.time()

    try:
        from optimum.onnxruntime import ORTModelForSpeechSeq2Seq
        from transformers import WhisperProcessor

        model = ORTModelForSpeechSeq2Seq.from_pretrained(
            MODEL_ID,
            export=True,
        )
        processor = WhisperProcessor.from_pretrained(MODEL_ID)

        elapsed = time.time() - t0
        print(f"  [OK] Model loaded and exported in {elapsed:.1f}s")
        print()

    except Exception as e:
        print(f"  [ERROR] Export failed: {e}")
        print()
        print("  Make sure you have installed:")
        print("    pip install torch transformers optimum[onnxruntime]")
        return 1

    # Step 2: Save
    print("  [2/3] Saving ONNX model to disk...")
    os.makedirs(SAVE_DIR, exist_ok=True)
    model.save_pretrained(SAVE_DIR)
    processor.save_pretrained(SAVE_DIR)
    print(f"  [OK] Saved to {SAVE_DIR}")
    print()

    # Step 3: Verify
    print("  [3/3] Verifying saved model loads correctly...")
    try:
        model2 = ORTModelForSpeechSeq2Seq.from_pretrained(SAVE_DIR)
        provider = model2.encoder.session.get_providers()[0]
        print(f"  [OK] Verified — provider: {provider}")
    except Exception as e:
        print(f"  [WARN] Verification failed: {e}")
        print("         The model files may still be usable.")

    print()
    print("=" * 64)
    print("  Done! Model ready for transcription.")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())

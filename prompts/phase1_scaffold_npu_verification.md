# Phase 1 — Project scaffold + NPU verification

Paste everything below this line as your first message to Antigravity.

---

Set up a Windows desktop app project (Python backend + a simple web-based UI
using a local Flask/FastAPI server + HTML/JS frontend, or Electron if you
think that's more reliable) called "OfflineScribe" — an offline meeting
transcription and summarization assistant for a Snapdragon X Elite/Plus
laptop (Hexagon NPU).

This repo already has a README.md, .gitignore, and docs/API_CONTRACT.md —
read docs/API_CONTRACT.md now and follow its request/response JSON shapes
exactly in every later phase. Do not invent different field names.

Before writing app logic, verify the environment:
- Confirm Python is ARM64-native (not running under x86 emulation) since
  that affects NPU access
- Install onnxruntime-qnn (Qualcomm's QNN execution provider for ONNX
  Runtime) and confirm it can list the QNN NPU as an available execution
  provider
- Write a tiny test script (backend/verify_npu.py) that loads a small ONNX
  model and runs one inference through the QNN execution provider, and
  prints which provider actually executed it (NPU vs CPU fallback) — this
  must be provably true, not assumed
- Implement GET /api/health and GET /api/npu-status exactly as defined in
  docs/API_CONTRACT.md
- Set up a clean project structure inside the existing /backend and
  /frontend folders: backend gets /app, /app/routes, /app/services,
  /app/models, /tests; frontend gets /src/components

Do not proceed to the transcription feature until verify_npu.py confirms
NPU execution end-to-end and /api/npu-status returns npu_confirmed: true.

---

## Before moving to Phase 2, confirm:
- [ ] `python backend/verify_npu.py` prints `QNNExecutionProvider`, not CPU
- [ ] `GET /api/health` and `GET /api/npu-status` both respond correctly
- [ ] Project structure matches docs/API_CONTRACT.md expectations
- [ ] `git add . && git commit -m "feat: verify QNN/NPU execution provider on ARM64"`

If NPU verification fails here, stop and debug this before writing any more
code — this is the one blocker that can sink the whole build if found late.

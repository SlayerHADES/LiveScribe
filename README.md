# OfflineScribe

**Offline meeting & lecture assistant — on-device Whisper transcription + local LLM summarization, running entirely on the Snapdragon Hexagon NPU. No internet required. No audio ever leaves the device.**

Built for the [Snapdragon® AI Lab Build & Present Challenge](https://unstop.com) (Qualcomm).

---

## The problem

Meeting and lecture transcription tools today all send your audio to the cloud. That's a real privacy problem for confidential meetings, and it stops working the moment you lose connectivity — on a flight, in a basement lab, in a low-connectivity classroom.

## The solution

OfflineScribe runs the entire pipeline — speech-to-text and summarization — locally on the Snapdragon NPU via ONNX Runtime's QNN execution provider. It works with wifi fully disabled, proven live in the demo.

## Why this needs the NPU (not just "AI with a UI")

| | Cloud-based tools | OfflineScribe |
|---|---|---|
| Works offline | ❌ | ✅ |
| Audio leaves the device | ✅ (privacy risk) | ❌ (never) |
| Inference hardware | Remote GPU cluster | On-device Hexagon NPU |
| Latency | Network-dependent | ~300 ms/chunk |

Benchmark numbers and the execution-provider proof (QNN vs CPU fallback) are captured live in the app's debug panel — see `/docs/benchmarks.md` after running Phase 4.

## Architecture

```
┌─────────────┐    audio chunks    ┌──────────────────┐
│  Frontend    │ ─────────────────▶│  Backend (FastAPI)│
│  (mic UI,    │                    │                   │
│  live text)  │◀───────────────── │  Whisper (QNN/NPU)│
└─────────────┘   transcript/ws     │        ↓          │
                                    │  Local LLM (QNN)  │
                                    │  → summary JSON   │
                                    └──────────────────┘
```

Full request/response contract: see `docs/API_CONTRACT.md`.

## Tech stack

- **Transcription:** Whisper (base/small), ONNX format, via `onnxruntime-qnn`
- **Summarization:** Quantized small instruction-tuned LLM (Llama-3.2-1B/3B or Phi-3-mini), ONNX Runtime GenAI, QNN execution provider
- **Backend:** Python (FastAPI), WebSocket streaming for live transcript
- **Frontend:** HTML/JS (or React/Vite) — minimal, dark-mode, demo-optimized
- **Hardware:** Snapdragon X Elite/Plus (HP Omnibook), Hexagon NPU

## Setup

```bash
# 1. Clone
git clone https://github.com/kshitij/offlinescribe.git
cd offlinescribe

# 2. Backend (must be ARM64-native Python — see docs/npu_verification.md)
cd backend
pip install -r requirements.txt
python verify_npu.py   # confirms QNN execution provider is available

# 3. Download models (not committed to repo — see docs/models.md)
python scripts/download_models.py

# 4. Run backend
uvicorn app.main:app --reload

# 5. Frontend (separate terminal)
cd ../frontend
npm install
npm run dev
```

Open `http://localhost:5173` (or wherever Vite prints), click **Start Recording**, and speak.

## Demo

- Live demo: mic → live transcript → "Summarize Now" → structured summary + action items
- **Offline proof:** enable airplane mode, everything still works — indicator shown in-app
- Backup video (in case of live demo issues): `docs/demo.mp4`

## Team

Kshitij M. — solo build, Snapdragon AI Lab Challenge 2026

## License

MIT — see `LICENSE`

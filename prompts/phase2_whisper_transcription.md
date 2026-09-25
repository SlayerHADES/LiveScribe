# Phase 2 — Whisper on-device transcription

Only paste this after Phase 1's NPU verification checklist is fully checked off.

---

Download a Whisper model (base or small size — prioritize responsiveness
over max accuracy) in ONNX format, ideally pulled/pre-optimized from
Qualcomm AI Hub if available, otherwise convert openai/whisper-base to ONNX
and quantize it for QNN.

Follow docs/API_CONTRACT.md section 3 (Live transcription stream) exactly —
same WebSocket path, same JSON field names for transcript_chunk and silence
messages.

Build a backend module that:
- Captures audio from the system microphone in rolling ~5-second chunks
- Runs each chunk through the Whisper ONNX model via the QNN execution
  provider (NPU)
- Streams the resulting transcript text back to the frontend via
  WS /ws/transcribe, appending to a running transcript
- Sends a `silence` message type (not empty text) for no-speech chunks
- Logs per-chunk inference latency to the console so we can benchmark later

Build a minimal frontend: a "Start/Stop Recording" button and a live-updating
transcript box that handles both transcript_chunk and silence message types
correctly. Test it by speaking into the mic and confirming transcript
accuracy and that the NPU (not CPU) is doing the work — check the
execution_provider field on each chunk message.

---

## Before moving to Phase 3, confirm:
- [ ] Speaking into the mic produces a live, readable transcript
- [ ] Console/logs show `execution_provider: QNNExecutionProvider` per chunk, not CPU
- [ ] Silence periods don't fill the transcript with blank lines
- [ ] `git add . && git commit -m "feat: on-device Whisper transcription via QNN"`

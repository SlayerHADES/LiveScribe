# OfflineScribe — API Contract

Pin this before Phase 2. Paste the relevant section into each Antigravity prompt
so backend and frontend are built to the same spec instead of drifting.

---

## 1. Health check

`GET /api/health`

Response `200`:
```json
{ "status": "ok", "npu_provider": "QNNExecutionProvider" }
```

## 2. NPU verification (Phase 1)

`GET /api/npu-status`

Response `200`:
```json
{
  "execution_provider": "QNNExecutionProvider",
  "npu_confirmed": true,
  "fallback_to_cpu": false
}
```
Frontend uses this to show a red/green NPU indicator in the benchmark panel.

## 3. Live transcription stream (Phase 2)

`WS /ws/transcribe`

Client → server: raw audio chunks (binary, ~5s each) or base64-encoded PCM.

Server → client, one message per processed chunk:
```json
{
  "type": "transcript_chunk",
  "text": "the sentence just transcribed",
  "chunk_id": 14,
  "latency_ms": 312,
  "execution_provider": "QNNExecutionProvider"
}
```

Silence / no-speech chunks are **not** sent as empty text — server should send:
```json
{ "type": "silence", "chunk_id": 15 }
```
so the frontend can skip rendering instead of filling the transcript with blank lines.

## 4. Summarization (Phase 3)

`POST /api/summarize`

Request:
```json
{ "transcript": "full or last-N-minutes transcript text" }
```

Response `200`:
```json
{
  "summary": "2-3 sentence summary",
  "decisions": ["decision one", "decision two"],
  "action_items": [
    { "task": "send follow-up email", "owner": "Priya" },
    { "task": "book venue", "owner": null }
  ],
  "latency_ms": 1840,
  "execution_provider": "QNNExecutionProvider"
}
```
`owner` is `null` when no name was mentioned — frontend renders "unassigned".

## 5. Network / offline status (Phase 4)

`GET /api/network-status`

Response `200`:
```json
{ "online": false }
```
Poll every few seconds from the frontend to drive the "Offline Mode" indicator.
Must reflect the real OS-level connectivity check, not a hardcoded value.

## 6. Benchmark panel (Phase 4)

`GET /api/benchmarks`

Response `200`:
```json
{
  "transcription": [
    { "chunk_id": 14, "latency_ms": 312, "provider": "QNNExecutionProvider" }
  ],
  "summarization": [
    { "call_id": 1, "latency_ms": 1840, "provider": "QNNExecutionProvider" }
  ]
}
```

## 7. Export notes (Phase 5)

`POST /api/export`

Request:
```json
{ "format": "markdown" }
```

Response `200`: file download (`.md`), containing transcript + summary + action items.

---

### Rule for every Antigravity prompt from Phase 2 onward
Include this line: *"Follow the request/response JSON shapes exactly as defined in
docs/API_CONTRACT.md — do not invent new field names."* This is what keeps a
multi-phase agent build from producing a frontend and backend that technically
both run but don't actually talk to each other correctly.

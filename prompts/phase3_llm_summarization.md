# Phase 3 — Local LLM summarization

Only paste this after Phase 2's checklist is fully checked off.

---

Add a local LLM for summarization — use a small instruction-tuned model
(e.g. a quantized Llama-3.2-1B/3B or Phi-3-mini in ONNX/QNN-compatible
format) that can run on-device via ONNX Runtime GenAI with the QNN provider.

Follow docs/API_CONTRACT.md section 4 (Summarization) exactly — same
endpoint path, same response JSON shape (summary, decisions[], action_items[]
with task/owner fields, latency_ms, execution_provider).

Build a backend module that:
- Takes the full running transcript (or the last N minutes of it)
- Sends it to the local LLM with a prompt instructing it to produce:
  (1) a short summary, (2) a bulleted list of decisions made,
  (3) a bulleted list of action items with owners if mentioned (owner is
  null when no name was mentioned)
- Returns structured JSON matching docs/API_CONTRACT.md exactly
- Runs this on-demand (POST /api/summarize) rather than continuously, to
  keep resource usage sane

Add a "Summarize Now" button to the frontend that calls POST /api/summarize
and displays the structured output (summary, decisions, action items with
owners) below the transcript. Confirm this also executes via the NPU/QNN
provider and log its latency.

---

## Before moving to Phase 4, confirm:
- [ ] "Summarize Now" returns a real summary + decisions + action items from actual spoken content
- [ ] Response JSON field names match docs/API_CONTRACT.md exactly
- [ ] execution_provider on the summarize response is QNNExecutionProvider, not CPU
- [ ] `git add . && git commit -m "feat: local LLM summarization pipeline"`

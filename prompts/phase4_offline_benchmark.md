# Phase 4 — Offline proof + benchmark mode

Only paste this after Phase 3's checklist is fully checked off.

---

Add a visible "Offline Mode" indicator to the UI that checks and displays
whether the system currently has network connectivity (GET /api/network-status
per docs/API_CONTRACT.md section 5), to reinforce that the app works with
wifi fully disabled — this needs to be genuinely true, so test it with the
machine in airplane mode end to end.

Add a benchmark/debug panel (GET /api/benchmarks per docs/API_CONTRACT.md
section 6) that displays, for each transcription chunk and each
summarization call:
- Execution provider used (QNN/NPU vs CPU)
- Inference latency in ms
- Rough power/CPU usage if easily obtainable via a system API

This panel is for the demo — it should look clean enough to show on stage,
not just raw console logs.

---

## Before moving to Phase 5, confirm:
- [ ] Turn on airplane mode, restart the app, full flow (record → transcript → summarize) still works
- [ ] Offline indicator correctly flips to "offline" in airplane mode and back when reconnected
- [ ] Benchmark panel shows real latency numbers and execution provider per call, not placeholders
- [ ] Copy these real numbers into README.md's benchmark table (replace the `<fill in>` placeholder)
- [ ] `git add . && git commit -m "feat: offline mode indicator + NPU benchmark panel"`

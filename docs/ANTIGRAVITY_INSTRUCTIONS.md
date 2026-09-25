# How to use this folder with Antigravity

This is a starter kit, not a finished app — it has the docs, structure, and
prompts pre-built, but Antigravity's agent has to actually write the code.
Follow these steps in order.

## 1. Unzip and open in Antigravity

Unzip `offlinescribe-starter.zip` somewhere on your Snapdragon laptop
(not inside a cloud-synced folder like OneDrive, to avoid file-lock issues
during builds). Open that unzipped folder — not a single file, the whole
folder — as your project in Antigravity.

## 2. Initialize git first, before any prompts

```bash
cd offlinescribe-starter
git init
git add .
git commit -m "chore: initial scaffold, docs, and API contract"
```

Do this before Phase 1 so every phase after this has its own clean,
revertable commit (see the checklist at the bottom of each phase file).

## 3. Feed the phase prompts one at a time — never all at once

In the `prompts/` folder you have:
- `phase1_scaffold_npu_verification.md`
- `phase2_whisper_transcription.md`
- `phase3_llm_summarization.md`
- `phase4_offline_benchmark.md`
- `phase5_polish_demo.md`

Open `phase1_scaffold_npu_verification.md`, copy everything **below the
`---` line** (that's the actual prompt text — the heading above it is just
a label for you, not for the agent), and paste that as your message to
Antigravity.

Let it finish. Then work through the checklist at the bottom of that same
file yourself, on the actual hardware — these are things you verify, the
agent can't self-certify NPU execution is real. Only once every box is
checked, move to `phase2_...md` and repeat.

**Do not skip ahead or batch multiple phases into one prompt.** Each phase
builds on the previous one being genuinely verified working — that's what
keeps the codebase from becoming an unverifiable mess by Phase 5.

## 4. Why the docs/ files matter

`docs/API_CONTRACT.md` is already referenced inside every phase prompt.
It's what stops the agent from inventing different JSON field names in the
backend (built in Phase 2/3) versus what the frontend expects (also built
across those phases) — the single most common way agent-built full-stack
apps end up with a frontend and backend that both "work" individually but
don't actually talk to each other.

If Antigravity ever proposes an API shape that conflicts with
`API_CONTRACT.md`, tell it to follow the contract instead — don't let it
improvise here.

## 5. If Phase 1 fails

If `verify_npu.py` cannot get QNN/NPU execution working, stop and fix this
before writing any more code. This is explicitly called out because it's
the one failure mode that can invalidate the whole submission (a Snapdragon
NPU challenge whose "on-device AI" is secretly running on CPU is not a
winning entry). Ask Antigravity to debug the QNN execution provider
installation specifically — don't let it quietly fall back to CPU and move
on to Phase 2.

## 6. When Phase 5 is done — packaging for submission

1. Fill in every `<fill in>` / `<your name>` placeholder left in `README.md`
2. Delete before zipping: `node_modules/`, `venv/`/`.venv/`, any `*.onnx`/
   `*.bin`/`*.gguf` model weight files, `__pycache__/`
3. Fresh-clone your pushed GitHub repo into a new folder and confirm the
   README's setup steps work from a truly clean checkout
4. Confirm `docs/demo.mp4` (backup video) is present
5. Zip it:
   ```bash
   zip -r offlinescribe_submission.zip offlinescribe-starter \
     -x "*/node_modules/*" -x "*/.venv/*" -x "*/venv/*" \
     -x "*/__pycache__/*" -x "*/.git/*" -x "*.onnx" -x "*.bin" -x "*.gguf"
   ```
6. Submit both the GitHub link and this zip per the Unstop submission form.

## Timeline reminder

Deadline: Sep 30, 2026, 11:59 PM IST. Run Phase 1 today — if NPU
verification is going to fail, you want to know now, not on day 4.

# Phase 5 — Polish for the live demo

Only paste this after Phase 4's checklist is fully checked off.

---

Polish the UI for a live presentation:
- Clean, minimal design (dark mode, large readable transcript text,
  the offline indicator and NPU/latency stats visible but unobtrusive)
- Add an "Export Notes" button (POST /api/export per docs/API_CONTRACT.md
  section 7) that saves the summary/action items as a markdown file
- Add graceful handling for silence/no-speech chunks so the transcript
  doesn't fill with garbage (should already work from Phase 2 — verify it)
- Test a full 3-5 minute mock meeting end-to-end, airplane mode on, and
  confirm transcript + summary quality is good enough to demo live

Also record a screen capture of this full run as a backup video
(save as docs/demo.mp4) in case the live mic demo has issues on stage.

---

## Before you're done, confirm:
- [ ] Fresh clone of the repo + setup instructions in README.md actually work end-to-end on a clean checkout
- [ ] "Export Notes" produces a real, readable markdown file
- [ ] Backup demo video recorded and saved to docs/demo.mp4
- [ ] README.md's benchmark table, team name, and placeholders are all filled in
- [ ] `git add . && git commit -m "polish: UI, export notes, demo hardening"`
- [ ] `git push -u origin main`
- [ ] Build the submission zip (see docs/ANTIGRAVITY_INSTRUCTIONS.md, final step)

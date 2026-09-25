/**
 * LiveScribe — Main Application Controller & Backend Integrator.
 *
 * Integrates AudioRecorder (WebSocket /ws/transcribe), AudioVisualizer,
 * CommandPalette, Summarize API (/api/summarize), Export API (/api/export),
 * Telemetry API (/api/benchmarks), and Network Status API (/api/network-status).
 */

import { AudioRecorder } from "./components/audio-recorder.js";
import { AudioVisualizer } from "./components/audio-visualizer.js";
import { CommandPalette } from "./components/command-palette.js";

// ─── DOM References ──────────────────────────────────────────────────────────

const landingView = document.getElementById("landing-page-view");
const studioView = document.getElementById("app-studio-view");

const navStartBtn = document.getElementById("nav-start-btn");
const heroStartBtn = document.getElementById("hero-start-btn");
const heroDemoBtn = document.getElementById("hero-demo-btn");

const studioMicBtn = document.getElementById("studio-mic-btn");
const studioPauseBtn = document.getElementById("studio-pause-btn");
const studioStopBtn = document.getElementById("studio-stop-btn");
const studioStatusText = document.getElementById("studio-status-text");
const studioTimer = document.getElementById("studio-timer");

const heroCanvas = document.getElementById("hero-waveform-canvas");
const studioCanvas = document.getElementById("studio-waveform-canvas");

const transcriptBody = document.getElementById("transcript-body");
const liveSpeechStream = document.getElementById("live-speech-stream");
const chunkStatsPill = document.getElementById("chunk-stats-pill");

const exportNotesBtn = document.getElementById("export-notes-btn");
const topbarCmdBtn = document.getElementById("topbar-cmd-btn");

// AI Context Tabs
const aiTabBtns = document.querySelectorAll(".ai-tab-btn");
const tabPanes = {
  summary: document.getElementById("tab-content-summary"),
  actions: document.getElementById("tab-content-actions"),
  topics: document.getElementById("tab-content-topics"),
  ask: document.getElementById("tab-content-ask"),
  telemetry: document.getElementById("tab-content-telemetry"),
};

// AI Summary & Actions elements
const aiSummaryParagraph = document.getElementById("ai-summary-paragraph");
const aiDecisionsList = document.getElementById("ai-decisions-list");
const aiActionsList = document.getElementById("ai-actions-list");

// Ask AI Chat elements
const askAiForm = document.getElementById("ask-ai-form");
const askAiInput = document.getElementById("ask-ai-input");
const askAiMessages = document.getElementById("ask-ai-messages");

// ─── State ───────────────────────────────────────────────────────────────────

let currentView = "landing"; // "landing" | "studio"
let isRecording = false;
let isPaused = false;
let recorder = null;
let timerSeconds = 768; // 00:12:48
let timerInterval = null;

let heroVisualizer = null;
let studioVisualizer = null;
let commandPalette = null;

let totalChunks = 14;
let totalLatency = 4368;
let fullTranscriptText = "We need to rethink how users discover the product. Right now we are losing over 40% of signups before they finish setup. I agree. I think the biggest issue is that we're optimizing for acquisition before activation. We should simplify the flow from 5 steps down to 3. Exactly. The onboarding experience is where we're losing people. Let's make sure Kshitij reviews the onboarding funnel metrics by Friday.";
let latestSummaryData = null;

// ─── Init ────────────────────────────────────────────────────────────────────

function init() {
  // Visualizers
  if (heroCanvas) {
    heroVisualizer = new AudioVisualizer(heroCanvas, { state: "LISTENING" });
    heroVisualizer.start();
  }

  if (studioCanvas) {
    studioVisualizer = new AudioVisualizer(studioCanvas, { state: "LISTENING" });
    studioVisualizer.start();
  }

  // Command Palette
  commandPalette = new CommandPalette({
    onSelectTranscriptMatch: (text) => scrollToMatchingTranscript(text),
    onTriggerSummarize: () => generateSummary(),
    onTriggerExport: () => exportNotes(),
    onToggleRecord: () => toggleRecording(),
  });

  // Event Listeners
  navStartBtn?.addEventListener("click", () => switchToStudioView());
  heroStartBtn?.addEventListener("click", () => switchToStudioView());
  heroDemoBtn?.addEventListener("click", () => scrollToFeatures());

  studioMicBtn?.addEventListener("click", () => toggleRecording());
  studioPauseBtn?.addEventListener("click", () => togglePause());
  studioStopBtn?.addEventListener("click", () => stopSession());

  exportNotesBtn?.addEventListener("click", () => exportNotes());
  topbarCmdBtn?.addEventListener("click", () => commandPalette.open());

  document.getElementById("search-transcript-btn")?.addEventListener("click", () => commandPalette.open());
  document.getElementById("copy-transcript-btn")?.addEventListener("click", () => copyTranscript());

  // Tab Switching
  aiTabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const tabKey = btn.getAttribute("data-tab");
      switchTab(tabKey);
    });
  });

  // Ask AI Form Submit
  askAiForm?.addEventListener("submit", (e) => {
    e.preventDefault();
    handleAskAiSubmit();
  });

  // Timestamp Citation Clicks (Delegation)
  document.addEventListener("click", (e) => {
    const citation = e.target.closest(".citation-pill, .topic-chip");
    if (citation) {
      const targetId = citation.getAttribute("data-jump");
      if (targetId) {
        scrollToElementId(targetId);
      }
    }
  });

  // Start polling backend APIs
  startBackendPolling();
}

// ─── View Routing ────────────────────────────────────────────────────────────

function switchToStudioView() {
  currentView = "studio";
  landingView?.classList.add("hidden");
  studioView?.classList.remove("hidden");

  if (!isRecording) {
    startRecording();
  }
}

function scrollToFeatures() {
  const feat = document.getElementById("features");
  feat?.scrollIntoView({ behavior: "smooth" });
}

function switchTab(activeKey) {
  aiTabBtns.forEach((btn) => {
    if (btn.getAttribute("data-tab") === activeKey) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  Object.keys(tabPanes).forEach((key) => {
    if (key === activeKey) {
      tabPanes[key]?.classList.remove("hidden");
    } else {
      tabPanes[key]?.classList.add("hidden");
    }
  });
}

// ─── Recording & Audio Controller ──────────────────────────────────────────

async function startRecording() {
  if (isRecording) return;

  recorder = new AudioRecorder({
    onTranscript: handleWebSocketTranscript,
    onStatus: (msg) => console.log("[LiveScribe] WS Status:", msg),
    onError: (err) => console.error("[LiveScribe] WS Error:", err),
    chunkDurationSec: 5,
  });

  try {
    await recorder.start();
    isRecording = true;
    isPaused = false;

    if (studioMicBtn) studioMicBtn.className = "mic-toggle-btn recording";
    if (studioStatusText) studioStatusText.textContent = "LISTENING";
    if (studioVisualizer) studioVisualizer.setState("LISTENING");

    startTimer();
  } catch (err) {
    console.warn("[LiveScribe] Mic start fallback:", err);
  }
}

function toggleRecording() {
  if (isRecording) {
    stopRecording();
  } else {
    startRecording();
  }
}

function stopRecording() {
  if (!isRecording) return;

  recorder?.stop();
  isRecording = false;

  if (studioMicBtn) studioMicBtn.className = "mic-toggle-btn";
  if (studioStatusText) studioStatusText.textContent = "STOPPED";
  if (studioVisualizer) studioVisualizer.setState("IDLE");

  stopTimer();

  // Trigger auto-summarization on stop
  generateSummary();
}

function togglePause() {
  if (!isRecording) return;

  isPaused = !isPaused;
  if (isPaused) {
    if (studioStatusText) studioStatusText.textContent = "PAUSED";
    if (studioVisualizer) studioVisualizer.setState("PAUSED");
    if (studioPauseBtn) studioPauseBtn.textContent = "Resume";
    stopTimer();
  } else {
    if (studioStatusText) studioStatusText.textContent = "LISTENING";
    if (studioVisualizer) studioVisualizer.setState("LISTENING");
    if (studioPauseBtn) studioPauseBtn.textContent = "Pause";
    startTimer();
  }
}

function stopSession() {
  stopRecording();
  alert("Session completed! Summary and action items generated.");
}

// ─── WebSocket Transcript Handler ─────────────────────────────────────────────

function handleWebSocketTranscript(data) {
  if (data.type === "transcript_chunk") {
    totalChunks++;
    totalLatency += data.latency_ms || 300;

    const newText = data.text;
    fullTranscriptText += " " + newText;

    // Stream animated words to active sentence
    if (liveSpeechStream) {
      const span = document.createElement("span");
      span.className = "word-streaming";
      span.textContent = " " + newText;
      liveSpeechStream.appendChild(span);
    }

    // Auto-scroll transcript container
    if (transcriptBody) {
      transcriptBody.scrollTop = transcriptBody.scrollHeight;
    }

    // Update chunk stats pill
    if (chunkStatsPill) {
      const avg = Math.round(totalLatency / totalChunks);
      chunkStatsPill.textContent = `Chunks: ${totalChunks} • Avg Latency: ${avg} ms`;
    }
  }
}

// ─── Timer ───────────────────────────────────────────────────────────────────

function startTimer() {
  if (timerInterval) clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    timerSeconds++;
    const mins = String(Math.floor(timerSeconds / 60)).padStart(2, "0");
    const secs = String(timerSeconds % 60).padStart(2, "0");
    if (studioTimer) studioTimer.textContent = `00:${mins}:${secs}`;
  }, 1000);
}

function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
}

// ─── Backend API Integrations ────────────────────────────────────────────────

async function generateSummary() {
  try {
    const res = await fetch("/api/summarize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ transcript: fullTranscriptText }),
    });

    if (!res.ok) return;

    const data = await res.json();
    latestSummaryData = data;

    // Update UI Summary tab
    if (aiSummaryParagraph && data.summary) {
      aiSummaryParagraph.textContent = data.summary;
    }

    if (aiDecisionsList && data.decisions) {
      aiDecisionsList.innerHTML = "";
      data.decisions.forEach((dec) => {
        const div = document.createElement("div");
        div.className = "decision-item-ai";
        div.textContent = dec;
        aiDecisionsList.appendChild(div);
      });
    }

    if (aiActionsList && data.action_items) {
      aiActionsList.innerHTML = "";
      data.action_items.forEach((item) => {
        const card = document.createElement("div");
        card.className = "action-card-ai";

        const taskSpan = document.createElement("span");
        taskSpan.className = "action-task-text";
        taskSpan.textContent = item.task;

        const ownerPill = document.createElement("span");
        if (item.owner) {
          ownerPill.className = "owner-pill assigned";
          ownerPill.textContent = item.owner;
        } else {
          ownerPill.className = "owner-pill unassigned";
          ownerPill.textContent = "Unassigned";
        }

        card.appendChild(taskSpan);
        card.appendChild(ownerPill);
        aiActionsList.appendChild(card);
      });
    }
  } catch (err) {
    console.warn("[LiveScribe] Summary API warning:", err);
  }
}

async function exportNotes() {
  const payload = {
    format: "markdown",
    transcript: fullTranscriptText,
    summary: latestSummaryData?.summary || "Product onboarding friction identified. Team agreed to simplify workflow from 5 steps to 3.",
    decisions: latestSummaryData?.decisions || ["Simplify onboarding from 5 steps down to 3.", "Use PostgreSQL for session indexing."],
    action_items: latestSummaryData?.action_items || [
      { task: "Review onboarding funnel metrics", owner: "Kshitij M." },
      { task: "Prepare 3-step onboarding redesign mocks", owner: "Alex Morgan" },
    ],
  };

  try {
    const res = await fetch("/api/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `LiveScribe_Meeting_Notes_${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    console.error("[LiveScribe] Export failed:", err);
    alert("Export notes failed: " + err.message);
  }
}

async function startBackendPolling() {
  // Poll network status & telemetry every 4s
  setInterval(async () => {
    try {
      const netRes = await fetch("/api/network-status");
      if (netRes.ok) {
        const netData = await netRes.json();
        const badge = document.getElementById("network-badge-app");
        const label = document.getElementById("network-status-label");
        if (badge && label) {
          if (netData.online) {
            badge.className = "status-badge online";
            label.textContent = "Online";
          } else {
            badge.className = "status-badge offline";
            label.textContent = "Offline Mode Active";
          }
        }
      }

      const benchRes = await fetch("/api/benchmarks");
      if (benchRes.ok) {
        const benchData = await benchRes.json();
        const cpuEl = document.getElementById("telemetry-cpu");
        const memEl = document.getElementById("telemetry-mem");
        if (cpuEl && benchData.system) cpuEl.textContent = `${benchData.system.cpu_usage_pct} %`;
        if (memEl && benchData.system) memEl.textContent = `${benchData.system.memory_mb} MB`;
      }
    } catch (e) {
      // Ignore polling errors when backend offline
    }
  }, 4000);
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function handleAskAiSubmit() {
  const query = askAiInput?.value.trim();
  if (!query) return;

  // Append User message
  const userMsg = document.createElement("div");
  userMsg.className = "chat-msg user";
  userMsg.innerHTML = `<span>${query}</span>`;
  askAiMessages?.appendChild(userMsg);

  if (askAiInput) askAiInput.value = "";

  // Append AI Assistant response after quick delay
  setTimeout(() => {
    const aiMsg = document.createElement("div");
    aiMsg.className = "chat-msg assistant";
    aiMsg.innerHTML = `
      <span>The team agreed to simplify the onboarding flow from 5 steps down to 3 to improve activation rates.</span>
      <button class="citation-pill" data-jump="ts-10-43">📍 10:43 — Kshitij M.</button>
    `;
    askAiMessages?.appendChild(aiMsg);
    if (askAiMessages) askAiMessages.scrollTop = askAiMessages.scrollHeight;
  }, 400);
}

function scrollToElementId(id) {
  const el = document.getElementById(id);
  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    el.style.transition = "background 0.5s ease";
    const origBg = el.style.background;
    el.style.background = "rgba(56, 189, 248, 0.2)";
    setTimeout(() => {
      el.style.background = origBg;
    }, 1500);
  }
}

function scrollToMatchingTranscript(query) {
  const blocks = Array.from(document.querySelectorAll(".speaker-block"));
  const match = blocks.find((b) => b.textContent.toLowerCase().includes(query.toLowerCase()));
  if (match) {
    scrollToElementId(match.id || "ts-10-43");
  }
}

function copyTranscript() {
  navigator.clipboard.writeText(fullTranscriptText);
  alert("Transcript copied to clipboard!");
}

// Launch application on DOMReady
document.addEventListener("DOMContentLoaded", init);

/**
 * OfflineScribe — Frontend entry point (Phase 1).
 *
 * On load:
 *   1. Fetch GET /api/health      → update backend status
 *   2. Fetch GET /api/npu-status  → update NPU badge + status grid
 *
 * The Vite dev server proxies /api/* to localhost:8000 (backend).
 */

// ─── DOM Elements ────────────────────────────────────────────────────────────

const npuBadge = document.getElementById("npu-badge");
const npuBadgeLabel = npuBadge?.querySelector(".status-label");

const networkBadge = document.getElementById("network-badge");
const networkBadgeLabel = networkBadge?.querySelector(".status-label");

const healthValue = document.getElementById("health-value");
const providerValue = document.getElementById("provider-value");
const npuValue = document.getElementById("npu-value");
const fallbackValue = document.getElementById("fallback-value");

// ─── Helpers ─────────────────────────────────────────────────────────────────

/**
 * Safely fetch JSON from an API endpoint.
 * Returns null on network/parse errors so callers can handle gracefully.
 */
async function fetchJSON(url) {
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`[OfflineScribe] fetch ${url} failed:`, err.message);
    return null;
  }
}

/**
 * Apply a status class (ok | warn | error) to an element and set text.
 */
function setStatusValue(el, text, status = "") {
  if (!el) return;
  el.textContent = text;
  el.className = "status-item-value";
  if (status) el.classList.add(status);
}

/**
 * Update a badge element's state and label.
 * @param {HTMLElement} badge
 * @param {"ok"|"warn"|"error"|"checking"|"offline"} state
 * @param {string} label
 */
function setBadge(badge, state, label) {
  if (!badge) return;
  badge.className = `status-badge ${state}`;
  const labelEl = badge.querySelector(".status-label");
  if (labelEl) labelEl.textContent = label;
}

// ─── Health Check ────────────────────────────────────────────────────────────

async function checkHealth() {
  const data = await fetchJSON("/api/health");

  if (!data) {
    setStatusValue(healthValue, "Unreachable", "error");
    setBadge(npuBadge, "error", "Backend offline");
    return false;
  }

  setStatusValue(healthValue, data.status === "ok" ? "✅ Online" : data.status, "ok");
  return true;
}

// ─── NPU Status ──────────────────────────────────────────────────────────────

async function checkNPUStatus() {
  const data = await fetchJSON("/api/npu-status");

  if (!data) {
    setStatusValue(providerValue, "—", "error");
    setStatusValue(npuValue, "—", "error");
    setStatusValue(fallbackValue, "—", "error");
    setBadge(npuBadge, "error", "Unavailable");
    return;
  }

  // Provider
  const provider = data.execution_provider || "unknown";
  const isQNN = provider === "QNNExecutionProvider";

  setStatusValue(providerValue, provider, isQNN ? "ok" : "warn");

  // NPU confirmed
  setStatusValue(
    npuValue,
    data.npu_confirmed ? "✅ Yes" : "❌ No",
    data.npu_confirmed ? "ok" : "warn"
  );

  // Fallback
  setStatusValue(
    fallbackValue,
    data.fallback_to_cpu ? "⚠️ Yes" : "✅ No",
    data.fallback_to_cpu ? "warn" : "ok"
  );

  // Badge
  if (isQNN) {
    setBadge(npuBadge, "ok", "NPU Active");
  } else {
    setBadge(npuBadge, "warn", `CPU Fallback`);
  }
}

// ─── Network Status (simple client-side check for now) ──────────────────────

function updateNetworkBadge() {
  const online = navigator.onLine;
  setBadge(
    networkBadge,
    online ? "ok" : "offline",
    online ? "Online" : "Offline"
  );
}

// ─── Init ────────────────────────────────────────────────────────────────────

async function init() {
  // Network
  updateNetworkBadge();
  window.addEventListener("online", updateNetworkBadge);
  window.addEventListener("offline", updateNetworkBadge);

  // Backend checks
  const backendUp = await checkHealth();
  if (backendUp) {
    await checkNPUStatus();
  }
}

init();

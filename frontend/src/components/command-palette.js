/**
 * CommandPalette — Raycast-inspired Cmd+K command palette modal.
 *
 * Provides real-time search across transcripts, topics, and app actions.
 */

export class CommandPalette {
  /**
   * @param {Object} opts
   * @param {function} opts.onSelectTranscriptMatch
   * @param {function} opts.onTriggerSummarize
   * @param {function} opts.onTriggerExport
   * @param {function} opts.onToggleRecord
   */
  constructor(opts = {}) {
    this.onSelectMatch = opts.onSelectTranscriptMatch || (() => {});
    this.onSummarize = opts.onTriggerSummarize || (() => {});
    this.onExport = opts.onTriggerExport || (() => {});
    this.onToggleRecord = opts.onToggleRecord || (() => {});

    this.dialog = null;
    this.input = null;
    this.resultsContainer = null;
    this.isOpen = false;

    this._initUI();
    this._bindKeyboard();
  }

  _initUI() {
    // Create modal dialog HTML if not present
    let overlay = document.getElementById("cmd-palette-overlay");
    if (!overlay) {
      overlay = document.createElement("div");
      overlay.id = "cmd-palette-overlay";
      overlay.className = "cmd-palette-overlay hidden";
      overlay.innerHTML = `
        <div class="cmd-palette-card glass-card">
          <div class="cmd-palette-header">
            <span class="cmd-search-icon">🔍</span>
            <input type="text" id="cmd-palette-input" placeholder="Search transcript, commands, or topics... (Esc to close)" autocomplete="off" />
            <kbd class="cmd-kbd">ESC</kbd>
          </div>
          <div id="cmd-palette-results" class="cmd-palette-results">
            <div class="cmd-group-title">Quick Actions</div>
            <div class="cmd-item" data-action="record">
              <span class="cmd-item-icon">🎙</span>
              <span class="cmd-item-label">Start / Stop Recording</span>
              <kbd class="cmd-item-key">Space</kbd>
            </div>
            <div class="cmd-item" data-action="summarize">
              <span class="cmd-item-icon">⚡</span>
              <span class="cmd-item-label">Generate AI Meeting Summary</span>
              <kbd class="cmd-item-key">⌘S</kbd>
            </div>
            <div class="cmd-item" data-action="export">
              <span class="cmd-item-icon">📥</span>
              <span class="cmd-item-label">Export Notes as Markdown</span>
              <kbd class="cmd-item-key">⌘E</kbd>
            </div>
          </div>
        </div>
      `;
      document.body.appendChild(overlay);
    }

    this.overlay = overlay;
    this.input = overlay.querySelector("#cmd-palette-input");
    this.resultsContainer = overlay.querySelector("#cmd-palette-results");

    // Close on overlay click outside card
    this.overlay.addEventListener("click", (e) => {
      if (e.target === this.overlay) this.close();
    });

    // Input search handler
    this.input.addEventListener("input", () => this._handleSearch());

    // Result item click
    this.resultsContainer.addEventListener("click", (e) => {
      const item = e.target.closest(".cmd-item");
      if (!item) return;

      const action = item.getAttribute("data-action");
      if (action === "record") this.onToggleRecord();
      else if (action === "summarize") this.onSummarize();
      else if (action === "export") this.onExport();
      else if (action === "transcript-match") {
        const text = item.getAttribute("data-text");
        this.onSelectMatch(text);
      }
      this.close();
    });
  }

  _bindKeyboard() {
    window.addEventListener("keydown", (e) => {
      // Cmd+K or Ctrl+K
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        this.toggle();
      } else if (e.key === "Escape" && this.isOpen) {
        this.close();
      }
    });
  }

  toggle() {
    if (this.isOpen) this.close();
    else this.open();
  }

  open() {
    this.isOpen = true;
    this.overlay.classList.remove("hidden");
    setTimeout(() => this.input.focus(), 50);
  }

  close() {
    this.isOpen = false;
    this.overlay.classList.add("hidden");
    if (this.input) this.input.value = "";
  }

  _handleSearch() {
    const query = (this.input.value || "").trim().toLowerCase();
    if (!query) {
      this._renderDefaultActions();
      return;
    }

    // Search live transcript DOM
    const chunks = Array.from(document.querySelectorAll(".transcript-chunk"));
    const matches = [];

    chunks.forEach((chunk) => {
      const text = chunk.textContent.trim();
      if (text.toLowerCase().includes(query)) {
        matches.push(text);
      }
    });

    this.resultsContainer.innerHTML = "";

    if (matches.length > 0) {
      const groupTitle = document.createElement("div");
      groupTitle.className = "cmd-group-title";
      groupTitle.textContent = `Transcript Matches (${matches.length})`;
      this.resultsContainer.appendChild(groupTitle);

      matches.slice(0, 8).forEach((text) => {
        const item = document.createElement("div");
        item.className = "cmd-item";
        item.setAttribute("data-action", "transcript-match");
        item.setAttribute("data-text", text);
        item.innerHTML = `
          <span class="cmd-item-icon">💬</span>
          <span class="cmd-item-label">${this._highlightText(text, query)}</span>
          <span class="cmd-item-meta">Jump to line</span>
        `;
        this.resultsContainer.appendChild(item);
      });
    } else {
      const empty = document.createElement("div");
      empty.className = "cmd-empty-msg";
      empty.textContent = `No transcript matches found for "${query}"`;
      this.resultsContainer.appendChild(empty);
    }
  }

  _renderDefaultActions() {
    this.resultsContainer.innerHTML = `
      <div class="cmd-group-title">Quick Actions</div>
      <div class="cmd-item" data-action="record">
        <span class="cmd-item-icon">🎙</span>
        <span class="cmd-item-label">Start / Stop Recording</span>
        <kbd class="cmd-item-key">Space</kbd>
      </div>
      <div class="cmd-item" data-action="summarize">
        <span class="cmd-item-icon">⚡</span>
        <span class="cmd-item-label">Generate AI Meeting Summary</span>
        <kbd class="cmd-item-key">⌘S</kbd>
      </div>
      <div class="cmd-item" data-action="export">
        <span class="cmd-item-icon">📥</span>
        <span class="cmd-item-label">Export Notes as Markdown</span>
        <kbd class="cmd-item-key">⌘E</kbd>
      </div>
    `;
  }

  _highlightText(text, query) {
    const idx = text.toLowerCase().indexOf(query);
    if (idx === -1) return text;
    const before = text.slice(0, idx);
    const match = text.slice(idx, idx + query.length);
    const after = text.slice(idx + query.length);
    return `${before}<mark class="cmd-highlight">${match}</mark>${after}`;
  }
}

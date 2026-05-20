/*
 * Noble Mind Press — Study Tools
 *
 * Drop-in module that adds three features to any book chapter page:
 *
 *   1. URL ?q=<term>  →  scroll to and highlight the term (used by the
 *                        books.html search to land readers on the match)
 *   2. Text selection →  popup with "Highlight" / "Highlight + Note"
 *                        Highlights persist per-page in localStorage.
 *   3. Floating "📓" button bottom-right → opens a panel listing the
 *                        current chapter's saved highlights and notes,
 *                        with click-to-scroll and delete controls.
 *
 * All state is local to the user's browser. No server calls. No
 * accounts. Works offline.
 *
 * Include from any chapter HTML with:
 *   <script src="/assets/study-tools.js" defer></script>
 */
(function () {
  "use strict";

  // ---- styling, injected once ----------------------------------------------

  const STYLE = `
    mark.nm-search-hit {
      background: rgba(196, 168, 84, 0.55);
      color: inherit;
      padding: 0 2px;
      border-radius: 2px;
    }
    mark.nm-highlight {
      background: rgba(255, 235, 130, 0.55);
      color: inherit;
      padding: 0 2px;
      border-radius: 2px;
      cursor: pointer;
    }
    mark.nm-highlight[data-has-note="true"] {
      background: rgba(255, 200, 120, 0.65);
      border-bottom: 2px solid rgba(196, 81, 63, 0.7);
    }
    .nm-selection-popup {
      position: absolute;
      z-index: 9999;
      display: none;
      gap: 6px;
      padding: 6px;
      background: rgba(15, 15, 18, 0.96);
      border: 1px solid rgba(196, 168, 84, 0.4);
      border-radius: 8px;
      box-shadow: 0 6px 24px rgba(0,0,0,0.45);
      font-family: 'Segoe UI', Georgia, serif;
    }
    .nm-selection-popup.visible { display: flex; }
    .nm-selection-popup button {
      background: rgba(196, 168, 84, 0.12);
      color: #f0ece4;
      border: 1px solid rgba(196, 168, 84, 0.25);
      border-radius: 6px;
      padding: 6px 12px;
      cursor: pointer;
      font-size: 0.85rem;
      font-family: inherit;
    }
    .nm-selection-popup button:hover {
      background: rgba(196, 168, 84, 0.22);
      border-color: rgba(196, 168, 84, 0.5);
    }
    .nm-tools-fab {
      position: fixed;
      right: 20px; bottom: 20px;
      width: 52px; height: 52px;
      border-radius: 50%;
      background: rgba(15, 15, 18, 0.92);
      border: 1px solid rgba(196, 168, 84, 0.45);
      color: rgba(196, 168, 84, 0.95);
      font-size: 1.4rem;
      cursor: pointer;
      z-index: 9998;
      display: flex; align-items: center; justify-content: center;
      box-shadow: 0 6px 24px rgba(0,0,0,0.5);
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .nm-tools-fab:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 28px rgba(196,168,84,0.35);
    }
    .nm-tools-fab .nm-fab-count {
      position: absolute;
      top: -4px; right: -4px;
      background: rgba(196, 81, 63, 0.95);
      color: #fff;
      min-width: 20px; height: 20px;
      border-radius: 10px;
      font-size: 0.7rem;
      font-weight: 700;
      display: flex; align-items: center; justify-content: center;
      padding: 0 5px;
    }
    .nm-tools-panel {
      position: fixed;
      right: 20px; bottom: 84px;
      width: min(380px, calc(100vw - 40px));
      max-height: 70vh;
      background: rgba(15, 15, 18, 0.97);
      border: 1px solid rgba(196, 168, 84, 0.35);
      border-radius: 14px;
      box-shadow: 0 12px 40px rgba(0,0,0,0.55);
      z-index: 9998;
      display: none;
      flex-direction: column;
      overflow: hidden;
      font-family: 'Segoe UI', Georgia, serif;
    }
    .nm-tools-panel.visible { display: flex; }
    .nm-tools-panel header {
      padding: 12px 16px;
      background: rgba(0,0,0,0.35);
      border-bottom: 1px solid rgba(196, 168, 84, 0.2);
      display: flex; justify-content: space-between; align-items: center;
    }
    .nm-tools-panel header h3 {
      margin: 0;
      font-size: 1rem;
      color: rgba(196, 168, 84, 0.95);
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }
    .nm-tools-panel header .nm-close {
      background: none; border: none;
      color: rgba(192, 184, 168, 0.8);
      font-size: 1.3rem;
      cursor: pointer;
      line-height: 1;
    }
    .nm-tools-panel .nm-list {
      overflow-y: auto;
      padding: 8px 12px;
      flex: 1;
    }
    .nm-tools-panel .nm-empty {
      padding: 20px 16px;
      text-align: center;
      color: rgba(192, 184, 168, 0.7);
      font-size: 0.9rem;
      line-height: 1.5;
    }
    .nm-tools-panel .nm-item {
      padding: 10px 0;
      border-bottom: 1px solid rgba(148, 163, 184, 0.12);
      font-size: 0.85rem;
      line-height: 1.5;
    }
    .nm-tools-panel .nm-item:last-child { border-bottom: none; }
    .nm-tools-panel .nm-item .nm-quote {
      color: rgba(240, 236, 228, 0.95);
      cursor: pointer;
    }
    .nm-tools-panel .nm-item .nm-quote:hover { color: rgba(196, 168, 84, 1); }
    .nm-tools-panel .nm-item .nm-note {
      margin-top: 6px;
      padding: 6px 8px;
      background: rgba(196, 168, 84, 0.07);
      border-left: 2px solid rgba(196, 168, 84, 0.55);
      color: rgba(192, 184, 168, 0.95);
      font-style: italic;
      font-size: 0.8rem;
    }
    .nm-tools-panel .nm-item .nm-actions {
      display: flex; gap: 8px;
      margin-top: 6px;
      font-size: 0.75rem;
    }
    .nm-tools-panel .nm-item .nm-actions button {
      background: none; border: none;
      color: rgba(192, 184, 168, 0.7);
      cursor: pointer;
      padding: 2px 6px;
      font-size: 0.75rem;
      font-family: inherit;
    }
    .nm-tools-panel .nm-item .nm-actions button:hover {
      color: rgba(196, 168, 84, 1);
    }
    .nm-note-modal {
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.7);
      z-index: 10000;
      display: none;
      align-items: center; justify-content: center;
      padding: 20px;
    }
    .nm-note-modal.visible { display: flex; }
    .nm-note-modal .nm-modal-card {
      background: rgba(15, 15, 18, 0.98);
      border: 1px solid rgba(196, 168, 84, 0.35);
      border-radius: 14px;
      padding: 20px;
      max-width: 460px; width: 100%;
      box-shadow: 0 12px 40px rgba(0,0,0,0.6);
      font-family: 'Segoe UI', Georgia, serif;
    }
    .nm-note-modal h3 {
      margin: 0 0 10px 0;
      font-size: 0.95rem;
      color: rgba(196, 168, 84, 0.95);
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }
    .nm-note-modal .nm-modal-quote {
      padding: 10px 12px;
      background: rgba(255, 235, 130, 0.12);
      border-left: 2px solid rgba(196, 168, 84, 0.7);
      color: rgba(240, 236, 228, 0.95);
      font-size: 0.9rem;
      line-height: 1.5;
      margin-bottom: 12px;
      max-height: 120px;
      overflow-y: auto;
    }
    .nm-note-modal textarea {
      width: 100%;
      min-height: 120px;
      padding: 10px;
      background: rgba(0,0,0,0.4);
      border: 1px solid rgba(148, 163, 184, 0.25);
      border-radius: 8px;
      color: rgba(240, 236, 228, 0.95);
      font-family: inherit;
      font-size: 0.9rem;
      resize: vertical;
    }
    .nm-note-modal textarea:focus {
      outline: none;
      border-color: rgba(196, 168, 84, 0.6);
    }
    .nm-note-modal .nm-modal-actions {
      display: flex; justify-content: flex-end; gap: 10px;
      margin-top: 14px;
    }
    .nm-note-modal .nm-modal-actions button {
      padding: 8px 18px;
      border-radius: 8px;
      cursor: pointer;
      font-family: inherit;
      font-size: 0.85rem;
      border: 1px solid;
    }
    .nm-note-modal .nm-modal-actions .nm-btn-cancel {
      background: rgba(0,0,0,0.3);
      border-color: rgba(148, 163, 184, 0.2);
      color: rgba(192, 184, 168, 0.9);
    }
    .nm-note-modal .nm-modal-actions .nm-btn-save {
      background: rgba(196, 168, 84, 0.18);
      border-color: rgba(196, 168, 84, 0.5);
      color: rgba(255, 235, 130, 0.95);
    }
    .nm-note-modal .nm-modal-actions button:hover { filter: brightness(1.15); }
    @media (max-width: 600px) {
      .nm-tools-fab { right: 14px; bottom: 14px; width: 48px; height: 48px; font-size: 1.25rem; }
      .nm-tools-panel { right: 10px; left: 10px; width: auto; bottom: 70px; }
    }
  `;

  // ---- localStorage helpers -----------------------------------------------

  const STORAGE_KEY = "nm_study_" + window.location.pathname;

  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return { highlights: [] };
      const parsed = JSON.parse(raw);
      return { highlights: Array.isArray(parsed.highlights) ? parsed.highlights : [] };
    } catch (e) { return { highlights: [] }; }
  }

  function saveState(state) {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }
    catch (e) {}
  }

  let state = loadState();

  // ---- text wrapping --------------------------------------------------------

  function findContentRoot() {
    return document.querySelector(".content")
        || document.querySelector(".chapter-body")
        || document.querySelector(".glass-page-inner")
        || document.body;
  }

  function escapeRegExp(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  /**
   * Find the first text-node range matching `needle`. If `precedingContext`
   * is provided, the match must be immediately preceded by that context
   * (used to disambiguate when the same phrase appears multiple times).
   * Returns a Range or null.
   */
  function findTextRange(root, needle, precedingContext) {
    if (!needle) return null;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: (node) => {
        const p = node.parentElement;
        if (!p) return NodeFilter.FILTER_REJECT;
        // Skip text inside our own UI
        if (p.closest(".nm-tools-fab, .nm-tools-panel, .nm-selection-popup, .nm-note-modal")) {
          return NodeFilter.FILTER_REJECT;
        }
        if (p.tagName === "SCRIPT" || p.tagName === "STYLE") {
          return NodeFilter.FILTER_REJECT;
        }
        return NodeFilter.FILTER_ACCEPT;
      },
    });
    const lowerNeedle = needle.toLowerCase();
    const lowerCtx = precedingContext ? precedingContext.toLowerCase() : null;
    let prevText = "";
    let node;
    while ((node = walker.nextNode())) {
      const txt = node.nodeValue;
      const lower = txt.toLowerCase();
      let start = 0;
      while (true) {
        const idx = lower.indexOf(lowerNeedle, start);
        if (idx === -1) break;
        // If we have context, check that the preceding text matches.
        if (lowerCtx) {
          const beforeChars = (prevText + txt.substring(0, idx)).slice(-lowerCtx.length);
          if (beforeChars !== lowerCtx) {
            start = idx + 1;
            continue;
          }
        }
        const range = document.createRange();
        range.setStart(node, idx);
        range.setEnd(node, idx + needle.length);
        return range;
      }
      prevText = (prevText + txt).slice(-200); // keep a sliding window
    }
    return null;
  }

  function wrapRangeWith(range, tagName, attrs) {
    if (!range || range.collapsed) return null;
    try {
      const wrapper = document.createElement(tagName);
      if (attrs) {
        for (const k in attrs) wrapper.setAttribute(k, attrs[k]);
      }
      // Only safe to surroundContents when range is within a single text node
      range.surroundContents(wrapper);
      return wrapper;
    } catch (e) {
      // Range spans multiple nodes — fall back to extracting and reinserting
      try {
        const wrapper = document.createElement(tagName);
        if (attrs) for (const k in attrs) wrapper.setAttribute(k, attrs[k]);
        wrapper.appendChild(range.extractContents());
        range.insertNode(wrapper);
        return wrapper;
      } catch (e2) {
        return null;
      }
    }
  }

  // ---- URL ?q= search highlight --------------------------------------------

  function handleSearchQuery() {
    const params = new URLSearchParams(window.location.search);
    const q = params.get("q");
    if (!q || q.length < 2) return;
    const root = findContentRoot();
    const range = findTextRange(root, q, null);
    if (range) {
      const mark = wrapRangeWith(range, "mark", { class: "nm-search-hit" });
      if (mark) {
        mark.scrollIntoView({ behavior: "smooth", block: "center" });
        // Clean up the ?q= from the URL so refreshing doesn't re-trigger
        const newUrl = window.location.pathname + window.location.hash;
        history.replaceState(null, "", newUrl);
      }
    }
  }

  // ---- restore persisted highlights ----------------------------------------

  function applyPersistedHighlights() {
    const root = findContentRoot();
    for (const h of state.highlights) {
      const range = findTextRange(root, h.text, h.context);
      if (range) {
        wrapRangeWith(range, "mark", {
          class: "nm-highlight",
          "data-id": h.id,
          "data-has-note": h.note ? "true" : "false",
        });
      }
    }
  }

  // ---- selection popup ------------------------------------------------------

  let popup = null;
  let activeRange = null;

  function ensurePopup() {
    if (popup) return popup;
    popup = document.createElement("div");
    popup.className = "nm-selection-popup";
    popup.innerHTML = `
      <button data-action="highlight">Highlight</button>
      <button data-action="highlight-note">Highlight + Note</button>
    `;
    document.body.appendChild(popup);
    popup.addEventListener("mousedown", (e) => e.preventDefault());
    popup.addEventListener("click", (e) => {
      const btn = e.target.closest("button");
      if (!btn) return;
      const action = btn.getAttribute("data-action");
      if (action === "highlight") createHighlight(false);
      if (action === "highlight-note") createHighlight(true);
    });
    return popup;
  }

  function showPopupAtSelection() {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed) { hidePopup(); return; }
    const text = sel.toString().trim();
    if (text.length < 2) { hidePopup(); return; }

    const range = sel.getRangeAt(0);
    const root = findContentRoot();
    if (!root.contains(range.commonAncestorContainer)) { hidePopup(); return; }
    if (range.commonAncestorContainer.parentElement &&
        range.commonAncestorContainer.parentElement.closest(".nm-tools-fab, .nm-tools-panel")) {
      hidePopup();
      return;
    }

    activeRange = range.cloneRange();
    const rect = range.getBoundingClientRect();
    const p = ensurePopup();
    p.classList.add("visible");
    // Position above the selection if there's room, otherwise below
    const popupHeight = 44;
    const top = (rect.top + window.scrollY > popupHeight + 10)
      ? rect.top + window.scrollY - popupHeight - 8
      : rect.bottom + window.scrollY + 8;
    let left = rect.left + window.scrollX + (rect.width / 2) - 100;
    left = Math.max(8, Math.min(left, window.innerWidth - 220));
    p.style.top = top + "px";
    p.style.left = left + "px";
  }

  function hidePopup() {
    if (popup) popup.classList.remove("visible");
  }

  // ---- highlight creation --------------------------------------------------

  function getPrecedingContext(range, n) {
    const node = range.startContainer;
    if (node.nodeType !== Node.TEXT_NODE) return "";
    const before = node.nodeValue.substring(0, range.startOffset);
    if (before.length >= n) return before.slice(-n);
    // Walk backward through previous text nodes to gather enough context
    const root = findContentRoot();
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
    const nodes = [];
    let n2;
    while ((n2 = walker.nextNode())) {
      nodes.push(n2);
      if (n2 === node) break;
    }
    let acc = before;
    for (let i = nodes.length - 2; i >= 0 && acc.length < n; i--) {
      acc = nodes[i].nodeValue + acc;
    }
    return acc.slice(-n);
  }

  function createHighlight(promptForNote) {
    if (!activeRange) { hidePopup(); return; }
    const text = activeRange.toString().trim();
    if (!text) { hidePopup(); return; }

    const context = getPrecedingContext(activeRange, 30);
    const id = "h" + Date.now() + "-" + Math.floor(Math.random() * 1000);
    const highlight = {
      id, text, context, color: "yellow",
      note: "", ts: Date.now(),
    };

    const wrapped = wrapRangeWith(activeRange, "mark", {
      class: "nm-highlight",
      "data-id": id,
      "data-has-note": "false",
    });
    if (!wrapped) { hidePopup(); return; }

    state.highlights.push(highlight);
    saveState(state);
    refreshFabCount();
    hidePopup();
    window.getSelection().removeAllRanges();
    activeRange = null;

    if (promptForNote) {
      openNoteModal(highlight);
    }
  }

  function deleteHighlight(id) {
    state.highlights = state.highlights.filter((h) => h.id !== id);
    saveState(state);
    document.querySelectorAll(`mark.nm-highlight[data-id="${id}"]`).forEach((el) => {
      const parent = el.parentNode;
      while (el.firstChild) parent.insertBefore(el.firstChild, el);
      parent.removeChild(el);
      parent.normalize();
    });
    refreshFabCount();
    renderPanel();
  }

  // ---- note modal -----------------------------------------------------------

  let noteModal = null;

  function ensureNoteModal() {
    if (noteModal) return noteModal;
    noteModal = document.createElement("div");
    noteModal.className = "nm-note-modal";
    noteModal.innerHTML = `
      <div class="nm-modal-card">
        <h3>Note</h3>
        <div class="nm-modal-quote"></div>
        <textarea placeholder="Type your note about this highlight..."></textarea>
        <div class="nm-modal-actions">
          <button class="nm-btn-cancel">Cancel</button>
          <button class="nm-btn-save">Save</button>
        </div>
      </div>
    `;
    document.body.appendChild(noteModal);
    noteModal.addEventListener("click", (e) => {
      if (e.target === noteModal) closeNoteModal();
    });
    noteModal.querySelector(".nm-btn-cancel").addEventListener("click", closeNoteModal);
    noteModal.querySelector(".nm-btn-save").addEventListener("click", saveNoteFromModal);
    return noteModal;
  }

  let activeNoteHighlight = null;

  function openNoteModal(highlight) {
    activeNoteHighlight = highlight;
    const m = ensureNoteModal();
    m.querySelector(".nm-modal-quote").textContent = highlight.text;
    m.querySelector("textarea").value = highlight.note || "";
    m.classList.add("visible");
    setTimeout(() => m.querySelector("textarea").focus(), 50);
  }

  function closeNoteModal() {
    if (noteModal) noteModal.classList.remove("visible");
    activeNoteHighlight = null;
  }

  function saveNoteFromModal() {
    if (!activeNoteHighlight) return;
    const noteText = noteModal.querySelector("textarea").value.trim();
    activeNoteHighlight.note = noteText;
    const h = state.highlights.find((x) => x.id === activeNoteHighlight.id);
    if (h) {
      h.note = noteText;
      saveState(state);
    }
    document.querySelectorAll(`mark.nm-highlight[data-id="${activeNoteHighlight.id}"]`).forEach((el) => {
      el.setAttribute("data-has-note", noteText ? "true" : "false");
    });
    renderPanel();
    closeNoteModal();
  }

  // ---- floating button + panel ---------------------------------------------

  let fab = null;
  let panel = null;

  function ensureFab() {
    if (fab) return fab;
    fab = document.createElement("button");
    fab.className = "nm-tools-fab";
    fab.setAttribute("aria-label", "My highlights and notes");
    fab.innerHTML = '📓<span class="nm-fab-count" style="display:none">0</span>';
    fab.addEventListener("click", togglePanel);
    document.body.appendChild(fab);
    return fab;
  }

  function refreshFabCount() {
    if (!fab) return;
    const count = state.highlights.length;
    const el = fab.querySelector(".nm-fab-count");
    if (count > 0) {
      el.textContent = String(count);
      el.style.display = "flex";
    } else {
      el.style.display = "none";
    }
  }

  function ensurePanel() {
    if (panel) return panel;
    panel = document.createElement("div");
    panel.className = "nm-tools-panel";
    panel.innerHTML = `
      <header>
        <h3>My Highlights</h3>
        <button class="nm-close" aria-label="Close">×</button>
      </header>
      <div class="nm-list"></div>
    `;
    document.body.appendChild(panel);
    panel.querySelector(".nm-close").addEventListener("click", () => {
      panel.classList.remove("visible");
    });
    return panel;
  }

  function togglePanel() {
    const p = ensurePanel();
    if (p.classList.contains("visible")) {
      p.classList.remove("visible");
    } else {
      renderPanel();
      p.classList.add("visible");
    }
  }

  function renderPanel() {
    if (!panel) return;
    const list = panel.querySelector(".nm-list");
    if (state.highlights.length === 0) {
      list.innerHTML = '<div class="nm-empty">No highlights yet. Select any text on this page to save a highlight or attach a note.</div>';
      return;
    }
    const sorted = [...state.highlights].sort((a, b) => a.ts - b.ts);
    list.innerHTML = sorted.map((h) => `
      <div class="nm-item">
        <div class="nm-quote" data-id="${h.id}">"${escapeHtml(h.text)}"</div>
        ${h.note ? `<div class="nm-note">${escapeHtml(h.note)}</div>` : ""}
        <div class="nm-actions">
          <button data-action="note" data-id="${h.id}">${h.note ? "Edit note" : "Add note"}</button>
          <button data-action="delete" data-id="${h.id}">Delete</button>
        </div>
      </div>
    `).join("");

    list.querySelectorAll(".nm-quote").forEach((q) => {
      q.addEventListener("click", () => {
        const id = q.getAttribute("data-id");
        const mark = document.querySelector(`mark.nm-highlight[data-id="${id}"]`);
        if (mark) {
          mark.scrollIntoView({ behavior: "smooth", block: "center" });
          panel.classList.remove("visible");
        }
      });
    });
    list.querySelectorAll("button[data-action]").forEach((b) => {
      b.addEventListener("click", (e) => {
        const action = b.getAttribute("data-action");
        const id = b.getAttribute("data-id");
        if (action === "delete") {
          if (confirm("Delete this highlight?")) deleteHighlight(id);
        } else if (action === "note") {
          const h = state.highlights.find((x) => x.id === id);
          if (h) openNoteModal(h);
        }
      });
    });
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  // ---- existing highlight click → open note --------------------------------

  function bindHighlightClicks() {
    document.addEventListener("click", (e) => {
      const mark = e.target.closest("mark.nm-highlight");
      if (!mark) return;
      const id = mark.getAttribute("data-id");
      const h = state.highlights.find((x) => x.id === id);
      if (h) openNoteModal(h);
    });
  }

  // ---- init -----------------------------------------------------------------

  function injectStyle() {
    const style = document.createElement("style");
    style.textContent = STYLE;
    document.head.appendChild(style);
  }

  function init() {
    injectStyle();
    handleSearchQuery();
    applyPersistedHighlights();
    ensureFab();
    refreshFabCount();
    bindHighlightClicks();

    // Selection popup
    let popupTimer = null;
    document.addEventListener("selectionchange", () => {
      if (popupTimer) clearTimeout(popupTimer);
      popupTimer = setTimeout(showPopupAtSelection, 150);
    });
    document.addEventListener("mousedown", (e) => {
      if (e.target.closest(".nm-selection-popup, .nm-tools-fab, .nm-tools-panel, .nm-note-modal")) return;
      hidePopup();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

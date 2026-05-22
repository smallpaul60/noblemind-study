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
    .nm-tools-panel .nm-toolbar {
      display: flex;
      gap: 6px;
      padding: 8px 12px;
      background: rgba(0,0,0,0.2);
      border-bottom: 1px solid rgba(196, 168, 84, 0.12);
    }
    .nm-tools-panel .nm-toolbar button {
      flex: 1;
      background: rgba(196, 168, 84, 0.1);
      border: 1px solid rgba(196, 168, 84, 0.22);
      border-radius: 6px;
      color: rgba(240, 236, 228, 0.92);
      padding: 6px 10px;
      cursor: pointer;
      font-family: inherit;
      font-size: 0.78rem;
      letter-spacing: 0.02em;
    }
    .nm-tools-panel .nm-toolbar button:hover {
      background: rgba(196, 168, 84, 0.2);
      border-color: rgba(196, 168, 84, 0.5);
      color: rgba(255, 235, 130, 0.95);
    }
    .nm-tools-panel .nm-toolbar .nm-toolbar-msg {
      font-size: 0.72rem;
      color: rgba(192, 184, 168, 0.75);
      padding: 4px 6px;
      align-self: center;
      font-style: italic;
    }
    .nm-tools-panel .nm-search-row {
      padding: 8px 12px;
      border-bottom: 1px solid rgba(196, 168, 84, 0.12);
      background: rgba(0,0,0,0.18);
    }
    .nm-tools-panel .nm-search-input {
      width: 100%;
      padding: 7px 10px;
      background: rgba(0,0,0,0.45);
      border: 1px solid rgba(148, 163, 184, 0.25);
      border-radius: 6px;
      color: rgba(240, 236, 228, 0.95);
      font-family: inherit;
      font-size: 0.82rem;
      box-sizing: border-box;
    }
    .nm-tools-panel .nm-search-input:focus {
      outline: none;
      border-color: rgba(196, 168, 84, 0.6);
      background: rgba(0,0,0,0.6);
    }
    .nm-tools-panel .nm-search-input::placeholder {
      color: rgba(192, 184, 168, 0.55);
      font-style: italic;
    }
    .nm-tools-panel .nm-item .nm-where {
      display: block;
      font-size: 0.72rem;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      color: rgba(196, 168, 84, 0.85);
      margin-bottom: 4px;
    }
    .nm-tools-panel .nm-item .nm-where .nm-where-sep {
      color: rgba(192, 184, 168, 0.45);
      margin: 0 4px;
    }
    .nm-tools-panel .nm-item mark.nm-match {
      background: rgba(255, 235, 130, 0.45);
      color: inherit;
      padding: 0 1px;
      border-radius: 2px;
    }
    .nm-help-fab {
      position: fixed;
      left: 20px; bottom: 20px;
      padding: 9px 16px;
      border-radius: 22px;
      background: rgba(15, 15, 18, 0.92);
      border: 1px solid rgba(196, 168, 84, 0.45);
      color: rgba(196, 168, 84, 0.95);
      font-size: 0.85rem;
      font-family: 'Segoe UI', Georgia, serif;
      letter-spacing: 0.04em;
      cursor: pointer;
      z-index: 9998;
      box-shadow: 0 6px 24px rgba(0,0,0,0.5);
      transition: transform 0.2s, box-shadow 0.2s, background 0.2s;
    }
    .nm-help-fab:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 28px rgba(196,168,84,0.35);
      background: rgba(20, 20, 24, 0.96);
    }
    .nm-help-fab .nm-help-icon {
      display: inline-block;
      width: 18px; height: 18px;
      border: 1px solid rgba(196, 168, 84, 0.65);
      border-radius: 50%;
      text-align: center;
      line-height: 16px;
      font-size: 0.78rem;
      margin-right: 7px;
      vertical-align: -2px;
    }
    .nm-help-popup {
      position: fixed;
      top: 80px; right: 30px;
      width: min(380px, calc(100vw - 30px));
      max-height: 80vh;
      background: rgba(15, 15, 18, 0.98);
      border: 1px solid rgba(196, 168, 84, 0.4);
      border-radius: 14px;
      box-shadow: 0 16px 48px rgba(0,0,0,0.6);
      z-index: 10001;
      display: none;
      flex-direction: column;
      overflow: hidden;
      font-family: 'Segoe UI', Georgia, serif;
    }
    .nm-help-popup.visible { display: flex; }
    .nm-help-popup-header {
      padding: 12px 16px;
      background: rgba(0,0,0,0.45);
      border-bottom: 1px solid rgba(196, 168, 84, 0.22);
      display: flex; justify-content: space-between; align-items: center;
      cursor: move;
      user-select: none;
      touch-action: none;
    }
    .nm-help-popup-header h3 {
      margin: 0;
      font-size: 0.95rem;
      color: rgba(196, 168, 84, 0.95);
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }
    .nm-help-popup-header .nm-help-close {
      background: none;
      border: none;
      color: rgba(192, 184, 168, 0.85);
      font-size: 1.35rem;
      line-height: 1;
      cursor: pointer;
      padding: 0 4px;
    }
    .nm-help-popup-header .nm-help-close:hover {
      color: rgba(255, 235, 130, 0.95);
    }
    .nm-help-popup-body {
      padding: 14px 18px 18px 18px;
      overflow-y: auto;
      color: rgba(232, 226, 212, 0.92);
      font-size: 0.88rem;
      line-height: 1.55;
    }
    .nm-help-popup-body h4 {
      margin: 14px 0 6px 0;
      font-size: 0.8rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: rgba(196, 168, 84, 0.95);
    }
    .nm-help-popup-body h4:first-child {
      margin-top: 0;
    }
    .nm-help-popup-body p {
      margin: 0 0 8px 0;
    }
    .nm-help-popup-body ul {
      margin: 0 0 8px 0;
      padding-left: 20px;
    }
    .nm-help-popup-body li {
      margin: 0 0 4px 0;
    }
    .nm-help-popup-body code,
    .nm-help-popup-body kbd {
      background: rgba(196, 168, 84, 0.14);
      padding: 1px 5px;
      border-radius: 4px;
      font-size: 0.82em;
      font-family: 'Consolas', 'Menlo', monospace;
      color: rgba(255, 235, 130, 0.95);
    }
    .nm-help-popup-body .nm-help-hint {
      font-size: 0.78rem;
      color: rgba(192, 184, 168, 0.75);
      font-style: italic;
      margin-top: 6px;
    }
    @media (max-width: 600px) {
      .nm-tools-fab { right: 14px; bottom: 14px; width: 48px; height: 48px; font-size: 1.25rem; }
      .nm-tools-panel { right: 10px; left: 10px; width: auto; bottom: 70px; }
      .nm-help-fab { left: 14px; bottom: 14px; padding: 8px 13px; font-size: 0.8rem; }
      .nm-help-popup { top: 10px; left: 10px; right: 10px; width: auto; max-height: 85vh; }
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

  // ---- export / import backup ----------------------------------------------

  const STORAGE_PREFIX = "nm_study_";
  const BACKUP_FORMAT = "noblemind-highlights-v1";

  function collectAllHighlights() {
    const pages = {};
    let total = 0;
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (!key || !key.startsWith(STORAGE_PREFIX)) continue;
      try {
        const parsed = JSON.parse(localStorage.getItem(key));
        if (parsed && Array.isArray(parsed.highlights) && parsed.highlights.length > 0) {
          const pagePath = key.slice(STORAGE_PREFIX.length);
          pages[pagePath] = { highlights: parsed.highlights };
          total += parsed.highlights.length;
        }
      } catch (e) { /* skip corrupt entries */ }
    }
    return { pages, total };
  }

  function exportBackup() {
    const { pages, total } = collectAllHighlights();
    if (total === 0) {
      flashToolbarMessage("Nothing to back up yet.");
      return;
    }
    const payload = {
      format: BACKUP_FORMAT,
      exported_at: new Date().toISOString(),
      page_count: Object.keys(pages).length,
      highlight_count: total,
      pages,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const stamp = new Date().toISOString().slice(0, 10);
    a.href = url;
    a.download = `noblemind-highlights-${stamp}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    flashToolbarMessage(`Saved ${total} highlight${total === 1 ? "" : "s"} from ${Object.keys(pages).length} page${Object.keys(pages).length === 1 ? "" : "s"}.`);
  }

  function importBackup(file) {
    const reader = new FileReader();
    reader.onload = () => {
      let payload;
      try { payload = JSON.parse(reader.result); }
      catch (e) {
        flashToolbarMessage("Could not read that file — not valid JSON.");
        return;
      }
      if (!payload || payload.format !== BACKUP_FORMAT || !payload.pages || typeof payload.pages !== "object") {
        flashToolbarMessage("That doesn't look like a Noble Mind backup file.");
        return;
      }
      let addedHighlights = 0;
      let touchedPages = 0;
      for (const pagePath in payload.pages) {
        const incoming = payload.pages[pagePath];
        if (!incoming || !Array.isArray(incoming.highlights)) continue;
        const key = STORAGE_PREFIX + pagePath;
        let existing = { highlights: [] };
        try {
          const raw = localStorage.getItem(key);
          if (raw) {
            const parsed = JSON.parse(raw);
            if (parsed && Array.isArray(parsed.highlights)) existing = parsed;
          }
        } catch (e) { /* fall back to empty */ }
        const existingIds = new Set(existing.highlights.map((h) => h.id));
        let pageAdded = 0;
        for (const h of incoming.highlights) {
          if (!h || typeof h.id !== "string" || existingIds.has(h.id)) continue;
          existing.highlights.push(h);
          existingIds.add(h.id);
          pageAdded++;
        }
        if (pageAdded > 0) {
          try { localStorage.setItem(key, JSON.stringify(existing)); }
          catch (e) { /* quota — skip silently */ }
          touchedPages++;
          addedHighlights += pageAdded;
        }
      }
      // Reload state for the current page and re-render
      state = loadState();
      applyPersistedHighlights();
      refreshFabCount();
      renderPanel();
      if (addedHighlights === 0) {
        flashToolbarMessage("No new highlights to add — backup already matches.");
      } else {
        flashToolbarMessage(`Restored ${addedHighlights} highlight${addedHighlights === 1 ? "" : "s"} across ${touchedPages} page${touchedPages === 1 ? "" : "s"}.`);
      }
    };
    reader.onerror = () => flashToolbarMessage("Could not read that file.");
    reader.readAsText(file);
  }

  function flashToolbarMessage(msg) {
    if (!panel) return;
    const toolbar = panel.querySelector(".nm-toolbar");
    if (!toolbar) return;
    let el = toolbar.querySelector(".nm-toolbar-msg");
    if (!el) {
      el = document.createElement("div");
      el.className = "nm-toolbar-msg";
      toolbar.appendChild(el);
    }
    el.textContent = msg;
    clearTimeout(flashToolbarMessage._t);
    flashToolbarMessage._t = setTimeout(() => { if (el) el.textContent = ""; }, 4000);
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
      <div class="nm-toolbar">
        <button data-action="export" title="Download a backup of every highlight and note in this browser, across all books">Export backup</button>
        <button data-action="import" title="Restore highlights and notes from a backup file">Import backup</button>
        <input type="file" class="nm-import-input" accept=".json,application/json" style="display:none" />
      </div>
      <div class="nm-search-row">
        <input type="search" class="nm-search-input" placeholder="Find in my notes — across every book…" aria-label="Search highlights and notes across all books" />
      </div>
      <div class="nm-list"></div>
    `;
    document.body.appendChild(panel);
    panel.querySelector(".nm-close").addEventListener("click", () => {
      panel.classList.remove("visible");
    });
    panel.querySelector('[data-action="export"]').addEventListener("click", exportBackup);
    const fileInput = panel.querySelector(".nm-import-input");
    panel.querySelector('[data-action="import"]').addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", (e) => {
      const file = e.target.files && e.target.files[0];
      if (file) importBackup(file);
      fileInput.value = "";
    });
    const searchInput = panel.querySelector(".nm-search-input");
    let searchTimer = null;
    searchInput.addEventListener("input", () => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => renderPanel(), 120);
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

  // ---- pretty names from URL paths -----------------------------------------

  const SMALL_WORDS = new Set([
    "a","an","and","or","but","of","the","to","for","in","on","with","by","as","at"
  ]);

  function titleCase(s) {
    return s.split(/\s+/).filter(Boolean).map((w, i) => {
      const lw = w.toLowerCase();
      if (i > 0 && SMALL_WORDS.has(lw)) return lw;
      return w.charAt(0).toUpperCase() + w.slice(1).toLowerCase();
    }).join(" ");
  }

  function prettyBookFromPath(pathname) {
    const parts = pathname.split("/").filter(Boolean);
    if (parts.length === 0) return "";
    let dir = parts[0];
    // CamelCase → spaces, then snake_case / kebab-case → spaces
    let spaced = dir.replace(/([a-z])([A-Z])/g, "$1 $2")
                    .replace(/([A-Z]+)([A-Z][a-z])/g, "$1 $2")
                    .replace(/[_-]/g, " ");
    return titleCase(spaced);
  }

  function prettyChapterFromPath(pathname) {
    const parts = pathname.split("/").filter(Boolean);
    if (parts.length < 2) return "";
    const file = parts[parts.length - 1].replace(/\.html?$/i, "");
    const m = file.match(/^chapter-?0*(\d+)$/i);
    if (m) return `Chapter ${m[1]}`;
    return titleCase(file.replace(/[-_]/g, " "));
  }

  // ---- cross-notes search --------------------------------------------------

  function getSearchQuery() {
    if (!panel) return "";
    const input = panel.querySelector(".nm-search-input");
    return input ? input.value.trim() : "";
  }

  function collectAllNotes() {
    // Returns [{ pagePath, highlight }, ...] from every nm_study_* key.
    const all = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (!key || !key.startsWith(STORAGE_PREFIX)) continue;
      try {
        const parsed = JSON.parse(localStorage.getItem(key));
        if (!parsed || !Array.isArray(parsed.highlights)) continue;
        const pagePath = key.slice(STORAGE_PREFIX.length);
        for (const h of parsed.highlights) all.push({ pagePath, highlight: h });
      } catch (e) { /* skip corrupt */ }
    }
    return all;
  }

  function highlightMatch(text, query) {
    if (!query) return escapeHtml(text);
    const idx = text.toLowerCase().indexOf(query.toLowerCase());
    if (idx === -1) return escapeHtml(text);
    const before = escapeHtml(text.slice(0, idx));
    const match = escapeHtml(text.slice(idx, idx + query.length));
    const after = escapeHtml(text.slice(idx + query.length));
    return `${before}<mark class="nm-match">${match}</mark>${after}`;
  }

  function renderPanel() {
    if (!panel) return;
    const list = panel.querySelector(".nm-list");
    const query = getSearchQuery();
    if (query) {
      renderSearchResults(list, query);
    } else {
      renderCurrentChapter(list);
    }
  }

  function renderCurrentChapter(list) {
    if (state.highlights.length === 0) {
      list.innerHTML = '<div class="nm-empty">No highlights yet on this page. Select any text to save a highlight or attach a note. Or type above to search every book.</div>';
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
      b.addEventListener("click", () => {
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

  function renderSearchResults(list, query) {
    const all = collectAllNotes();
    const lq = query.toLowerCase();
    const currentPath = window.location.pathname;
    // Match against highlight text and note body
    const matches = all.filter(({ highlight }) => {
      const t = (highlight.text || "").toLowerCase();
      const n = (highlight.note || "").toLowerCase();
      return t.includes(lq) || n.includes(lq);
    });
    if (matches.length === 0) {
      list.innerHTML = `<div class="nm-empty">No highlights or notes match <em>${escapeHtml(query)}</em>.</div>`;
      return;
    }
    // Sort: current page first, then by book name, then by chapter
    matches.sort((a, b) => {
      const aHere = a.pagePath === currentPath ? 0 : 1;
      const bHere = b.pagePath === currentPath ? 0 : 1;
      if (aHere !== bHere) return aHere - bHere;
      if (a.pagePath !== b.pagePath) return a.pagePath.localeCompare(b.pagePath);
      return (a.highlight.ts || 0) - (b.highlight.ts || 0);
    });
    list.innerHTML = `
      <div class="nm-empty" style="text-align:left;padding:8px 4px 12px 4px;">
        Found ${matches.length} match${matches.length === 1 ? "" : "es"} across your notes.
      </div>
      ${matches.map(({ pagePath, highlight }, idx) => {
        const book = prettyBookFromPath(pagePath);
        const chap = prettyChapterFromPath(pagePath);
        const isHere = pagePath === currentPath;
        return `
          <div class="nm-item" data-idx="${idx}">
            <span class="nm-where">
              ${escapeHtml(book)}
              ${chap ? `<span class="nm-where-sep">·</span>${escapeHtml(chap)}` : ""}
              ${isHere ? `<span class="nm-where-sep">·</span><span style="color:rgba(255,235,130,0.85)">this page</span>` : ""}
            </span>
            <div class="nm-quote" data-page="${escapeHtml(pagePath)}" data-text="${escapeHtml(highlight.text)}">"${highlightMatch(highlight.text, query)}"</div>
            ${highlight.note ? `<div class="nm-note">${highlightMatch(highlight.note, query)}</div>` : ""}
          </div>
        `;
      }).join("")}
    `;
    list.querySelectorAll(".nm-quote").forEach((q) => {
      q.addEventListener("click", () => {
        const page = q.getAttribute("data-page");
        const text = q.getAttribute("data-text");
        if (page === currentPath) {
          // Already here — scroll to it
          const root = findContentRoot();
          const range = findTextRange(root, text, null);
          if (range) {
            const node = range.startContainer.parentElement;
            if (node) node.scrollIntoView({ behavior: "smooth", block: "center" });
          }
          panel.classList.remove("visible");
        } else {
          // Navigate; the ?q= handler on the destination will scroll + highlight
          window.location.href = page + "?q=" + encodeURIComponent(text);
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

  // ---- Tools / Help popup --------------------------------------------------

  const HELP_HTML = `
    <h4>About this reader</h4>
    <p>Every book here is free to read online, with a matching PDF and EPUB. Once a page loads, it works offline.</p>

    <h4>Search across every book</h4>
    <p>On the <strong>Books</strong> page, the search bar at the top searches the full text of every book at once. Click any result to jump to the matching paragraph in that chapter.</p>

    <h4>Highlight a sentence</h4>
    <p>While reading any chapter, select a sentence with your mouse or finger. A small popup appears with:</p>
    <ul>
      <li><strong>Highlight</strong> — saves a yellow highlight on the phrase.</li>
      <li><strong>Highlight + Note</strong> — saves the highlight <em>and</em> opens a box where you can type a note.</li>
    </ul>

    <h4>Your notebook</h4>
    <p>The <strong>📓 button</strong> at the bottom-right of every chapter page opens your notebook. It lists every highlight and note you've saved on that page. Click any item to scroll back to it. The red badge shows how many are on the current page.</p>

    <h4>Search every note you've saved</h4>
    <p>Inside the notebook, type in the <em>"Find in my notes"</em> box to search across every book — not just this chapter. Results show the book and chapter; click one to navigate there with the highlight ready to view.</p>

    <h4>Back up your notes</h4>
    <p>Your highlights and notes live in this browser only. If you clear browsing data they will be erased. Use <strong>Export backup</strong> in the notebook to save a JSON file to your drive, and <strong>Import backup</strong> to restore it later — on any browser or computer.</p>

    <h4>Offline reading</h4>
    <p>You can read on a plane or without internet. Pages you've already visited stay cached.</p>

    <p class="nm-help-hint">Drag the title bar above to move this panel anywhere on the screen. Click the × to close it.</p>
  `;

  let helpFab = null;
  let helpPopup = null;

  function ensureHelpFab() {
    if (helpFab) return helpFab;
    helpFab = document.createElement("button");
    helpFab.className = "nm-help-fab";
    helpFab.setAttribute("aria-label", "Open Tools and Help");
    helpFab.innerHTML = '<span class="nm-help-icon">?</span>Tools';
    helpFab.addEventListener("click", toggleHelpPopup);
    document.body.appendChild(helpFab);
    return helpFab;
  }

  function ensureHelpPopup() {
    if (helpPopup) return helpPopup;
    helpPopup = document.createElement("div");
    helpPopup.className = "nm-help-popup";
    helpPopup.innerHTML = `
      <div class="nm-help-popup-header">
        <h3>Tools &amp; Tips</h3>
        <button class="nm-help-close" aria-label="Close">×</button>
      </div>
      <div class="nm-help-popup-body">${HELP_HTML}</div>
    `;
    document.body.appendChild(helpPopup);
    helpPopup.querySelector(".nm-help-close").addEventListener("click", () => {
      helpPopup.classList.remove("visible");
    });
    makeDraggable(helpPopup, helpPopup.querySelector(".nm-help-popup-header"));
    restoreHelpPopupPosition(helpPopup);
    return helpPopup;
  }

  function toggleHelpPopup() {
    const p = ensureHelpPopup();
    if (p.classList.contains("visible")) {
      p.classList.remove("visible");
    } else {
      p.classList.add("visible");
    }
  }

  function restoreHelpPopupPosition(p) {
    try {
      const raw = localStorage.getItem("nm_help_pos");
      if (!raw) return;
      const pos = JSON.parse(raw);
      if (!pos || typeof pos.left !== "number" || typeof pos.top !== "number") return;
      const maxLeft = window.innerWidth - 80;
      const maxTop = window.innerHeight - 80;
      const left = Math.max(0, Math.min(pos.left, maxLeft));
      const top = Math.max(0, Math.min(pos.top, maxTop));
      p.style.left = left + "px";
      p.style.top = top + "px";
      p.style.right = "auto";
    } catch (e) { /* ignore */ }
  }

  function saveHelpPopupPosition(p) {
    try {
      const rect = p.getBoundingClientRect();
      localStorage.setItem("nm_help_pos", JSON.stringify({ left: rect.left, top: rect.top }));
    } catch (e) { /* quota — ignore */ }
  }

  function makeDraggable(el, handle) {
    let dragging = false;
    let startX = 0, startY = 0;
    let originX = 0, originY = 0;

    handle.addEventListener("pointerdown", (e) => {
      // Don't drag if the user clicked the close button
      if (e.target.closest(".nm-help-close")) return;
      dragging = true;
      const rect = el.getBoundingClientRect();
      originX = rect.left;
      originY = rect.top;
      startX = e.clientX;
      startY = e.clientY;
      // Pin to absolute pixel position so right: auto and left: px take over
      el.style.left = originX + "px";
      el.style.top = originY + "px";
      el.style.right = "auto";
      handle.setPointerCapture(e.pointerId);
      e.preventDefault();
    });

    handle.addEventListener("pointermove", (e) => {
      if (!dragging) return;
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      let newLeft = originX + dx;
      let newTop = originY + dy;
      // Keep at least 40px of the popup on-screen so it can't be dragged off entirely
      const rect = el.getBoundingClientRect();
      newLeft = Math.max(40 - rect.width, Math.min(newLeft, window.innerWidth - 40));
      newTop = Math.max(0, Math.min(newTop, window.innerHeight - 40));
      el.style.left = newLeft + "px";
      el.style.top = newTop + "px";
    });

    const endDrag = (e) => {
      if (!dragging) return;
      dragging = false;
      try { handle.releasePointerCapture(e.pointerId); } catch (_) {}
      saveHelpPopupPosition(el);
    };
    handle.addEventListener("pointerup", endDrag);
    handle.addEventListener("pointercancel", endDrag);
  }

  // ---- init -----------------------------------------------------------------

  function injectStyle() {
    const style = document.createElement("style");
    style.textContent = STYLE;
    document.head.appendChild(style);
  }

  function isChapterPage() {
    return !!document.querySelector(".glass-page-inner");
  }

  function init() {
    injectStyle();

    // Tools/Help button is on every page that loads this script.
    ensureHelpFab();

    // Highlights / notes / search land are chapter-only.
    if (!isChapterPage()) return;

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
      if (e.target.closest(".nm-selection-popup, .nm-tools-fab, .nm-tools-panel, .nm-note-modal, .nm-help-fab, .nm-help-popup")) return;
      hidePopup();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

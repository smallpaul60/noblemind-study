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
    /* Feature 2 — paragraph permalinks */
    .nm-para-anchor {
      display: inline-block;
      margin-left: 8px;
      opacity: 0;
      color: rgba(196, 168, 84, 0.6);
      text-decoration: none;
      cursor: pointer;
      transition: opacity 0.18s, color 0.18s;
      font-size: 0.85em;
      user-select: none;
      vertical-align: baseline;
    }
    p:hover > .nm-para-anchor,
    h2:hover > .nm-para-anchor,
    h3:hover > .nm-para-anchor,
    .nm-para-anchor:focus,
    .nm-para-anchor:hover {
      opacity: 1;
      color: rgba(255, 235, 130, 0.95);
    }
    @media (hover: none) {
      .nm-para-anchor { opacity: 0.35; }
    }
    .nm-copy-toast {
      position: fixed;
      bottom: 80px;
      left: 50%;
      transform: translateX(-50%);
      padding: 9px 18px;
      background: rgba(15, 15, 18, 0.96);
      border: 1px solid rgba(196, 168, 84, 0.45);
      border-radius: 22px;
      color: rgba(255, 235, 130, 0.95);
      font-size: 0.85rem;
      font-family: 'Segoe UI', Georgia, serif;
      z-index: 10003;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.22s;
    }
    .nm-copy-toast.visible { opacity: 1; }

    /* Feature 3 — display preferences (font size + line spacing).
       Font scaling lives on <html> so every rem-based size in chapter
       pages scales proportionally; ancestor-class line-height rules stay
       targeted at <p>/<li> inside chapter content. */
    html.nm-font-large { font-size: 112.5%; }
    html.nm-font-larger { font-size: 128%; }
    html.nm-leading-loose .glass-page-inner p,
    html.nm-leading-loose .glass-page-inner li { line-height: 1.95; }
    html.nm-leading-looser .glass-page-inner p,
    html.nm-leading-looser .glass-page-inner li { line-height: 2.15; }
    .nm-display-row {
      display: flex; flex-wrap: wrap; align-items: center;
      gap: 6px; margin: 6px 0 10px 0;
    }
    .nm-display-row .nm-display-label {
      font-size: 0.75rem;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: rgba(192, 184, 168, 0.75);
      margin-right: 4px;
      min-width: 88px;
    }
    .nm-display-row button {
      background: rgba(196, 168, 84, 0.10);
      border: 1px solid rgba(196, 168, 84, 0.22);
      border-radius: 6px;
      color: rgba(240, 236, 228, 0.92);
      padding: 4px 10px;
      cursor: pointer;
      font-family: inherit;
      font-size: 0.78rem;
    }
    .nm-display-row button:hover {
      background: rgba(196, 168, 84, 0.2);
      border-color: rgba(196, 168, 84, 0.5);
    }
    .nm-display-row button.nm-active {
      background: rgba(196, 168, 84, 0.32);
      border-color: rgba(255, 235, 130, 0.65);
      color: rgba(255, 235, 130, 0.95);
    }

    /* Feature 4 — Continue reading prompt on book index */
    .nm-continue-banner {
      margin: 0 0 1.8rem 0;
      padding: 14px 18px;
      background: linear-gradient(135deg, rgba(196,168,84,0.16), rgba(196,81,63,0.10));
      border: 1px solid rgba(196, 168, 84, 0.4);
      border-radius: 12px;
      display: flex; justify-content: space-between; align-items: center;
      flex-wrap: wrap; gap: 12px;
      font-family: 'Segoe UI', Georgia, serif;
    }
    .nm-continue-banner .nm-continue-label {
      font-size: 0.78rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: rgba(196, 168, 84, 0.85);
      margin-bottom: 3px;
    }
    .nm-continue-banner .nm-continue-where {
      font-size: 1.05rem;
      color: rgba(240, 236, 228, 0.96);
    }
    .nm-continue-banner .nm-continue-link {
      padding: 8px 16px;
      background: rgba(255, 235, 130, 0.18);
      border: 1px solid rgba(255, 235, 130, 0.55);
      border-radius: 8px;
      color: rgba(255, 235, 130, 0.95);
      text-decoration: none;
      font-size: 0.85rem;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      transition: background 0.2s, transform 0.2s;
    }
    .nm-continue-banner .nm-continue-link:hover {
      background: rgba(255, 235, 130, 0.3);
      transform: translateY(-1px);
    }
    .nm-continue-banner .nm-continue-dismiss {
      background: none;
      border: none;
      color: rgba(192, 184, 168, 0.55);
      cursor: pointer;
      font-size: 1.2rem;
      padding: 0 6px;
      line-height: 1;
    }
    .nm-continue-banner .nm-continue-dismiss:hover { color: rgba(255, 235, 130, 0.9); }

    /* Feature 5 — per-book search on the index page */
    .nm-book-search-row {
      margin: 0 0 1.6rem 0;
    }
    .nm-book-search-input {
      width: 100%;
      padding: 10px 14px;
      background: rgba(0,0,0,0.45);
      border: 1px solid rgba(148, 163, 184, 0.28);
      border-radius: 10px;
      color: rgba(240, 236, 228, 0.95);
      font-family: 'Segoe UI', Georgia, serif;
      font-size: 0.92rem;
      box-sizing: border-box;
    }
    .nm-book-search-input:focus {
      outline: none;
      border-color: rgba(196, 168, 84, 0.6);
      background: rgba(0,0,0,0.6);
    }
    .nm-book-search-input::placeholder {
      color: rgba(192, 184, 168, 0.55);
      font-style: italic;
    }
    .nm-book-search-results {
      margin-top: 10px;
      max-height: 50vh;
      overflow-y: auto;
      border: 1px solid rgba(148, 163, 184, 0.15);
      border-radius: 10px;
      background: rgba(0,0,0,0.3);
      display: none;
    }
    .nm-book-search-results.visible { display: block; }
    .nm-book-search-results .nm-bs-item {
      padding: 10px 14px;
      border-bottom: 1px solid rgba(148, 163, 184, 0.08);
      cursor: pointer;
      transition: background 0.15s;
    }
    .nm-book-search-results .nm-bs-item:last-child { border-bottom: none; }
    .nm-book-search-results .nm-bs-item:hover { background: rgba(196, 168, 84, 0.10); }
    .nm-book-search-results .nm-bs-where {
      font-size: 0.74rem;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      color: rgba(196, 168, 84, 0.85);
      margin-bottom: 4px;
    }
    .nm-book-search-results .nm-bs-snippet {
      font-size: 0.88rem;
      color: rgba(232, 226, 212, 0.92);
      line-height: 1.45;
    }
    .nm-book-search-results .nm-bs-empty {
      padding: 16px;
      text-align: center;
      font-size: 0.85rem;
      color: rgba(192, 184, 168, 0.7);
      font-style: italic;
    }
    .nm-book-search-results mark.nm-match {
      background: rgba(255, 235, 130, 0.45);
      color: inherit;
      padding: 0 1px;
      border-radius: 2px;
    }

    /* Feature 6 — Strong's hover on Greek/Hebrew transliterations */
    .nm-strongs-ref {
      color: rgba(255, 213, 110, 0.95);
      border-bottom: 1px dotted rgba(196, 168, 84, 0.55);
      cursor: pointer;
      transition: background 0.15s, border-color 0.15s, color 0.15s;
      padding: 0 1px;
    }
    .nm-strongs-ref:hover,
    .nm-strongs-ref:focus {
      background: rgba(196, 168, 84, 0.18);
      border-bottom-color: rgba(255, 235, 130, 0.9);
      color: rgba(255, 235, 130, 0.98);
      outline: none;
    }
    .nm-strongs-popup {
      position: absolute;
      z-index: 10002;
      max-width: 380px;
      min-width: 240px;
      background: rgba(15, 15, 18, 0.98);
      border: 1px solid rgba(196, 168, 84, 0.42);
      border-radius: 10px;
      padding: 12px 14px;
      box-shadow: 0 12px 36px rgba(0,0,0,0.6);
      color: rgba(232, 226, 212, 0.95);
      font-family: 'Segoe UI', Georgia, serif;
      font-size: 0.88rem;
      line-height: 1.55;
      display: none;
    }
    .nm-strongs-popup.visible { display: block; }
    .nm-strongs-popup .nm-sp-header {
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 8px;
    }
    .nm-strongs-popup .nm-sp-number {
      font-size: 0.74rem;
      letter-spacing: 0.10em;
      text-transform: uppercase;
      color: rgba(196, 168, 84, 0.95);
      font-weight: 700;
    }
    .nm-strongs-popup .nm-sp-close {
      background: none; border: none;
      color: rgba(192, 184, 168, 0.7);
      cursor: pointer;
      font-size: 1.15rem;
      line-height: 1;
      padding: 0 2px;
    }
    .nm-strongs-popup .nm-sp-close:hover { color: rgba(255, 235, 130, 0.95); }
    .nm-strongs-popup .nm-sp-word {
      font-size: 1.4rem;
      color: rgba(255, 235, 130, 0.98);
      line-height: 1.4;
      margin-bottom: 2px;
      /* Make sure unicode Greek/Hebrew renders well */
      font-family: 'Cardo', 'Times New Roman', Georgia, serif;
    }
    .nm-strongs-popup .nm-sp-pron {
      font-style: italic;
      color: rgba(192, 184, 168, 0.85);
      font-size: 0.85rem;
      margin-bottom: 8px;
    }
    .nm-strongs-popup .nm-sp-def {
      max-height: 220px;
      overflow-y: auto;
      font-size: 0.88rem;
      color: rgba(232, 226, 212, 0.94);
    }
    .nm-strongs-popup .nm-sp-loading {
      font-style: italic;
      color: rgba(192, 184, 168, 0.7);
    }
    .nm-strongs-popup .nm-sp-footer {
      margin-top: 8px;
      padding-top: 8px;
      border-top: 1px solid rgba(148, 163, 184, 0.12);
      font-size: 0.7rem;
      color: rgba(192, 184, 168, 0.55);
      font-style: italic;
      text-align: right;
    }

    /* Feature 1 — verse-reference hover popups */
    .nm-verse-ref {
      color: rgba(196, 168, 84, 0.95);
      text-decoration: none;
      border-bottom: 1px dotted rgba(196, 168, 84, 0.55);
      cursor: pointer;
      transition: background 0.15s, border-color 0.15s;
      padding: 0 1px;
    }
    .nm-verse-ref:hover,
    .nm-verse-ref:focus {
      background: rgba(196, 168, 84, 0.16);
      border-bottom-color: rgba(255, 235, 130, 0.9);
      color: rgba(255, 235, 130, 0.98);
      outline: none;
    }
    .nm-verse-popup {
      position: absolute;
      z-index: 10002;
      max-width: 380px;
      min-width: 220px;
      background: rgba(15, 15, 18, 0.98);
      border: 1px solid rgba(196, 168, 84, 0.4);
      border-radius: 10px;
      padding: 12px 14px 12px 14px;
      box-shadow: 0 12px 36px rgba(0,0,0,0.6);
      color: rgba(232, 226, 212, 0.95);
      font-family: 'Segoe UI', Georgia, serif;
      font-size: 0.88rem;
      line-height: 1.55;
      display: none;
    }
    .nm-verse-popup.visible { display: block; }
    .nm-verse-popup .nm-vp-header {
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 6px;
    }
    .nm-verse-popup .nm-vp-cite {
      font-size: 0.78rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: rgba(196, 168, 84, 0.95);
      font-weight: 700;
    }
    .nm-verse-popup .nm-vp-close {
      background: none; border: none;
      color: rgba(192, 184, 168, 0.7);
      cursor: pointer;
      font-size: 1.15rem;
      line-height: 1;
      padding: 0 2px;
    }
    .nm-verse-popup .nm-vp-close:hover { color: rgba(255, 235, 130, 0.95); }
    .nm-verse-popup .nm-vp-body {
      max-height: 280px;
      overflow-y: auto;
    }
    .nm-verse-popup .nm-vp-body .nm-vp-verse {
      margin-bottom: 4px;
    }
    .nm-verse-popup .nm-vp-body .nm-vp-vnum {
      font-size: 0.72em;
      vertical-align: super;
      color: rgba(196, 168, 84, 0.85);
      margin-right: 3px;
    }
    .nm-verse-popup .nm-vp-loading {
      font-style: italic;
      color: rgba(192, 184, 168, 0.7);
    }
    .nm-verse-popup .nm-vp-translation {
      margin-top: 8px;
      padding-top: 8px;
      border-top: 1px solid rgba(148, 163, 184, 0.12);
      font-size: 0.72rem;
      color: rgba(192, 184, 168, 0.6);
      font-style: italic;
      text-align: right;
    }

    @media (max-width: 600px) {
      .nm-tools-fab { right: 14px; bottom: 14px; width: 48px; height: 48px; font-size: 1.25rem; }
      .nm-tools-panel { right: 10px; left: 10px; width: auto; bottom: 70px; }
      .nm-help-fab { left: 14px; bottom: 14px; padding: 8px 13px; font-size: 0.8rem; }
      .nm-help-popup { top: 10px; left: 10px; right: 10px; width: auto; max-height: 85vh; }
      .nm-verse-popup { max-width: calc(100vw - 30px); }
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
    <h4>Display</h4>
    <div class="nm-display-row" data-row="font">
      <span class="nm-display-label">Text size</span>
      <button data-size="default">A</button>
      <button data-size="large">A+</button>
      <button data-size="larger">A++</button>
    </div>
    <div class="nm-display-row" data-row="leading">
      <span class="nm-display-label">Line spacing</span>
      <button data-leading="default">Normal</button>
      <button data-leading="loose">Loose</button>
      <button data-leading="looser">Looser</button>
    </div>

    <h4>About this reader</h4>
    <p>Every book here is free to read online, with a matching PDF and EPUB. Once a page loads, it works offline.</p>

    <h4>Search across every book</h4>
    <p>On the <strong>Books</strong> page, the search bar at the top searches the full text of every book at once. Each book's table of contents also has a search box that searches only that book.</p>

    <h4>Verse references</h4>
    <p>Scripture references in book text (like <em>John 3:16</em> or <em>1 Corinthians 13:4–7</em>) are underlined with a small dot underline. Click one to see the verse text inline. Shows the <strong>NASB 1995</strong> when online (via the Bolls.life Bible API) and falls back to the embedded <strong>King James Version</strong> when offline. The popup labels which translation it is showing.</p>

    <h4>Greek &amp; Hebrew terms</h4>
    <p>When a chapter uses a Greek or Hebrew word (like <em>agapē</em>, <em>makrothumeō</em>, <em>shalom</em>, or <em>Elohim</em>), the word will be subtly highlighted in warm gold. Click it for the Strong's entry — original script, pronunciation, and definition. Works offline.</p>

    <h4>Highlight a sentence</h4>
    <p>While reading any chapter, select a sentence with your mouse or finger. A small popup appears with:</p>
    <ul>
      <li><strong>Highlight</strong> — saves a yellow highlight on the phrase.</li>
      <li><strong>Highlight + Note</strong> — saves the highlight <em>and</em> opens a box where you can type a note.</li>
    </ul>

    <h4>Your notebook</h4>
    <p>The <strong>📓 button</strong> at the bottom-right of every chapter page opens your notebook. It lists every highlight and note you've saved on that page, and lets you search across every book. The red badge shows how many highlights are on the current page.</p>

    <h4>Continue where you left off</h4>
    <p>When you return to a book's table of contents, a <strong>Resume</strong> button appears at the top showing the last chapter you read.</p>

    <h4>Share a paragraph</h4>
    <p>Hover over any paragraph and a small <code>¶</code> mark appears at the end. Click it to copy a direct link to that paragraph — useful when sharing a specific passage with someone in your study group.</p>

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
    helpPopup.querySelectorAll('.nm-display-row[data-row="font"] button').forEach((b) => {
      b.addEventListener("click", () => setFontPref(b.getAttribute("data-size")));
    });
    helpPopup.querySelectorAll('.nm-display-row[data-row="leading"] button').forEach((b) => {
      b.addEventListener("click", () => setLeadingPref(b.getAttribute("data-leading")));
    });
    refreshDisplayControls();
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

  function getPageType() {
    if (document.querySelector(".lesson-grid")) return "book-index";
    if (document.querySelector(".glass-page-inner")) return "book-chapter";
    return "catalog";
  }

  function init() {
    injectStyle();
    applyDisplayPreferences();      // Feature 3 — apply persisted font/leading
    ensureHelpFab();                 // Tools button on every page

    const pageType = getPageType();
    if (pageType === "book-chapter") initChapterPage();
    else if (pageType === "book-index") initBookIndexPage();
  }

  function initChapterPage() {
    handleSearchQuery();
    applyPersistedHighlights();
    ensureFab();
    refreshFabCount();
    bindHighlightClicks();
    injectParagraphAnchors();    // Feature 2
    recordLastChapter();          // Feature 4 (writer side)
    linkifyVerseRefs();           // Feature 1
    linkifyStrongsTerms();        // Feature 6

    let popupTimer = null;
    document.addEventListener("selectionchange", () => {
      if (popupTimer) clearTimeout(popupTimer);
      popupTimer = setTimeout(showPopupAtSelection, 150);
    });
    document.addEventListener("mousedown", (e) => {
      if (e.target.closest(".nm-selection-popup, .nm-tools-fab, .nm-tools-panel, .nm-note-modal, .nm-help-fab, .nm-help-popup, .nm-verse-popup, .nm-verse-ref")) return;
      hidePopup();
    });
  }

  function initBookIndexPage() {
    injectContinueBanner();       // Feature 4 (reader side)
    injectBookSearch();            // Feature 5
  }

  // ============================================================
  // Feature 2 — per-paragraph permalinks
  // ============================================================

  function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).catch(() => fallbackCopy(text));
    }
    return fallbackCopy(text);
  }
  function fallbackCopy(text) {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.left = "-10000px";
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand("copy"); } catch (e) {}
    document.body.removeChild(ta);
  }
  function flashCopyToast(message) {
    let toast = document.querySelector(".nm-copy-toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.className = "nm-copy-toast";
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add("visible");
    clearTimeout(flashCopyToast._t);
    flashCopyToast._t = setTimeout(() => toast.classList.remove("visible"), 1800);
  }

  function injectParagraphAnchors() {
    const root = findContentRoot();
    if (!root) return;
    // Skip paragraphs that are inside nav, header, footer, or other chrome
    const paragraphs = Array.from(root.querySelectorAll("p")).filter((p) => {
      if (p.closest(".nav-controls, .footer-nav, footer, header.glass-page-header, .nm-tools-panel, .nm-help-popup, .nm-selection-popup")) return false;
      // Must have meaningful text content (skip empty/short)
      return p.textContent.trim().length >= 20;
    });
    let seq = 0;
    for (const p of paragraphs) {
      seq++;
      if (!p.id) p.id = "p" + seq;
      // Don't re-add the anchor if already there
      if (p.querySelector(".nm-para-anchor")) continue;
      const a = document.createElement("a");
      a.href = "#" + p.id;
      a.className = "nm-para-anchor";
      a.title = "Copy link to this paragraph";
      a.setAttribute("aria-label", "Copy link to this paragraph");
      a.textContent = "¶";
      a.addEventListener("click", (e) => {
        e.preventDefault();
        const url = window.location.origin + window.location.pathname + "#" + p.id;
        Promise.resolve(copyToClipboard(url)).then(() => flashCopyToast("Paragraph link copied"));
        history.replaceState(null, "", "#" + p.id);
      });
      p.appendChild(a);
    }
    // Scroll into view on landing
    const hash = window.location.hash;
    if (hash && /^#p\d+$/.test(hash)) {
      const target = document.getElementById(hash.slice(1));
      if (target) setTimeout(() => target.scrollIntoView({ behavior: "smooth", block: "center" }), 150);
    }
  }

  // ============================================================
  // Feature 3 — display preferences (font size + line spacing)
  // ============================================================

  const DISPLAY_KEY = "nm_display";
  const FONT_CLASSES = ["nm-font-large", "nm-font-larger"];
  const LEAD_CLASSES = ["nm-leading-loose", "nm-leading-looser"];

  function getDisplayPrefs() {
    try {
      const raw = localStorage.getItem(DISPLAY_KEY);
      if (!raw) return { font: "default", leading: "default" };
      const p = JSON.parse(raw);
      return {
        font: ["default", "large", "larger"].includes(p.font) ? p.font : "default",
        leading: ["default", "loose", "looser"].includes(p.leading) ? p.leading : "default",
      };
    } catch (e) { return { font: "default", leading: "default" }; }
  }

  function saveDisplayPrefs(prefs) {
    try { localStorage.setItem(DISPLAY_KEY, JSON.stringify(prefs)); }
    catch (e) {}
  }

  function applyDisplayPreferences() {
    const prefs = getDisplayPrefs();
    const root = document.documentElement;
    root.classList.remove(...FONT_CLASSES, ...LEAD_CLASSES);
    if (prefs.font === "large") root.classList.add("nm-font-large");
    else if (prefs.font === "larger") root.classList.add("nm-font-larger");
    if (prefs.leading === "loose") root.classList.add("nm-leading-loose");
    else if (prefs.leading === "looser") root.classList.add("nm-leading-looser");
  }

  function setFontPref(size) {
    const prefs = getDisplayPrefs();
    prefs.font = size;
    saveDisplayPrefs(prefs);
    applyDisplayPreferences();
    refreshDisplayControls();
  }
  function setLeadingPref(leading) {
    const prefs = getDisplayPrefs();
    prefs.leading = leading;
    saveDisplayPrefs(prefs);
    applyDisplayPreferences();
    refreshDisplayControls();
  }
  function refreshDisplayControls() {
    if (!helpPopup) return;
    const prefs = getDisplayPrefs();
    helpPopup.querySelectorAll('.nm-display-row[data-row="font"] button').forEach((b) => {
      b.classList.toggle("nm-active", b.getAttribute("data-size") === prefs.font);
    });
    helpPopup.querySelectorAll('.nm-display-row[data-row="leading"] button').forEach((b) => {
      b.classList.toggle("nm-active", b.getAttribute("data-leading") === prefs.leading);
    });
  }

  // ============================================================
  // Feature 4 — Continue where you left off
  // ============================================================

  const LAST_KEY_PREFIX = "nm_last_";

  function bookDirFromPath(pathname) {
    const parts = pathname.split("/").filter(Boolean);
    return parts.length > 0 ? parts[0] : null;
  }
  function isIndexFilename(pathname) {
    const parts = pathname.split("/").filter(Boolean);
    if (parts.length === 0) return false;
    const last = parts[parts.length - 1];
    return last === "" || last.toLowerCase() === "index.html";
  }

  function chapterLabelFromDOM() {
    // Prefer the lesson-num + lesson-title pattern, else the h1, else prettyChapterFromPath
    const root = findContentRoot();
    if (root) {
      const h1 = root.querySelector("h1");
      if (h1) {
        const txt = h1.textContent.replace(/\s+/g, " ").trim();
        if (txt) return txt;
      }
    }
    return prettyChapterFromPath(window.location.pathname);
  }

  function recordLastChapter() {
    const bookDir = bookDirFromPath(window.location.pathname);
    if (!bookDir) return;
    if (isIndexFilename(window.location.pathname)) return; // index isn't a chapter
    const entry = {
      url: window.location.pathname,
      label: chapterLabelFromDOM(),
      ts: Date.now(),
    };
    try { localStorage.setItem(LAST_KEY_PREFIX + bookDir, JSON.stringify(entry)); }
    catch (e) {}
  }

  function getLastChapter(bookDir) {
    try {
      const raw = localStorage.getItem(LAST_KEY_PREFIX + bookDir);
      if (!raw) return null;
      const e = JSON.parse(raw);
      if (!e || typeof e.url !== "string") return null;
      return e;
    } catch (e) { return null; }
  }

  function injectContinueBanner() {
    const bookDir = bookDirFromPath(window.location.pathname);
    if (!bookDir) return;
    const last = getLastChapter(bookDir);
    if (!last) return;
    // Only show if the last-visited URL differs from this index URL
    if (last.url === window.location.pathname) return;
    const root = findContentRoot();
    if (!root) return;
    const banner = document.createElement("div");
    banner.className = "nm-continue-banner";
    banner.innerHTML = `
      <div>
        <div class="nm-continue-label">Continue reading</div>
        <div class="nm-continue-where">${escapeHtml(last.label || "Last chapter")}</div>
      </div>
      <a class="nm-continue-link" href="${escapeHtml(last.url)}">Resume →</a>
      <button class="nm-continue-dismiss" aria-label="Dismiss continue prompt" title="Dismiss">×</button>
    `;
    // Insert at the very top of the content root, after nav controls if present
    const navControls = root.querySelector(".nav-controls");
    if (navControls && navControls.nextSibling) {
      root.insertBefore(banner, navControls.nextSibling);
    } else {
      root.insertBefore(banner, root.firstChild);
    }
    banner.querySelector(".nm-continue-dismiss").addEventListener("click", () => {
      banner.remove();
      try { localStorage.removeItem(LAST_KEY_PREFIX + bookDir); } catch (e) {}
    });
  }

  // ============================================================
  // Feature 5 — search within a single book
  // ============================================================

  let _searchIndex = null;
  let _searchIndexLoading = null;

  function loadSearchIndex() {
    if (_searchIndex) return Promise.resolve(_searchIndex);
    if (_searchIndexLoading) return _searchIndexLoading;
    _searchIndexLoading = fetch("/search_index.json")
      .then((r) => r.json())
      .then((data) => {
        _searchIndex = Array.isArray(data) ? data : [];
        return _searchIndex;
      })
      .catch(() => { _searchIndex = []; return _searchIndex; });
    return _searchIndexLoading;
  }

  function injectBookSearch() {
    const bookDir = bookDirFromPath(window.location.pathname);
    if (!bookDir) return;
    const root = findContentRoot();
    if (!root) return;
    // Find lesson-grid (or chapter list) to anchor the search above it
    const lessonGrid = root.querySelector(".lesson-grid, .chapters");
    if (!lessonGrid) return;
    if (root.querySelector(".nm-book-search-row")) return; // idempotent

    const row = document.createElement("div");
    row.className = "nm-book-search-row";
    row.innerHTML = `
      <input type="search" class="nm-book-search-input" placeholder="Search this book…" aria-label="Search within this book" />
      <div class="nm-book-search-results" aria-live="polite"></div>
    `;
    lessonGrid.parentNode.insertBefore(row, lessonGrid);

    const input = row.querySelector(".nm-book-search-input");
    const results = row.querySelector(".nm-book-search-results");
    let debounce = null;

    input.addEventListener("input", () => {
      const q = input.value.trim();
      clearTimeout(debounce);
      if (q.length < 2) {
        results.classList.remove("visible");
        results.innerHTML = "";
        return;
      }
      debounce = setTimeout(() => runBookSearch(bookDir, q, results), 140);
    });
  }

  function runBookSearch(bookDir, query, resultsEl) {
    loadSearchIndex().then((index) => {
      const lq = query.toLowerCase();
      const bookEntries = index.filter((e) => typeof e.url === "string" && e.url.startsWith(bookDir + "/"));
      const matches = [];
      for (const entry of bookEntries) {
        const text = (entry.text || "").toLowerCase();
        const title = (entry.title || "").toLowerCase();
        const label = (entry.label || "").toLowerCase();
        const idxT = text.indexOf(lq);
        const inTitle = title.includes(lq) || label.includes(lq);
        if (idxT === -1 && !inTitle) continue;
        // Snippet: window around the first match (or first 160 chars of text)
        let snippet = "";
        if (idxT !== -1) {
          const start = Math.max(0, idxT - 60);
          const end = Math.min(entry.text.length, idxT + query.length + 80);
          snippet = (start > 0 ? "…" : "") + entry.text.slice(start, end) + (end < entry.text.length ? "…" : "");
        } else {
          snippet = entry.text.slice(0, 160) + (entry.text.length > 160 ? "…" : "");
        }
        matches.push({ entry, snippet });
      }
      renderBookSearchResults(resultsEl, matches, query);
    });
  }

  function renderBookSearchResults(el, matches, query) {
    if (matches.length === 0) {
      el.innerHTML = `<div class="nm-bs-empty">No matches for <em>${escapeHtml(query)}</em> in this book.</div>`;
      el.classList.add("visible");
      return;
    }
    el.innerHTML = matches.map(({ entry, snippet }) => `
      <div class="nm-bs-item" data-url="/${escapeHtml(entry.url)}" data-query="${escapeHtml(query)}">
        <div class="nm-bs-where">${escapeHtml(entry.label || "")}${entry.title ? " · " + escapeHtml(entry.title) : ""}</div>
        <div class="nm-bs-snippet">${highlightMatch(snippet, query)}</div>
      </div>
    `).join("");
    el.classList.add("visible");
    el.querySelectorAll(".nm-bs-item").forEach((it) => {
      it.addEventListener("click", () => {
        const url = it.getAttribute("data-url");
        const q = it.getAttribute("data-query");
        window.location.href = url + "?q=" + encodeURIComponent(q);
      });
    });
  }

  // ============================================================
  // Feature 1 — verse-reference hover popups
  // ============================================================

  const BOOK_NAMES = {
    // OT
    "genesis":1,"gen":1,"gn":1,
    "exodus":2,"exod":2,"exo":2,"ex":2,
    "leviticus":3,"lev":3,"lv":3,
    "numbers":4,"num":4,"nu":4,"nm":4,
    "deuteronomy":5,"deut":5,"dt":5,
    "joshua":6,"josh":6,"jos":6,"jsh":6,
    "judges":7,"judg":7,"jdg":7,"jdgs":7,
    "ruth":8,"rth":8,"ru":8,
    "1 samuel":9,"1samuel":9,"1 sam":9,"1sam":9,"1 sm":9,"1sm":9,
    "2 samuel":10,"2samuel":10,"2 sam":10,"2sam":10,"2 sm":10,"2sm":10,
    "1 kings":11,"1kings":11,"1 kgs":11,"1kgs":11,"1 ki":11,"1ki":11,
    "2 kings":12,"2kings":12,"2 kgs":12,"2kgs":12,"2 ki":12,"2ki":12,
    "1 chronicles":13,"1chronicles":13,"1 chr":13,"1chr":13,"1 chron":13,"1chron":13,
    "2 chronicles":14,"2chronicles":14,"2 chr":14,"2chr":14,"2 chron":14,"2chron":14,
    "ezra":15,"ezr":15,
    "nehemiah":16,"neh":16,
    "esther":17,"esth":17,"est":17,
    "job":18,"jb":18,
    "psalms":19,"psalm":19,"ps":19,"psa":19,"pss":19,
    "proverbs":20,"prov":20,"pr":20,"prv":20,
    "ecclesiastes":21,"eccl":21,"ecc":21,"qoh":21,
    "song of solomon":22,"song of songs":22,"song":22,"sos":22,"ss":22,"canticles":22,
    "isaiah":23,"isa":23,"is":23,
    "jeremiah":24,"jer":24,
    "lamentations":25,"lam":25,
    "ezekiel":26,"ezek":26,"eze":26,"ezk":26,
    "daniel":27,"dan":27,"dn":27,
    "hosea":28,"hos":28,
    "joel":29,"joe":29,"jl":29,
    "amos":30,"am":30,
    "obadiah":31,"obad":31,"ob":31,
    "jonah":32,"jnh":32,"jon":32,
    "micah":33,"mic":33,"mi":33,
    "nahum":34,"nah":34,"na":34,
    "habakkuk":35,"hab":35,"hb":35,
    "zephaniah":36,"zeph":36,"zep":36,
    "haggai":37,"hag":37,"hg":37,
    "zechariah":38,"zech":38,"zec":38,
    "malachi":39,"mal":39,
    // NT
    "matthew":40,"matt":40,"mt":40,
    "mark":41,"mk":41,"mar":41,
    "luke":42,"lk":42,"luk":42,
    "john":43,"jn":43,"joh":43,
    "acts":44,"ac":44,
    "romans":45,"rom":45,"rm":45,
    "1 corinthians":46,"1corinthians":46,"1 cor":46,"1cor":46,"1 co":46,
    "2 corinthians":47,"2corinthians":47,"2 cor":47,"2cor":47,"2 co":47,
    "galatians":48,"gal":48,
    "ephesians":49,"eph":49,
    "philippians":50,"phil":50,"php":50,
    "colossians":51,"col":51,
    "1 thessalonians":52,"1thessalonians":52,"1 thess":52,"1thess":52,"1 th":52,
    "2 thessalonians":53,"2thessalonians":53,"2 thess":53,"2thess":53,"2 th":53,
    "1 timothy":54,"1timothy":54,"1 tim":54,"1tim":54,"1 ti":54,
    "2 timothy":55,"2timothy":55,"2 tim":55,"2tim":55,"2 ti":55,
    "titus":56,"tit":56,
    "philemon":57,"philem":57,"phlm":57,"phm":57,
    "hebrews":58,"heb":58,
    "james":59,"jas":59,"jms":59,
    "1 peter":60,"1peter":60,"1 pet":60,"1pet":60,"1 pe":60,"1pe":60,
    "2 peter":61,"2peter":61,"2 pet":61,"2pet":61,"2 pe":61,"2pe":61,
    "1 john":62,"1john":62,"1 jn":62,"1jn":62,
    "2 john":63,"2john":63,"2 jn":63,"2jn":63,
    "3 john":64,"3john":64,"3 jn":64,"3jn":64,
    "jude":65,"jud":65,
    "revelation":66,"rev":66,"rv":66,"apocalypse":66,
  };

  // Pretty display names from book number
  const BOOK_PRETTY = {
    1:"Genesis",2:"Exodus",3:"Leviticus",4:"Numbers",5:"Deuteronomy",
    6:"Joshua",7:"Judges",8:"Ruth",9:"1 Samuel",10:"2 Samuel",
    11:"1 Kings",12:"2 Kings",13:"1 Chronicles",14:"2 Chronicles",
    15:"Ezra",16:"Nehemiah",17:"Esther",18:"Job",19:"Psalms",20:"Proverbs",
    21:"Ecclesiastes",22:"Song of Solomon",23:"Isaiah",24:"Jeremiah",
    25:"Lamentations",26:"Ezekiel",27:"Daniel",28:"Hosea",29:"Joel",
    30:"Amos",31:"Obadiah",32:"Jonah",33:"Micah",34:"Nahum",35:"Habakkuk",
    36:"Zephaniah",37:"Haggai",38:"Zechariah",39:"Malachi",
    40:"Matthew",41:"Mark",42:"Luke",43:"John",44:"Acts",45:"Romans",
    46:"1 Corinthians",47:"2 Corinthians",48:"Galatians",49:"Ephesians",
    50:"Philippians",51:"Colossians",52:"1 Thessalonians",53:"2 Thessalonians",
    54:"1 Timothy",55:"2 Timothy",56:"Titus",57:"Philemon",58:"Hebrews",
    59:"James",60:"1 Peter",61:"2 Peter",62:"1 John",63:"2 John",64:"3 John",
    65:"Jude",66:"Revelation",
  };

  // Build regex from BOOK_NAMES — longest keys first to ensure greedy match
  let _verseRefRegex = null;
  function buildVerseRefRegex() {
    if (_verseRefRegex) return _verseRefRegex;
    const keys = Object.keys(BOOK_NAMES).sort((a, b) => b.length - a.length);
    const escapedKeys = keys.map((k) => k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replace(/\s+/g, "\\s+"));
    // (?:Book) [optional period or comma not consumed] [whitespace] (chapter):(verse)[-(end)]
    const pattern = "(?:^|(?<=[^A-Za-z0-9]))" + "(" + escapedKeys.join("|") + ")" + "\\.?\\s+(\\d{1,3}):(\\d{1,3})(?:\\s*[\\-\\u2013]\\s*(\\d{1,3}))?";
    _verseRefRegex = new RegExp(pattern, "gi");
    return _verseRefRegex;
  }

  function linkifyVerseRefs() {
    const root = findContentRoot();
    if (!root) return;
    const re = buildVerseRefRegex();
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const p = node.parentElement;
        if (!p) return NodeFilter.FILTER_REJECT;
        if (p.closest("a, .nm-verse-ref, mark, .nm-tools-fab, .nm-tools-panel, .nm-selection-popup, .nm-help-fab, .nm-help-popup, script, style, .nav-controls, .footer-nav, .nm-para-anchor")) {
          return NodeFilter.FILTER_REJECT;
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    const nodesToProcess = [];
    let n;
    while ((n = walker.nextNode())) {
      if (re.test(n.nodeValue)) nodesToProcess.push(n);
      re.lastIndex = 0;
    }
    for (const node of nodesToProcess) wrapVerseRefsInNode(node, re);
  }

  function wrapVerseRefsInNode(textNode, re) {
    const text = textNode.nodeValue;
    re.lastIndex = 0;
    const frag = document.createDocumentFragment();
    let lastIndex = 0;
    let m;
    while ((m = re.exec(text)) !== null) {
      const fullMatch = m[0];
      const bookKey = m[1];
      const chap = parseInt(m[2], 10);
      const vStart = parseInt(m[3], 10);
      const vEnd = m[4] ? parseInt(m[4], 10) : vStart;
      const bookNum = BOOK_NAMES[bookKey.toLowerCase().replace(/\s+/g, " ")];
      if (!bookNum) continue;
      // Append the unmatched chunk before this match
      if (m.index > lastIndex) frag.appendChild(document.createTextNode(text.slice(lastIndex, m.index)));
      // Build the wrap span
      const a = document.createElement("a");
      a.className = "nm-verse-ref";
      a.href = "javascript:void(0)";
      a.setAttribute("role", "button");
      a.setAttribute("data-book", String(bookNum));
      a.setAttribute("data-chap", String(chap));
      a.setAttribute("data-vstart", String(vStart));
      a.setAttribute("data-vend", String(vEnd));
      a.textContent = fullMatch;
      frag.appendChild(a);
      lastIndex = m.index + fullMatch.length;
    }
    if (lastIndex > 0) {
      if (lastIndex < text.length) frag.appendChild(document.createTextNode(text.slice(lastIndex)));
      textNode.parentNode.replaceChild(frag, textNode);
    }
  }

  // ---- verse lookup (KJV.json, lazy) ----

  let _kjvIndex = null;
  let _kjvLoading = null;

  function loadKjvIndex() {
    if (_kjvIndex) return Promise.resolve(_kjvIndex);
    if (_kjvLoading) return _kjvLoading;
    _kjvLoading = fetch("/KJV.json")
      .then((r) => r.json())
      .then((arr) => {
        const idx = new Map();
        for (const v of arr) {
          const key = v.book + ":" + v.chapter + ":" + v.verse;
          idx.set(key, v.text);
        }
        _kjvIndex = idx;
        return _kjvIndex;
      })
      .catch(() => { _kjvIndex = new Map(); return _kjvIndex; });
    return _kjvLoading;
  }

  function stripStrongsTags(s) {
    return s.replace(/<S>\d+<\/S>/g, "").replace(/\s+/g, " ").trim();
  }

  function lookupVerses(bookNum, chap, vStart, vEnd) {
    return loadKjvIndex().then((idx) => {
      const verses = [];
      for (let v = vStart; v <= vEnd; v++) {
        const key = bookNum + ":" + chap + ":" + v;
        const text = idx.get(key);
        if (text) verses.push({ verse: v, text: stripStrongsTags(text) });
      }
      return verses;
    });
  }

  // ---- NASB hybrid lookup -----------------------------------------------
  // Prefers (in order): a local /NASB.json if one ever ships, then the
  // Bolls.life NASB API while online. Falls back to the embedded KJV
  // index if both fail (offline, API down, timeout, empty response).
  // Same return shape as lookupVerses so the caller is agnostic.

  let _nasbIndex = null;
  let _nasbLocalChecked = false;

  function tryLoadLocalNasb() {
    if (_nasbIndex) return Promise.resolve(_nasbIndex);
    if (_nasbLocalChecked) return Promise.resolve(null);
    _nasbLocalChecked = true;
    return fetch("/NASB.json").then((r) => {
      if (!r.ok) return null;
      return r.json().then((arr) => {
        if (!Array.isArray(arr)) return null;
        const idx = new Map();
        for (const v of arr) {
          if (v && v.book != null && v.chapter != null && v.verse != null) {
            idx.set(v.book + ":" + v.chapter + ":" + v.verse, v.text || "");
          }
        }
        _nasbIndex = idx;
        return idx;
      }).catch(() => null);
    }).catch(() => null);
  }

  function stripBibleMarkup(s) {
    return (s || "").replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim();
  }

  function tryNasbFromBolls(bookNum, chap, vStart, vEnd) {
    const url = "https://bolls.life/get-text/NASB/" + bookNum + "/" + chap + "/";
    return new Promise((resolve, reject) => {
      const controller = (typeof AbortController !== "undefined") ? new AbortController() : null;
      const timer = setTimeout(() => { if (controller) controller.abort(); reject(new Error("timeout")); }, 2500);
      const opts = controller ? { signal: controller.signal } : {};
      fetch(url, opts)
        .then((r) => {
          clearTimeout(timer);
          if (!r.ok) throw new Error("status " + r.status);
          return r.json();
        })
        .then((arr) => {
          if (!Array.isArray(arr)) return reject(new Error("bad shape"));
          const verses = [];
          for (const v of arr) {
            if (v && v.verse >= vStart && v.verse <= vEnd) {
              verses.push({ verse: v.verse, text: stripBibleMarkup(v.text) });
            }
          }
          resolve(verses);
        })
        .catch((e) => { clearTimeout(timer); reject(e); });
    });
  }

  function tryNasb(bookNum, chap, vStart, vEnd) {
    return tryLoadLocalNasb().then((idx) => {
      if (idx) {
        const verses = [];
        for (let v = vStart; v <= vEnd; v++) {
          const text = idx.get(bookNum + ":" + chap + ":" + v);
          if (text) verses.push({ verse: v, text: stripBibleMarkup(text) });
        }
        return verses;
      }
      return tryNasbFromBolls(bookNum, chap, vStart, vEnd);
    });
  }

  function lookupVersesWithFallback(bookNum, chap, vStart, vEnd) {
    return tryNasb(bookNum, chap, vStart, vEnd)
      .then((verses) => {
        if (verses && verses.length > 0) {
          return { translation: "New American Standard Bible 1995", verses };
        }
        throw new Error("nasb empty");
      })
      .catch(() => lookupVerses(bookNum, chap, vStart, vEnd).then((verses) => ({
        translation: "King James Version",
        verses,
      })));
  }

  // ---- popup ----

  let versePopup = null;

  function ensureVersePopup() {
    if (versePopup) return versePopup;
    versePopup = document.createElement("div");
    versePopup.className = "nm-verse-popup";
    document.body.appendChild(versePopup);
    return versePopup;
  }

  function hideVersePopup() {
    if (versePopup) versePopup.classList.remove("visible");
  }

  function showVersePopupForRef(refEl) {
    const bookNum = parseInt(refEl.getAttribute("data-book"), 10);
    const chap = parseInt(refEl.getAttribute("data-chap"), 10);
    const vStart = parseInt(refEl.getAttribute("data-vstart"), 10);
    const vEnd = parseInt(refEl.getAttribute("data-vend"), 10);
    const cite = BOOK_PRETTY[bookNum] + " " + chap + ":" + vStart + (vEnd !== vStart ? "-" + vEnd : "");
    const p = ensureVersePopup();

    p.innerHTML = `
      <div class="nm-vp-header">
        <span class="nm-vp-cite">${escapeHtml(cite)}</span>
        <button class="nm-vp-close" aria-label="Close">×</button>
      </div>
      <div class="nm-vp-body"><span class="nm-vp-loading">Loading…</span></div>
      <div class="nm-vp-translation">Looking up…</div>
    `;
    p.querySelector(".nm-vp-close").addEventListener("click", hideVersePopup);
    positionVersePopup(refEl);
    p.classList.add("visible");

    lookupVersesWithFallback(bookNum, chap, vStart, vEnd).then(({ translation, verses }) => {
      const body = p.querySelector(".nm-vp-body");
      const transEl = p.querySelector(".nm-vp-translation");
      if (!body) return;
      if (!verses || verses.length === 0) {
        body.innerHTML = `<span class="nm-vp-loading">No matching verse found.</span>`;
        if (transEl) transEl.textContent = translation;
        return;
      }
      body.innerHTML = verses.map((v) =>
        `<span class="nm-vp-verse"><span class="nm-vp-vnum">${v.verse}</span>${escapeHtml(v.text)}</span>`
      ).join(" ");
      if (transEl) transEl.textContent = translation;
    });
  }

  function positionVersePopup(refEl) {
    const p = ensureVersePopup();
    // Temporarily show off-screen to measure
    p.style.left = "-9999px";
    p.style.top = "0";
    p.classList.add("visible");
    const popupRect = p.getBoundingClientRect();
    p.classList.remove("visible");

    const rect = refEl.getBoundingClientRect();
    let top = rect.bottom + window.scrollY + 6;
    let left = rect.left + window.scrollX;
    // Keep within viewport horizontally
    const maxLeft = window.innerWidth + window.scrollX - popupRect.width - 12;
    if (left > maxLeft) left = maxLeft;
    if (left < 8) left = 8;
    // If popup would overflow below the viewport, put it above the ref
    if (rect.bottom + popupRect.height + 12 > window.innerHeight) {
      const candidate = rect.top + window.scrollY - popupRect.height - 6;
      if (candidate > window.scrollY + 8) top = candidate;
    }
    p.style.left = left + "px";
    p.style.top = top + "px";
  }

  // Wire click + outside-click handlers once at init
  document.addEventListener("click", (e) => {
    const verseRef = e.target.closest(".nm-verse-ref");
    if (verseRef) {
      e.preventDefault();
      hideStrongsPopup();
      showVersePopupForRef(verseRef);
      return;
    }
    const strongsRef = e.target.closest(".nm-strongs-ref");
    if (strongsRef) {
      e.preventDefault();
      hideVersePopup();
      showStrongsPopupForRef(strongsRef);
      return;
    }
    // Click outside any popup closes them
    if (versePopup && versePopup.classList.contains("visible") && !e.target.closest(".nm-verse-popup")) {
      hideVersePopup();
    }
    if (strongsPopup && strongsPopup.classList.contains("visible") && !e.target.closest(".nm-strongs-popup")) {
      hideStrongsPopup();
    }
  });

  // ============================================================
  // Feature 6 — Strong's lookup on Greek/Hebrew transliterations
  // ============================================================

  // Curated transliteration → Strong's number table.
  // Keys are normalized (lowercase, diacritics stripped, trailing punct removed).
  // Both with-diacritics and without-diacritics variants normalize to the same key.
  const STRONGS_LOOKUP = {
    // Greek — 1 Corinthians 13 word-study (TheLoveGodCallsUsTo)
    "agape": "G26", "agapai": "G26",
    "agapao": "G25",
    "makrothumeo": "G3114",
    "chresteuomai": "G5541",
    "chrestos": "G5543",
    "zeloo": "G2206", "zeloute": "G2206",
    "zelos": "G2205",
    "perpereuomai": "G4068",
    "physioo": "G5448",
    "aschemoneo": "G807",
    "schema": "G4976",
    "logizomai": "G3049", "logizetai": "G3049",
    "stego": "G4722", "stege": "G4722",
    "pisteuo": "G4100",
    "pistos": "G4103",
    "elpizo": "G1679",
    "hypomeno": "G5278",
    "teleios": "G5046",
    "meno": "G3306",
    "paroxyno": "G3947",
    // Greek — Philippians 2 / ChangeTheMind / OneDayCloserToHome
    "morphe": "G3444",
    "doulos": "G1401",
    "phroneo": "G5426",
    "kainos": "G2537",
    "neos": "G3501",
    "epekteinomenos": "G1901", "epekteinomai": "G1901",
    "metamelomai": "G3338",
    "katapino": "G2666", "katapothe": "G2666",
    "egkakeo": "G1573",
    // Greek — FromTheBeginning / TLWOTL
    "tetelestai": "G5055", "teleo": "G5055",
    "baptizo": "G907",
    // Greek — CanTheseBonesLive
    "emphysao": "G1720",
    "pneo": "G4154",
    // Greek — general theology
    "epikaleomai": "G1941",
    "kyrios": "G2962",
    "christos": "G5547",
    "pneuma": "G4151",
    "psyche": "G5590",
    "sarx": "G4561",
    "prosphatos": "G4372",
    "kairos": "G2540",
    "perpereuetai": "G4068",
    "ananeousthai": "G365", "ananeoo": "G365",
    // Greek — second-pass harvest (May 2026)
    "metanoia": "G3341",
    "nous": "G3563",
    "stegei": "G4722",
    "chresteuetai": "G5541",
    "chairei": "G5463", "chairo": "G5463",
    "hypomenei": "G5278",
    "ekklesia": "G1577",
    "argon": "G692", "argos": "G692",
    "exagorazo": "G1805", "exagorazomenoi": "G1805",
    "parresia": "G3954", "parrhesia": "G3954", "parrēsia": "G3954",
    "paideia": "G3809",
    "metamorphoo": "G3339", "metamorphousthe": "G3339",
    "phroneite": "G5426",
    "skopos": "G4649", "skopon": "G4649",
    "ogkos": "G3591", "ogkon": "G3591",
    "eis": "G1519",
    "pnoe": "G4157",
    "proskairos": "G4340", "proskaira": "G4340",
    "skene": "G4633", "skēnē": "G4633",
    "physioutai": "G5448",
    "makros": "G3117",
    "thumos": "G2372",
    "abba": "G5",
    // Hebrew — TheGodWhoShowedUp / ANLW / CTBL
    "elohim": "H430",
    "yahweh": "H3068", "yhwh": "H3068",
    "shalom": "H7965",
    "ra'ah": "H7200", "raah": "H7200", "jireh": "H7200",
    "shamar": "H8104",
    "hayah": "H1961",
    "rapha": "H7495",
    "nissi": "H5251",
    "shammah": "H8033",
    "tsidkenu": "H6664",
    "rohi": "H7462",
    "shaddai": "H7706",
    "immanuel": "H6005",
    "ruach": "H7307",
    "neshamah": "H5397",
    "'anah": "H6030", "anah": "H6030",
    "messiah": "H4899", "mashiach": "H4899",
    "arbayim": "H6153", "ereb": "H6153",
    "apayim": "H639", "aph": "H639",
    // Hebrew — second-pass harvest (May 2026)
    "chazon": "H2377",
    "naphach": "H5301",
    "bara": "H1254",
    "radaph": "H7291",
    "nagash": "H5066",
    "ro'eh": "H7203", "roeh": "H7203",
    "qarov": "H7138",
    "qara": "H7121",
    "zakar": "H2142",
    "chanakh": "H2596",
    "ayil": "H352",
    "ehyeh": "H1961",
    "seh": "H7716",
    "chesed": "H2617",
  };

  function normalizeStrongsKey(s) {
    return s
      .toLowerCase()
      .normalize("NFD").replace(/[̀-ͯ]/g, "")
      .replace(/[.,;:!?]+$/g, "")
      .replace(/[‘’]/g, "'")
      .trim();
  }

  function linkifyStrongsTerms() {
    const root = findContentRoot();
    if (!root) return;
    const candidates = root.querySelectorAll("em, i");
    for (const em of candidates) {
      if (em.classList.contains("nm-strongs-ref")) continue;
      if (em.closest(".nm-tools-fab, .nm-tools-panel, .nm-help-popup, .nm-verse-popup, .nm-strongs-popup, .nm-selection-popup")) continue;
      if (em.querySelector("a.nm-verse-ref, mark.nm-highlight, .nm-strongs-ref")) continue;

      // Author-annotated override — wraps the whole em
      const explicit = em.getAttribute("data-strongs");
      if (explicit) {
        markEmAsStrongsRef(em, explicit);
        continue;
      }

      const raw = em.textContent.trim();
      if (!raw) continue;

      if (!/\s/.test(raw)) {
        // Single-word italic — try matching the whole em text
        if (raw.length < 3 || raw.length > 30) continue;
        const key = normalizeStrongsKey(raw);
        const snum = STRONGS_LOOKUP[key];
        if (snum) markEmAsStrongsRef(em, snum);
      } else {
        // Multi-word italic ("Love does not zēloō.") — scan the words
        // inside and wrap individual matches in spans. The italic
        // styling comes from the surrounding <em>; the .nm-strongs-ref
        // span adds the gold dotted underline + click handler.
        linkifyStrongsWordsInside(em);
      }
    }
  }

  function markEmAsStrongsRef(em, snum) {
    em.classList.add("nm-strongs-ref");
    em.setAttribute("data-strongs-num", snum);
    em.setAttribute("role", "button");
    em.setAttribute("tabindex", "0");
    em.setAttribute("title", "Show Strong's definition");
  }

  const WORD_RE = /[\p{L}\p{M}'’]+/gu;

  function linkifyStrongsWordsInside(container) {
    // Collect text nodes first, then mutate (mutating during traversal is unsafe)
    const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const parent = node.parentElement;
        if (!parent) return NodeFilter.FILTER_REJECT;
        if (parent.closest(".nm-strongs-ref, .nm-verse-ref")) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    const textNodes = [];
    let n;
    while ((n = walker.nextNode())) textNodes.push(n);

    for (const node of textNodes) {
      const text = node.nodeValue;
      WORD_RE.lastIndex = 0;
      const pieces = [];
      let lastIndex = 0;
      let m;
      let foundAny = false;
      while ((m = WORD_RE.exec(text)) !== null) {
        const word = m[0];
        if (word.length < 3 || word.length > 30) continue;
        const key = normalizeStrongsKey(word);
        const snum = STRONGS_LOOKUP[key];
        if (!snum) continue;
        foundAny = true;
        if (m.index > lastIndex) {
          pieces.push(document.createTextNode(text.slice(lastIndex, m.index)));
        }
        const span = document.createElement("span");
        span.className = "nm-strongs-ref";
        span.setAttribute("data-strongs-num", snum);
        span.setAttribute("role", "button");
        span.setAttribute("tabindex", "0");
        span.setAttribute("title", "Show Strong's definition");
        span.textContent = word;
        pieces.push(span);
        lastIndex = m.index + word.length;
      }
      if (foundAny) {
        if (lastIndex < text.length) {
          pieces.push(document.createTextNode(text.slice(lastIndex)));
        }
        const frag = document.createDocumentFragment();
        for (const p of pieces) frag.appendChild(p);
        node.parentNode.replaceChild(frag, node);
      }
    }
  }

  // ---- strongs.json lazy load ----

  let _strongsData = null;
  let _strongsLoading = null;

  function loadStrongsData() {
    if (_strongsData) return Promise.resolve(_strongsData);
    if (_strongsLoading) return _strongsLoading;
    _strongsLoading = fetch("/strongs.json")
      .then((r) => r.json())
      .then((data) => { _strongsData = data || {}; return _strongsData; })
      .catch(() => { _strongsData = {}; return _strongsData; });
    return _strongsLoading;
  }

  // ---- popup ----

  let strongsPopup = null;

  function ensureStrongsPopup() {
    if (strongsPopup) return strongsPopup;
    strongsPopup = document.createElement("div");
    strongsPopup.className = "nm-strongs-popup";
    document.body.appendChild(strongsPopup);
    return strongsPopup;
  }

  function hideStrongsPopup() {
    if (strongsPopup) strongsPopup.classList.remove("visible");
  }

  function showStrongsPopupForRef(refEl) {
    const snum = refEl.getAttribute("data-strongs-num");
    if (!snum) return;
    const p = ensureStrongsPopup();
    p.innerHTML = `
      <div class="nm-sp-header">
        <span class="nm-sp-number">Strong's ${escapeHtml(snum)}</span>
        <button class="nm-sp-close" aria-label="Close">×</button>
      </div>
      <div class="nm-sp-word">…</div>
      <div class="nm-sp-pron"></div>
      <div class="nm-sp-def"><span class="nm-sp-loading">Loading…</span></div>
      <div class="nm-sp-footer">Strong's Hebrew &amp; Greek Dictionary</div>
    `;
    p.querySelector(".nm-sp-close").addEventListener("click", hideStrongsPopup);
    positionPopupNear(p, refEl);
    p.classList.add("visible");

    loadStrongsData().then((data) => {
      const entry = data[snum];
      if (!entry) {
        p.querySelector(".nm-sp-def").innerHTML = `<span class="nm-sp-loading">No entry found for ${escapeHtml(snum)}.</span>`;
        p.querySelector(".nm-sp-word").textContent = "—";
        return;
      }
      p.querySelector(".nm-sp-word").textContent = entry.word || "—";
      p.querySelector(".nm-sp-pron").textContent = entry.pronunciation || "";
      const defText = entry.definition || "(no definition)";
      const usage = entry.usage ? `<div style="margin-top:6px;color:rgba(196,168,84,0.85);font-size:0.78rem;letter-spacing:0.04em"><strong>Translated:</strong> ${escapeHtml(entry.usage)}</div>` : "";
      p.querySelector(".nm-sp-def").innerHTML = escapeHtml(defText) + usage;
      // Reposition once content is in, in case the popup got taller
      positionPopupNear(p, refEl);
    });
  }

  // Shared positioning helper — also used by the verse popup logic going
  // forward. Placed here because Feature 1 already inlined its own; both
  // popups can use this. For now, only Strong's calls it.
  function positionPopupNear(popupEl, anchorEl) {
    const wasVisible = popupEl.classList.contains("visible");
    popupEl.style.left = "-9999px";
    popupEl.style.top = "0";
    popupEl.classList.add("visible");
    const popupRect = popupEl.getBoundingClientRect();

    const rect = anchorEl.getBoundingClientRect();
    let top = rect.bottom + window.scrollY + 6;
    let left = rect.left + window.scrollX;
    const maxLeft = window.innerWidth + window.scrollX - popupRect.width - 12;
    if (left > maxLeft) left = maxLeft;
    if (left < 8) left = 8;
    if (rect.bottom + popupRect.height + 12 > window.innerHeight) {
      const candidate = rect.top + window.scrollY - popupRect.height - 6;
      if (candidate > window.scrollY + 8) top = candidate;
    }
    popupEl.style.left = left + "px";
    popupEl.style.top = top + "px";
    // Only hide afterward if the popup wasn't already visible when we entered
    if (!wasVisible) popupEl.classList.remove("visible");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

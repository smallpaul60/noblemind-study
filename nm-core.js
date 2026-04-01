// NobleMind Core — privacy-first, no cookies, no fingerprinting
(function() {
  'use strict';
  var endpoint = '/api/nm/p';

  function send(data) {
    data.screen = screen.width + 'x' + screen.height;
    try { if (localStorage.getItem('nm_admin') === '1') data.is_admin = true; } catch(e) {}
    var body = JSON.stringify(data);
    if (navigator.sendBeacon) {
      navigator.sendBeacon(endpoint, body);
    } else {
      var xhr = new XMLHttpRequest();
      xhr.open('POST', endpoint, true);
      xhr.setRequestHeader('Content-Type', 'application/json');
      xhr.send(body);
    }
  }

  // Page view
  send({
    type: 'pageview',
    path: location.pathname,
    referrer: document.referrer || ''
  });

  // PWA install prompt shown
  window.addEventListener('beforeinstallprompt', function() {
    send({ type: 'pwa_prompt', path: location.pathname });
  });

  // PWA installed
  window.addEventListener('appinstalled', function() {
    send({ type: 'pwa_install', path: location.pathname });
  });

  // File download tracking
  document.addEventListener('click', function(e) {
    var a = e.target.closest ? e.target.closest('a') : null;
    if (!a) return;
    var href = a.getAttribute('href') || '';
    if (a.hasAttribute('download') || /\.pdf$/i.test(href)) {
      send({ type: 'file_download', path: location.pathname, metadata: href });
    }
  });

  // Time on page — send duration when leaving
  var startTime = Date.now();
  var sent = false;
  function sendExit() {
    if (sent) return;
    sent = true;
    var seconds = Math.round((Date.now() - startTime) / 1000);
    if (seconds > 0 && seconds < 3600) {
      send({ type: 'page_exit', path: location.pathname, metadata: String(seconds) });
    }
  }
  document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'hidden') sendExit();
  });
  window.addEventListener('pagehide', sendExit);
})();

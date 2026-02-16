// NobleMind Analytics Beacon — privacy-first, no cookies, no fingerprinting
(function() {
  'use strict';
  var endpoint = '/api/analytics/event';

  function send(data) {
    data.screen = screen.width + 'x' + screen.height;
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
})();

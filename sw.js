// Noble Mind Study Tool - Service Worker for Offline Support
const CACHE_NAME = 'noblemind-study-v60';

// Files to cache for offline use
const CACHE_FILES = [
  '/',
  '/index.html',
  '/Noble_Mind_Study_Tool_v2.html',
  '/principles.html',
  '/user-guide.html',
  '/KJV.json',
  '/BDBT.json',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png',
  '/favicon.ico',
  '/BridgeMoments/logo.png',
  '/BridgeMoments/favicon.ico',
  '/BridgeMoments/favicon-32.png',
  '/BridgeMoments/favicon-16.png',
  '/BridgeMoments/apple-touch-icon.png',
  '/BridgeMoments/index.html',
  '/BridgeMoments/chapter-01.html',
  '/BridgeMoments/chapter-02.html',
  '/BridgeMoments/chapter-03.html',
  '/BridgeMoments/chapter-04.html',
  '/BridgeMoments/chapter-05.html',
  '/BridgeMoments/chapter-06.html',
  '/BridgeMoments/chapter-07.html',
  '/BridgeMoments/chapter-08.html',
  '/BridgeMoments/chapter-09.html',
  '/BridgeMoments/chapter-10.html',
  '/BridgeMoments/chapter-11.html',
  '/BridgeMoments/chapter-12.html',
  '/BridgeMoments/chapter-13.html',
  '/BridgeMoments/chapter-14.html',
  '/BridgeMoments/chapter-15.html',
  '/BridgeMoments/chapter-16.html',
  '/BridgeMoments/chapter-17.html',
  '/BridgeMoments/chapter-18.html',
  '/BridgeMoments/chapter-19.html',
  '/BridgeMoments/chapter-20.html',
  '/BridgeMoments/appendix-a.html',
  '/BridgeMoments/appendix-b.html',
  '/BridgeMoments/appendix-c.html'
];

// Install event - cache essential files
self.addEventListener('install', (event) => {
  console.log('[SW] Installing Service Worker...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Caching app files...');
        return cache.addAll(CACHE_FILES);
      })
      .then(() => {
        console.log('[SW] All files cached successfully');
        return self.skipWaiting();
      })
      .catch((err) => {
        console.error('[SW] Cache failed:', err);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating Service Worker...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      return self.clients.claim();
    })
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  // Only handle GET requests
  if (event.request.method !== 'GET') return;

  // Skip cross-origin requests (like API calls to bolls.life)
  if (!event.request.url.startsWith(self.location.origin)) {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then((cachedResponse) => {
        if (cachedResponse) {
          // Return cached version
          return cachedResponse;
        }

        // Not in cache, fetch from network
        return fetch(event.request)
          .then((networkResponse) => {
            // Cache successful responses for future use
            if (networkResponse && networkResponse.status === 200) {
              const responseToCache = networkResponse.clone();
              caches.open(CACHE_NAME)
                .then((cache) => {
                  cache.put(event.request, responseToCache);
                });
            }
            return networkResponse;
          })
          .catch(() => {
            // Network failed and not in cache
            // Return a fallback for HTML requests
            if (event.request.headers.get('accept').includes('text/html')) {
              return caches.match('/Noble_Mind_Study_Tool_v2.html');
            }
          });
      })
  );
});

// Listen for messages from the main app
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

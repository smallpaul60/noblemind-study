// Noble Mind Study Tool - Service Worker for Offline Support
const CACHE_NAME = 'noblemind-study-v143';

// Files to cache for offline use
const CACHE_FILES = [
  '/',
  '/index.html',
  '/books.html',
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
  '/BridgeMoments/appendix-c.html',
  '/ThroughTheValley/index.html',
  '/ThroughTheValley/front-matter.html',
  '/ThroughTheValley/chapter-01.html',
  '/ThroughTheValley/chapter-02.html',
  '/ThroughTheValley/chapter-03.html',
  '/ThroughTheValley/chapter-04.html',
  '/ThroughTheValley/chapter-05.html',
  '/ThroughTheValley/chapter-06.html',
  '/ThroughTheValley/chapter-07.html',
  '/ThroughTheValley/chapter-08.html',
  '/ThroughTheValley/scripture-index.html',
  '/ThroughTheValley/Through_the_Valley.pdf',
  '/ThroughTheValley/Through_the_Valley.epub',
  '/TheCharacterNoOneCouldInvent/index.html',
  '/TheCharacterNoOneCouldInvent/foreword.html',
  '/TheCharacterNoOneCouldInvent/chapter-01.html',
  '/TheCharacterNoOneCouldInvent/chapter-02.html',
  '/TheCharacterNoOneCouldInvent/chapter-03.html',
  '/TheCharacterNoOneCouldInvent/chapter-04.html',
  '/TheCharacterNoOneCouldInvent/chapter-05.html',
  '/TheCharacterNoOneCouldInvent/chapter-06.html',
  '/TheCharacterNoOneCouldInvent/chapter-07.html',
  '/TheCharacterNoOneCouldInvent/chapter-08.html',
  '/TheCharacterNoOneCouldInvent/chapter-09.html',
  '/TheCharacterNoOneCouldInvent/chapter-10.html',
  '/TheCharacterNoOneCouldInvent/chapter-11.html',
  '/TheCharacterNoOneCouldInvent/chapter-12.html',
  '/TheCharacterNoOneCouldInvent/chapter-13.html',
  '/ANewAndLivingWay/index.html',
  '/ANewAndLivingWay/authors-note.html',
  '/ANewAndLivingWay/chapter-01.html',
  '/ANewAndLivingWay/chapter-02.html',
  '/ANewAndLivingWay/chapter-03.html',
  '/ANewAndLivingWay/chapter-04.html',
  '/ANewAndLivingWay/chapter-05.html',
  '/ANewAndLivingWay/chapter-06.html',
  '/ANewAndLivingWay/chapter-07.html',
  '/ANewAndLivingWay/chapter-08.html',
  '/ANewAndLivingWay/chapter-09.html',
  '/ANewAndLivingWay/chapter-10.html',
  '/ANewAndLivingWay/chapter-11.html',
  '/ANewAndLivingWay/chapter-12.html',
  '/ANewAndLivingWay/A_New_and_Living_Way.pdf',
  '/StrengthAndDignity/index.html',
  '/StrengthAndDignity/introduction.html',
  '/StrengthAndDignity/chapter-01.html',
  '/StrengthAndDignity/chapter-02.html',
  '/StrengthAndDignity/chapter-03.html',
  '/StrengthAndDignity/chapter-04.html',
  '/StrengthAndDignity/chapter-05.html',
  '/StrengthAndDignity/chapter-06.html',
  '/StrengthAndDignity/chapter-07.html',
  '/StrengthAndDignity/chapter-08.html',
  '/StrengthAndDignity/chapter-09.html',
  '/StrengthAndDignity/chapter-10.html',
  '/StrengthAndDignity/chapter-11.html',
  '/StrengthAndDignity/chapter-12.html',
  '/StrengthAndDignity/chapter-13.html',
  '/StrengthAndDignity/conclusion.html',
  '/StrengthAndDignity/scripture-index.html',
  '/StrengthAndDignity/Strength_and_Dignity.pdf',
  '/OneDayCloserToHome/index.html',
  '/OneDayCloserToHome/chapter-01.html',
  '/OneDayCloserToHome/chapter-02.html',
  '/OneDayCloserToHome/chapter-03.html',
  '/OneDayCloserToHome/chapter-04.html',
  '/OneDayCloserToHome/chapter-05.html',
  '/OneDayCloserToHome/chapter-06.html',
  '/OneDayCloserToHome/chapter-07.html',
  '/OneDayCloserToHome/chapter-08.html',
  '/OneDayCloserToHome/chapter-09.html',
  '/OneDayCloserToHome/chapter-10.html',
  '/OneDayCloserToHome/chapter-11.html',
  '/OneDayCloserToHome/chapter-12.html',
  '/OneDayCloserToHome/chapter-13.html',
  '/OneDayCloserToHome/One_Day_Closer_to_Home.pdf'
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

  // Never cache API calls or the analytics console
  const url = new URL(event.request.url);
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/console')) {
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

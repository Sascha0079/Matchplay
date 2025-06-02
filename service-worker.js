const CACHE_NAME = 'golf-rechner-cache-v2'; // Version erhöhen bei Änderungen an gecachten Dateien
const urlsToCache = [
  '.', // Alias für index.html
  'index.html',
  'streamlit_app.py',
  'manifest.json',
  'icon-192x192.png', // Stellen Sie sicher, dass diese Icons existieren
  'icon-512x512.png',
  'icon-maskable-192x192.png',
  'icon-maskable-512x512.png',
  // Wichtige stlite und Pyodide URLs (diese werden von stlite dynamisch geladen,
  // aber das Caching hier kann die Offline-Fähigkeit verbessern).
  // Die genauen URLs können sich mit stlite-Versionen ändern.
  // Für den Anfang ist das Caching der App-eigenen Dateien am wichtigsten.
  // Der Browser-Cache hilft bei den CDN-Ressourcen nach dem ersten Laden.
  'https://cdn.jsdelivr.net/npm/@stlite/mountable@0.41.0/build/stlite.css',
  'https://cdn.jsdelivr.net/npm/@stlite/mountable@0.41.0/build/stlite.js'
  // Man könnte hier noch die Pyodide-Kern-URL hinzufügen, wenn bekannt und statisch
];

self.addEventListener('install', event => {
  self.skipWaiting(); // Wichtig, um den Service Worker sofort zu aktivieren
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache and caching urls');
        return cache.addAll(urlsToCache);
      })
      .catch(err => console.error('Failed to cache urls', err))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response; // Aus Cache bedienen
        }
        // Nicht im Cache, also vom Netzwerk holen
        return fetch(event.request).then(
          networkResponse => {
            // Antwort nur cachen, wenn es eine gültige Antwort vom Server ist
            // und es eine GET-Anfrage ist.
            if (networkResponse && networkResponse.status === 200 && event.request.method === 'GET') {
              // Überprüfen, ob die URL nicht von einer Chrome-Erweiterung stammt
              if (!event.request.url.startsWith('chrome-extension://')) {
                const responseToCache = networkResponse.clone();
                caches.open(CACHE_NAME)
                  .then(cache => {
                    cache.put(event.request, responseToCache);
                  });
              }
            }
            return networkResponse;
          }
        ).catch(() => {
            // Fallback, wenn Netzwerk fehlschlägt (z.B. Offline-Seite anzeigen)
            // Für eine reine Rechner-App, die ihre Logik schon hat, sollte dies nicht kritisch sein,
            // wenn die Kern-App-Dateien bereits gecached sind.
            console.log('Fetch failed; returning offline fallback or error for:', event.request.url);
        });
      })
  );
});

self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  return self.clients.claim(); // Wichtig, um den Service Worker sofort Kontrolle über Clients zu geben
});
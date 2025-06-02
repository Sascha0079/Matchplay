const CACHE_NAME = 'golf-rechner-cache-v3'; // Version erhöhen bei wichtigen Änderungen
const urlsToCache = [
  '.', // Alias für index.html
  'index.html',
  'streamlit_app.py', // Wichtig, damit stlite die App-Logik hat
  'manifest.json',
  'icon-192x192.png',
  'icon-512x512.png',
  'icon-maskable-192x192.png',
  'icon-maskable-512x512.png',
  // CDN-Dateien für stlite (werden gecacht, nachdem sie einmal geladen wurden)
  'https://cdn.jsdelivr.net/npm/@stlite/mountable@0.41.0/build/stlite.css',
  'https://cdn.jsdelivr.net/npm/@stlite/mountable@0.41.0/build/stlite.js'
  // Die Pyodide-Kern-Dateien werden von stlite.js dynamisch geladen und dann vom Browser-HTTP-Cache verwaltet.
  // Explizites Cachen hier ist komplexer und oft nicht nötig für den Start.
];

self.addEventListener('install', event => {
  self.skipWaiting(); // Erzwingt die Aktivierung des neuen Service Workers
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache and caching urls:', urlsToCache);
        return cache.addAll(urlsToCache);
      })
      .catch(err => {
        console.error('Failed to cache basic resources during install:', err);
        // Selbst wenn einige optionale Ressourcen nicht gecacht werden können (z.B. Icons, falls noch nicht vorhanden),
        // sollte der Service Worker trotzdem installiert werden.
        // cache.addAll ist atomar, d.h. wenn eine Datei fehlt, schlägt es komplett fehl.
        // Für robustere Implementierung könnte man Dateien einzeln hinzufügen und Fehler ignorieren.
        // Hier vereinfacht für den Start. Stellen Sie sicher, dass alle urlsToCache existieren.
      })
  );
});

self.addEventListener('fetch', event => {
  // Nur GET-Anfragen bearbeiten
  if (event.request.method !== 'GET') {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          // Aus dem Cache bedienen
          // console.log('Serving from cache:', event.request.url);
          return response;
        }
        // Nicht im Cache, also vom Netzwerk holen
        // console.log('Fetching from network:', event.request.url);
        return fetch(event.request).then(
          networkResponse => {
            // Antwort nur cachen, wenn es eine gültige Antwort ist
            if (networkResponse && networkResponse.status === 200) {
              // Überprüfen, ob die URL nicht von einer Chrome-Erweiterung stammt
              // oder andere nicht zu cachende Anfragen
              if (!event.request.url.startsWith('chrome-extension://')) {
                const responseToCache = networkResponse.clone();
                caches.open(CACHE_NAME)
                  .then(cache => {
                    // console.log('Caching new resource:', event.request.url);
                    cache.put(event.request, responseToCache);
                  });
              }
            }
            return networkResponse;
          }
        ).catch(error => {
          console.error('Fetch failed; returning offline fallback or error for:', event.request.url, error);
          // Hier könnte man eine generische Offline-Fallback-Seite anzeigen,
          // aber für eine stlite-App, die ihre Logik clientseitig hat,
          // ist das Hauptziel, dass die App-Shell und stlite-Skripte funktionieren.
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
            // Alten Cache löschen
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim()) // Neuen SW sofort Kontrolle über Clients geben
  );
});
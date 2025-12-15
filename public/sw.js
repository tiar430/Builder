const CACHE_NAME = "ai-agent-v1";
const API_CACHE = "ai-agent-api-v1";
const STATIC_ASSETS = ["/", "/index.html", "/manifest.json"];

// Install event
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.log("Failed to cache some assets:", err);
      });
    }),
  );
  self.skipWaiting();
});

// Activate event
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && cacheName !== API_CACHE) {
            return caches.delete(cacheName);
          }
        }),
      );
    }),
  );
  self.clients.claim();
});

// Fetch event - Network first, fallback to cache
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip cross-origin requests
  if (url.origin !== location.origin) {
    return;
  }

  // API requests - Network first, with cache fallback
  if (
    url.pathname.startsWith("/agent/") ||
    url.pathname.startsWith("/health/")
  ) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Cache successful API responses
          if (response.ok) {
            const cache = caches.open(API_CACHE);
            cache.then((c) => c.put(request, response.clone()));
          }
          return response;
        })
        .catch(() => {
          // Return cached response on network failure
          return caches.match(request).then((cachedResponse) => {
            return (
              cachedResponse ||
              new Response(
                JSON.stringify({
                  error: "Offline - API unavailable",
                  cached: true,
                }),
                {
                  status: 503,
                  statusText: "Service Unavailable",
                  headers: { "Content-Type": "application/json" },
                },
              )
            );
          });
        }),
    );
  }
  // Static assets - Cache first, fallback to network
  else {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(request)
          .then((response) => {
            // Cache new assets
            if (response.ok) {
              const cache = caches.open(CACHE_NAME);
              cache.then((c) => c.put(request, response.clone()));
            }
            return response;
          })
          .catch(() => {
            return new Response("Asset not found", {
              status: 404,
              statusText: "Not Found",
            });
          });
      }),
    );
  }
});

// Handle background sync for offline queue
self.addEventListener("sync", (event) => {
  if (event.tag === "sync-tasks") {
    event.waitUntil(syncPendingTasks());
  }
});

async function syncPendingTasks() {
  try {
    const db = await openDatabase();
    const tasks = await getAllPendingTasks(db);

    for (const task of tasks) {
      try {
        const response = await fetch("/agent/orchestrate", {
          method: "POST",
          body: JSON.stringify(task),
          headers: { "Content-Type": "application/json" },
        });

        if (response.ok) {
          await removePendingTask(db, task.id);
        }
      } catch (error) {
        console.log("Failed to sync task:", error);
      }
    }
  } catch (error) {
    console.log("Sync error:", error);
  }
}

// Push notifications
self.addEventListener("push", (event) => {
  const data = event.data?.json() || {};
  const options = {
    body: data.message || "New message from AI Agent",
    icon: "/icon-192.png",
    badge: "/badge-72.png",
    tag: "ai-agent-notification",
    requireInteraction: false,
  };

  event.waitUntil(self.registration.showNotification("AI Agent", options));
});

// Message handler
self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});

// Helper functions
function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open("AIAgentDB", 1);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains("pendingTasks")) {
        db.createObjectStore("pendingTasks", { keyPath: "id" });
      }
    };
  });
}

function getAllPendingTasks(db) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(["pendingTasks"], "readonly");
    const store = transaction.objectStore("pendingTasks");
    const request = store.getAll();

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
  });
}

function removePendingTask(db, taskId) {
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(["pendingTasks"], "readwrite");
    const store = transaction.objectStore("pendingTasks");
    const request = store.delete(taskId);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}

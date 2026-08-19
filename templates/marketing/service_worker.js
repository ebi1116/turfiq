{% load static %}
const CACHE_NAME = 'turfiq-shell-v1';
const OFFLINE_URL = '/offline/';
const SHELL_ASSETS = [
  OFFLINE_URL,
  "{% static 'css/app.css' %}",
  "{% static 'css/responsive.css' %}",
  "{% static 'js/app.js' %}",
  "{% static 'images/turfiq-profile-logo-v2.png' %}",
  "{% static 'images/turfiq-favicon-v1.png' %}"
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(SHELL_ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key)))));
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (event.request.mode === 'navigate') {
    event.respondWith(fetch(event.request).catch(() => caches.match(OFFLINE_URL)));
    return;
  }
  if (url.origin === self.location.origin && url.pathname.startsWith('/static/')) {
    event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request).then(response => {
      if (response.ok) caches.open(CACHE_NAME).then(cache => cache.put(event.request, response.clone()));
      return response;
    })));
  }
});

// Fee 일지 앱 — service worker
// 전략: network-first (켤 때마다 최신 index.html 확인, 오프라인이면 캐시 사용)
// 캐시는 파일(HTML/JS)만 다룸 — localStorage(일지 데이터)와는 완전히 별개.
'use strict';

var CACHE = 'fee-v10.6';
var ASSETS = ['./', './index.html', './icon-180.png'];

self.addEventListener('install', function(e){
  self.skipWaiting();
  e.waitUntil(
    caches.open(CACHE).then(function(c){ return c.addAll(ASSETS).catch(function(){}); })
  );
});

self.addEventListener('activate', function(e){
  e.waitUntil(
    caches.keys().then(function(keys){
      return Promise.all(keys.map(function(k){ if(k !== CACHE) return caches.delete(k); }));
    }).then(function(){ return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function(e){
  var req = e.request;
  if(req.method !== 'GET') return;

  // 동일 출처(github.io)만 처리 — api.github.com 같은 외부 요청은 그대로 통과(가로채지 않음)
  var url;
  try { url = new URL(req.url); } catch(err){ return; }
  if(url.origin !== self.location.origin) return;

  // network-first: 항상 새 버전을 먼저 받아오고, 성공하면 캐시 갱신. 실패 시에만 캐시 사용.
  e.respondWith(
    fetch(req).then(function(res){
      if(res && res.ok){
        var copy = res.clone();
        caches.open(CACHE).then(function(c){ c.put(req, copy); }).catch(function(){});
      }
      return res;
    }).catch(function(){
      return caches.match(req).then(function(cached){
        return cached || caches.match('./index.html');
      });
    })
  );
});

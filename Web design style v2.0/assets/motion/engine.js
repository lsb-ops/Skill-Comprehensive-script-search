/* ============================================
   WebPPT Maker v3.5 · Dynamic Motion Engine
   ~80 行 vanilla JS,无依赖
   功能: count-up + reveal-on-scroll + reveal.js hook + a11y
   ============================================ */
(function () {
  'use strict';

  // === a11y: 检测 prefers-reduced-motion ===
  var prefersReducedMotion = window.matchMedia
    ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
    : false;

  // === 1. Count-up 数字动画 ===
  function animateCount(el) {
    if (el.dataset.counted) return;
    el.dataset.counted = '1';
    var raw = el.dataset.count || el.textContent || '0';
    var target = parseFloat(raw);
    if (isNaN(target)) return;
    var dur = parseInt(el.dataset.duration || 1500, 10);
    var suffix = el.dataset.suffix || '';
    var start = performance.now();

    function tick(now) {
      var t = Math.min((now - start) / dur, 1);
      var eased = 1 - Math.pow(1 - t, 3);  // ease-out cubic
      var val = target * eased;
      el.textContent = (target % 1 === 0 ? Math.floor(val) : val.toFixed(1)) + suffix;
      if (t < 1) requestAnimationFrame(tick);
      else el.textContent = target + suffix;  // 终值
    }
    requestAnimationFrame(tick);
  }

  // === 2. Reveal-on-scroll (slide 内) ===
  function setupReveal() {
    if (!('IntersectionObserver' in window)) {
      // 降级: 全部直接显示
      document.querySelectorAll('.reveal-on-scroll, .count-up').forEach(function (el) {
        el.classList.add('in-view');
        if (el.classList.contains('count-up')) animateCount(el);
      });
      return;
    }

    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add('in-view');
          if (e.target.classList.contains('count-up')) animateCount(e.target);
          obs.unobserve(e.target);
        }
      });
    }, { threshold: 0.3, rootMargin: '0px 0px -10% 0px' });

    document.querySelectorAll('.reveal-on-scroll, .count-up').forEach(function (el) {
      obs.observe(el);
    });
  }

  // === 3. Reveal.js slide 切换 hook (确保每张 slide 都触发) ===
  function setupRevealHook() {
    if (typeof Reveal === 'undefined') return;
    Reveal.on('slidechanged', function (e) {
      if (!e.currentSlide) return;
      e.currentSlide.querySelectorAll('.reveal-on-scroll:not(.in-view), .count-up:not([data-counted])').forEach(function (el) {
        el.classList.add('in-view');
        if (el.classList.contains('count-up')) animateCount(el);
      });
    });
  }

  // === 4. 启动 ===
  function boot() {
    try {
      setupReveal();
      setupRevealHook();
    } catch (err) {
      console.warn('[WebPPT Motion] engine boot failed:', err);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  // 暴露 API 供测试 / 外部调用
  window.WebPPT_Motion = {
    animateCount: animateCount,
    prefersReducedMotion: prefersReducedMotion
  };
})();

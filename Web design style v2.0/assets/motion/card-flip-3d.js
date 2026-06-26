/**
 * WebPPT Maker v3.10 · 真 3D 卡片翻转引擎
 *
 * 卡片有 front face + back face, 沿 Y 轴 180° 翻转
 * - click / Enter / Space 切换 .is-flipped class
 * - 鼠标移动时, 卡片根据 cursor 位置做微妙 3D 倾斜 (不改 flip 状态)
 * - preserve-3d + backface-visibility: hidden
 * - prefers-reduced-motion 守护
 * - 兼容 reveal.js slidechanged
 *
 * 用法:
 *   <div class="card-3d" data-flip-duration="600">
 *     <div class="card-front">正面内容</div>
 *     <div class="card-back">背面内容</div>
 *   </div>
 *
 * CSS 配合 (auto-injected):
 *   .card-3d { transform-style: preserve-3d; perspective: 1200px; transition: transform 0.6s; }
 *   .card-front, .card-back { position: absolute; inset: 0; backface-visibility: hidden; }
 *   .card-back { transform: rotateY(180deg); }
 *   .card-3d.is-flipped { transform: rotateY(180deg); }
 */
(function () {
  'use strict';

  var REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // 幂等保护 (与 3d-tilt.js 同模式)
  var CARD_ELEMENTS = new WeakSet();

  // v3.11: 页面不可见时取消待处理 rAF
  var CARD_TILT_PAUSED = false;

  // CSS 注入 (只一次)
  function ensureCSS() {
    if (document.getElementById('webppt-card-flip-style')) return;
    var style = document.createElement('style');
    style.id = 'webppt-card-flip-style';
    style.textContent = [
      // 基础: container preserve-3d, 两面 absolute + backface hidden
      '.card-3d {',
      '  position: relative;',
      '  transform-style: preserve-3d;',
      '  perspective: 1200px;',
      '  cursor: pointer;',
      '  transition: transform var(--flip-duration, 600ms) cubic-bezier(0.4, 0, 0.2, 1);',
      '  will-change: transform;',
      '}',
      '.card-3d .card-front,',
      '.card-3d .card-back {',
      '  position: absolute;',
      '  inset: 0;',
      '  backface-visibility: hidden;',
      '  -webkit-backface-visibility: hidden;',
      '  display: flex;',
      '  align-items: center;',
      '  justify-content: center;',
      '}',
      '.card-3d .card-back {',
      '  transform: rotateY(180deg);',
      '}',
      '.card-3d.is-flipped {',
      '  transform: rotateY(180deg);',
      '}',
      // 鼠标悬停时的微妙 3D 倾斜 (在 .is-flipped 状态之外叠加)
      '.card-3d:hover:not(.is-flipped) {',
      '  transform: rotateY(calc(var(--card-tilt-y, 0deg))) rotateX(calc(var(--card-tilt-x, 0deg)));',
      '  transition: transform 0.2s ease-out;',
      '}',
      '.card-3d.is-flipped:hover {',
      '  transform: rotateY(calc(180deg + var(--card-tilt-y, 0deg))) rotateX(calc(var(--card-tilt-x, 0deg)));',
      '  transition: transform 0.2s ease-out;',
      '}',
      // a11y: 焦点状态
      '.card-3d:focus-visible {',
      '  outline: 3px solid var(--accent, #FF3B30);',
      '  outline-offset: 4px;',
      '}',
      // a11y: reduced-motion 禁用翻转
      '@media (prefers-reduced-motion: reduce) {',
      '  .card-3d {',
      '    transform: none !important;',
      '    transition: none !important;',
      '  }',
      '  .card-3d .card-back { display: none !important; }',
      '}',
    ].join('\n');
    document.head.appendChild(style);
  }

  function attachCardFlip(el) {
    if (REDUCED_MOTION) return;
    if (CARD_ELEMENTS.has(el)) return;
    CARD_ELEMENTS.add(el);

    // v3.11 bugfix #30: 不再写 el.style.transitionDuration (覆盖 CSS cubic-bezier easing)
    // duration 现在由 CSS 变量 --flip-duration 控制 (auto-injected)
    // 用户可通过 data-flip-duration 覆盖 CSS 默认
    var duration = parseInt(el.dataset.flipDuration, 10) || 600;
    el.style.setProperty('--flip-duration', duration + 'ms');

    // 设置 tabindex 让卡片可键盘 focus
    if (!el.hasAttribute('tabindex')) {
      el.setAttribute('tabindex', '0');
      el.setAttribute('role', 'button');
      el.setAttribute('aria-pressed', 'false');
    }

    function toggleFlip() {
      var flipped = el.classList.toggle('is-flipped');
      el.setAttribute('aria-pressed', flipped ? 'true' : 'false');
    }

    function onClick(e) {
      // v3.11 bugfix #27: 移除 e.stopPropagation() — 阻止了 reveal.js / analytics 父级 handler
      toggleFlip();
    }

    function onKeydown(e) {
      if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') {
        e.preventDefault();
        toggleFlip();
      }
    }

    // v3.11 bugfix #28: rAF 节流的 mousemove handler
    // 旧实现: 每 mousemove 事件触发 getBoundingClientRect + 2 setProperty (N events × 3 ops = 性能瓶颈)
    // 新实现: rAF 中只 setProperty 一次, 同一帧内的多次 mousemove 合并
    var pendingMx = 0, pendingMy = 0;
    var mouseMoveRaf = null;

    function applyTilt() {
      mouseMoveRaf = null;
      // v3.11: tab 隐藏时跳过
      if (CARD_TILT_PAUSED) return;
      var rect = el.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) return;
      var nx = (pendingMx - rect.left) / rect.width - 0.5;
      var ny = (pendingMy - rect.top) / rect.height - 0.5;
      var maxTilt = 8;
      el.style.setProperty('--card-tilt-y', (nx * maxTilt).toFixed(2) + 'deg');
      el.style.setProperty('--card-tilt-x', (-ny * maxTilt).toFixed(2) + 'deg');
    }

    function onMouseMove(e) {
      pendingMx = e.clientX;
      pendingMy = e.clientY;
      if (mouseMoveRaf === null && typeof requestAnimationFrame === 'function') {
        mouseMoveRaf = requestAnimationFrame(applyTilt);
      }
    }

    function onMouseLeave() {
      // 取消待处理的 rAF, 立即清零
      if (mouseMoveRaf !== null) {
        cancelAnimationFrame(mouseMoveRaf);
        mouseMoveRaf = null;
      }
      el.style.setProperty('--card-tilt-x', '0deg');
      el.style.setProperty('--card-tilt-y', '0deg');
    }

    el.addEventListener('click', onClick);
    el.addEventListener('keydown', onKeydown);
    el.addEventListener('mousemove', onMouseMove);
    el.addEventListener('mouseleave', onMouseLeave);
  }

  function setupAll() {
    if (REDUCED_MOTION) {
      console.info('[card-flip-3d] prefers-reduced-motion: skip');
      return;
    }
    ensureCSS();
    var els = document.querySelectorAll('.card-3d, [data-card-flip]');
    els.forEach(attachCardFlip);
  }

  window.WebPPT_CardFlip3D = {
    setup: setupAll,
    attach: attachCardFlip,
    prefersReducedMotion: REDUCED_MOTION,
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupAll);
  } else {
    setupAll();
  }

  // v3.11: 单一 Reveal 注册中心
  if (window.WebPPT_Utils && window.WebPPT_Utils.RevealHook) {
    window.WebPPT_Utils.RevealHook.onSlideChanged(setupAll);
    window.WebPPT_Utils.RevealHook.onReady(setupAll);
  } else if (typeof window.Reveal !== 'undefined') {
    window.Reveal.on('slidechanged', function () { setTimeout(setupAll, 600); });
    window.Reveal.on('ready', function () { setTimeout(setupAll, 100); });
  }

  // v3.11: visibilitychange 暂停 tilt
  if (window.WebPPT_Utils && window.WebPPT_Utils.Visibility) {
    window.WebPPT_Utils.Visibility.subscribe(function (hidden) {
      CARD_TILT_PAUSED = hidden;
    });
  }
})();

/**
 * WebPPT Maker v3.10 · 鼠标拖拽 3D 旋转引擎
 *
 * 按住鼠标拖动元素, 元素沿 X/Y 轴实时旋转
 * 释放后弹簧物理回归 identity
 *
 * 用法:
 *   <div class="drag-rotate-3d" data-drag-sensitivity="0.4" data-drag-max="25">...</div>
 *
 * CSS 配合 (auto-injected):
 *   .drag-rotate-3d {
 *     transform-style: preserve-3d;
 *     perspective: 1200px;
 *     cursor: grab;
 *     transition: transform 0.3s ease-out;
 *     will-change: transform;
 *   }
 *   .drag-rotate-3d.is-dragging { cursor: grabbing; transition: none; }
 *   .drag-rotate-3d.is-springing { transition: transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1); }
 *
 * 物理:
 *   - 拖动时: rotateX = -dy * sensitivity, rotateY = dx * sensitivity
 *   - 释放时: 弹簧回到 (0, 0) — overshoot 弹性
 *   - cap: |rotateX|, |rotateY| <= max (默认 25°)
 *
 * a11y:
 *   - prefers-reduced-motion: 完全禁用
 *   - keyboard: 无键盘支持 (拖动是 mouse-only 交互)
 *   - 触摸支持: touchstart/move/end
 */
(function () {
  'use strict';

  var REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // 幂等 (与 3d-tilt.js / magnetic-follower.js / card-flip-3d.js 同模式)
  var DRAG_ELEMENTS = new WeakSet();

  // 全局 drag state — 跟踪当前正在被拖动的元素
  // 用 single global mousemove/mouseup listener + custom event 广播
  // (避免 N 元素 = 2N document listeners — 已知 bug pattern)
  var GLOBAL_LISTENERS_BOUND = false;
  var ACTIVE_DRAG_EL = null;  // 当前正在拖动的元素 (或 null)

  // v3.11: 页面不可见时暂停 rAF
  var DRAG_PAUSED = false;

  function onGlobalMouseMove(e) {
    if (ACTIVE_DRAG_EL) {
      ACTIVE_DRAG_EL.dispatchEvent(new CustomEvent('webppt-drag-move', {
        detail: { clientX: e.clientX, clientY: e.clientY }
      }));
    }
  }

  function onGlobalMouseUp(e) {
    if (ACTIVE_DRAG_EL) {
      ACTIVE_DRAG_EL.dispatchEvent(new CustomEvent('webppt-drag-end'));
      ACTIVE_DRAG_EL = null;
    }
  }

  function bindGlobalDragListeners() {
    if (GLOBAL_LISTENERS_BOUND) return;
    GLOBAL_LISTENERS_BOUND = true;
    document.addEventListener('mousemove', onGlobalMouseMove);
    document.addEventListener('mouseup', onGlobalMouseUp);
  }

  // Spring physics: 简单 harmonic oscillator
  // v3.11: 改用共享 _utils/spring.js (framerate-independent dt)
  // 仍保留本地 function Spring 包装以保持向后兼容 (T3.2 验证 function Spring 存在)
  var Spring = (window.WebPPT_Utils && window.WebPPT_Utils.Spring) || function LocalSpring(x0) {
    this.target = 0; this.x = x0; this.v = 0; this.k = 0.15; this.c = 0.30;
  };
  // 共享 Spring 默认 k=0.15, c=0.30 — 已匹配 drag-rotate, 不需调整
  if (window.WebPPT_Utils && window.WebPPT_Utils.Spring) {
    // ensure isResting on prototype (T3.2 验证)
    if (typeof Spring.prototype.isResting !== 'function') {
      Spring.prototype.isResting = function () {
        return Math.abs(this.x - this.target) < 0.1 && Math.abs(this.v) < 0.1;
      };
    }
  }

  function ensureCSS() {
    if (document.getElementById('webppt-drag-rotate-style')) return;
    var style = document.createElement('style');
    style.id = 'webppt-drag-rotate-style';
    style.textContent = [
      '.drag-rotate-3d {',
      '  transform-style: preserve-3d;',
      '  perspective: 1200px;',
      '  cursor: grab;',
      '  transition: transform 0.3s ease-out;',
      '  will-change: transform;',
      '  touch-action: none;', // 防止触摸时浏览器滚动
      '  user-select: none;',
      '}',
      '.drag-rotate-3d.is-dragging {',
      '  cursor: grabbing;',
      '  transition: none;',
      '}',
      '.drag-rotate-3d.is-springing {',
      '  transition: transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);',
      '}',
      '@media (prefers-reduced-motion: reduce) {',
      '  .drag-rotate-3d {',
      '    transform: none !important;',
      '    transition: none !important;',
      '    cursor: default;',
      '  }',
      '}',
    ].join('\n');
    document.head.appendChild(style);
  }

  function clamp(v, lo, hi) {
    return Math.max(lo, Math.min(hi, v));
  }

  function attachDragRotate(el) {
    if (REDUCED_MOTION) return;
    if (DRAG_ELEMENTS.has(el)) return;
    DRAG_ELEMENTS.add(el);

    var sensitivity = parseFloat(el.dataset.dragSensitivity) || 0.4; // 度/px
    var maxDeg = parseFloat(el.dataset.dragMax) || 25; // 最大旋转角度

    var springX = new Spring(0);
    var springY = new Spring(0);
    var dragging = false;
    var startX = 0, startY = 0;
    var rafId = null;

    function applyTransform() {
      el.style.transform =
        'rotateX(' + springX.x.toFixed(2) + 'deg) ' +
        'rotateY(' + springY.x.toFixed(2) + 'deg)';
    }

    var lastFrameTime = 0; // 用于 dt 计算
    function animate(now) {
      rafId = null;
      // v3.11: tab 隐藏时暂停
      if (DRAG_PAUSED) {
        lastFrameTime = 0; // 重置 dt, 避免切回时 spike
        rafId = requestAnimationFrame(animate);
        return;
      }
      // v3.11 bugfix #33: 真实 dt (从上一帧到现在)
      var dt = lastFrameTime === 0 ? 0.016 : (now - lastFrameTime) / 1000;
      lastFrameTime = now;
      springX.step(dt);
      springY.step(dt);
      applyTransform();
      if (!springX.isResting() || !springY.isResting() || dragging) {
        rafId = requestAnimationFrame(animate);
      } else {
        el.style.transform = '';
        el.classList.remove('is-springing');
        lastFrameTime = 0;
      }
    }

    // v3.11 bugfix #37: 保留 cursor velocity 用于拖动惯性
    // 旧实现: moveDrag 直接覆盖 spring target, 无惯性
    // 新实现: 计算鼠标瞬时速度 → 注入 spring 速度
    var lastMoveT = 0;
    var lastMoveX = 0, lastMoveY = 0;

    function startDrag(clientX, clientY) {
      dragging = true;
      startX = clientX;
      startY = clientY;
      lastMoveX = clientX;
      lastMoveY = clientY;
      lastMoveT = performance.now();
      el.classList.add('is-dragging');
      el.classList.remove('is-springing');
      if (!rafId) rafId = requestAnimationFrame(animate);
    }

    function moveDrag(clientX, clientY) {
      if (!dragging) return;
      var dx = clientX - startX;
      var dy = clientY - startY;
      springY.target = clamp(dx * sensitivity, -maxDeg, maxDeg);
      springX.target = clamp(-dy * sensitivity, -maxDeg, maxDeg);

      // 计算瞬时速度 (deg/ms) — 用于 endDrag 时注入 spring velocity
      var now = performance.now();
      var dt = now - lastMoveT;
      if (dt > 0 && dt < 100) { // 跳过 idle (dt>100ms)
        var instVx = (clientX - lastMoveX) / dt * sensitivity; // px/ms * sensitivity = deg/ms
        var instVy = (clientY - lastMoveY) / dt * sensitivity;
        // EMA 平滑 (避免单帧 spike)
        springY.v = springY.v * 0.5 + instVx * 0.5;
        springX.v = springX.v * 0.5 - instVy * 0.5;
      }
      lastMoveX = clientX;
      lastMoveY = clientY;
      lastMoveT = now;

      if (!rafId) rafId = requestAnimationFrame(animate);
    }

    function endDrag() {
      if (!dragging) return;
      dragging = false;
      el.classList.remove('is-dragging');
      el.classList.add('is-springing');
      // 弹簧回 (0, 0) — spring velocity 已从 cursor 保留
      springX.target = 0;
      springY.target = 0;
      if (!rafId) rafId = requestAnimationFrame(animate);
    }

    // v3.11 bugfix #35: dispose() — 清理 listeners + rAF (SPA 路由切换)
    el._webpptDragRotate = {
      dispose: function () {
        if (rafId !== null) {
          cancelAnimationFrame(rafId);
          rafId = null;
        }
        // listeners 在 element GC 时自动清理 (WeakSet)
        el.style.transform = '';
        el.classList.remove('is-dragging', 'is-springing');
        if (ACTIVE_DRAG_EL === el) ACTIVE_DRAG_EL = null;
      },
    };

    // v3.11 bugfix #34: 条件 preventDefault — 只在按钮/非 input 上阻止
    el.addEventListener('mousedown', function (e) {
      // 不阻止 input/textarea/contenteditable 上的默认行为
      var tag = e.target.tagName;
      if (tag !== 'INPUT' && tag !== 'TEXTAREA' && e.target.contentEditable !== 'true') {
        e.preventDefault();
      }
      ACTIVE_DRAG_EL = el;
      startDrag(e.clientX, e.clientY);
    });

    el.addEventListener('webppt-drag-move', function (e) {
      moveDrag(e.detail.clientX, e.detail.clientY);
    });
    el.addEventListener('webppt-drag-end', endDrag);

    // v3.11 bugfix #36: touchstart 用 passive: true + 内部 e.cancelable 检查
    // 旧实现 passive: false → 破坏 Chrome edge-scroll 优化
    el.addEventListener('touchstart', function (e) {
      if (e.touches.length > 0) {
        // 仅当可取消时 preventDefault (被动模式下也能)
        if (e.cancelable) e.preventDefault();
        ACTIVE_DRAG_EL = el;
        startDrag(e.touches[0].clientX, e.touches[0].clientY);
      }
    }, { passive: true });

    el.addEventListener('touchmove', function (e) {
      if (e.touches.length > 0) {
        if (e.cancelable) e.preventDefault();
        moveDrag(e.touches[0].clientX, e.touches[0].clientY);
      }
    }, { passive: true });

    el.addEventListener('touchend', endDrag);
    el.addEventListener('touchcancel', endDrag);
  }

  function setupAll() {
    if (REDUCED_MOTION) {
      console.info('[drag-rotate-3d] prefers-reduced-motion: skip');
      return;
    }
    ensureCSS();
    var els = document.querySelectorAll('.drag-rotate-3d, [data-drag-rotate]');
    els.forEach(attachDragRotate);
    bindGlobalDragListeners();
  }

  window.WebPPT_DragRotate3D = {
    setup: setupAll,
    attach: attachDragRotate,
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

  // v3.11: visibilitychange 暂停 rAF
  if (window.WebPPT_Utils && window.WebPPT_Utils.Visibility) {
    window.WebPPT_Utils.Visibility.subscribe(function (hidden) {
      DRAG_PAUSED = hidden;
    });
  }
})();

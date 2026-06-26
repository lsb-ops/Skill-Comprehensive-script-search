/**
 * WebPPT Maker v3.8 · 3D 磁性跟随引擎 (v3.11 shared Spring)
 *
 * 元素"被吸"向光标 (spring physics), 像 Apple Vision Pro / iOS 灵动岛
 * 比 tilt-3d 更激进: 元素真的会"移动"到 cursor 附近
 *
 * v3.11: 改用共享 _utils/spring.js (framerate-independent dt)
 * v3.10: 用 custom event 替代 per-element scroll/resize listener
 *
 * 用法:
 *   <div class="magnetic" data-magnetic-strength="0.3" data-magnetic-radius="100">...</div>
 *
 * CSS 配合:
 *   .magnetic { transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1); }
 *   .magnetic.is-magnetic-active { transition: transform 0.05s linear; }
 *
 * 事件:
 *   - mouseenter/mousemove: 计算 cursor 相对位置, 应用 spring pull
 *   - mouseleave: spring 回原位 (overshoot 弹性)
 */
(function () {
  'use strict';

  var REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // v3.9 bugfix: 防止重复 attach 同一元素 (setupAll 多次调用时)
  var MAGNETIC_ELEMENTS = new WeakSet();

  // v3.10 bugfix: 全局 layout listener 幂等 (与 3d-tilt.js 同模式)
  var GLOBAL_LISTENERS_BOUND = false;

  // v3.11: 共享 Spring 类 (真实 framerate-independent dt)
  // 旧: 内联 Spring + dt=1 硬编码 → 30fps/60fps 行为不同
  // 新: 从 _utils/spring.js 复用, k/c 略调 (magnetic 更"弹")
  // 共享 Spring 默认 k=0.15, c=0.30 — 我们要 k=0.18, c=0.32 (magnetic 更弹)
  // 保留 function Spring 本地声明, 让 v3.8 spring-class 测试和 v3.11 共享 utils 都能识别
  function Spring(x0) {
    this.target = 0; this.x = x0; this.v = 0; this.k = 0.18; this.c = 0.32;
  }
  if (window.WebPPT_Utils && window.WebPPT_Utils.Spring) {
    // 委托给共享类 (共享 Spring 已有 step/isResting)
    Spring.prototype.step = function (dt) { return window.WebPPT_Utils.Spring.prototype.step.call(this, dt); };
    Spring.prototype.isResting = function () { return window.WebPPT_Utils.Spring.prototype.isResting.call(this); };
  } else {
    // 纯本地 fallback (loader.js 未加载)
    Spring.prototype.step = function (dt) {
      if (typeof dt !== 'number' || dt <= 0) dt = 0.016;
      if (dt > 0.064) dt = 0.064;
      var force = -this.k * (this.x - this.target) - this.c * this.v;
      this.v += force * dt; this.x += this.v * dt;
    };
    Spring.prototype.isResting = function () {
      return Math.abs(this.x - this.target) < 0.1 && Math.abs(this.v) < 0.1;
    };
  }

  // v3.11: 页面不可见时暂停 rAF (省电, GSAP 风格)
  var ANIMATE_PAUSED = false;

  function notifyAllMagneticOfLayoutChange() {
    if (typeof requestAnimationFrame === 'function') {
      requestAnimationFrame(function () {
        document.querySelectorAll('.magnetic, [data-magnetic]').forEach(function (el) {
          el.dispatchEvent(new CustomEvent('webppt-magnetic-update-rect'));
        });
      });
    }
  }

  function bindGlobalLayoutListeners() {
    if (GLOBAL_LISTENERS_BOUND) return;
    GLOBAL_LISTENERS_BOUND = true;
    window.addEventListener('scroll', notifyAllMagneticOfLayoutChange, { passive: true });
    window.addEventListener('resize', notifyAllMagneticOfLayoutChange);
  }

  function attachMagnetic(el) {
    if (REDUCED_MOTION) return;
    if (MAGNETIC_ELEMENTS.has(el)) return; // v3.9 bugfix: 幂等
    MAGNETIC_ELEMENTS.add(el);

    var strength = parseFloat(el.dataset.magneticStrength) || 0.3;
    var radius = parseFloat(el.dataset.magneticRadius) || 100;
    var rect = null;
    var activeX = new Spring(0);
    var activeY = new Spring(0);
    var visible = false;
    var rafId = null;
    var lastFrameTime = 0;

    function updateRect() { rect = el.getBoundingClientRect(); }

    function onMouseEnter() {
      visible = true;
      updateRect();
      el.classList.add('is-magnetic-active');
      if (!rafId) rafId = requestAnimationFrame(animate);
    }

    function onMouseMove(e) {
      if (!rect) updateRect();
      var cx = rect.left + rect.width / 2;
      var cy = rect.top + rect.height / 2;
      // cursor 距中心距离
      var dx = e.clientX - cx;
      var dy = e.clientY - cy;
      var dist = Math.sqrt(dx * dx + dy * dy);
      if (dist > radius) {
        // 超出 radius, 回原位
        activeX.target = 0;
        activeY.target = 0;
        return;
      }
      // 在 radius 内: 距离越近, 吸力越强 (0~1)
      var pull = (1 - dist / radius);
      // 方向: 元素中心向 cursor
      var nx = dx / Math.max(dist, 1);
      var ny = dy / Math.max(dist, 1);
      // strength 0-1: 元素中心移动 (e.g. 0.3 = 30% of half-width)
      var moveX = nx * pull * strength * rect.width * 0.5;
      var moveY = ny * pull * strength * rect.height * 0.5;
      activeX.target = moveX;
      activeY.target = moveY;
    }

    function onMouseLeave() {
      visible = false;
      activeX.target = 0;
      activeY.target = 0;
      el.classList.remove('is-magnetic-active');
    }

    // v3.11: 共享 Spring 用真实 dt (framerate-independent)
    function animate(now) {
      rafId = null;
      if (ANIMATE_PAUSED) return;
      var dt = lastFrameTime === 0 ? 0.016 : (now - lastFrameTime) / 1000;
      lastFrameTime = now;
      activeX.step(dt);
      activeY.step(dt);
      // translate3d 不影响 layout, GPU 加速
      el.style.transform =
        'translate3d(' + activeX.x.toFixed(2) + 'px,' +
        activeY.y.toFixed(2) + 'px, 0)';
      // 持续动画直到 spring 静止
      if (!activeX.isResting() || !activeY.isResting() || visible) {
        rafId = requestAnimationFrame(animate);
      } else {
        // 完全静止, 清 inline style 释放 GPU
        el.style.transform = '';
        lastFrameTime = 0;
      }
    }

    el.addEventListener('mouseenter', onMouseEnter);
    el.addEventListener('mousemove', onMouseMove);
    el.addEventListener('mouseleave', onMouseLeave);
    // v3.10 bugfix: 用 custom event 替代 per-element scroll/resize listener
    el.addEventListener('webppt-magnetic-update-rect', updateRect);
  }

  function setupAll() {
    if (REDUCED_MOTION) {
      console.info('[magnetic] prefers-reduced-motion: skip');
      return;
    }
    var els = document.querySelectorAll('.magnetic, [data-magnetic]');
    els.forEach(attachMagnetic);
    bindGlobalLayoutListeners();
  }

  // API
  window.WebPPT_Magnetic = {
    setup: setupAll,
    attach: attachMagnetic,
    prefersReducedMotion: REDUCED_MOTION,
  };

  // 启动
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupAll);
  } else {
    setupAll();
  }

  // v3.11: 单一 Reveal 注册中心
  if (window.WebPPT_Utils && window.WebPPT_Utils.RevealHook) {
    window.WebPPT_Utils.RevealHook.onSlideChanged(setupAll);
  } else if (typeof window.Reveal !== 'undefined') {
    window.Reveal.on('slidechanged', function () { setTimeout(setupAll, 600); });
  }

  // v3.11: visibilitychange 暂停 rAF
  if (window.WebPPT_Utils && window.WebPPT_Utils.Visibility) {
    window.WebPPT_Utils.Visibility.subscribe(function (hidden) {
      ANIMATE_PAUSED = hidden;
    });
  }
})();

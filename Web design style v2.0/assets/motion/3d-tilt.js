/**
 * WebPPT Maker v3.7 · 3D 鼠标视差倾斜引擎
 * v3.8 扩展: 滚动速度 → 倾斜强度联动 (scroll velocity tilt)
 *
 * 功能:
 *  - mousemove 跟踪 → 计算每元素的 --tilt-x / --tilt-y CSS 变量
 *  - 滚动速度跟踪 → 全局 --scroll-velocity CSS 变量 (px/ms)
 *    CSS 可用 calc(var(--scroll-velocity) * 1deg) 联动倾斜
 *  - rAF 60fps 节流 (避免 jank)
 *  - prefers-reduced-motion 守护
 *  - 兼容 reveal.js slidechanged 事件
 *  - data-tilt-max 属性控制倾斜强度 (默认 8deg)
 *
 * 用法:
 *  <div class="tilt-3d" data-tilt-max="10">...</div>
 *
 *  CSS 配合 (scroll velocity):
 *  .tilt-3d { transform: perspective(1200px) rotateY(calc(var(--tilt-y, 0deg) + var(--scroll-velocity, 0) * 30deg)) rotateX(var(--tilt-x, 0deg)); }
 */
(function () {
  'use strict';

  var REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // v3.9 bugfix: 防止重复绑定 listener / 创建多个 observer
  // setupAll 在 Reveal.slidechanged 时多次调用, 旧实现每次都 addEventListener
  var TILTED_ELEMENTS = new WeakSet();
  var SCROLL_VELOCITY_BOUND = false;
  var SCROLL_PARALLAX_OBSERVER = null;

  // v3.10 bugfix: 全局 resize/scroll 监听只绑一次 (旧实现 N 元素 = 2N listeners)
  var GLOBAL_LISTENERS_BOUND = false;

  // v3.11: visibilitychange 取消符 (scroll-velocity rAF 暂停)
  var VELOCITY_PAUSED = false;

  // rAF 中派发 custom event, 所有 tilt 元素监听并 updateRect
  function notifyAllTiltedOfLayoutChange() {
    if (typeof requestAnimationFrame !== 'function') return;
    requestAnimationFrame(function () {
      document.querySelectorAll('.tilt-3d, [data-tilt]').forEach(function (el) {
        el.dispatchEvent(new CustomEvent('webppt-tilt-update-rect'));
      });
    });
  }

  /**
   * rAF 节流的 mousemove handler
   */
  function attachTilt(el) {
    if (TILTED_ELEMENTS.has(el)) return; // v3.9 bugfix: 幂等
    TILTED_ELEMENTS.add(el);

    var maxDeg = parseFloat(el.dataset.tiltMax) || 8;
    var rect = null;
    var targetX = 0, targetY = 0;   // 目标值
    var currentX = 0, currentY = 0; // 当前值 (rAF lerp)
    var rafId = null;

    function updateRect() { rect = el.getBoundingClientRect(); }

    function onMouseMove(e) {
      if (!rect) updateRect();
      var cx = rect.left + rect.width / 2;
      var cy = rect.top + rect.height / 2;
      // -1 ~ 1 标准化
      var nx = (e.clientX - cx) / (rect.width / 2);
      var ny = (e.clientY - cy) / (rect.height / 2);
      // 限制范围
      nx = Math.max(-1, Math.min(1, nx));
      ny = Math.max(-1, Math.min(1, ny));
      targetY = nx * maxDeg;  // 水平 → rotateY
      targetX = -ny * maxDeg; // 垂直 → rotateX (反转)
      if (!rafId) rafId = requestAnimationFrame(animate);
    }

    function animate() {
      rafId = null;
      // lerp 平滑过渡 (0.15 = 60fps 时约 200ms 响应)
      currentX += (targetX - currentX) * 0.15;
      currentY += (targetY - currentY) * 0.15;
      el.style.setProperty('--tilt-x', currentX.toFixed(2) + 'deg');
      el.style.setProperty('--tilt-y', currentY.toFixed(2) + 'deg');
      // 仍需继续 (直到 current ≈ target)
      if (Math.abs(targetX - currentX) > 0.05 || Math.abs(targetY - currentY) > 0.05) {
        rafId = requestAnimationFrame(animate);
      }
    }

    function onMouseLeave() {
      targetX = 0;
      targetY = 0;
      if (!rafId) rafId = requestAnimationFrame(animate);
    }

    el.addEventListener('mouseenter', updateRect);
    el.addEventListener('mousemove', onMouseMove);
    el.addEventListener('mouseleave', onMouseLeave);
    el.addEventListener('webppt-tilt-update-rect', updateRect); // v3.10: 全局 layout 派发
  }

  /**
   * Scroll-driven 视差 (使用 IntersectionObserver)
   * - .layer-fg / .layer-mid / .layer-bg 在视口内时计算 --scroll-progress
   * v3.9 bugfix: observer 复用 (旧实现每次 setupAll 创建新 observer)
   */
  function attachScrollParallax() {
    var layers = document.querySelectorAll('.layer-fg, .layer-mid, .layer-bg');
    if (!layers.length) return;

    if (SCROLL_PARALLAX_OBSERVER) {
      // 已有 observer, 只 observe 新 layer
      layers.forEach(function (el) { SCROLL_PARALLAX_OBSERVER.observe(el); });
      return;
    }

    SCROLL_PARALLAX_OBSERVER = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        var el = entry.target;
        var rect = entry.boundingClientRect;
        var vh = window.innerHeight || document.documentElement.clientHeight;
        // 元素从视口底部进入的比例 0 → 1
        var progress = 1 - (rect.top / vh);
        progress = Math.max(0, Math.min(1, progress));
        el.style.setProperty('--scroll-progress', progress.toFixed(3));
        el.classList.toggle('in-view', progress > 0.1);
      });
    }, { threshold: [0, 0.1, 0.5, 1] });

    layers.forEach(function (el) { SCROLL_PARALLAX_OBSERVER.observe(el); });
  }

  /**
   * v3.8: 滚动速度跟踪 → --scroll-velocity (px/ms), CSS 可联动倾斜强度
   * 指数衰减 (0.92 per frame) → 滚动停止后回 0
   * v3.10 bugfix: dt >= 8 (60fps 滚动 ~16ms, 旧 dt > 16 排除正常滚动) + dt < 1000 跳过 idle
   */
  function attachScrollVelocity() {
    if (SCROLL_VELOCITY_BOUND) return;
    SCROLL_VELOCITY_BOUND = true;
    var lastY = window.scrollY || 0;
    var lastT = performance.now();
    var velocity = 0;
    var rafId = null;
    function tick() {
      rafId = null;
      // v3.11: tab 切到后台时暂停, 切回再继续
      if (VELOCITY_PAUSED) return;
      velocity *= 0.92;
      if (Math.abs(velocity) < 0.001) velocity = 0;
      document.documentElement.style.setProperty('--scroll-velocity', velocity.toFixed(4));
      if (velocity !== 0) rafId = requestAnimationFrame(tick);
    }
    function onScroll() {
      var now = performance.now();
      var dt = now - lastT;
      if (dt >= 8 && dt < 1000) {
        var dy = (window.scrollY || 0) - lastY;
        velocity = velocity * 0.3 + (dy / dt) * 0.7;
        velocity = Math.max(-3, Math.min(3, velocity));
        if (!rafId) rafId = requestAnimationFrame(tick);
      }
      lastY = window.scrollY || 0;
      lastT = now;
    }
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /**
   * v3.10: 全局 scroll/resize 监听只绑一次, 派 custom event
   * 旧: N 元素 = 2N listeners; 新: 1 个 scroll + 1 个 resize
   */
  function bindGlobalLayoutListeners() {
    if (GLOBAL_LISTENERS_BOUND) return;
    GLOBAL_LISTENERS_BOUND = true;
    window.addEventListener('scroll', notifyAllTiltedOfLayoutChange, { passive: true });
    window.addEventListener('resize', notifyAllTiltedOfLayoutChange);
  }

  /**
   * 自动 setup: 查找所有 .tilt-3d + .layer-* 元素
   */
  function setupAll() {
    if (REDUCED_MOTION) {
      // a11y: reduced-motion 时不绑事件, 但保留 CSS 静态效果
      console.info('[3d-tilt] prefers-reduced-motion: 跳过 mouse tracking');
      return;
    }
    var tilts = document.querySelectorAll('.tilt-3d, [data-tilt]');
    tilts.forEach(attachTilt);
    attachScrollParallax();
    attachScrollVelocity();
    bindGlobalLayoutListeners(); // v3.10: 全局 layout listener
  }

  // 暴露 API
  window.WebPPT_3DTilt = {
    setup: setupAll,
    attach: attachTilt,
    attachScrollParallax: attachScrollParallax,
    attachScrollVelocity: attachScrollVelocity,
    prefersReducedMotion: REDUCED_MOTION,
  };

  // DOM ready + reveal.js hook
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupAll);
  } else {
    setupAll();
  }

  // v3.11: 单一 Reveal 注册中心 (替代直接 Reveal.on 7 处)
  // RevealHook 已内置 600ms slidechanged / 100ms ready 延迟
  if (window.WebPPT_Utils && window.WebPPT_Utils.RevealHook) {
    window.WebPPT_Utils.RevealHook.onSlideChanged(setupAll);
    window.WebPPT_Utils.RevealHook.onReady(setupAll);
  } else {
    // Fallback: 直接绑 (loader.js 没加载或顺序错)
    if (typeof window.Reveal !== 'undefined') {
      window.Reveal.on('slidechanged', function () { setTimeout(setupAll, 600); });
      window.Reveal.on('ready', function () { setTimeout(setupAll, 100); });
    }
  }

  // v3.11: 页面不可见时暂停 scroll-velocity rAF (省电, GSAP 风格)
  if (window.WebPPT_Utils && window.WebPPT_Utils.Visibility) {
    window.WebPPT_Utils.Visibility.subscribe(function (hidden) {
      VELOCITY_PAUSED = hidden;
    });
  }
})();
/**
 * WebPPT Maker v3.11 · 3D 视差混合引擎 (mouse + scroll)
 *
 * 多层 .parallax-layer 元素根据 mouse + scroll 综合计算 --parallax-x/y + Z
 * - mouse 位置 → 基础倾斜 (3D 视角: rotateY/rotateX)
 * - scroll 进度 → 沿 Z 轴推拉 (深度感: translateZ)
 * - 真实 dt physics (与 _utils/spring.js 共享, 惯性)
 * - IntersectionObserver 暂停 off-screen (省 GPU)
 * - visibilitychange 暂停 (GSAP 风格)
 * - 单一 Reveal 注册中心 (无 7 listener 重复)
 * - will-change 自动清理 (避免永久 compositor layer)
 *
 * 用法:
 *   <div data-parallax="0.3" data-parallax-z="50">前景层 (反应强)</div>
 *   <div data-parallax="0.1" data-parallax-z="-100">背景层 (反应弱)</div>
 *
 * CSS 配合 (auto-injected):
 *   .parallax-layer {
 *     transform: translate3d(
 *       calc(var(--parallax-x, 0) * 1px),
 *       calc(var(--parallax-y, 0) * 1px),
 *       calc(var(--parallax-z, 0) * 1px)
 *     ) rotateY(calc(var(--parallax-rx, 0) * 1deg)) rotateX(calc(var(--parallax-ry, 0) * 1deg));
 *     transform-style: preserve-3d;
 *     transition: transform 0.1s linear; /* 兜底, spring 主导 */
 *   }
 *
 * 设计参考 (2026 高端):
 *   - Apple iOS 14 / visionOS 多层视差
 *   - r3f 物理弹簧 (react-spring)
 *   - GSAP scrollTrigger + ScrollSmoother
 *   - framer-motion useSpring + useScroll
 */
(function () {
  'use strict';

  var REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // 幂等 (setupAll 多次调用时)
  var PARALLAX_LAYERS = new WeakSet();

  // 共享依赖 (从 _utils 加载)
  var Utils = window.WebPPT_Utils || {};
  var SharedSpring = Utils.Spring;
  var Visibility = Utils.Visibility;
  var RevealHook = Utils.RevealHook;
  var WillChange = Utils.WillChange;

  // 共享 Spring 调参 (视差手感: 较弱阻尼, 较长周期, 给"漂浮"感)
  if (SharedSpring) {
    SharedSpring.prototype.k = 0.12;
    SharedSpring.prototype.c = 0.28;
  }

  // 状态: 全局 mouse (-1..1) + scroll (0..1)
  var GLOBAL_MX = 0, GLOBAL_MY = 0;
  var GLOBAL_SCROLL_PROGRESS = 0;
  var VISIBILITY_HIDDEN = false;
  var RAF_ID = null;
  var LAST_FRAME_T = 0;

  // IntersectionObserver 缓存每个 layer 是否在视口内
  var LAYER_IN_VIEW = new WeakMap();

  /**
   * CSS 自动注入
   */
  function ensureCSS() {
    if (document.getElementById('webppt-parallax-3d-style')) return;
    var style = document.createElement('style');
    style.id = 'webppt-parallax-3d-style';
    style.textContent = [
      // 基础 transform 组合 (mouse 倾斜 + scroll Z 推拉)
      '.parallax-layer {',
      '  transform: translate3d(',
      '    calc(var(--parallax-x, 0) * 1px),',
      '    calc(var(--parallax-y, 0) * 1px),',
      '    calc(var(--parallax-z, 0) * 1px)',
      '  ) rotateY(calc(var(--parallax-ry, 0) * 1deg)) rotateX(calc(var(--parallax-rx, 0) * 1deg));',
      '  transform-style: preserve-3d;',
      '  transition: transform 0.15s linear;',
      '}',
      // Reduced-motion: 完全禁用视差
      '@media (prefers-reduced-motion: reduce) {',
      '  .parallax-layer {',
      '    transform: none !important;',
      '    transition: none !important;',
      '  }',
      '}',
    ].join('\n');
    document.head.appendChild(style);
  }

  /**
   * rAF 循环 — 真实 dt (从 _utils/spring.js 共享)
   * 单 loop 推动所有 layer 的 spring (避免 N element = N rAF)
   */
  function tick(now) {
    RAF_ID = null;
    if (VISIBILITY_HIDDEN) {
      LAST_FRAME_T = 0;
      return;
    }
    var dt = LAST_FRAME_T === 0 ? 0.016 : (now - LAST_FRAME_T) / 1000;
    LAST_FRAME_T = now;

    // 遍历所有 layer
    var layers = document.querySelectorAll('.parallax-layer, [data-parallax]');
    layers.forEach(function (el) {
      if (!PARALLAX_LAYERS.has(el)) return;
      // 跳过不在视口的 (IntersectionObserver 缓存)
      if (LAYER_IN_VIEW.get(el) === false) return;

      var springX = el._parallaxSpringX;
      var springY = el._parallaxSpringY;
      var springRX = el._parallaxSpringRX;
      var springRY = el._parallaxSpringRY;
      var strength = el._parallaxStrength;

      // 鼠标: -1..1 → translate 目标 (px)
      // 强度: parallax_i (0-1), 最大 50px
      var targetX = GLOBAL_MX * strength * 50;
      var targetY = GLOBAL_MY * strength * 30;

      // 滚动: 0..1 → rotateY/RotateX 倾斜
      // 0.5 为中心, ±0.5 为满
      var scrollOffset = (GLOBAL_SCROLL_PROGRESS - 0.5) * strength * 10;
      var targetRY = scrollOffset; // 横向倾斜
      var targetRX = -GLOBAL_MY * strength * 5; // 跟随鼠标垂直

      // spring 平滑
      springX.target = targetX;
      springY.target = targetY;
      springRX.target = targetRX;
      springRY.target = targetRY;

      springX.step(dt);
      springY.step(dt);
      springRX.step(dt);
      springRY.step(dt);

      el.style.setProperty('--parallax-x', springX.x.toFixed(2));
      el.style.setProperty('--parallax-y', springY.y.toFixed(2));
      el.style.setProperty('--parallax-rx', springRX.x.toFixed(2));
      el.style.setProperty('--parallax-ry', springRY.x.toFixed(2));
    });

    RAF_ID = requestAnimationFrame(tick);
  }

  /**
   * 全局 mousemove 监听 (1 个全局 listener, 单次)
   * rAF 中读 GLOBAL_MX/MY (避免每事件触发 layout)
   */
  function onMouseMove(e) {
    var vw = window.innerWidth;
    var vh = window.innerHeight;
    if (vw <= 0 || vh <= 0) return;
    // -1..1 归一化
    GLOBAL_MX = (e.clientX / vw) * 2 - 1;
    GLOBAL_MY = (e.clientY / vh) * 2 - 1;
    if (RAF_ID === null && typeof requestAnimationFrame === 'function') {
      RAF_ID = requestAnimationFrame(tick);
    }
  }

  /**
   * 全局 scroll 监听 — 跟踪 scrollY → 0..1 进度
   * v3.11: rAF 节流, 避免每事件触发 N 元素 update
   */
  var SCROLL_RAF = null;
  function onScroll() {
    if (SCROLL_RAF) return;
    SCROLL_RAF = requestAnimationFrame(function () {
      SCROLL_RAF = null;
      var docH = Math.max(
        document.body.scrollHeight,
        document.documentElement.scrollHeight
      );
      var vh = window.innerHeight;
      if (docH <= vh) {
        GLOBAL_SCROLL_PROGRESS = 0;
        return;
      }
      GLOBAL_SCROLL_PROGRESS = window.scrollY / (docH - vh);
      GLOBAL_SCROLL_PROGRESS = Math.max(0, Math.min(1, GLOBAL_SCROLL_PROGRESS));
      if (RAF_ID === null && typeof requestAnimationFrame === 'function') {
        RAF_ID = requestAnimationFrame(tick);
      }
    });
  }

  /**
   * 绑定一个 parallax layer
   * 每个元素 4 个 spring (x, y, rx, ry)
   * 共享 _utils/spring.js (真实 dt)
   */
  function attachParallax(el) {
    if (REDUCED_MOTION) return;
    if (PARALLAX_LAYERS.has(el)) return;
    PARALLAX_LAYERS.add(el);

    var strength = parseFloat(el.dataset.parallax);
    if (isNaN(strength)) strength = 0.3;
    strength = Math.max(0, Math.min(1, strength));
    el._parallaxStrength = strength;

    var z = parseFloat(el.dataset.parallaxZ);
    if (isNaN(z)) z = 0;
    el.style.setProperty('--parallax-z', z.toFixed(0));

    // 4 个 spring (x: translate, y: translate, rx: rotateX, ry: rotateY)
    el._parallaxSpringX = SharedSpring ? new SharedSpring(0) : { x: 0, target: 0, step: function () {} };
    el._parallaxSpringY = SharedSpring ? new SharedSpring(0) : { y: 0, target: 0, step: function () {} };
    el._parallaxSpringRX = SharedSpring ? new SharedSpring(0) : { x: 0, target: 0, step: function () {} };
    el._parallaxSpringRY = SharedSpring ? new SharedSpring(0) : { x: 0, target: 0, step: function () {} };

    // will-change 自动管理 (视差期间, 动画结束后清理)
    if (WillChange) {
      WillChange.set(el, 'transform', 800);
    } else {
      el.style.willChange = 'transform';
    }

    // 初始进入视口
    LAYER_IN_VIEW.set(el, true);
  }

  /**
   * IntersectionObserver — 跟踪每个 layer 在视口内
   * 不在视口的 layer 跳过 spring step (省 GPU)
   */
  var OBSERVER = null;
  function setupIntersectionObserver() {
    if (OBSERVER) return;
    if (typeof IntersectionObserver === 'undefined') return;
    OBSERVER = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        LAYER_IN_VIEW.set(entry.target, entry.isIntersecting);
      });
    }, { threshold: 0.01 });
    // observe 所有现有 layer
    var layers = document.querySelectorAll('.parallax-layer, [data-parallax]');
    layers.forEach(function (el) {
      if (PARALLAX_LAYERS.has(el)) OBSERVER.observe(el);
    });
  }

  /**
   * 启动全局 listener (1 mousemove + 1 scroll)
   */
  function startGlobalListeners() {
    if (window._webpptParallaxGlobalBound) return;
    window._webpptParallaxGlobalBound = true;
    window.addEventListener('mousemove', onMouseMove, { passive: true });
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  function setupAll() {
    if (REDUCED_MOTION) {
      console.info('[parallax-3d] prefers-reduced-motion: skip');
      return;
    }
    ensureCSS();
    var layers = document.querySelectorAll('.parallax-layer, [data-parallax]');
    layers.forEach(attachParallax);
    setupIntersectionObserver();
    startGlobalListeners();
    if (RAF_ID === null && typeof requestAnimationFrame === 'function') {
      RAF_ID = requestAnimationFrame(tick);
    }
  }

  // 暴露 API
  window.WebPPT_Parallax3D = {
    setup: setupAll,
    attach: attachParallax,
    prefersReducedMotion: REDUCED_MOTION,
  };

  // 启动
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupAll);
  } else {
    setupAll();
  }

  // v3.11: 单一 Reveal 注册中心
  if (RevealHook) {
    RevealHook.onSlideChanged(setupAll);
    RevealHook.onReady(setupAll);
  } else if (typeof window.Reveal !== 'undefined') {
    window.Reveal.on('slidechanged', function () { setTimeout(setupAll, 600); });
    window.Reveal.on('ready', function () { setTimeout(setupAll, 100); });
  }

  // v3.11: visibilitychange 暂停 (GSAP 风格)
  if (Visibility) {
    Visibility.subscribe(function (hidden) {
      VISIBILITY_HIDDEN = hidden;
      if (!hidden && RAF_ID === null && typeof requestAnimationFrame === 'function') {
        RAF_ID = requestAnimationFrame(tick);
      }
    });
  }
})();

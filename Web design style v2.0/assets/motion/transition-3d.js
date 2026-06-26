/**
 * WebPPT Maker v3.9 · 3D slide transition 引擎
 *
 * Reveal.js 默认 transition 是 slide/convex/concave (2D)
 * v3.9 加入 3D 立方体翻转 transition (cube-flip)
 *
 * 3 种 transition:
 *   - cube-flip-left  : 当前 slide 沿 Y 轴 -90° 旋出, 下一 slide 从 +90° 旋入
 *   - cube-flip-right : 反向
 *   - cube-flip-up    : 沿 X 轴翻转 (从天而降)
 *
 * 用法:
 *   模板自动加载. 在 Reveal.initialize({ transition: 'cube-flip-left' }) 设置
 *   或运行时调用 WebPPT_Transition3D.set('cube-flip-left')
 *
 * 物理:
 *   - transform-style: preserve-3d + perspective: 2000px on .slides
 *   - 当前 section rotateY(-90deg) translateZ(50%)
 *   - 下一 section rotateY(90deg) translateZ(50%) → rotateY(0)
 */
(function () {
  'use strict';

  var REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // v3.9 bugfix: 防止重复绑 slidechanged listener
  var BOUND = false;
  var CURRENT_TRANSITION = 'cube-flip-left';
  var DURATION_MS = 700;

  /**
   * 注入 3D transition CSS 到 document
   * (只在第一次 set 时注入, 幂等)
   */
  function ensureCSS() {
    if (document.getElementById('webppt-3d-transition-style')) return;

    var style = document.createElement('style');
    style.id = 'webppt-3d-transition-style';
    style.textContent = [
      // 通用: .slides 容器启用 preserve-3d
      '.reveal .slides { transform-style: preserve-3d; perspective: 2000px; }',
      '.reveal .slides > section { transform-style: preserve-3d; backface-visibility: hidden; }',

      // === cube-flip-left: 当前向左翻出, 下一从右旋入 ===
      '@keyframes webppt-cube-left-out {',
      '  from { transform: rotateY(0deg) translateZ(0); opacity: 1; }',
      '  to   { transform: rotateY(-90deg) translateZ(-300px); opacity: 0.3; }',
      '}',
      '@keyframes webppt-cube-left-in {',
      '  from { transform: rotateY(90deg) translateZ(0); opacity: 0.3; }',
      '  to   { transform: rotateY(0deg) translateZ(0); opacity: 1; }',
      '}',
      '.reveal.transition-cube-flip-left section.past {',
      '  animation: webppt-cube-left-out ' + DURATION_MS + 'ms cubic-bezier(0.4, 0, 0.2, 1) forwards;',
      '}',
      // v3.10 bugfix: 只 target .present, 不再 .future
      // 旧代码 .future + .present 导致所有未来 slide 都被强制"旋入"到 0deg → 全部可见
      '.reveal.transition-cube-flip-left section.present {',
      '  animation: webppt-cube-left-in ' + DURATION_MS + 'ms cubic-bezier(0.4, 0, 0.2, 1) forwards;',
      '}',
      // 未来 slide 保持 90deg 边缘位置 (不可见)
      '.reveal.transition-cube-flip-left section.future {',
      '  transform: rotateY(90deg) translateZ(0); opacity: 0.3;',
      '}',

      // === cube-flip-right: 反向 ===
      '@keyframes webppt-cube-right-out {',
      '  from { transform: rotateY(0deg) translateZ(0); opacity: 1; }',
      '  to   { transform: rotateY(90deg) translateZ(-300px); opacity: 0.3; }',
      '}',
      '@keyframes webppt-cube-right-in {',
      '  from { transform: rotateY(-90deg) translateZ(0); opacity: 0.3; }',
      '  to   { transform: rotateY(0deg) translateZ(0); opacity: 1; }',
      '}',
      '.reveal.transition-cube-flip-right section.past {',
      '  animation: webppt-cube-right-out ' + DURATION_MS + 'ms cubic-bezier(0.4, 0, 0.2, 1) forwards;',
      '}',
      // v3.10 bugfix: 只 target .present
      '.reveal.transition-cube-flip-right section.present {',
      '  animation: webppt-cube-right-in ' + DURATION_MS + 'ms cubic-bezier(0.4, 0, 0.2, 1) forwards;',
      '}',
      // 未来 slide 保持 -90deg 边缘位置
      '.reveal.transition-cube-flip-right section.future {',
      '  transform: rotateY(-90deg) translateZ(0); opacity: 0.3;',
      '}',

      // === cube-flip-up: 从天而降 (沿 X 轴) ===
      '@keyframes webppt-cube-up-out {',
      '  from { transform: rotateX(0deg) translateZ(0); opacity: 1; }',
      '  to   { transform: rotateX(90deg) translateZ(-300px); opacity: 0.3; }',
      '}',
      '@keyframes webppt-cube-up-in {',
      '  from { transform: rotateX(-90deg) translateZ(0); opacity: 0.3; }',
      '  to   { transform: rotateX(0deg) translateZ(0); opacity: 1; }',
      '}',
      '.reveal.transition-cube-flip-up section.past {',
      '  animation: webppt-cube-up-out ' + DURATION_MS + 'ms cubic-bezier(0.4, 0, 0.2, 1) forwards;',
      '}',
      // v3.10 bugfix: 只 target .present
      '.reveal.transition-cube-flip-up section.present {',
      '  animation: webppt-cube-up-in ' + DURATION_MS + 'ms cubic-bezier(0.4, 0, 0.2, 1) forwards;',
      '}',
      // 未来 slide 保持 -90deg (X 轴) 边缘位置
      '.reveal.transition-cube-flip-up section.future {',
      '  transform: rotateX(-90deg) translateZ(0); opacity: 0.3;',
      '}',

      // === Reduced-motion: 完全禁用 3D transition ===
      '@media (prefers-reduced-motion: reduce) {',
      '  .reveal.transition-cube-flip-left section,',
      '  .reveal.transition-cube-flip-right section,',
      '  .reveal.transition-cube-flip-up section {',
      '    animation: none !important;',
      '    transform: none !important;',
      '    opacity: 1 !important;',
      '  }',
      '}',
    ].join('\n');
    document.head.appendChild(style);
  }

  /**
   * 设置当前 3D transition
   * v3.10 bugfix: 即使 reduced-motion, 也要更新 CURRENT_TRANSITION 状态
   * 旧实现 early-return 导致 current() 返回旧值 → slidechanged 触发时操作旧 class
   */
  function set(name) {
    // v3.10 bugfix: 总是先更新状态, 再根据 reduced-motion 决定是否操作 DOM
    if (name && name.indexOf('cube-flip') === 0) {
      CURRENT_TRANSITION = name;
    }
    if (REDUCED_MOTION) {
      console.info('[transition-3d] prefers-reduced-motion: skip');
      return;
    }
    ensureCSS();
    var reveal = document.querySelector('.reveal');
    if (!reveal) return;
    // 移除旧 class
    reveal.classList.remove(
      'transition-cube-flip-left',
      'transition-cube-flip-right',
      'transition-cube-flip-up'
    );
    if (name && name.indexOf('cube-flip') === 0) {
      reveal.classList.add('transition-' + name);
    }
  }

  /**
   * 初始化: 自动 bind Reveal.slidechanged (清理 future/past 后重新强制 reflow)
   */
  function setupAll() {
    if (REDUCED_MOTION) return;
    if (BOUND) return;
    BOUND = true;
    ensureCSS();
    if (typeof window.Reveal !== 'undefined') {
      window.Reveal.on('slidechanged', function () {
        // 不切换 transition, 只确保 future/past 重新触发 animation
        // 通过先 remove + reflow + add 强制 restart
        var reveal = document.querySelector('.reveal');
        if (!reveal) return;
        var activeClass = 'transition-' + CURRENT_TRANSITION;
        if (!reveal.classList.contains(activeClass)) return;
        // 强制 reflow 让 animation 重新触发 (取消再添加 class)
        reveal.classList.remove(activeClass);
        // 触发 reflow
        void reveal.offsetWidth;
        reveal.classList.add(activeClass);
      });
    }
  }

  // API
  window.WebPPT_Transition3D = {
    set: set,
    setup: setupAll,
    current: function () { return CURRENT_TRANSITION; },
    prefersReducedMotion: REDUCED_MOTION,
    DURATION_MS: DURATION_MS,
  };

  // 启动
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupAll);
  } else {
    setupAll();
  }

  // v3.11: 单一 Reveal 注册中心 (替代直接 Reveal.on)
  if (window.WebPPT_Utils && window.WebPPT_Utils.RevealHook) {
    window.WebPPT_Utils.RevealHook.onReady(setupAll);
  } else if (typeof window.Reveal !== 'undefined') {
    window.Reveal.on('ready', function () { setTimeout(setupAll, 100); });
  }
})();
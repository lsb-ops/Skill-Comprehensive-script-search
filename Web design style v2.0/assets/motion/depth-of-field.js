/**
 * WebPPT Maker v3.9 · Depth-of-Field 引擎 (真 3D 场景景深)
 *
 * 计算每个 .dof-element 的 z 深度 (基于 translateZ 或 data-z-depth),
 * 用 CSS filter: blur() 模拟景深效果 (远的模糊, 近的清晰)。
 * 配合 .tilt-3d 形成真 3D 场景错觉。
 *
 * 用法:
 *   <div class="dof-element" data-z-depth="0">焦点元素</div>
 *   <div class="dof-element" data-z-depth="-200">背景元素</div>
 *   <div class="dof-element" data-z-depth="+200">前景元素</div>
 *
 * CSS 效果 (auto-generated):
 *   --z-depth: 用户设定值 (px)
 *   filter: blur(calc(abs(var(--z-depth)) * 0.005px))
 *
 * 触发更新:
 *   - 鼠标移动 → 重新计算最近聚焦元素 (近 z=0 的元素 blur=0)
 *   - 滚动 → 重新计算元素到视口中心的距离 (越远 blur 越大)
 *   - Reveal slidechanged → 重算
 */
(function () {
  'use strict';

  var REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // v3.9 bugfix: 全局 listener 幂等
  var MOUSE_BOUND = false;
  var SCROLL_BOUND = false;
  var DOF_ELEMENTS = new WeakSet();

  function ensureCSS() {
    if (document.getElementById('webppt-dof-style')) return;
    var style = document.createElement('style');
    style.id = 'webppt-dof-style';
    style.textContent = [
      // 基础: --z-depth 默认 0 (在焦点平面)
      // v3.10 bugfix: 拆分为 3 个独立变量, 避免 scroll/mouse race
      //   --z-depth: 用户设定的 base depth
      //   --dof-scroll-offset: 滚动导致的 blur 增量
      //   --dof-mouse-offset: 鼠标对焦导致的 blur 减量
      '.dof-element {',
      '  --z-depth: 0px;',
      '  --dof-scroll-offset: 0px;',
      '  --dof-mouse-offset: 0px;',
      // 总 z = base + scroll - mouse, max(0, ...) 防止 blur 接受负值
      // v3.10 bugfix: 移除 abs() (浏览器支持差), 改用 max()
      '  filter: blur(calc(max(0, var(--z-depth, 0px) + var(--dof-scroll-offset, 0px) - var(--dof-mouse-offset, 0px)) * 0.004));',
      '  transition: filter 0.4s cubic-bezier(0.16, 1, 0.3, 1);',
      '  will-change: filter;',
      '}',
      // Reduced-motion
      '@media (prefers-reduced-motion: reduce) {',
      '  .dof-element {',
      '    filter: none !important;',
      '    transition: none !important;',
      '  }',
      '}',
    ].join('\n');
    document.head.appendChild(style);
  }

  function attachDOF(el) {
    if (REDUCED_MOTION) return;
    if (DOF_ELEMENTS.has(el)) return;
    DOF_ELEMENTS.add(el);
    var z = parseFloat(el.dataset.zDepth) || 0;
    el.style.setProperty('--z-depth', z + 'px');
  }

  function setupAll() {
    if (REDUCED_MOTION) {
      console.info('[depth-of-field] prefers-reduced-motion: skip');
      return;
    }
    ensureCSS();
    var els = document.querySelectorAll('.dof-element, [data-z-depth]');
    els.forEach(attachDOF);

    // 监听滚动 → 根据距离视口中心远近微调模糊
    if (!SCROLL_BOUND) {
      SCROLL_BOUND = true;
      window.addEventListener('scroll', scheduleScrollUpdate, { passive: true });
    }
    if (!MOUSE_BOUND) {
      MOUSE_BOUND = true;
      window.addEventListener('mousemove', scheduleMouseUpdate, { passive: true });
    }
    scheduleScrollUpdate();
  }

  // v3.10 bugfix: rAF 节流, 避免每事件触发 N 元素 layout thrash
  var SCROLL_RAF = null;
  var MOUSE_RAF = null;
  var LAST_MOUSE_EVENT = null;

  // v3.11: 页面不可见时暂停 rAF
  var DOF_PAUSED = false;

  function scheduleScrollUpdate() {
    if (SCROLL_RAF) return;
    SCROLL_RAF = requestAnimationFrame(function () {
      SCROLL_RAF = null;
      updateByScroll();
    });
  }

  function scheduleMouseUpdate(e) {
    LAST_MOUSE_EVENT = e; // 保存最新事件, rAF 中读取 (避免 stale closure)
    if (MOUSE_RAF) return;
    MOUSE_RAF = requestAnimationFrame(function () {
      MOUSE_RAF = null;
      if (LAST_MOUSE_EVENT) updateByMouse(LAST_MOUSE_EVENT);
    });
  }

  /**
   * 滚动: 元素距视口中心 > 30% 视口高度时, blur 加倍
   * (模拟对焦平面外的元素被虚化)
   * v3.10 bugfix: 写入 --dof-scroll-offset 而不是 --z-depth (避免与 mouse race)
   */
  function updateByScroll() {
    if (REDUCED_MOTION) return;
    // v3.11: tab 隐藏时跳过 (background 不更新)
    if (DOF_PAUSED) return;
    var vh = window.innerHeight || document.documentElement.clientHeight;
    if (vh <= 0) return; // BUG #5 fix: 防止 0 除
    var center = window.scrollY + vh / 2;
    var elements = document.querySelectorAll('.dof-element, [data-z-depth]');
    elements.forEach(function (el) {
      var rect = el.getBoundingClientRect();
      if (rect.height <= 0) return; // BUG #6 fix: 隐藏元素跳过
      var elCenter = window.scrollY + rect.top + rect.height / 2;
      var dist = Math.abs(elCenter - center) / vh;
      // 越远, 越模糊 (offset 加在 base 之上)
      var scrollOffset = dist * 60; // px (CSS 0.004 倍率, 即 60px → 0.24 模糊)
      el.style.setProperty('--dof-scroll-offset', scrollOffset.toFixed(2) + 'px');
    });
  }

  /**
   * 鼠标: 鼠标所在区域的元素 blur 减弱 (对焦)
   * v3.10 bugfix: 写入 --dof-mouse-offset, 累加而非覆盖 --z-depth
   */
  function updateByMouse(e) {
    if (REDUCED_MOTION) return;
    // v3.11: tab 隐藏时跳过
    if (DOF_PAUSED) return;
    var vw = window.innerWidth;
    var vh = window.innerHeight;
    if (vw <= 0 || vh <= 0) return; // BUG #5 fix
    var elements = document.querySelectorAll('.dof-element, [data-z-depth]');
    elements.forEach(function (el) {
      var rect = el.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0) return; // BUG #6 fix
      var cx = rect.left + rect.width / 2;
      var cy = rect.top + rect.height / 2;
      var dx = (e.clientX - cx) / (vw / 2);
      var dy = (e.clientY - cy) / (vh / 2);
      var dist = Math.sqrt(dx * dx + dy * dy);
      // 鼠标越近, 越清晰 (增大 mouse offset = 减量 = 更清晰)
      var focus = Math.max(0, 1 - dist);
      var mouseOffset = focus * 80; // px
      el.style.setProperty('--dof-mouse-offset', mouseOffset.toFixed(2) + 'px');
    });
  }

  // API
  window.WebPPT_DOF = {
    setup: setupAll,
    attach: attachDOF,
    updateByScroll: updateByScroll,
    updateByMouse: updateByMouse,
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
  } else if (typeof window.Reveal !== 'undefined') {
    window.Reveal.on('slidechanged', function () { setTimeout(setupAll, 600); });
  }

  // v3.11: visibilitychange 暂停 DOF 更新
  if (window.WebPPT_Utils && window.WebPPT_Utils.Visibility) {
    window.WebPPT_Utils.Visibility.subscribe(function (hidden) {
      DOF_PAUSED = hidden;
    });
  }
})();
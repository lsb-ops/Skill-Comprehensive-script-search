/**
 * WebPPT Maker v3.8 · 动态阴影追踪引擎
 *
 * 监听全局 mousemove,计算 cursor 位置 → 在 :root 上设置 --light-x / --light-y
 * CSS 可用此值让 box-shadow 跟随 cursor 方向变化
 *
 * 用法:
 *   <div class="dynamic-shadow">...</div>
 *
 * CSS 配合:
 *   .dynamic-shadow {
 *     box-shadow:
 *       calc(var(--light-x, 0) * 1px) calc(var(--light-y, 0) * 1px) 30px
 *       rgba(0, 0, 0, 0.15);
 *   }
 *
 * 物理模型:
 *   - 光源在 cursor 位置 (简化)
 *   - 元素阴影方向 = 远离光 = -(cursor.x - center.x), -(cursor.y - center.y)
 *   - 阴影强度 = 距离 (越远越淡)
 */
(function () {
  'use strict';

  var REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var MAX_OFFSET = 30;   // 阴影最大偏移 (px)
  // v3.10 bugfix: 移除 dead code MAX_BLUR (从未被使用)

  // v3.9 bugfix: 防止重复 attach 同一元素
  var SHADOW_ELEMENTS = new WeakSet();

  // v3.10 bugfix: 默认 CSS 模板, 让 .dynamic-shadow 元素默认有阴影 (且能组合用户自定义 box-shadow)
  // 不再用 JS 强写 el.style.boxShadow (会覆盖用户已有的 box-shadow)
  function ensureCSS() {
    if (document.getElementById('webppt-shadow-style')) return;
    var style = document.createElement('style');
    style.id = 'webppt-shadow-style';
    style.textContent = [
      '.dynamic-shadow {',
      '  --shadow-tx: 0px;',
      '  --shadow-ty: 0px;',
      '  --shadow-blur: 30px;',
      '  --shadow-opacity: 0.18;',
      // 用户的 box-shadow 会自动 cascade 到此元素上, 不会被 JS 覆盖
      // 通过 var(--shadow-tx) 等微调, 通过 filter: drop-shadow 添加动态偏移
      '  filter: drop-shadow(',
      '    calc(var(--shadow-tx, 0px))',
      '    calc(var(--shadow-ty, 0px))',
      '    var(--shadow-blur, 30px)',
      '    rgba(0, 0, 0, var(--shadow-opacity, 0.18))',
      '  );',
      '  transition: filter 0.3s cubic-bezier(0.16, 1, 0.3, 1);',
      '}',
      '@media (prefers-reduced-motion: reduce) {',
      '  .dynamic-shadow { filter: none !important; transition: none !important; }',
      '}',
    ].join('\n');
    document.head.appendChild(style);
  }

  function attachShadow(el) {
    if (REDUCED_MOTION) return;
    if (SHADOW_ELEMENTS.has(el)) return; // v3.9 bugfix: 幂等
    SHADOW_ELEMENTS.add(el);

    var baseOpacity = parseFloat(el.dataset.shadowOpacity) || 0.18;
    var baseBlur = parseFloat(el.dataset.shadowBlur) || 30;

    // 缓存 baseBlur/baseOpacity 到 CSS var (CSS 模板中默认 30/0.18)
    el.style.setProperty('--shadow-blur', baseBlur + 'px');
    el.style.setProperty('--shadow-opacity', String(baseOpacity));

    function onMove(e) {
      var rect = el.getBoundingClientRect();
      var cx = rect.left + rect.width / 2;
      var cy = rect.top + rect.height / 2;
      // 元素中心到 cursor 的方向 (1 → -1 归一化)
      var dx = (e.clientX - cx) / (Math.max(rect.width, rect.height) / 2);
      var dy = (e.clientY - cy) / (Math.max(rect.width, rect.height) / 2);
      dx = Math.max(-1, Math.min(1, dx));
      dy = Math.max(-1, Math.min(1, dy));
      // 阴影方向 = 远离 cursor (取负)
      var offsetX = -dx * MAX_OFFSET;
      var offsetY = -dy * MAX_OFFSET;
      // v3.10 bugfix: 只 set CSS vars, 不再覆盖 el.style.boxShadow
      // 用户的 box-shadow 现在可与 .dynamic-shadow filter: drop-shadow 共存
      el.style.setProperty('--shadow-tx', offsetX.toFixed(2) + 'px');
      el.style.setProperty('--shadow-ty', offsetY.toFixed(2) + 'px');
    }

    function onLeave() {
      el.style.setProperty('--shadow-tx', '0px');
      el.style.setProperty('--shadow-ty', '0px');
    }

    el.addEventListener('mousemove', onMove);
    el.addEventListener('mouseleave', onLeave);
  }

  function setupAll() {
    if (REDUCED_MOTION) {
      console.info('[shadow-tracker] prefers-reduced-motion: skip');
      return;
    }
    ensureCSS();
    var els = document.querySelectorAll('.dynamic-shadow, [data-dynamic-shadow]');
    els.forEach(attachShadow);
  }

  // API
  window.WebPPT_Shadow = {
    setup: setupAll,
    attach: attachShadow,
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
})();
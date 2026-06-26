/**
 * WebPPT Maker v3.20 · Spring Preset Helper (CSS linear() 重写版)
 *
 * === v3.20 重大变更 (per docs/RESEARCH_2026_OPEN_SOURCE.md §v3.20) ===
 *
 * v3.20 弃用 JS spring 物理求解, 改用浏览器原生 CSS linear() 函数:
 *   - 5 个 spring 级别来自 open-props@1.7.23 真实值 (curl 验证)
 *   - 浏览器在主线程外插值 (compositor), 性能优于 RAF JS
 *   - 自动 respect prefers-reduced-motion (CSS @media query)
 *   - 见 assets/motion/easing-spring.css
 *
 * === 历史 (v3.13-v3.18.1) ===
 *
 * v3.13-v3.18.1: 自研 JS spring 物理求解器 (k/c 双参数)
 * v3.18.1: 诚实承认 NOT Apple HIG / NOT Open Props / NOT Framer Motion
 *
 * === v3.20 新行为 ===
 *
 * - JS animate() 仍保留 (兼容旧代码), 但内部改为: 设置 CSS animation-timing-function
 *   + CSS keyframes, 让浏览器做主线程外插值
 * - preset 名映射到 --ease-spring-1..5:
 *     snappy   → spring-4 (强调)
 *     balanced → spring-3 (中等)
 *     bouncy   → spring-5 (最强烈)
 *     heavy    → spring-2 (轻柔)
 *     wobbly   → spring-3 (中等, 别名)
 *
 * 用法 (HTML, 推荐):
 *   <div data-anim="spring-4">按钮</div>     <!-- 用 CSS data-anim 属性 -->
 *   <div data-spring-preset="snappy">按钮</div> <!-- 兼容旧用法, 自动转换 -->
 *
 * 用法 (CSS, 推荐):
 *   .my-button { transition-timing-function: var(--ease-spring-4); }
 *   .my-modal  { animation-timing-function: var(--ease-spring-4); }
 *
 * 用法 (JS, 兼容旧 API):
 *   WebPPT_Spring.animate(el, { preset: 'snappy' });
 *   // 内部: el.style.animationTimingFunction = 'var(--ease-spring-4)'
 *   // + 触发 CSS @keyframes (data-spring-preset="snappy" 选择器)
 */

(function () {
  'use strict';

  // === v3.20 preset 映射 (snappy/balanced/bouncy/heavy → spring-1..5) ===
  // 真实值来自 open-props@1.7.23 (curl 验证)
  var PRESET_TO_SPRING = {
    snappy:   'spring-4',  // 强调 (Modal, Toast 弹出)
    balanced: 'spring-3',  // 中等 (按钮按下, 卡片浮起)
    bouncy:   'spring-5',  // 最强烈 (页面切换)
    heavy:    'spring-2',  // 轻柔 (hover)
    wobbly:   'spring-3'   // 中等 (别名, 兼容 v3.13)
  };

  // 元素选择 + 自动映射
  function pickPreset(el) {
    var explicit = el.getAttribute('data-spring-preset');
    if (explicit && PRESET_TO_SPRING[explicit]) {
      return PRESET_TO_SPRING[explicit];
    }
    // fallback: 根据 data-attn 自动选
    var attn = el.getAttribute('data-attn');
    if (attn === 'critical') return 'spring-5';   // 强调: 最强烈
    if (attn === 'high') return 'spring-4';       // 次强调: 强调
    if (attn === 'normal') return 'spring-3';     // 默认: 中等
    if (attn === 'low' || attn === 'deco') return 'spring-2';  // 弱: 轻柔
    return 'spring-3';                            // 默认
  }

  // 动画单元素 (v3.20 改为 CSS linear(), 浏览器主线程外插值)
  function animateEl(el, opts) {
    opts = opts || {};
    var presetName = opts.preset || pickPreset(el);
    var springLevel = PRESET_TO_SPRING[presetName] || 'spring-3';

    // v3.20: 设置 CSS animation-timing-function + 触发 CSS keyframes
    // 浏览器在 compositor 线程插值, 性能优于 RAF JS
    el.style.animationTimingFunction = 'var(--ease-' + springLevel + ')';

    // 兼容: 设置 data-anim 属性让 CSS 选择器生效
    el.setAttribute('data-anim', springLevel);

    // 兼容旧 API: opts.axis → CSS transform 起点
    // 注意: 实际 transform 由调用方的 CSS @keyframes 控制
    // 这里只是触发 transition (如果 CSS 有定义)
    if (opts.from !== undefined && opts.to !== undefined) {
      var dist = opts.distance || 16;
      var axis = opts.axis || 'x';
      var fromVal = opts.from;
      var toVal = opts.to;
      if (axis === 'y') {
        el.style.transform = 'translateY(' + (fromVal * dist) + 'px)';
      } else if (axis === 'scale') {
        el.style.transform = 'scale(' + (0.5 + 0.5 * fromVal) + ')';
      } else {
        el.style.transform = 'translateX(' + (fromVal * dist) + 'px)';
      }
      el.style.opacity = String(fromVal);
      // 强制 reflow
      void el.offsetWidth;
      // 触发 transition 到目标
      requestAnimationFrame(function () {
        if (axis === 'y') {
          el.style.transform = 'translateY(' + (toVal * dist) + 'px)';
        } else if (axis === 'scale') {
          el.style.transform = 'scale(' + (0.5 + 0.5 * toVal) + ')';
        } else {
          el.style.transform = 'translateX(' + (toVal * dist) + 'px)';
        }
        el.style.opacity = String(toVal);
        // transition 监听完成
        var done = function () {
          el.removeEventListener('transitionend', done);
          if (opts.onComplete) opts.onComplete(el);
        };
        el.addEventListener('transitionend', done);
      });
      el.style.transition = 'transform 400ms, opacity 400ms';
    } else if (opts.onComplete) {
      // 立即回调 (无 from/to 时)
      opts.onComplete(el);
    }

    // 返回控制对象 (v3.20 简化: stop 仅清除属性)
    return {
      stop: function () {
        el.style.transition = '';
        el.style.transform = '';
        el.style.opacity = '';
      }
    };
  }

  // 批量动画 (stagger 自动, 兼容旧 API)
  function animateMany(els, opts) {
    opts = opts || {};
    var stagger = opts.stagger || 80; // ms
    var controls = [];

    Array.prototype.forEach.call(els, function (el, i) {
      if (i > 0) {
        setTimeout(function () {
          var ctrl = animateEl(el, {
            preset: opts.preset || 'snappy',
            to: 1,
            from: 0,
            axis: opts.axis || 'y',
            distance: opts.distance || 16
          });
          if (ctrl) controls.push(ctrl);
        }, i * stagger);
      } else {
        var ctrl = animateEl(el, {
          preset: opts.preset || 'snappy',
          to: 1,
          from: 0,
          axis: opts.axis || 'y',
          distance: opts.distance || 16
        });
        if (ctrl) controls.push(ctrl);
      }
    });

    return controls;
  }

  // 暴露全局 API
  window.WebPPT_Spring = {
    animate: animateEl,
    animateMany: animateMany,
    pickPreset: pickPreset,
    presets: PRESET_TO_SPRING,  // v3.20: 暴露新映射
    // 兼容 v3.13-v3.18.1 旧 PRESETS (snappy/balanced/bouncy/heavy)
    legacyPresets: {
      snappy: { level: 'spring-4' },
      balanced: { level: 'spring-3' },
      bouncy: { level: 'spring-5' },
      heavy: { level: 'spring-2' },
      wobbly: { level: 'spring-3' }
    }
  };
})();
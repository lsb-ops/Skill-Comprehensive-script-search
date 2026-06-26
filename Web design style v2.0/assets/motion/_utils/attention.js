/**
 * WebPPT Maker v3.12 · 视线吸引动效 (Motion Attention)
 *
 * 基于 IntersectionObserver + attention level 的分级入场动效
 * 配合 attention-hierarchy.css 的 [data-attn="critical|high|normal|low|deco"]
 *
 * 核心规则:
 * 1. critical: 600ms + scale + 大位移 (强调, 先入场)
 * 2. high: 400ms + fade-up (支撑证据, 紧跟)
 * 3. normal: 250ms + fade (正文, 顺畅入场)
 * 4. low: 150ms + fade (辅助, 几乎无感)
 * 5. deco: 0ms (装饰无入场, 立即就位)
 *
 * + Eye stagger: 父子元素按 --enter-delay 顺序入场
 * + prefers-reduced-motion: 自动降级为 opacity-only
 *
 * 用法 (HTML 端):
 *   <div data-attn="critical">主标题</div>
 *   <ul data-eye-stagger="normal">
 *     <li>1</li><li>2</li><li>3</li>
 *   </ul>
 *
 * 用法 (JS 端):
 *   WebPPT_Attention.observe(rootEl);    // 观察某个容器
 *   WebPPT_Attention.refresh();           // 重新扫描
 */

(function () {
  'use strict';

  // Reduced motion 检测
  var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Attention 级别 → 入场配置
  var ENTER_PRESETS = {
    critical: {
      duration: 600,
      translateY: 24,
      scale: 0.92,
      opacity: 0,
      easing: 'cubic-bezier(0.2, 0, 0, 1)'    // MD3 emphasized decelerate
    },
    high: {
      duration: 400,
      translateY: 16,
      scale: 0.96,
      opacity: 0,
      easing: 'cubic-bezier(0.2, 0, 0, 1)'
    },
    normal: {
      duration: 250,
      translateY: 8,
      scale: 1,
      opacity: 0,
      easing: 'cubic-bezier(0, 0, 0.2, 1)'    // standard decelerate
    },
    low: {
      duration: 150,
      translateY: 4,
      scale: 1,
      opacity: 0,
      easing: 'linear'
    },
    deco: {
      duration: 0,
      translateY: 0,
      scale: 1,
      opacity: 1,
      easing: 'linear'
    }
  };

  // 应用单元素入场
  function animateEnter(el) {
    var level = el.getAttribute('data-attn') || 'normal';
    var preset = ENTER_PRESETS[level];
    if (!preset) preset = ENTER_PRESETS.normal;

    // Reduced motion: 只做 fade, 不做位移
    if (prefersReducedMotion) {
      preset = { duration: 100, translateY: 0, scale: 1, opacity: 0, easing: 'linear' };
    }

    // Stagger 延迟 (从 CSS var 读取, --enter-delay)
    // BUG-05 fix: 改进正则容忍空格 + 加 console.warn 提示静默失败
    var delayStr = getComputedStyle(el).getPropertyValue('--enter-delay').trim();
    var delay = 0;
    if (delayStr) {
      // 改进: 容忍 calc 内部空格, 支持 ms/s 单位
      var match = delayStr.match(/calc\(\s*([\d.]+)(ms|s)?\s*\*\s*(\d+)\s*\)/);
      if (match) {
        var base = parseFloat(match[1]);
        var unit = match[2] || 'ms';
        var mult = parseFloat(match[3]);
        delay = base * mult;
        if (unit === 's') delay = delay * 1000;
      } else {
        // fallback: 简单数字 + 单位
        var simpleMatch = delayStr.match(/^([\d.]+)(ms|s)?$/);
        if (simpleMatch) {
          delay = parseFloat(simpleMatch[1]);
          if (simpleMatch[2] === 's') delay = delay * 1000;
        } else {
          // BUG-05: 解析失败时 console.warn 提示
          if (typeof console !== 'undefined' && console.warn) {
            console.warn('[attention.js] 无法解析 --enter-delay:', delayStr, '(元素:', el.tagName + '.' + (el.className || ''), ')');
          }
        }
      }
    }

    // 起点: 设置初始 transform/opacity (不触发 layout)
    el.style.willChange = 'transform, opacity';
    el.style.transform = 'translateY(' + preset.translateY + 'px) scale(' + preset.scale + ')';
    el.style.opacity = preset.opacity;

    // 强制 reflow 让 transition 生效
    void el.offsetHeight;

    // RAF 后启动 transition (确保初始样式已应用)
    setTimeout(function () {
      el.style.transition =
        'transform ' + preset.duration + 'ms ' + preset.easing + ' ' + delay + 'ms, ' +
        'opacity ' + preset.duration + 'ms ' + preset.easing + ' ' + delay + 'ms';
      el.style.transform = 'translateY(0) scale(1)';
      el.style.opacity = '1';
    }, 10);

    // 动画完成后清理
    var totalMs = preset.duration + delay + 50;
    setTimeout(function () {
      el.style.transition = '';
      el.style.transform = '';
      el.style.opacity = '';
      el.style.willChange = '';
      el.classList.add('attn-entered');
    }, totalMs);
  }

  // 立即入场 (元素已在视口内, 无需观察)
  function enterImmediate(el) {
    animateEnter(el);
  }

  // IntersectionObserver 单例
  var observer = null;
  function ensureObserver() {
    if (observer) return observer;
    if (!('IntersectionObserver' in window)) {
      // Fallback: 立即全部入场
      return null;
    }
    observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          animateEnter(entry.target);
          observer.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.1,
      // BUG-02 fix: rootMargin 方向 -10% → +10% (提前 10% 触发, 不卡顿)
      rootMargin: '0px 0px 10% 0px'
    });
    return observer;
  }

  // 扫描整个文档, 找到所有 data-attn 元素
  function refresh(root) {
    var scope = root || document;
    var elements = scope.querySelectorAll('[data-attn]:not(.attn-entered)');

    var obs = ensureObserver();
    elements.forEach(function (el) {
      if (!obs) {
        // 无 observer: 直接入场
        enterImmediate(el);
        return;
      }
      // 检查是否已在视口
      var rect = el.getBoundingClientRect();
      var inView = rect.top < window.innerHeight && rect.bottom > 0;
      if (inView) {
        enterImmediate(el);
        obs.unobserve(el);
      } else {
        obs.observe(el);
      }
    });
  }

  // 暴露 API
  window.WebPPT_Attention = {
    refresh: refresh,
    enter: enterImmediate,
    observe: refresh,
    config: ENTER_PRESETS
  };

  // DOMContentLoaded 后自动 refresh
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { refresh(); });
  } else {
    // 已经在 DOMContentLoaded 之后
    refresh();
  }
})();
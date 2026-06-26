/**
 * WebPPT Maker v3.11 · will-change 自动管理
 *
 * setProperty('will-change', prop) → 动画结束后自动清除
 * 避免永久 compositor layer 浪费 GPU 内存
 *
 * 用法:
 *   WillChange.set(el, 'transform', 600); // 600ms 后自动清除
 *   WillChange.set(el, ['transform', 'opacity'], 400);
 */
(function () {
  'use strict';

  function set(el, prop, durationMs) {
    if (!el || !prop) return;
    var props = Array.isArray(prop) ? prop.join(', ') : prop;
    el.style.setProperty('will-change', props);
    if (durationMs && durationMs > 0) {
      setTimeout(function () {
        // 仅在仍是这个值时清除 (避免被新动画覆盖)
        var current = el.style.getPropertyValue('will-change');
        if (current === props || current === props.replace(/\s*,\s*/g, ', ')) {
          el.style.removeProperty('will-change');
        }
      }, durationMs);
    }
  }

  function clear(el) {
    if (!el) return;
    el.style.removeProperty('will-change');
  }

  window.WebPPT_Utils = window.WebPPT_Utils || {};
  window.WebPPT_Utils.WillChange = { set: set, clear: clear };
})();

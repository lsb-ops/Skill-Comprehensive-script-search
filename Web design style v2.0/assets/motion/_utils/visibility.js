/**
 * WebPPT Maker v3.11 · 页面可见性 API (visibilitychange)
 *
 * 监听 document.hidden, 触发回调 (true=隐藏, false=显示)
 * 用于 rAF 循环在 tab 切到后台时暂停, 省电
 *
 * 用法:
 *   var unsub = WebPPT_Utils.Visibility.subscribe(function (hidden) {
 *     if (hidden) cancelAnimationFrame(rafId);
 *     else rafId = requestAnimationFrame(animate);
 *   });
 *   // unsub() 取消订阅
 */
(function () {
  'use strict';

  var CALLBACKS = [];
  var BOUND = false;

  function fire(hidden) {
    for (var i = 0; i < CALLBACKS.length; i++) {
      try { CALLBACKS[i](hidden); } catch (e) { /* 静默 */ }
    }
  }

  function onVisibilityChange() {
    fire(document.hidden);
  }

  function bindOnce() {
    if (BOUND) return;
    if (typeof document === 'undefined') return;
    if (typeof document.addEventListener !== 'function') return;
    BOUND = true;
    document.addEventListener('visibilitychange', onVisibilityChange);
  }

  window.WebPPT_Utils = window.WebPPT_Utils || {};
  window.WebPPT_Utils.Visibility = {
    subscribe: function (cb) {
      if (typeof cb !== 'function') return function () {};
      bindOnce();
      CALLBACKS.push(cb);
      return function () {
        var i = CALLBACKS.indexOf(cb);
        if (i >= 0) CALLBACKS.splice(i, 1);
      };
    },
    isHidden: function () {
      return typeof document !== 'undefined' && document.hidden;
    },
  };
})();

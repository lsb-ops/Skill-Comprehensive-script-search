/**
 * WebPPT Maker v3.11 · Reveal.js 单一注册中心
 *
 * 替代 8 个 motion 引擎各自 Reveal.on('slidechanged', setupAll) (7+ listener 重复)
 * 单一全局 listener + 订阅模式
 *
 * 用法:
 *   WebPPT_Utils.RevealHook.onSlideChanged(function () {
 *     // mySetup(); — 会在每次 slide 切换后 ~600ms 调用
 *   });
 */
(function () {
  'use strict';

  var SLIDE_CBS = [];
  var READY_CBS = [];
  var SLIDE_BOUND = false;
  var READY_BOUND = false;
  var SLIDE_DELAY = 600; // ms, 等 reveal transition 完成

  function bindSlideOnce() {
    if (SLIDE_BOUND) return;
    if (typeof window.Reveal === 'undefined') return;
    SLIDE_BOUND = true;
    window.Reveal.on('slidechanged', function () {
      for (var i = 0; i < SLIDE_CBS.length; i++) {
        try { setTimeout(SLIDE_CBS[i], SLIDE_DELAY); } catch (e) {}
      }
    });
  }

  function bindReadyOnce() {
    if (READY_BOUND) return;
    if (typeof window.Reveal === 'undefined') return;
    READY_BOUND = true;
    window.Reveal.on('ready', function () {
      for (var i = 0; i < READY_CBS.length; i++) {
        try { setTimeout(READY_CBS[i], 100); } catch (e) {}
      }
    });
  }

  // 监听 Reveal 是否在之后才出现 (defer)
  var POLL_COUNT = 0;
  function pollReveal() {
    if (typeof window.Reveal !== 'undefined') {
      bindSlideOnce();
      bindReadyOnce();
      return;
    }
    if (++POLL_COUNT > 100) return; // 10s 上限
    setTimeout(pollReveal, 100);
  }
  if (typeof window !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', pollReveal);
    } else {
      pollReveal();
    }
  }

  window.WebPPT_Utils = window.WebPPT_Utils || {};
  window.WebPPT_Utils.RevealHook = {
    onSlideChanged: function (cb) {
      if (typeof cb !== 'function') return;
      SLIDE_CBS.push(cb);
      bindSlideOnce();
    },
    onReady: function (cb) {
      if (typeof cb !== 'function') return;
      READY_CBS.push(cb);
      bindReadyOnce();
    },
    _internal: {
      slideCount: function () { return SLIDE_CBS.length; },
      readyCount: function () { return READY_CBS.length; },
    },
  };
})();

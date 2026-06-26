/**
 * WebPPT Maker v3.11 · 共享 utils 加载器
 *
 * 4 个共享模块按依赖顺序加载:
 *   spring.js (无依赖)
 *   will-change.js (无依赖)
 *   visibility.js (无依赖)
 *   reveal-hook.js (无依赖, 但需要 Reveal.js 存在, 自己 poll)
 *
 * 加载方式: 在 HTML 模板中 <script src="./assets/motion/_utils/loader.js"></script>
 * loader.js 动态注入 4 个 <script> 标签 (同步)
 *
 * 也可以直接在模板中按顺序写 4 个 <script> — loader.js 只是简化模板维护
 */
(function () {
  'use strict';

  if (typeof window === 'undefined') return;

  var base = './assets/motion/_utils/';
  var scripts = ['spring.js', 'will-change.js', 'visibility.js', 'reveal-hook.js'];

  // 找到当前 script 自己的目录 (loader.js 的位置)
  var currentScript = document.currentScript;
  var basePath = base;
  if (currentScript && currentScript.src) {
    // 当前 script 的 src → 取 dirname
    var src = currentScript.src;
    var lastSlash = src.lastIndexOf('/');
    if (lastSlash >= 0) {
      basePath = src.substring(0, lastSlash + 1);
    }
  }

  // 同步顺序加载 4 个 utils
  scripts.forEach(function (name) {
    var s = document.createElement('script');
    s.src = basePath + name;
    // 不 defer/async, 确保按顺序
    document.head.appendChild(s);
  });
})();

/**
 * ⚠️  DEPRECATED in v3.15 · 已被 archetype-applier.js 取代
 * ⚠️  替代: assets/composition/archetype-applier.js
 * ⚠️  原因: data-theme 切换只是换颜色, v3.15 切换整个 archetype 视觉语言
 * ⚠️  保留此文件仅为 v3.14 回归测试, 不再用于生产
 *
 * WebPPT Maker v3.14 · Theme Applier (主题应用器)
 *
 * 根据 WebPPT_ThemeDetect 判定结果, 自动套用:
 * 1. data-theme 属性 (CSS 端切换)
 * 2. data-pairing 属性 (type pairing)
 * 3. <body> / <html> 标签
 * 4. 重新触发入场动画 (如果需要)
 *
 * 用法:
 *   WebPPT_ThemeApplier.apply('business');           // 应用商务主题
 *   WebPPT_ThemeApplier.applyFromContent(content);   // 检测+应用
 *   WebPPT_ThemeApplier.applyPairing('editorial');   // 应用 type pairing
 */

(function () {
  'use strict';

  // === 主题 → pairing 映射 ===
  var THEME_PAIRING = {
    business:   'editorial',    /* Serif heading + Sans body */
    tech:       'tech',         /* Sans heading + Mono accent */
    education:  'editorial',    /* Serif heading + Sans body (温暖) */
    fashion:    'fashion'       /* Display heading + Sans body */
  };

  // === 应用主题到 DOM ===
  function apply(themeName) {
    if (!themeName) themeName = 'business';

    // 设置 data-theme
    document.documentElement.setAttribute('data-theme', themeName);
    document.body.setAttribute('data-theme', themeName);

    // 设置 data-pairing
    var pairing = THEME_PAIRING[themeName] || 'editorial';
    document.documentElement.setAttribute('data-pairing', pairing);
    document.body.setAttribute('data-pairing', pairing);

    // 触发自定义事件 (其他组件可监听)
    var event = new CustomEvent('webppt:theme-applied', {
      detail: { theme: themeName, pairing: pairing }
    });
    document.dispatchEvent(event);

    return { theme: themeName, pairing: pairing };
  }

  // === 应用 pairing (不切换主题) ===
  function applyPairing(pairingName) {
    document.documentElement.setAttribute('data-pairing', pairingName);
    document.body.setAttribute('data-pairing', pairingName);
  }

  // === 从内容自动检测并应用 ===
  function applyFromContent(content) {
    if (!window.WebPPT_ThemeDetect) {
      console.warn('[theme-applier] WebPPT_ThemeDetect 未加载');
      return null;
    }
    var theme = window.WebPPT_ThemeDetect.detect(content);
    return apply(theme);
  }

  // === 从多个内容智能分析 + 应用 ===
  function applyFromContents(contentList) {
    if (!window.WebPPT_ThemeDetect) {
      console.warn('[theme-applier] WebPPT_ThemeDetect 未加载');
      return null;
    }
    var analysis = window.WebPPT_ThemeDetect.analyze(contentList);
    var result = apply(analysis.dominant);
    result.analysis = analysis;
    return result;
  }

  // === 获取当前主题 ===
  function getCurrent() {
    return {
      theme: document.body.getAttribute('data-theme'),
      pairing: document.body.getAttribute('data-pairing')
    };
  }

  // === 暴露 API ===
  window.WebPPT_ThemeApplier = {
    apply: apply,
    applyPairing: applyPairing,
    applyFromContent: applyFromContent,
    applyFromContents: applyFromContents,
    getCurrent: getCurrent,
    THEME_PAIRING: THEME_PAIRING
  };

  // === 自动初始化 (DOMContentLoaded 后) ===
  function autoInit() {
    // 检查是否已有显式 data-theme (用户手动设置)
    var existingTheme = document.body.getAttribute('data-theme') ||
                        document.documentElement.getAttribute('data-theme');
    if (existingTheme) return;

    // 检查 meta 配置
    var meta = document.querySelector('meta[name="webppt-theme"]');
    if (meta && meta.content) {
      apply(meta.content);
      return;
    }

    // 检查页面的 <h1> 或 .title 文本 (作为内容提示)
    var titleEl = document.querySelector('h1, .title');
    if (titleEl) {
      var titleText = titleEl.textContent || '';
      applyFromContent(titleText);
      return;
    }

    // 默认商务主题
    apply('business');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoInit);
  } else {
    autoInit();
  }
})();
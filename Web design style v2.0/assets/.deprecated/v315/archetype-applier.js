/**
 * WebPPT Maker v3.15 · Archetype Applier (原型应用器)
 *
 * 与 theme-applier 的本质区别:
 * - theme-applier: 切换 data-theme (改颜色)
 * - archetype-applier: 应用 data-archetype (改**整个视觉语言**)
 *
 * 应用内容:
 * 1. data-archetype 属性 (CSS 端切换完整原型)
 * 2. data-role 属性 (叙事角色, 用于 narrative.css)
 * 3. data-tone 属性 (色调: light/dark)
 * 4. 触发自定义事件 (其他组件可监听)
 *
 * 用法:
 *   WebPPT_ArchetypeApplier.apply('hero', { role: 'hook', tone: 'light' });
 *   WebPPT_ArchetypeApplier.applyFromContent({ title: 'Q3 营收 1.2 亿', body: '' }, 1, 5);
 *   WebPPT_ArchetypeApplier.applySequence([{title:'...'}, {title:'...'}]);
 */

(function () {
  'use strict';

  // === 验证 archetype 是否合法 ===
  var VALID_ARCHETYPES = ['hero', 'action-title', 'big-number', 'comparison', 'quote', 'flow', 'cta'];

  function isValid(name) {
    return VALID_ARCHETYPES.indexOf(name) !== -1;
  }

  // === 应用单个原型到元素 ===
  function apply(archetypeName, options) {
    options = options || {};
    if (!isValid(archetypeName)) archetypeName = 'hero';

    var root = options.root || document.body;

    // 清除旧 archetype 属性
    root.removeAttribute('data-archetype');

    // 设置新 archetype
    root.setAttribute('data-archetype', archetypeName);

    // 设置 role (叙事角色)
    if (options.role) {
      root.setAttribute('data-role', options.role);
    }

    // 设置 tone (色调)
    if (options.tone) {
      root.setAttribute('data-tone', options.tone);
    } else {
      root.removeAttribute('data-tone');
    }

    // 触发自定义事件
    var event = new CustomEvent('webppt:archetype-applied', {
      detail: {
        archetype: archetypeName,
        role: options.role,
        tone: options.tone
      }
    });
    root.dispatchEvent(event);

    return {
      archetype: archetypeName,
      role: options.role || null,
      tone: options.tone || null
    };
  }

  // === 从内容自动检测并应用 ===
  function applyFromContent(content, sequence, total) {
    if (!window.WebPPT_ArchetypeDetect) {
      console.warn('[archetype-applier] WebPPT_ArchetypeDetect 未加载, 默认使用 hero');
      return apply('hero');
    }

    var ctx = {
      title: content.title || '',
      body: content.body || '',
      type: content.type,
      sequence: sequence || 1,
      total: total || 1
    };

    var archetype = window.WebPPT_ArchetypeDetect.detect(ctx);
    var role = window.WebPPT_ArchetypeDetect.inferRole(ctx, archetype);

    // 根据 archetype 自动判断 tone
    var tone = autoTone(archetype);

    return apply(archetype, { role: role, tone: tone, root: content.root });
  }

  // === 批量应用整个序列 ===
  function applySequence(slides, options) {
    options = options || {};
    if (!Array.isArray(slides) || slides.length === 0) {
      console.warn('[archetype-applier] applySequence 需要幻灯片数组');
      return [];
    }

    if (!window.WebPPT_ArchetypeDetect) {
      console.warn('[archetype-applier] ArchetypeDetect 未加载');
      return [];
    }

    var analysis = window.WebPPT_ArchetypeDetect.analyzeSequence(slides);
    var results = [];

    analysis.forEach(function (item, idx) {
      var slideEl = options.slides && options.slides[idx]
        ? options.slides[idx]
        : (document.querySelectorAll('.slide, [data-slide-index]')[idx] || document.body);

      var tone = autoTone(item.archetype);
      var result = apply(item.archetype, {
        role: item.role,
        tone: tone,
        root: slideEl
      });
      results.push(result);
    });

    return results;
  }

  // === 自动判断 tone (深浅) ===
  function autoTone(archetype) {
    // CTA 默认深色 (沉浸), hero 可深可浅, 其余浅
    if (archetype === 'cta') return 'dark';
    if (archetype === 'hero') return null; // 默认浅
    return 'light';
  }

  // === 获取当前 archetype 信息 ===
  function getCurrent(root) {
    root = root || document.body;
    return {
      archetype: root.getAttribute('data-archetype'),
      role: root.getAttribute('data-role'),
      tone: root.getAttribute('data-tone')
    };
  }

  // === 清除所有 archetype 属性 ===
  function clear(root) {
    root = root || document.body;
    root.removeAttribute('data-archetype');
    root.removeAttribute('data-role');
    root.removeAttribute('data-tone');
  }

  // === 暴露 API ===
  window.WebPPT_ArchetypeApplier = {
    apply: apply,
    applyFromContent: applyFromContent,
    applySequence: applySequence,
    getCurrent: getCurrent,
    clear: clear,
    isValid: isValid,
    VALID_ARCHETYPES: VALID_ARCHETYPES
  };
})();
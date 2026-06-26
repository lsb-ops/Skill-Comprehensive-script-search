/**
 * WebPPT Maker v3.16 · Section Type Detector
 *
 * 与 v3.15 archetype-detect 的本质区别:
 * - archetype-detect: 检测"幻灯片原型" (slide thinking) → 已废弃
 * - section-detect: 检测"网页 section 类型" (web component)
 *
 * 检测维度:
 * 1. 显式 data-section 属性 (优先)
 * 2. class 命名约定 (.nav / .hero / .features 等)
 * 3. DOM 结构特征 (semantic analysis)
 * 4. 内容特征 (数字/价格/FAQ/比较)
 *
 * 用法:
 *   const section = SectionDetect.detect(element);
 *   // → "nav" | "hero" | "features" | "big-number" | "comparison"
 *   //   | "testimonial" | "faq" | "pricing" | "gallery" | "cta" | "footer"
 */

(function () {
  'use strict';

  var VALID_SECTIONS = ['nav', 'hero', 'features', 'big-number', 'comparison',
                        'testimonial', 'faq', 'pricing', 'gallery', 'cta', 'footer'];

  // === 显式检测 ===
  function detectExplicit(el) {
    var explicit = el.getAttribute('data-section');
    if (explicit && VALID_SECTIONS.indexOf(explicit) !== -1) {
      return explicit;
    }
    return null;
  }

  // === class 命名约定 ===
  function detectFromClass(el) {
    var classes = el.className || '';
    if (typeof classes !== 'string') return null;

    // 优先级: page-nav > nav, page-hero > hero
    if (/\bpage-nav\b|\bnav-section\b/.test(classes)) return 'nav';
    if (/\bpage-hero\b|\bhero-section\b/.test(classes)) return 'hero';
    if (/\bfeatures-grid\b|\bfeature-section\b/.test(classes)) return 'features';
    if (/\b(stats|big-number|numbers)-grid\b/.test(classes)) return 'big-number';
    if (/\bcomparison-table\b/.test(classes)) return 'comparison';
    if (/\btestimonial(-featured|-grid)?\b/.test(classes)) return 'testimonial';
    if (/\bfaq(-list|-section)?\b/.test(classes)) return 'faq';
    if (/\bpricing-(grid|section|card)\b/.test(classes)) return 'pricing';
    if (/\bportfolio-grid\b|\bgallery-grid\b/.test(classes)) return 'gallery';
    if (/\bcta-(featured|section)\b/.test(classes)) return 'cta';
    if (/\bpage-footer\b|\bfooter-section\b/.test(classes)) return 'footer';

    return null;
  }

  // === DOM 结构特征 ===
  function detectFromDOM(el) {
    // Nav: 有 nav links + brand
    if (el.querySelector('.nav-links, .nav-brand, .nav-cta')) return 'nav';

    // Hero: 有 hero-headline + hero-sub
    if (el.querySelector('.hero-headline, .hero-eyebrow')) return 'hero';

    // Features: 有 feature-card 多个
    var featureCards = el.querySelectorAll('.feature-card');
    if (featureCards.length >= 3) return 'features';

    // Big-number: 有 stat-figure + stat-label
    if (el.querySelector('.stat-figure, .stats-grid')) return 'big-number';

    // Comparison: 有 comparison-table
    if (el.querySelector('.comparison-table, table')) {
      var headers = el.querySelectorAll('th');
      if (headers.length >= 3) return 'comparison';
    }

    // Testimonial: 有 testimonial-quote
    if (el.querySelector('.testimonial-quote, .testimonial-card-quote')) return 'testimonial';

    // FAQ: 有 faq-item + faq-question
    if (el.querySelectorAll('.faq-item').length >= 2) return 'faq';

    // Pricing: 有 pricing-card 多个
    var pricingCards = el.querySelectorAll('.pricing-card');
    if (pricingCards.length >= 2) return 'pricing';

    // Gallery: 有 gallery-grid + gallery-item 多个
    var galleryItems = el.querySelectorAll('.gallery-item');
    if (galleryItems.length >= 3) return 'gallery';

    // CTA: 有 cta-headline + cta-actions
    if (el.querySelector('.cta-headline, .cta-actions')) return 'cta';

    // Footer: 有 footer-links
    if (el.querySelector('.footer-links, .footer-social')) return 'footer';

    return null;
  }

  // === 内容特征 (无明确标记时 fallback) ===
  function detectFromContent(el) {
    var text = (el.textContent || '').trim();

    // 短文 + 大量 question marks → FAQ
    var questionCount = (text.match(/\?/g) || []).length;
    if (questionCount >= 3 && text.length < 3000) return 'faq';

    // 大量 $ 符号 → pricing
    var dollarCount = (text.match(/\$\d/g) || []).length;
    if (dollarCount >= 3) return 'pricing';

    // "vs" 多次出现 → comparison
    var vsCount = (text.match(/\bvs\.?\b|\bversus\b|\bcompare\b/gi) || []).length;
    if (vsCount >= 2) return 'comparison';

    return null;
  }

  // === 综合检测 ===
  function detect(element) {
    var el = element || document.body;
    if (!el || el.nodeType !== 1) return null;

    var explicit = detectExplicit(el);
    if (explicit) return explicit;

    var fromClass = detectFromClass(el);
    if (fromClass) return fromClass;

    var fromDOM = detectFromDOM(el);
    if (fromDOM) return fromDOM;

    var fromContent = detectFromContent(el);
    if (fromContent) return fromContent;

    return null;
  }

  // === 批量扫描整个页面 ===
  function detectAll() {
    var candidates = document.querySelectorAll('section, header, footer, main > div, [class*="section"]');
    var results = [];

    candidates.forEach(function (el) {
      var type = detect(el);
      if (type) {
        results.push({
          element: el,
          type: type
        });
      }
    });

    return results;
  }

  // === 自动应用 (批量) ===
  function autoApply() {
    var detected = detectAll();
    detected.forEach(function (item) {
      item.element.setAttribute('data-section', item.type);
    });
    return detected;
  }

  // === 暴露 API ===
  window.WebPPT_SectionDetect = {
    detect: detect,
    detectAll: detectAll,
    autoApply: autoApply,
    detectExplicit: detectExplicit,
    detectFromClass: detectFromClass,
    detectFromDOM: detectFromDOM,
    detectFromContent: detectFromContent,
    isValid: function (type) { return VALID_SECTIONS.indexOf(type) !== -1; },
    VALID_SECTIONS: VALID_SECTIONS
  };
})();
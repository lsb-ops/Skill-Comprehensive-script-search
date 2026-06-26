/**
 * WebPPT Maker v3.16 · Page Type Detector
 *
 * 与 v3.15 archetype-detect 的本质区别:
 * - archetype-detect: 检测"页"类型 (slide thinking) → 已废弃
 * - page-detect: 检测"页面类型" (web thinking, 6 种)
 *
 * 检测维度:
 * 1. URL 路径 (路由判断)
 * 2. meta 标签 (og:type, page-type)
 * 3. DOM 结构 (3栏 vs 单栏 vs grid)
 * 4. 内容比例 (文字 vs 图片 vs 代码 vs 数据)
 *
 * 用法:
 *   const page = PageDetect.detect();
 *   // → "landing" | "docs" | "blog" | "product" | "dashboard" | "portfolio"
 */

(function () {
  'use strict';

  var VALID_PAGE_TYPES = ['landing', 'docs', 'blog', 'product', 'dashboard', 'portfolio'];

  // === URL 路径检测 ===
  var URL_PATTERNS = [
    { type: 'docs',      patterns: ['/docs', '/documentation', '/api', '/reference', '/guide', '/help'] },
    { type: 'blog',      patterns: ['/blog', '/post', '/article', '/news', '/story', '/stories'] },
    { type: 'product',   patterns: ['/product', '/products', '/item', '/shop', '/store'] },
    { type: 'dashboard', patterns: ['/dashboard', '/admin', '/app', '/console', '/panel', '/inbox', '/workspace'] },
    { type: 'portfolio', patterns: ['/portfolio', '/work', '/projects', '/gallery', '/showcase'] },
    { type: 'landing',   patterns: ['/', '/home', '/index', '/about', '/pricing', '/features'] }
  ];

  function detectFromURL() {
    var path = window.location.pathname.toLowerCase();
    for (var i = 0; i < URL_PATTERNS.length; i++) {
      var entry = URL_PATTERNS[i];
      for (var j = 0; j < entry.patterns.length; j++) {
        var p = entry.patterns[j];
        if (p === '/' && path !== '/' && path !== '/index' && path !== '/index.html') {
          continue;
        }
        if (path === p || path.indexOf(p + '/') === 0 || path.indexOf(p + '?') === 0) {
          return entry.type;
        }
      }
    }
    return null;
  }

  // === meta 标签检测 ===
  function detectFromMeta() {
    var ogType = document.querySelector('meta[property="og:type"]');
    if (ogType && ogType.content) {
      var content = ogType.content.toLowerCase();
      if (content === 'article') return 'blog';
      if (content === 'product') return 'product';
      if (content === 'website') return 'landing';
    }

    var pageType = document.querySelector('meta[name="page-type"]');
    if (pageType && pageType.content) {
      var t = pageType.content.toLowerCase();
      if (VALID_PAGE_TYPES.indexOf(t) !== -1) return t;
    }

    var explicitType = document.body.getAttribute('data-page-type') ||
                       document.documentElement.getAttribute('data-page-type');
    if (explicitType && VALID_PAGE_TYPES.indexOf(explicitType) !== -1) {
      return explicitType;
    }

    return null;
  }

  // === DOM 结构检测 ===
  function detectFromDOM() {
    // Dashboard 特征: 有 sidebar + topbar 布局
    var hasSidebar = document.querySelector('[data-section="nav"][data-role="sidebar"]') ||
                     document.querySelector('.dashboard-sidebar, .admin-sidebar');
    var hasDashboardGrid = document.querySelector('.dashboard-grid');
    if (hasSidebar && hasDashboardGrid) return 'dashboard';

    // Docs 特征: 左侧 sidebar + 右侧 TOC + 代码块
    var codeBlocks = document.querySelectorAll('pre code, .code-block, .prism-code');
    var hasTOC = document.querySelector('[data-sticky="toc"]');
    var hasMainContent = document.querySelector('main .page-content, article .page-article');
    if (codeBlocks.length > 2 && hasTOC && hasMainContent) return 'docs';

    // Blog 特征: 单 article 元素 + 阅读进度
    var article = document.querySelector('article.page-article, main article');
    var progress = document.querySelector('[data-scroll-progress]');
    if (article && progress) return 'blog';

    // Product 特征: 有产品图 + 价格 + 规格表
    var productImage = document.querySelector('.page-hero-product-image, .product-image');
    var price = document.querySelector('.page-hero-price, .product-price');
    var specs = document.querySelector('.page-specs-table');
    if (productImage && (price || specs)) return 'product';

    // Portfolio 特征: 网格/瀑布流 + hover overlay
    var portfolioGrid = document.querySelector('[data-section="gallery"][data-layout="masonry"]') ||
                        document.querySelector('.portfolio-grid');
    if (portfolioGrid) return 'portfolio';

    // Landing 特征: 多个不同 section
    var sections = document.querySelectorAll('[data-section]');
    var sectionTypes = {};
    sections.forEach(function (s) {
      var t = s.getAttribute('data-section');
      sectionTypes[t] = (sectionTypes[t] || 0) + 1;
    });
    // Landing 通常有 hero + features + cta + footer
    if (sectionTypes['hero'] && sectionTypes['cta'] && sectionTypes['footer'] &&
        Object.keys(sectionTypes).length >= 4) {
      return 'landing';
    }

    return null;
  }

  // === 综合检测 (优先级: meta > URL > DOM) ===
  function detect(options) {
    options = options || {};
    var types = [];

    var fromMeta = detectFromMeta();
    var fromURL = detectFromURL();
    var fromDOM = detectFromDOM();

    if (fromMeta) types.push({ source: 'meta', type: fromMeta, weight: 10 });
    if (fromURL) types.push({ source: 'url', type: fromURL, weight: 7 });
    if (fromDOM) types.push({ source: 'dom', type: fromDOM, weight: 5 });

    if (types.length === 0) return 'landing';  // 默认

    // 投票: 找最多票的类型
    var votes = {};
    types.forEach(function (t) {
      votes[t.type] = (votes[t.type] || 0) + t.weight;
    });

    var winner = 'landing';
    var maxVotes = 0;
    Object.keys(votes).forEach(function (type) {
      if (votes[type] > maxVotes) {
        maxVotes = votes[type];
        winner = type;
      }
    });

    return winner;
  }

  // === 应用 page type 到 <html> ===
  function apply(pageType, options) {
    options = options || {};
    if (VALID_PAGE_TYPES.indexOf(pageType) === -1) {
      pageType = 'landing';
    }

    var root = options.root || document.documentElement;
    root.setAttribute('data-page-type', pageType);

    var event = new CustomEvent('webppt:page-type-applied', {
      detail: { type: pageType }
    });
    root.dispatchEvent(event);

    return pageType;
  }

  function detectAndApply(options) {
    return apply(detect(), options);
  }

  function isValid(type) {
    return VALID_PAGE_TYPES.indexOf(type) !== -1;
  }

  // === 暴露 API ===
  window.WebPPT_PageDetect = {
    detect: detect,
    detectFromURL: detectFromURL,
    detectFromMeta: detectFromMeta,
    detectFromDOM: detectFromDOM,
    apply: apply,
    detectAndApply: detectAndApply,
    isValid: isValid,
    VALID_PAGE_TYPES: VALID_PAGE_TYPES
  };
})();
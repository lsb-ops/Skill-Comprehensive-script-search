/**
 * WebPPT Maker v3.16 · Scroll Observer (滚动观察器)
 *
 * 取代 v3.15 的入场动画 + slide transition
 * 三大能力:
 * 1. IntersectionObserver 触发 [data-reveal] 入场
 * 2. Scroll 进度追踪 ([data-scroll-progress])
 * 3. Scroll-aware nav + scroll spy
 *
 * 性能原则:
 * - 用 rAF 节流
 * - will-change 释放
 * - reduced-motion 支持
 * - 移动端关闭视差
 */

(function () {
  'use strict';

  // === 配置 ===
  var CONFIG = {
    revealThreshold: 0.15,           // 元素进入 15% 可见时触发
    revealRootMargin: '0px 0px -10% 0px',
    progressThrottle: 16,             // 60fps
    scrollSpyThreshold: 0.4,
    enableParallax: !window.matchMedia('(prefers-reduced-motion: reduce)').matches
                  && window.innerWidth > 768  // 移动端禁用
  };

  // === 状态 ===
  var observers = [];
  var scrollHandlers = [];
  var ticking = false;

  // === Reveal Observer (入场动画) ===
  function initReveal() {
    var elements = document.querySelectorAll('[data-reveal], [data-reveal-stagger]');
    if (!elements.length) return;

    if (!('IntersectionObserver' in window)) {
      // 不支持时直接显示
      elements.forEach(function (el) { el.setAttribute('data-revealed', 'true'); });
      return;
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.setAttribute('data-revealed', 'true');
          observer.unobserve(entry.target);
        }
      });
    }, {
      threshold: CONFIG.revealThreshold,
      rootMargin: CONFIG.revealRootMargin
    });

    elements.forEach(function (el) { observer.observe(el); });
    observers.push(observer);
  }

  // === Scroll Progress (进度条) ===
  function initProgress() {
    var bars = document.querySelectorAll('[data-scroll-progress]');
    if (!bars.length) return;

    var updateProgress = function () {
      var docHeight = document.documentElement.scrollHeight - window.innerHeight;
      var progress = docHeight > 0 ? (window.scrollY / docHeight) * 100 : 0;
      bars.forEach(function (bar) {
        bar.style.setProperty('--scroll-progress', progress + '%');
      });
    };

    scrollHandlers.push(updateProgress);
  }

  // === Scroll-aware (滚动变色) ===
  function initScrollAware() {
    var elements = document.querySelectorAll('[data-scroll-aware]');
    if (!elements.length) return;

    var updateAware = function () {
      var scrolled = window.scrollY > 50;
      elements.forEach(function (el) {
        el.setAttribute('data-scrolled', scrolled ? 'true' : 'false');
      });
    };

    scrollHandlers.push(updateAware);
  }

  // === Scroll Direction (上下方向, 用于 hide-on-scroll) ===
  var lastScrollY = window.scrollY || 0;
  function initScrollDirection() {
    var elements = document.querySelectorAll('[data-hide-on-scroll-down="true"]');
    if (!elements.length) return;

    var updateDirection = function () {
      var currentY = window.scrollY;
      var direction = currentY > lastScrollY ? 'down' : 'up';
      // 仅当距离顶部 > 100 时才更新方向
      if (currentY > 100) {
        elements.forEach(function (el) {
          el.setAttribute('data-scroll-direction', direction);
        });
      }
      lastScrollY = currentY;
    };

    scrollHandlers.push(updateDirection);
  }

  // === Scroll Spy (nav 高亮当前 section) ===
  function initScrollSpy() {
    var navLinks = document.querySelectorAll('[data-section="nav"] .nav-link[data-target]');
    var sections = [];
    navLinks.forEach(function (link) {
      var targetId = link.getAttribute('data-target');
      var section = document.getElementById(targetId);
      if (section) sections.push({ link: link, el: section });
    });
    if (!sections.length) return;

    if (!('IntersectionObserver' in window)) return;

    var updateSpy = function () {
      // 找到最靠近顶部 40% 的 section
      var threshold = window.innerHeight * CONFIG.scrollSpyThreshold;
      var current = null;
      sections.forEach(function (s) {
        var rect = s.el.getBoundingClientRect();
        if (rect.top <= threshold && rect.bottom >= 0) {
          current = s;
        }
      });

      navLinks.forEach(function (link) { link.removeAttribute('data-active'); });
      if (current) current.link.setAttribute('data-active', 'true');
    };

    scrollHandlers.push(updateSpy);
  }

  // === Bottom CTA (滚动到底部时显示) ===
  function initBottomCTA() {
    var ctas = document.querySelectorAll('[data-sticky="bottom-cta"]');
    if (!ctas.length) return;

    var updateCTA = function () {
      var docHeight = document.documentElement.scrollHeight - window.innerHeight;
      var progress = docHeight > 0 ? window.scrollY / docHeight : 0;
      var visible = progress > 0.5;  // 滚动超过 50% 显示
      ctas.forEach(function (cta) {
        cta.setAttribute('data-visible', visible ? 'true' : 'false');
      });
    };

    scrollHandlers.push(updateCTA);
  }

  // === rAF 节流 ===
  function onScroll() {
    if (!ticking) {
      requestAnimationFrame(function () {
        scrollHandlers.forEach(function (handler) { handler(); });
        ticking = false;
      });
      ticking = true;
    }
  }

  // === FAQ 手风琴 (单独, 不依赖 scroll) ===
  function initFAQ() {
    var faqItems = document.querySelectorAll('[data-section="faq"] .faq-item');
    faqItems.forEach(function (item) {
      var question = item.querySelector('.faq-question');
      if (!question) return;

      question.addEventListener('click', function () {
        var isOpen = item.getAttribute('data-open') === 'true';
        item.setAttribute('data-open', isOpen ? 'false' : 'true');
      });

      // 键盘 a11y (Enter/Space)
      question.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          question.click();
        }
      });
    });
  }

  // === Mobile menu (汉堡) ===
  function initMobileMenu() {
    var navs = document.querySelectorAll('[data-section="nav"]');
    navs.forEach(function (nav) {
      var toggle = nav.querySelector('.nav-menu-toggle');
      if (!toggle) return;

      toggle.addEventListener('click', function () {
        var isOpen = nav.getAttribute('data-menu-open') === 'true';
        nav.setAttribute('data-menu-open', isOpen ? 'false' : 'true');
      });
    });
  }

  // === Pricing toggle (月/年切换) ===
  function initPricingToggle() {
    var toggles = document.querySelectorAll('[data-section="pricing"] .pricing-toggle');
    toggles.forEach(function (toggle) {
      var options = toggle.querySelectorAll('.pricing-toggle-option');
      options.forEach(function (opt) {
        opt.addEventListener('click', function () {
          options.forEach(function (o) { o.removeAttribute('data-active'); });
          opt.setAttribute('data-active', 'true');
          // 触发自定义事件, 价格计算由业务逻辑处理
          var event = new CustomEvent('webppt:pricing-change', {
            detail: { period: opt.getAttribute('data-period') || 'monthly' }
          });
          document.dispatchEvent(event);
        });
      });
    });
  }

  // === 全部初始化 ===
  function init() {
    initReveal();
    initProgress();
    initScrollAware();
    initScrollDirection();
    initScrollSpy();
    initBottomCTA();
    initFAQ();
    initMobileMenu();
    initPricingToggle();

    // 监听 scroll
    window.addEventListener('scroll', onScroll, { passive: true });
    // 首次触发
    onScroll();
  }

  // === 暴露 API ===
  window.WebPPT_ScrollObserver = {
    init: init,
    config: CONFIG,
    refresh: function () {
      // 动态内容添加后, 重新初始化 reveal
      initReveal();
    }
  };

  // === DOMContentLoaded 后自动初始化 ===
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
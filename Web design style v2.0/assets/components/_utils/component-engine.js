/**
 * WebPPT Maker v3.19.3 · Component Engine (组件交互引擎) — Real Radix a11y
 *
 * 6 个核心组件的交互逻辑, 与 assets/components/*.css 配套:
 * 1. Modal       — open/close, ESC, focus trap, scroll lock + a11y JS
 * 2. Tabs        — click, 键盘导航 (←/→/Home/End), ARIA 同步
 * 3. Carousel    — prev/next, dots, 拖拽 (touch+mouse), autoplay
 * 4. Toast       — 队列, 自动消失, 手动关闭, ARIA live
 * 5. Breadcrumbs — 移动端折叠展开
 * 6. Form        — 验证状态, 字符计数
 *
 * v3.19.3 真实 Radix 14 子包补齐 (curl 验证):
 * - react-remove-scroll: scrollbar 补偿 + overscroll-behavior
 * - theKashey/aria-hidden: sibling aria-hidden 隔离
 * - useFocusGuards: focusin 守卫, 防止焦点逃出
 * - data-autofocus: 显式指定 focus target
 * - findFocusable: 跳过 disabled/inert/hidden
 *
 * 仍 NOT 等价于 Radix (诚实声明):
 * - ❌ Presence animation (我们用 CSS animation, Radix 用 JS 控制)
 * - ❌ DismissableLayer pointerdown 序列 (我们用 click, 不区分 pointer)
 * - ❌ useControllableState 受控/非受控 (我们用 attribute only)
 * - ❌ react-compose-refs ref 合并
 * - ❌ react-slot Slot 模式
 *
 * 设计原则:
 * - 零依赖 (vanilla JS)
 * - 无障碍 (ARIA + 键盘 + 焦点守卫)
 * - 降级 (无 IO / matchMedia 时 fallback)
 * - 性能 (rAF + will-change)
 * - 与 scroll-observer.js 风格一致 (IIFE + var + CONFIG)
 */

(function () {
  'use strict';

  // === 全局配置 ===
  var CONFIG = {
    // Modal
    modalSelector: '[data-component="modal"]',
    modalOpenAttr: 'data-open',

    // Tabs
    tabsSelector: '[data-component="tabs"]',
    tabTriggerAttr: 'data-tab-trigger',
    tabPanelAttr: 'data-tab-panel',

    // Carousel
    carouselSelector: '[data-component="carousel"]',
    carouselTrackAttr: 'data-carousel-track',
    carouselArrowAttr: 'data-carousel-arrow',
    carouselDotAttr: 'data-carousel-dot',
    carouselSlideSelector: '.carousel-slide',
    carouselStateAttr: 'data-carousel-index',

    // Toast
    toastContainerSelector: '[data-component="toast-container"]',
    toastSelector: '[data-component="toast"]',
    toastCloseAttr: 'data-toast-close',
    defaultToastDuration: 4000,

    // Breadcrumbs
    breadcrumbsSelector: '[data-component="breadcrumbs"][data-collapsible="true"]',
    breadcrumbsExpandAttr: 'data-breadcrumbs-expand',

    // Form
    formSelector: '[data-component="form"]',
    formFieldSelector: '.form-field',
    formInputSelector: '.form-input, .form-textarea, .form-select',
    formCounterSelector: '.form-counter',
    formMaxLengthAttr: 'data-max-length',

    // Reduced motion
    reducedMotion: window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  };

  // === 状态 ===
  var modalStack = [];      // 嵌套 modal 栈
  var toastQueue = [];       // toast 队列 (overflow 时排队)
  var carousels = new Map(); // 每个 carousel 实例的 state
  var prevFocus = null;      // modal 打开前的焦点元素
  var originalBodyOverflow = '';
  var portalRoot = null;     // Portal root 元素 (用于浮层)

  // === v3.19.3 Real Radix-inspired A11y (curl 验证 theKashey/aria-hidden 1.2.3) ===

  // --- 滚动锁 (react-remove-scroll 真实模式) ---
  // 真实 src: https://unpkg.com/react-remove-scroll-bar@2.3.4/dist/es2015/utils.js
  // 关键: padding-right 补偿 scrollbar 消失导致的页面跳动
  // 关键: overscroll-behavior: contain 防止背景滚动溢出
  // 关键: 嵌套 modal counter, 最后一个关闭才恢复
  var scrollLockCounter = 0;
  var originalBodyPaddingRight = '';
  var originalBodyOverscrollBehavior = '';

  function getScrollbarGap() {
    // 真实算法 (react-remove-scroll getGapWidth):
    // gap = max(0, windowWidth - documentWidth + paddingRight - paddingLeft)
    if (typeof window === 'undefined') return 0;
    var docWidth = document.documentElement.clientWidth;
    var winWidth = window.innerWidth;
    return Math.max(0, winWidth - docWidth);
  }

  function lockBodyScroll() {
    scrollLockCounter++;
    if (scrollLockCounter > 1) return; // 嵌套时只锁一次
    var scrollbarGap = getScrollbarGap();
    originalBodyOverflow = document.body.style.overflow;
    originalBodyPaddingRight = document.body.style.paddingRight;
    originalBodyOverscrollBehavior = document.body.style.overscrollBehavior;
    document.body.style.overflow = 'hidden';
    document.body.style.overscrollBehavior = 'contain';
    if (scrollbarGap > 0) {
      // 补偿 scrollbar 宽度, 防止页面宽度变化导致 layout shift
      var cs = window.getComputedStyle(document.body);
      var currentPadding = parseInt(cs.paddingRight, 10) || 0;
      document.body.style.paddingRight = (currentPadding + scrollbarGap) + 'px';
    }
    document.body.setAttribute('data-scroll-locked', 'true');
  }

  function unlockBodyScroll() {
    if (scrollLockCounter === 0) return;
    scrollLockCounter--;
    if (scrollLockCounter > 0) return; // 还有嵌套 modal, 不解锁
    document.body.style.overflow = originalBodyOverflow;
    document.body.style.paddingRight = originalBodyPaddingRight;
    document.body.style.overscrollBehavior = originalBodyOverscrollBehavior;
    document.body.removeAttribute('data-scroll-locked');
  }

  // --- aria-hidden siblings (theKashey/aria-hidden 1.2.3 真实模式) ---
  // 真实 src: https://unpkg.com/aria-hidden@1.2.3/dist/es2015/index.js
  // 关键: 递归 walk body children, 给非 target 的元素加 aria-hidden="true"
  // 关键: 用 data-aria-hidden 标记 + counter 模式支持嵌套
  var ariaHiddenCounter = new WeakMap();

  function applyAriaHiddenSiblings(target) {
    if (!target || !document.body) return function () {};
    var hiddenNodes = [];
    var elementsToKeep = new Set();
    // Walk UP from target, mark all ancestors as "keep" (don't hide)
    var el = target;
    while (el && el !== document.body) {
      elementsToKeep.add(el);
      el = el.parentNode;
    }
    // Recursively walk body's children
    function deep(parent) {
      if (!parent) return;
      Array.prototype.forEach.call(parent.children, function (node) {
        if (elementsToKeep.has(node)) {
          deep(node);
        } else {
          // 跳过 aria-live 区域 (Radix 行为, 避免隐藏 live announcements)
          if (node.getAttribute('aria-live') === 'assertive' ||
              node.getAttribute('aria-live') === 'polite') {
            return;
          }
          var prev = ariaHiddenCounter.get(node) || 0;
          ariaHiddenCounter.set(node, prev + 1);
          if (prev === 0) {
            node.setAttribute('aria-hidden', 'true');
            node.setAttribute('data-aria-hidden', 'true');
          }
          hiddenNodes.push(node);
        }
      });
    }
    deep(document.body);
    return function undo() {
      hiddenNodes.forEach(function (node) {
        var prev = ariaHiddenCounter.get(node) || 1;
        ariaHiddenCounter.set(node, prev - 1);
        if (prev - 1 === 0) {
          node.removeAttribute('aria-hidden');
          node.removeAttribute('data-aria-hidden');
        }
      });
    };
  }

  // --- Focus guards (Radix useFocusGuards 简化) ---
  // 真实 src: Radix focus-guards 模式
  // 关键: 监听 focusin, 防止焦点跑到 modal 外的可聚焦元素
  var focusGuardsStack = []; // 每个 modal 配一个 focusin handler

  function installFocusGuards(modal) {
    function guard(e) {
      if (!modalStack.length) return;
      // 当前 modal 必须在栈中, 否则焦点跑出去了
      if (modalStack.indexOf(modal) === -1) return;
      var topModal = modalStack[modalStack.length - 1];
      if (topModal !== modal) return; // 嵌套时只 guard 顶层
      // 焦点不在 topModal 内, 强制拉回
      if (e.target && !topModal.contains(e.target)) {
        e.stopPropagation();
        var focusables = findFocusable(topModal);
        if (focusables.length) focusables[0].focus();
      }
    }
    document.addEventListener('focusin', guard);
    focusGuardsStack.push(guard);
    return function uninstall() {
      document.removeEventListener('focusin', guard);
      var idx = focusGuardsStack.indexOf(guard);
      if (idx > -1) focusGuardsStack.splice(idx, 1);
    };
  }

  // --- 改进的 findFocusable (跳过 disabled, hidden, inert) ---
  function findFocusable(modal) {
    var selector = [
      'a[href]:not([disabled]):not([tabindex="-1"])',
      'button:not([disabled]):not([tabindex="-1"])',
      'input:not([disabled]):not([type="hidden"]):not([tabindex="-1"])',
      'select:not([disabled]):not([tabindex="-1"])',
      'textarea:not([disabled]):not([tabindex="-1"])',
      '[tabindex]:not([tabindex="-1"]):not([disabled])',
      'audio[controls]',
      'video[controls]',
      'details > summary:first-of-type',
      '[contenteditable]:not([contenteditable="false"]):not([tabindex="-1"])'
    ].join(',');
    var nodes = Array.prototype.slice.call(modal.querySelectorAll(selector));
    return nodes.filter(function (el) {
      // 跳过 visually hidden 或 inert
      if (el.hasAttribute('inert')) return false;
      if (el.closest('[inert]')) return false;
      var rect = el.getBoundingClientRect();
      return rect.width > 0 || rect.height > 0 || el === document.activeElement;
    });
  }

  // --- data-autofocus 支持 (Radix Content autofocus 模式) ---
  function findAutofocusTarget(modal) {
    // 优先 data-autofocus 元素
    var explicit = modal.querySelector('[data-autofocus]');
    if (explicit) return explicit;
    // 其次 modal 本身 (如果 tabindex=-1)
    if (modal.hasAttribute('data-autofocus')) return modal;
    return null;
  }

  // === v3.18 Portal 抽象 (Radix UI 模式) ===
  // 浮层 (modal/tooltip/popover) 渲染到 body 末, 避免 z-index/overflow 父级裁切问题
  function ensurePortalRoot() {
    if (portalRoot && document.body.contains(portalRoot)) return portalRoot;
    portalRoot = document.createElement('div');
    portalRoot.setAttribute('data-webppt-portal', '');
    portalRoot.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:9999;';
    document.body.appendChild(portalRoot);
    return portalRoot;
  }

  function portalMount(el) {
    var root = ensurePortalRoot();
    // 临时禁用 portal root 的 pointer-events: none (让子元素可交互)
    root.style.pointerEvents = 'auto';
    el.setAttribute('data-portaled', 'true');
    root.appendChild(el);
  }

  function portalUnmount(el) {
    if (el && el.parentNode === portalRoot) {
      portalRoot.removeChild(el);
    }
    if (portalRoot && !portalRoot.children.length) {
      portalRoot.style.pointerEvents = 'none';
    }
  }

  // ====================================================================
  // 1. Modal — 模态对话框
  // ====================================================================

  /**
   * 打开 modal
   * @param {HTMLElement} modal
   */
  function openModal(modal) {
    if (!modal) return;
    var currentState = modal.getAttribute('data-state');
    if (currentState === 'open' || currentState === 'opening') return;

    // v3.18 State Machine: closed → opening → open
    modal.setAttribute('data-state', 'opening');
    modal.setAttribute(CONFIG.modalOpenAttr, 'true');
    modal.setAttribute('aria-hidden', 'false');

    // v3.18 Portal: 如果标记 data-portal="true", 挂载到 body 末
    if (modal.getAttribute('data-portal') === 'true') {
      portalMount(modal);
    }

    // 记录焦点以便恢复
    prevFocus = document.activeElement;

    // === v3.19.3 真实 Radix 模式 ===
    // 1) 滚动锁 (counter 模式, 支持嵌套)
    lockBodyScroll();
    modalStack.push(modal);

    // 2) aria-hidden siblings (theKashey/aria-hidden 1.2.3 真实模式)
    var undoAriaHidden = applyAriaHiddenSiblings(modal);
    modal.__undoAriaHidden = undoAriaHidden;

    // 3) Focus guards (useFocusGuards 简化版, 防止焦点逃出 modal)
    var uninstallGuards = installFocusGuards(modal);
    modal.__uninstallGuards = uninstallGuards;

    // 焦点移到 modal 内 (优先 data-autofocus, 其次第一个可聚焦)
    setTimeout(function () {
      var autofocus = findAutofocusTarget(modal);
      if (autofocus) {
        autofocus.focus();
      } else {
        var focusable = findFocusable(modal);
        if (focusable.length) focusable[0].focus();
      }
      // 打开完成
      modal.setAttribute('data-state', 'open');
    }, 50);
  }

  /**
   * 关闭 modal
   * @param {HTMLElement} modal
   */
  function closeModal(modal) {
    if (!modal) return;
    var currentState = modal.getAttribute('data-state');
    if (currentState === 'closed' || currentState === 'closing') return;

    // v3.18 State Machine: open → closing → closed
    modal.setAttribute('data-state', 'closing');
    modal.setAttribute(CONFIG.modalOpenAttr, 'false');
    modal.setAttribute('aria-hidden', 'true');

    // 从栈中移除
    var idx = modalStack.indexOf(modal);
    if (idx > -1) modalStack.splice(idx, 1);

    // 等待 closing 动画完成后卸载 (v3.20 Radix Presence 真实算法)
    // 不再 setTimeout(closeDuration) 硬编码, 而是监听 animationend
    if (global.WebPPTPresence) {
      var presence = global.WebPPTPresence.usePresence(modal, false);
      modal.__presence = presence;
      // 等 unmountSuspended → unmounted 转换
      var unsub = presence.subscribe(function (state) {
        if (state === 'unmounted') {
          unsub();
          modal.setAttribute('data-state', 'closed');
          if (modal.getAttribute('data-portal') === 'true') {
            portalUnmount(modal);
          }
        }
      });
    } else {
      // Fallback (无 Presence.js 加载): 用原 setTimeout
      var closeDuration = parseInt(getComputedStyle(modal).getPropertyValue('--modal-close-duration')) || 300;
      setTimeout(function () {
        modal.setAttribute('data-state', 'closed');
        if (modal.getAttribute('data-portal') === 'true') {
          portalUnmount(modal);
        }
      }, closeDuration);
    }

    // === v3.19.3 真实 Radix 模式 ===
    // 1) aria-hidden siblings 还原
    if (modal.__undoAriaHidden) {
      modal.__undoAriaHidden();
      delete modal.__undoAriaHidden;
    }
    // 2) focus guards 卸载
    if (modal.__uninstallGuards) {
      modal.__uninstallGuards();
      delete modal.__uninstallGuards;
    }
    // 3) 滚动锁还原 (counter 模式, 嵌套时只有顶层恢复)
    unlockBodyScroll();

    // 焦点恢复 (最后一个 modal 关闭时)
    if (modalStack.length === 0) {
      if (prevFocus && prevFocus.focus) prevFocus.focus();
      prevFocus = null;
    }
  }

  /**
   * Modal focus trap (Tab 键循环) — v3.19.3 用 findFocusable 改进
   */
  function trapFocus(e, modal) {
    if (e.key !== 'Tab') return;

    // 嵌套时只 trap 顶层 modal
    if (modalStack.length > 0 && modalStack[modalStack.length - 1] !== modal) return;

    var focusables = findFocusable(modal);
    if (focusables.length === 0) return;

    var first = focusables[0];
    var last = focusables[focusables.length - 1];
    var active = document.activeElement;

    if (e.shiftKey && (active === first || !modal.contains(active))) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && (active === last || !modal.contains(active))) {
      e.preventDefault();
      first.focus();
    }
  }

  /**
   * 初始化所有 modal
   */
  function initModals() {
    var modals = document.querySelectorAll(CONFIG.modalSelector);
    if (!modals.length) return;

    modals.forEach(function (modal) {
      // 默认关闭
      if (!modal.hasAttribute(CONFIG.modalOpenAttr)) {
        modal.setAttribute(CONFIG.modalOpenAttr, 'false');
        modal.setAttribute('aria-hidden', 'true');
      }
      // 确保 aria-modal (对话框标记)
      if (!modal.hasAttribute('role')) {
        modal.setAttribute('role', 'dialog');
      }
      if (!modal.hasAttribute('aria-modal')) {
        modal.setAttribute('aria-modal', 'true');
      }

      // 点击背景关闭
      modal.addEventListener('click', function (e) {
        if (e.target === modal) {
          var dismiss = modal.getAttribute('data-dismiss');
          if (dismiss !== 'false') closeModal(modal);
        }
      });

      // 关闭按钮
      var closeBtns = modal.querySelectorAll('[data-modal-close]');
      closeBtns.forEach(function (btn) {
        btn.addEventListener('click', function () { closeModal(modal); });
      });

      // 键盘 ESC + focus trap
      modal.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
          var dismiss = modal.getAttribute('data-dismiss');
          if (dismiss !== 'false') closeModal(modal);
        }
        trapFocus(e, modal);
      });
    });

    // 全局: 任何 [data-modal-open="selector"] 触发打开
    document.addEventListener('click', function (e) {
      var trigger = e.target.closest('[data-modal-open]');
      if (!trigger) return;
      var selector = trigger.getAttribute('data-modal-open');
      var target = document.querySelector(selector);
      if (target) {
        e.preventDefault();
        openModal(target);
      }
    });
  }

  // ====================================================================
  // 2. Tabs — 标签页
  // ====================================================================

  /**
   * 切换 tab
   * @param {HTMLElement} tabs
   * @param {string} tabId
   */
  function selectTab(tabs, tabId) {
    var triggers = tabs.querySelectorAll('[' + CONFIG.tabTriggerAttr + ']');
    var panels = tabs.querySelectorAll('[' + CONFIG.tabPanelAttr + ']');

    triggers.forEach(function (trigger) {
      var isActive = trigger.getAttribute(CONFIG.tabTriggerAttr) === tabId;
      trigger.setAttribute('aria-selected', isActive ? 'true' : 'false');
      trigger.setAttribute('tabindex', isActive ? '0' : '-1');
    });

    panels.forEach(function (panel) {
      var isActive = panel.getAttribute(CONFIG.tabPanelAttr) === tabId;
      panel.setAttribute('aria-hidden', isActive ? 'false' : 'true');
    });
  }

  /**
   * 键盘导航
   */
  function handleTabKey(e, tabs, triggers, currentIdx) {
    var orientation = tabs.getAttribute('data-orientation') || 'horizontal';
    var nextIdx = currentIdx;

    var prevKey = orientation === 'vertical' ? 'ArrowUp' : 'ArrowLeft';
    var nextKey = orientation === 'vertical' ? 'ArrowDown' : 'ArrowRight';

    if (e.key === prevKey) {
      nextIdx = currentIdx > 0 ? currentIdx - 1 : triggers.length - 1;
      e.preventDefault();
    } else if (e.key === nextKey) {
      nextIdx = currentIdx < triggers.length - 1 ? currentIdx + 1 : 0;
      e.preventDefault();
    } else if (e.key === 'Home') {
      nextIdx = 0;
      e.preventDefault();
    } else if (e.key === 'End') {
      nextIdx = triggers.length - 1;
      e.preventDefault();
    }

    if (nextIdx !== currentIdx) {
      triggers[nextIdx].focus();
      var tabId = triggers[nextIdx].getAttribute(CONFIG.tabTriggerAttr);
      selectTab(tabs, tabId);
    }
  }

  /**
   * 初始化所有 tabs
   */
  function initTabs() {
    var tabsGroups = document.querySelectorAll(CONFIG.tabsSelector);
    if (!tabsGroups.length) return;

    tabsGroups.forEach(function (tabs) {
      var triggers = Array.from(tabs.querySelectorAll('[' + CONFIG.tabTriggerAttr + ']'));
      var panels = tabs.querySelectorAll('[' + CONFIG.tabPanelAttr + ']');
      if (!triggers.length) return;

      // URL hash 同步 (可选)
      var hashSync = tabs.getAttribute('data-hash-sync') === 'true';

      // 初始化 ARIA 状态
      var hasSelected = false;
      triggers.forEach(function (trigger, idx) {
        var isActive = trigger.getAttribute('aria-selected') === 'true';
        if (isActive && !hasSelected) {
          hasSelected = true;
        } else if (!hasSelected && idx === 0) {
          // 默认第一个选中
          isActive = true;
        }
        trigger.setAttribute('aria-selected', isActive ? 'true' : 'false');
        trigger.setAttribute('tabindex', isActive ? '0' : '-1');
      });

      panels.forEach(function (panel) {
        var tabId = panel.getAttribute(CONFIG.tabPanelAttr);
        var trigger = triggers.find(function (t) { return t.getAttribute(CONFIG.tabTriggerAttr) === tabId; });
        var isActive = trigger && trigger.getAttribute('aria-selected') === 'true';
        panel.setAttribute('aria-hidden', isActive ? 'false' : 'true');
      });

      // 点击切换
      triggers.forEach(function (trigger, idx) {
        trigger.addEventListener('click', function () {
          var tabId = trigger.getAttribute(CONFIG.tabTriggerAttr);
          selectTab(tabs, tabId);
          if (hashSync) {
            history.replaceState(null, '', '#' + tabId);
          }
        });

        // 键盘导航
        trigger.addEventListener('keydown', function (e) {
          handleTabKey(e, tabs, triggers, idx);
        });
      });

      // URL hash 初始选中
      if (hashSync && window.location.hash) {
        var hash = window.location.hash.slice(1);
        var match = triggers.find(function (t) { return t.getAttribute(CONFIG.tabTriggerAttr) === hash; });
        if (match) selectTab(tabs, hash);
      }
    });
  }

  // ====================================================================
  // 3. Carousel — 轮播
  // ====================================================================

  /**
   * 更新 carousel 位置
   * @param {HTMLElement} carousel
   * @param {number} index
   */
  function goToSlide(carousel, index) {
    var state = carousels.get(carousel);
    if (!state) return;

    var loop = carousel.getAttribute('data-loop') === 'true';
    var slideCount = state.slides.length;
    var perView = state.perView;

    if (loop) {
      // 循环: index 可以为负或超界
      index = ((index % slideCount) + slideCount) % slideCount;
    } else {
      if (index < 0) index = 0;
      if (index > slideCount - perView) index = Math.max(0, slideCount - perView);
    }

    state.index = index;
    carousel.setAttribute(CONFIG.carouselStateAttr, index);

    // 更新 track transform
    if (state.track && state.slides.length > 0) {
      var slideWidth = state.slides[0].offsetWidth;
      var gap = parseFloat(getComputedStyle(state.track).gap) || 16;
      var offset = -(slideWidth + gap) * index;
      state.track.style.transform = 'translateX(' + offset + 'px)';
    }

    // 更新 arrows disabled
    var prevArrow = carousel.querySelector('[' + CONFIG.carouselArrowAttr + '="prev"]');
    var nextArrow = carousel.querySelector('[' + CONFIG.carouselArrowAttr + '="next"]');
    if (prevArrow) prevArrow.disabled = !loop && index === 0;
    if (nextArrow) nextArrow.disabled = !loop && index >= slideCount - perView;

    // 更新 dots
    var dots = carousel.querySelectorAll('[' + CONFIG.carouselDotAttr + ']');
    dots.forEach(function (dot, i) {
      dot.setAttribute('aria-current', i === index ? 'true' : 'false');
    });
  }

  /**
   * 拖拽支持 (touch + mouse)
   */
  function initDrag(carousel, state) {
    var startX = 0;
    var startTransform = 0;
    var isDragging = false;
    var moved = false;

    function getX(e) {
      return e.touches ? e.touches[0].clientX : e.clientX;
    }

    function onStart(e) {
      isDragging = true;
      moved = false;
      startX = getX(e);
      var transform = state.track.style.transform || 'translateX(0px)';
      var match = transform.match(/translateX\((-?\d+(?:\.\d+)?)px\)/);
      startTransform = match ? parseFloat(match[1]) : 0;
      carousel.setAttribute('data-dragging', 'true');
      pauseAutoplay(carousel);
    }

    function onMove(e) {
      if (!isDragging) return;
      var currentX = getX(e);
      var diff = currentX - startX;
      if (Math.abs(diff) > 5) moved = true;
      state.track.style.transform = 'translateX(' + (startTransform + diff) + 'px)';
      if (Math.abs(diff) > 0 && e.cancelable) e.preventDefault();
    }

    function onEnd(e) {
      if (!isDragging) return;
      isDragging = false;
      carousel.removeAttribute('data-dragging');

      var currentX = e.changedTouches ? e.changedTouches[0].clientX : e.clientX;
      var diff = currentX - startX;
      var threshold = 50;

      if (Math.abs(diff) > threshold) {
        if (diff < 0) goToSlide(carousel, state.index + 1);
        else goToSlide(carousel, state.index - 1);
      } else {
        goToSlide(carousel, state.index);
      }

      startAutoplay(carousel);
    }

    state.track.addEventListener('touchstart', onStart, { passive: true });
    state.track.addEventListener('touchmove', onMove, { passive: false });
    state.track.addEventListener('touchend', onEnd);

    state.track.addEventListener('mousedown', function (e) {
      e.preventDefault();
      onStart(e);
    });
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onEnd);

    // 阻止 drag 后触发 click
    state.track.addEventListener('click', function (e) {
      if (moved) {
        e.preventDefault();
        e.stopPropagation();
        moved = false;
      }
    }, true);
  }

  /**
   * 自动播放
   */
  function startAutoplay(carousel) {
    var state = carousels.get(carousel);
    if (!state || state.autoplayTimer) return;
    var interval = parseInt(carousel.getAttribute('data-autoplay'), 10) || 4000;
    if (CONFIG.reducedMotion) return;

    state.autoplayTimer = setInterval(function () {
      goToSlide(carousel, state.index + 1);
    }, interval);
  }

  function pauseAutoplay(carousel) {
    var state = carousels.get(carousel);
    if (state && state.autoplayTimer) {
      clearInterval(state.autoplayTimer);
      state.autoplayTimer = null;
    }
  }

  /**
   * 初始化所有 carousel
   */
  function initCarousels() {
    var carouselsList = document.querySelectorAll(CONFIG.carouselSelector);
    if (!carouselsList.length) return;

    carouselsList.forEach(function (carousel) {
      var track = carousel.querySelector('[' + CONFIG.carouselTrackAttr + ']');
      var slides = carousel.querySelectorAll(CONFIG.carouselSlideSelector);
      if (!track || !slides.length) return;

      var perView = parseInt(carousel.getAttribute('data-slides-per-view') || '1', 10);
      carousels.set(carousel, {
        track: track,
        slides: slides,
        index: 0,
        perView: perView,
        autoplayTimer: null
      });

      // Arrows
      var prevArrow = carousel.querySelector('[' + CONFIG.carouselArrowAttr + '="prev"]');
      var nextArrow = carousel.querySelector('[' + CONFIG.carouselArrowAttr + '="next"]');
      if (prevArrow) {
        prevArrow.addEventListener('click', function () {
          goToSlide(carousel, carousels.get(carousel).index - 1);
          pauseAutoplay(carousel);
          startAutoplay(carousel);
        });
      }
      if (nextArrow) {
        nextArrow.addEventListener('click', function () {
          goToSlide(carousel, carousels.get(carousel).index + 1);
          pauseAutoplay(carousel);
          startAutoplay(carousel);
        });
      }

      // Dots
      var dots = carousel.querySelectorAll('[' + CONFIG.carouselDotAttr + ']');
      dots.forEach(function (dot, i) {
        dot.addEventListener('click', function () {
          goToSlide(carousel, i);
          pauseAutoplay(carousel);
          startAutoplay(carousel);
        });
      });

      // Drag
      initDrag(carousel, carousels.get(carousel));

      // 键盘
      carousel.setAttribute('tabindex', '0');
      carousel.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowLeft') {
          goToSlide(carousel, carousels.get(carousel).index - 1);
          e.preventDefault();
        } else if (e.key === 'ArrowRight') {
          goToSlide(carousel, carousels.get(carousel).index + 1);
          e.preventDefault();
        }
      });

      // 初始位置
      goToSlide(carousel, 0);

      // 自动播放
      if (carousel.hasAttribute('data-autoplay')) {
        // hover 暂停
        carousel.addEventListener('mouseenter', function () { pauseAutoplay(carousel); });
        carousel.addEventListener('mouseleave', function () { startAutoplay(carousel); });
        startAutoplay(carousel);
      }
    });

    // 窗口 resize 重算
    var resizeTimer = null;
    window.addEventListener('resize', function () {
      if (resizeTimer) clearTimeout(resizeTimer);
      resizeTimer = setTimeout(function () {
        carouselsList.forEach(function (carousel) {
          var state = carousels.get(carousel);
          if (state) goToSlide(carousel, state.index);
        });
      }, 150);
    });
  }

  // ====================================================================
  // 4. Toast — 通知
  // ====================================================================

  /**
   * 显示 toast
   * @param {object} options - { message, type, duration, container }
   */
  function showToast(options) {
    options = options || {};
    var message = options.message || '';
    var title = options.title || '';
    var type = options.type || 'info';
    var duration = options.duration != null ? options.duration : CONFIG.defaultToastDuration;
    var container = options.container || document.querySelector(CONFIG.toastContainerSelector);

    if (!container) {
      console.warn('[component-engine] No toast container found');
      return;
    }

    var toast = document.createElement('div');
    toast.setAttribute('data-component', 'toast');
    toast.setAttribute('data-type', type);
    toast.setAttribute('role', type === 'error' ? 'alert' : 'status');
    toast.setAttribute('aria-live', type === 'error' ? 'assertive' : 'polite');

    var icons = { success: '✓', warning: '!', error: '✕', info: 'i' };
    toast.innerHTML =
      '<div class="toast-icon" aria-hidden="true">' + (icons[type] || icons.info) + '</div>' +
      '<div class="toast-content">' +
        (title ? '<p class="toast-title">' + escapeHTML(title) + '</p>' : '') +
        '<p class="toast-desc">' + escapeHTML(message) + '</p>' +
      '</div>' +
      '<button class="toast-close" ' + CONFIG.toastCloseAttr + '="true" aria-label="关闭">×</button>';

    container.appendChild(toast);

    // 关闭按钮
    toast.querySelector('[' + CONFIG.toastCloseAttr + ']').addEventListener('click', function () {
      dismissToast(toast);
    });

    // 自动消失
    if (duration > 0) {
      setTimeout(function () { dismissToast(toast); }, duration);
    }

    return toast;
  }

  /**
   * 关闭 toast
   */
  function dismissToast(toast) {
    if (!toast || !toast.parentNode) return;
    toast.setAttribute('data-state', 'closing');
    setTimeout(function () {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 200);
  }

  /**
   * 暴露全局 API
   */
  function initToasts() {
    var containers = document.querySelectorAll(CONFIG.toastContainerSelector);
    if (!containers.length) return;

    // 确保 ARIA
    containers.forEach(function (c) {
      if (!c.hasAttribute('aria-live')) c.setAttribute('aria-live', 'polite');
    });

    // 全局 API
    window.showToast = showToast;
  }

  // ====================================================================
  // 5. Breadcrumbs — 面包屑
  // ====================================================================

  function initBreadcrumbs() {
    var crumbs = document.querySelectorAll(CONFIG.breadcrumbsSelector);
    if (!crumbs.length) return;

    crumbs.forEach(function (crumbsEl) {
      var expandBtn = crumbsEl.querySelector('[' + CONFIG.breadcrumbsExpandAttr + ']');
      if (!expandBtn) return;

      expandBtn.addEventListener('click', function () {
        var expanded = crumbsEl.getAttribute('data-expanded') === 'true';
        crumbsEl.setAttribute('data-expanded', expanded ? 'false' : 'true');
        expandBtn.setAttribute('aria-expanded', expanded ? 'false' : 'true');
      });
    });
  }

  // ====================================================================
  // 6. Form — 表单
  // ====================================================================

  /**
   * 设置字段状态
   */
  function setFieldState(field, state) {
    field.setAttribute('data-state', state);
    field.setAttribute('aria-invalid', state === 'invalid' ? 'true' : 'false');
  }

  /**
   * 初始化所有 form
   */
  function initForms() {
    var forms = document.querySelectorAll(CONFIG.formSelector);
    if (!forms.length) return;

    forms.forEach(function (form) {
      // 字符计数
      var inputs = form.querySelectorAll(CONFIG.formInputSelector);
      inputs.forEach(function (input) {
        var maxLen = input.getAttribute(CONFIG.formMaxLengthAttr) || input.getAttribute('maxlength');
        if (!maxLen) return;
        maxLen = parseInt(maxLen, 10);

        var field = input.closest(CONFIG.formFieldSelector);
        if (!field) return;

        var counter = field.querySelector(CONFIG.formCounterSelector);
        if (!counter) {
          counter = document.createElement('p');
          counter.className = 'form-counter';
          counter.setAttribute('aria-live', 'polite');
          input.parentNode.insertBefore(counter, input.nextSibling);
        }
        counter.setAttribute('data-max', maxLen);

        function updateCount() {
          var len = (input.value || '').length;
          counter.textContent = len + ' / ' + maxLen;
          counter.setAttribute('data-over-limit', len > maxLen ? 'true' : 'false');
        }
        input.addEventListener('input', updateCount);
        updateCount();
      });

      // 内置验证 (required + type=email)
      form.addEventListener('submit', function (e) {
        var valid = true;
        inputs.forEach(function (input) {
          var field = input.closest(CONFIG.formFieldSelector);
          if (!field) return;
          var value = (input.value || '').trim();

          if (input.hasAttribute('required') && !value) {
            setFieldState(field, 'invalid');
            valid = false;
          } else if (input.type === 'email' && value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
            setFieldState(field, 'invalid');
            valid = false;
          } else if (value) {
            setFieldState(field, 'valid');
          } else {
            field.removeAttribute('data-state');
            input.removeAttribute('aria-invalid');
          }
        });

        if (!valid) {
          e.preventDefault();
          var firstInvalid = form.querySelector('.form-field[data-state="invalid"] ' + CONFIG.formInputSelector);
          if (firstInvalid) firstInvalid.focus();
        }
      });

      // input 事件清除 invalid
      inputs.forEach(function (input) {
        input.addEventListener('input', function () {
          var field = input.closest(CONFIG.formFieldSelector);
          if (field && field.getAttribute('data-state') === 'invalid') {
            setFieldState(field, 'pending');
          }
        });
      });
    });
  }

  // ====================================================================
  // 工具函数
  // ====================================================================

  function escapeHTML(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // ====================================================================
  // 自动初始化
  // ====================================================================

  function init() {
    initModals();
    initTabs();
    initCarousels();
    initToasts();
    initBreadcrumbs();
    initForms();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // 暴露 API (供手动调用)
  window.WebPPTComponent = {
    openModal: openModal,
    closeModal: closeModal,
    selectTab: selectTab,
    goToSlide: goToSlide,
    showToast: showToast,
    dismissToast: dismissToast,
    setFieldState: setFieldState
  };

})();
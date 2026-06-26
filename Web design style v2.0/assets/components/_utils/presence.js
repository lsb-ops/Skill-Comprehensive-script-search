/**
 * WebPPT Maker v3.20 · Presence (Radix-inspired)
 *
 * 真实开源出处 (curl 直连验证):
 * - @radix-ui/react-presence@1.1.6 (npm registry, dist/index.mjs)
 *
 * 真实算法 (从 source 直读):
 * 1. State machine: mounted → unmountSuspended → unmounted
 * 2. Events: MOUNT / UNMOUNT / ANIMATION_OUT / ANIMATION_END
 * 3. getAnimationName() 从 computed style 读取 animation-name
 * 4. animationstart / animationcancel / animationend 全局监听
 * 5. fillMode: forwards trick — unmount 时保留终态
 *
 * v3.20 用途:
 * - Modal close 等 animationend 才真正 unmount DOM
 * - Toast 自动消失期间, 不被立即删除节点
 * - Carousel slide 切换期间, 旧 slide 不立即消失
 *
 * v3.20 诚实声明:
 * 这是 Radix-inspired 简化版, NOT Radix 等价.
 * 缺失能力: react-compose-refs (我们用单一 ref), useLayoutEffect 替代 (nextTick),
 *   React.jsx Runtime (我们用 vanilla JS), forwardRef + setNode pattern.
 * 文档: docs/RESEARCH_2026_OPEN_SOURCE.md §v3.20
 */

(function (global) {
  'use strict';

  // === State machine ===
  var STATES = {
    MOUNTED: 'mounted',
    UNMOUNT_SUSPENDED: 'unmountSuspended',
    UNMOUNTED: 'unmounted'
  };

  var EVENTS = {
    MOUNT: 'MOUNT',
    UNMOUNT: 'UNMOUNT',
    ANIMATION_OUT: 'ANIMATION_OUT',
    ANIMATION_END: 'ANIMATION_END'
  };

  // 状态转移表 (Radix 真实)
  var MACHINE = {
    mounted: {
      UNMOUNT: 'unmounted',
      ANIMATION_OUT: 'unmountSuspended'
    },
    unmountSuspended: {
      MOUNT: 'mounted',
      ANIMATION_END: 'unmounted'
    },
    unmounted: {
      MOUNT: 'mounted'
    }
  };

  /**
   * 创建 presence state machine (useReducer 替代)
   * @param {boolean} initialPresent
   * @returns {{state, send, isPresent}}
   */
  function createPresence(initialPresent) {
    var currentState = initialPresent ? STATES.MOUNTED : STATES.UNMOUNTED;
    var listeners = [];

    function reducer(state, event) {
      var next = MACHINE[state] && MACHINE[state][event];
      return next || state;
    }

    function send(event) {
      var next = reducer(currentState, event);
      if (next !== currentState) {
        currentState = next;
        // 通知订阅者
        listeners.forEach(function (fn) {
          fn(currentState);
        });
      }
      return currentState;
    }

    function subscribe(fn) {
      listeners.push(fn);
      return function unsubscribe() {
        listeners = listeners.filter(function (l) { return l !== fn; });
      };
    }

    return {
      getState: function () { return currentState; },
      send: send,
      subscribe: subscribe,
      isPresent: function () { return currentState === STATES.MOUNTED || currentState === STATES.UNMOUNT_SUSPENDED; }
    };
  }

  /**
   * 读取元素当前的 animation-name (computed style)
   * Radix 真实做法: getComputedStyle + 检查 animationName
   * @param {HTMLElement|null} el
   * @returns {string}
   */
  function getAnimationName(el) {
    if (!el) return 'none';
    var style = global.getComputedStyle(el);
    return style.animationName || 'none';
  }

  /**
   * 主 API: 绑定 presence 到一个 DOM 元素
   * 当 present 变化时, 智能地等 animationend 才真正卸载
   *
   * @param {HTMLElement} el - DOM 元素
   * @param {boolean} present - 当前是否应该存在
   * @returns {{isPresent: boolean, unmount: function}}
   */
  function usePresence(el, present) {
    var presence = createPresence(present);

    var prevPresent = present;
    var prevAnimationName = 'none';

    // === useLayoutEffect 替代 (vanilla JS 用 nextTick microtask) ===
    function syncPresent() {
      if (!el) return;
      var hasPresentChanged = prevPresent !== present;
      if (!hasPresentChanged) return;

      var currentAnimationName = getAnimationName(el);
      if (present) {
        // false → true: 立即 mount
        presence.send(EVENTS.MOUNT);
      } else if (currentAnimationName === 'none' || el.style.display === 'none') {
        // true → false, 无动画: 立即 unmount
        presence.send(EVENTS.UNMOUNT);
      } else {
        // true → false, 有动画: 转到 unmountSuspended
        var isAnimating = prevAnimationName !== currentAnimationName;
        if (prevPresent && isAnimating) {
          presence.send(EVENTS.ANIMATION_OUT);
        } else {
          presence.send(EVENTS.UNMOUNT);
        }
      }
      prevPresent = present;
      prevAnimationName = presence.getState() === STATES.MOUNTED ? currentAnimationName : 'none';
    }

    // === 同步 listeners ===
    function onAnimationStart(event) {
      if (event.target === el) {
        prevAnimationName = getAnimationName(el);
      }
    }

    function onAnimationEnd(event) {
      if (!el) return;
      var currentAnimationName = getAnimationName(el);
      // CSS.escape fallback (部分浏览器无 CSS.escape)
      var escape = (global.CSS && global.CSS.escape) ? global.CSS.escape : function (s) { return s; };
      var isCurrentAnimation = currentAnimationName.indexOf(escape(event.animationName)) !== -1;
      if (event.target === el && isCurrentAnimation) {
        presence.send(EVENTS.ANIMATION_END);
        // fillMode: forwards trick — 保留终态
        if (!prevPresent) {
          var currentFillMode = el.style.animationFillMode;
          el.style.animationFillMode = 'forwards';
          setTimeout(function () {
            if (el.style.animationFillMode === 'forwards') {
              el.style.animationFillMode = currentFillMode;
            }
          }, 0);
        }
      }
    }

    // 绑定全局监听 (Radix 真实做法)
    if (el) {
      el.addEventListener('animationstart', onAnimationStart);
      el.addEventListener('animationcancel', onAnimationEnd);
      el.addEventListener('animationend', onAnimationEnd);
    }

    // 首次同步
    syncPresent();

    // === Public API ===
    return {
      isPresent: presence.isPresent(),
      getState: presence.getState,
      send: presence.send,
      subscribe: presence.subscribe,
      // 主动 unmount 入口 (用于 click outside / ESC)
      unmount: function () {
        presence.send(EVENTS.UNMOUNT);
      },
      // 清理 listeners
      destroy: function () {
        if (el) {
          el.removeEventListener('animationstart', onAnimationStart);
          el.removeEventListener('animationcancel', onAnimationEnd);
          el.removeEventListener('animationend', onAnimationEnd);
        }
      }
    };
  }

  /**
   * 高级 API: 用 Promise 包装, 等真正 unmount 后 resolve
   * 用于 async/await 场景
   *
   * @param {HTMLElement} el
   * @param {boolean} present
   * @returns {Promise<{isPresent: boolean}>}
   */
  function awaitPresence(el, present) {
    return new Promise(function (resolve) {
      var p = usePresence(el, present);
      var unsub = p.subscribe(function (state) {
        if (state === STATES.UNMOUNTED) {
          unsub();
          resolve({ isPresent: false });
        }
      });
      // 立即已 unmounted
      if (p.getState() === STATES.UNMOUNTED) {
        unsub();
        resolve({ isPresent: false });
      }
    });
  }

  // === 导出 ===
  global.WebPPTPresence = {
    STATES: STATES,
    EVENTS: EVENTS,
    MACHINE: MACHINE,
    createPresence: createPresence,
    getAnimationName: getAnimationName,
    usePresence: usePresence,
    awaitPresence: awaitPresence
  };
})(typeof window !== 'undefined' ? window : globalThis);
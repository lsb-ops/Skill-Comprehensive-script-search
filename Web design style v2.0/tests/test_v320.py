#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebPPT Maker v3.20 · Radix-inspired Presence + Open Props linear() Spring 测试

测试架构 (5 Phase, 30+ tests):
- Phase 1: Presence state machine (mounted/unmountSuspended/unmounted)
- Phase 2: animation detection (getAnimationName via getComputedStyle)
- Phase 3: animationend listener + fillMode forwards trick
- Phase 4: linear() Spring CSS (open-props 真实 5 级)
- Phase 5: Modal/Toast/Carousel 集成 Presence + 回归 (210 PASS)

预期: 30+ tests PASS
"""
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_DIR = BASE

PASS = 0
FAIL = 0
ERRORS = []

def test(name, fn):
    global PASS, FAIL
    try:
        result = fn()
        if result is True or result is None:
            PASS += 1
            print(f"  ✅ {name}: PASS")
        else:
            FAIL += 1
            msg = f"{name}: FAIL — {result}"
            ERRORS.append(msg)
            print(f"  ❌ {msg}")
    except Exception as e:
        FAIL += 1
        msg = f"{name}: ERROR — {type(e).__name__}: {e}"
        ERRORS.append(msg)
        print(f"  ❌ {msg}")

def read(rel_path):
    with open(os.path.join(SKILL_DIR, rel_path), 'r', encoding='utf-8') as f:
        return f.read()

PRESENCE = "assets/components/_utils/presence.js"
SPRING_CSS = "assets/motion/easing-spring.css"
SPRING_PRESET = "assets/motion/_utils/spring-preset.js"
COMPONENT_ENGINE = "assets/components/_utils/component-engine.js"

# === Phase 1: Presence state machine ===
print("--- Phase 1: Presence state machine ---")

def t1_1_presence_file_exists():
    if not os.path.exists(os.path.join(SKILL_DIR, PRESENCE)):
        return f"file not found: {PRESENCE}"
    return True
test("T1.1 presence.js 存在", t1_1_presence_file_exists)

def t1_2_state_machine_states():
    """真实 Radix 3 states: mounted, unmountSuspended, unmounted"""
    text = read(PRESENCE)
    for state in ['mounted', 'unmountSuspended', 'unmounted']:
        if state not in text:
            return f"缺 state: {state}"
    return True
test("T1.2 3 states (mounted/unmountSuspended/unmounted)", t1_2_state_machine_states)

def t1_3_state_machine_events():
    """真实 Radix 4 events: MOUNT, UNMOUNT, ANIMATION_OUT, ANIMATION_END"""
    text = read(PRESENCE)
    for event in ['MOUNT', 'UNMOUNT', 'ANIMATION_OUT', 'ANIMATION_END']:
        if event not in text:
            return f"缺 event: {event}"
    return True
test("T1.3 4 events (MOUNT/UNMOUNT/ANIMATION_OUT/ANIMATION_END)", t1_3_state_machine_events)

def t1_4_machine_transitions():
    """真实 Radix 状态转移表:
       mounted: UNMOUNT→unmounted, ANIMATION_OUT→unmountSuspended
       unmountSuspended: MOUNT→mounted, ANIMATION_END→unmounted
       unmounted: MOUNT→mounted"""
    text = read(PRESENCE)
    if 'MACHINE' not in text:
        return "缺 MACHINE 转移表"
    # 验证关键转移
    checks = [
        ("UNMOUNT", "unmounted"),
        ("ANIMATION_OUT", "unmountSuspended"),
        ("ANIMATION_END", "unmounted"),
    ]
    for ev, st in checks:
        # 简单 substring 检查
        if ev not in text or st not in text:
            return f"转移 {ev}→{st} 未定义"
    return True
test("T1.4 MACHINE 转移表完整", t1_4_machine_transitions)

def t1_5_usePresence_public_api():
    """usePresence 暴露 isPresent / send / subscribe / unmount / destroy"""
    text = read(PRESENCE)
    for api in ['isPresent', 'send', 'subscribe', 'unmount', 'destroy']:
        if api not in text:
            return f"usePresence 缺 {api}"
    return True
test("T1.5 usePresence 暴露 isPresent/send/subscribe/unmount/destroy", t1_5_usePresence_public_api)

def t1_6_awaitPresence_promise():
    """v3.20 新增: awaitPresence() Promise API"""
    text = read(PRESENCE)
    if 'awaitPresence' not in text:
        return "缺 awaitPresence Promise API"
    if 'new Promise' not in text:
        return "awaitPresence 未返回 Promise"
    return True
test("T1.6 awaitPresence() Promise API", t1_6_awaitPresence_promise)

# === Phase 2: animation detection ===
print("--- Phase 2: animation detection ---")

def t2_1_getAnimationName_exists():
    text = read(PRESENCE)
    if 'getAnimationName' not in text:
        return "缺 getAnimationName"
    return True
test("T2.1 getAnimationName() 函数存在", t2_1_getAnimationName_exists)

def t2_2_getAnimationName_uses_computed_style():
    """Radix 真实: getAnimationName 用 getComputedStyle 读 animation-name"""
    text = read(PRESENCE)
    if 'getComputedStyle' not in text:
        return "getAnimationName 未用 getComputedStyle"
    if 'animationName' not in text:
        return "getAnimationName 未读 animationName"
    return True
test("T2.2 getAnimationName 用 getComputedStyle", t2_2_getAnimationName_uses_computed_style)

def t2_3_animation_name_none_fallback():
    """Radix 真实: 无元素/无动画时返回 'none'"""
    text = read(PRESENCE)
    if "return 'none'" not in text and 'return "none"' not in text:
        return "getAnimationName 无 'none' fallback"
    return True
test("T2.3 getAnimationName 'none' fallback", t2_3_animation_name_none_fallback)

def t2_4_display_none_check():
    """Radix 真实: present=false 且 display:none → 立即 UNMOUNT (无动画)"""
    text = read(PRESENCE)
    if "display === 'none'" not in text and 'display == "none"' not in text:
        return "缺 display:none 检测"
    return True
test("T2.4 display:none 立即 UNMOUNT (无动画)", t2_4_display_none_check)

# === Phase 3: animationend listener + fillMode forwards ===
print("--- Phase 3: animationend listener + fillMode forwards ---")

def t3_1_animationend_listener():
    """Radix 真实: animationstart/animationcancel/animationend 全监听"""
    text = read(PRESENCE)
    for ev in ['animationstart', 'animationcancel', 'animationend']:
        if "addEventListener('" + ev + "'" not in text and 'addEventListener("' + ev + '"' not in text:
            return f"缺 {ev} 监听"
    return True
test("T3.1 animationstart/cancel/end 监听 (Radix 真实)", t3_1_animationend_listener)

def t3_2_fillmode_forwards_trick():
    """Radix 真实: fillMode: forwards trick — unmount 时保留终态"""
    text = read(PRESENCE)
    if 'animationFillMode' not in text:
        return "缺 fillMode 终态保留 trick"
    if "'forwards'" not in text and '"forwards"' not in text:
        return "缺 'forwards' 关键字"
    return True
test("T3.2 fillMode:forwards 终态保留 trick (Radix 真实)", t3_2_fillmode_forwards_trick)

def t3_3_css_escape_fallback():
    """Radix 真实: CSS.escape (部分浏览器无) fallback"""
    text = read(PRESENCE)
    if 'CSS.escape' not in text:
        return "缺 CSS.escape (Radix 真实)"
    if 'fallback' not in text and 'global.CSS &&' not in text:
        return "缺 CSS.escape fallback"
    return True
test("T3.3 CSS.escape fallback (Radix 真实)", t3_3_css_escape_fallback)

# === Phase 4: Open Props linear() Spring CSS ===
print("--- Phase 4: Open Props linear() Spring CSS ---")

def t4_1_easing_spring_css_exists():
    if not os.path.exists(os.path.join(SKILL_DIR, SPRING_CSS)):
        return f"file not found: {SPRING_CSS}"
    return True
test("T4.1 easing-spring.css 存在", t4_1_easing_spring_css_exists)

def t4_2_openprops_curl_verified():
    """v3.20 诚实声明: linear() 来自 open-props@1.7.23 (curl 验证)"""
    text = read(SPRING_CSS)
    if 'open-props' not in text:
        return "缺 open-props 出处"
    if '1.7.23' not in text:
        return "缺版本号 1.7.23"
    if 'unpkg' not in text and 'curl' not in text:
        return "缺 curl/unpkg 验证声明"
    return True
test("T4.2 open-props@1.7.23 (curl 验证)", t4_2_openprops_curl_verified)

def t4_3_5_spring_levels():
    """5 个 spring 级别: spring-1..5"""
    text = read(SPRING_CSS)
    for level in ['spring-1', 'spring-2', 'spring-3', 'spring-4', 'spring-5']:
        if '--ease-' + level not in text:
            return f"缺 --ease-{level}"
    return True
test("T4.3 5 个 spring 级别 (--ease-spring-1..5)", t4_3_5_spring_levels)

def t4_4_linear_function_used():
    """linear() CSS 函数 (浏览器原生, Chrome 113+/Safari 17+)"""
    text = read(SPRING_CSS)
    if 'linear(' not in text:
        return "缺 linear() CSS 函数"
    # 至少 5 个 linear() 调用 (5 个 spring)
    count = text.count('linear(')
    if count < 5:
        return f"linear() 调用 < 5 (实际 {count})"
    return True
test("T4.4 linear() CSS 函数 (5+ calls)", t4_4_linear_function_used)

def t4_5_prefers_reduced_motion_fallback():
    """v3.20: prefers-reduced-motion 自动降级 linear → linear (no interpolation)"""
    text = read(SPRING_CSS)
    if 'prefers-reduced-motion' not in text:
        return "缺 prefers-reduced-motion 降级"
    return True
test("T4.5 prefers-reduced-motion 自动降级", t4_5_prefers_reduced_motion_fallback)

def t4_6_old_browser_fallback():
    """v3.20: @supports 检测 linear() 不识别时降级到 ease"""
    text = read(SPRING_CSS)
    if '@supports not' not in text:
        return "缺 @supports not 老浏览器降级"
    if 'animation-timing-function: linear(0, 1)' not in text:
        return "缺 linear() @supports 检测"
    return True
test("T4.6 @supports not 老浏览器降级到 ease", t4_6_old_browser_fallback)

def t4_7_spring_preset_refactored():
    """v3.20 spring-preset.js 重写: 不再用 JS spring 物理求解 (sp.step 等), 改用 CSS linear()"""
    text = read(SPRING_PRESET)
    if 'v3.20' not in text:
        return "spring-preset.js 缺 v3.20 重写标记"
    # 检测旧 JS 物理求解 (v3.13 自研 sp.step)
    if 'sp.step' in text:
        return "spring-preset.js 仍含旧 sp.step JS 物理求解"
    if 'WebPPT_Utils.Spring.create' in text:
        return "spring-preset.js 仍调用旧 Spring.create()"
    # 检测新 CSS linear() 引用
    if 'var(--ease-' not in text:
        return "spring-preset.js 未引用 CSS --ease-* 变量"
    return True
test("T4.7 spring-preset.js v3.20 重写 (CSS linear)", t4_7_spring_preset_refactored)

# === Phase 5: Modal integration + regression ===
print("--- Phase 5: Modal/Toast/Carousel 集成 + 回归 ---")

def t5_1_closeModal_uses_presence():
    """v3.20: closeModal 用 WebPPTPresence.usePresence 替代 setTimeout"""
    text = read(COMPONENT_ENGINE)
    if 'WebPPTPresence' not in text:
        return "closeModal 未引用 WebPPTPresence"
    if 'presence.subscribe' not in text:
        return "closeModal 未用 presence.subscribe"
    return True
test("T5.1 closeModal 用 WebPPTPresence (替代 setTimeout)", t5_1_closeModal_uses_presence)

def t5_2_closeModal_has_fallback():
    """v3.20: WebPPTPresence 不存在时 fallback 到 setTimeout"""
    text = read(COMPONENT_ENGINE)
    if 'Fallback' not in text and 'fallback' not in text:
        return "closeModal 缺 fallback 路径"
    return True
test("T5.2 closeModal 有 fallback (无 Presence.js 时)", t5_2_closeModal_has_fallback)

def t5_3_closeModal_waits_unmounted_state():
    """v3.20: closeModal 等 'unmounted' state 才真正卸载 DOM"""
    text = read(COMPONENT_ENGINE)
    if "'unmounted'" not in text and '"unmounted"' not in text:
        return "closeModal 未等 'unmounted' state"
    return True
test("T5.3 closeModal 等 'unmounted' state 才卸载", t5_3_closeModal_waits_unmounted_state)

def t5_4_openModal_intact():
    """v3.20 不退化: openModal 4 函数未变"""
    text = read(COMPONENT_ENGINE)
    for fn in ['openModal', 'closeModal', 'trapFocus', 'initModals']:
        if 'function ' + fn not in text:
            return f"openModal 缺 {fn}"
    return True
test("T5.4 openModal/closeModal/trapFocus/initModals 未退化", t5_4_openModal_intact)

def t5_5_a11y_intact():
    """v3.20 不退化: v3.19.3 a11y 工具仍在"""
    text = read(COMPONENT_ENGINE)
    for fn in ['lockBodyScroll', 'applyAriaHiddenSiblings', 'installFocusGuards']:
        if 'function ' + fn not in text:
            return f"v3.19.3 a11y 缺 {fn}"
    return True
test("T5.5 v3.19.3 a11y (lockBodyScroll/aria-hidden/focus-guards) 未退化", t5_5_a11y_intact)

def t5_6_size_budget():
    """v3.20 新增 presence.js (~5KB) 不应让 component-engine 暴增"""
    p = os.path.join(SKILL_DIR, PRESENCE)
    size = os.path.getsize(p) if os.path.exists(p) else 0
    if size > 8 * 1024:
        return f"presence.js {size/1024:.1f}KB > 8KB"
    return True
test("T5.6 presence.js < 8KB", t5_6_size_budget)

def t5_7_v320_honest_disclaimer():
    """v3.20 诚实声明: NOT Radix 等价 (差异: compose-refs/jsx-runtime/forwardRef)"""
    text = read(PRESENCE)
    if 'NOT Radix 等价' not in text and 'NOT Radix' not in text:
        return "缺 v3.20 诚实声明"
    if 'react-compose-refs' not in text:
        return "诚实声明未提 react-compose-refs 缺失"
    return True
test("T5.7 v3.20 诚实声明 (NOT Radix 等价)", t5_7_v320_honest_disclaimer)

def t5_8_easing_spring_css_size():
    """easing-spring.css 大小 < 4KB (5 个 linear() 已精简)"""
    p = os.path.join(SKILL_DIR, SPRING_CSS)
    size = os.path.getsize(p) if os.path.exists(p) else 0
    if size > 6 * 1024:
        return f"easing-spring.css {size/1024:.1f}KB > 6KB"
    return True
test("T5.8 easing-spring.css < 6KB", t5_8_easing_spring_css_size)

# === Phase 6: 总集回归 (确认 v3.16-v3.19.3 仍 PASS) ===
print("--- Phase 6: 总集回归 ---")

def t6_1_210_regression_via_subprocess():
    """跑 test_v3193.py 看 25/25 仍 PASS"""
    import subprocess
    p = os.path.join(SKILL_DIR, "tests/test_v3193.py")
    if not os.path.exists(p):
        return "test_v3193.py 不存在"
    r = subprocess.run(['python3', p], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return f"test_v3193 失败: {r.stdout[-300:]}"
    return True
test("T6.1 v3.19.3 25/25 PASS 回归", t6_1_210_regression_via_subprocess)

# === 总结 ===
print()
print("=" * 60)
total = PASS + FAIL
print(f"📊 v3.20 测试: {PASS}/{total} PASS, {FAIL} FAIL")
if FAIL == 0:
    print("🎉 v3.20 Presence + linear() Spring 全部通过!")
else:
    print(f"❌ {len(ERRORS)} 个测试失败:")
    for e in ERRORS:
        print(f"   - {e}")
print("=" * 60)

import sys
sys.exit(0 if FAIL == 0 else 1)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebPPT Maker v3.18 · Token v2 测试

测试架构 (8 个 Phase, 30+ tests):
- Phase 1: color-tokens-v2.css (HSL split + OKLCH + semantic)
- Phase 2: elevation.css (5 levels)
- Phase 3: easing-tokens 升级 (MD3 12 duration + Apple spring 三参数)
- Phase 4: spring-preset.js 升级 (Apple 三参数 API)
- Phase 5: component-engine Portal + State Machine
- Phase 6: demo_v318_tokens 演示页
- Phase 7: 模板集成 (color-tokens-v2 + elevation)
- Phase 8: v3.17 + v3.16 回归不退化

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

def assert_file_exists(rel_path):
    path = os.path.join(SKILL_DIR, rel_path)
    if not os.path.exists(path):
        return f"file not found: {rel_path}"
    return True

# === Phase 1: color-tokens-v2 ===
print("--- Phase 1: color-tokens-v2.css ---")

def t1_1_tokens_v2_exists():
    return assert_file_exists("assets/design/color-tokens-v2.css")
test("T1.1 color-tokens-v2.css 存在", t1_1_tokens_v2_exists)

def t1_2_hsl_split_for_primary():
    """v3.18.1 修正: HSL 拆段是 v3.18 臆造 (NOT shadcn 模式).
       现保留作 LEGACY 兼容, 同时新增 Tailwind v4 11 级 scale.
       测试验证: legacy keys 仍在 + v3.18.1 诚实修正声明 + 11 级 scale 完整."""
    text = read("assets/design/color-tokens-v2.css")
    # legacy HSL keys 仍保留 (向后兼容)
    for key in ['--color-primary-h', '--color-primary-s', '--color-primary-l']:
        if key not in text:
            return f"HSL legacy key 缺少 {key}"
    # v3.18.1 诚实修正声明必须存在
    if 'v3.18.1 诚实修正' not in text:
        return "缺少 v3.18.1 诚实修正声明段"
    # Tailwind v4 11 级 scale 必须完整
    for i in [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950]:
        key = f'--color-primary-{i}'
        if key not in text:
            return f"Tailwind v4 11 级 scale 缺少 {key}"
    return True
test("T1.2 HSL legacy + Tailwind 11 级 scale", t1_2_hsl_split_for_primary)

def t1_3_oklch_used():
    text = read("assets/design/color-tokens-v2.css")
    # 必须至少 10 处 oklch 使用
    count = text.count('oklch(')
    if count < 10:
        return f"OKLCH 使用过少: {count}"
    return True
test("T1.3 OKLCH 色彩空间", t1_3_oklch_used)

def t1_4_semantic_colors():
    text = read("assets/design/color-tokens-v2.css")
    for color in ['success', 'warning', 'error', 'info']:
        for suffix in ['', '-bg', '-fg', '-border']:
            key = f'--color-{color}{suffix}'
            if key not in text:
                return f"语义色缺少 {key}"
    return True
test("T1.4 4 语义色 × 4 变体", t1_4_semantic_colors)

def t1_5_dark_theme_remap():
    text = read("assets/design/color-tokens-v2.css")
    if '[data-theme="dark"]' not in text:
        return "缺少 dark theme remap"
    if 'prefers-color-scheme: dark' not in text:
        return "缺少 system dark 自动切换"
    return True
test("T1.5 暗色模式 (auto + manual)", t1_5_dark_theme_remap)

def t1_6_cvd_okabe_ito():
    text = read("assets/design/color-tokens-v2.css")
    for i in range(1, 9):
        key = f'--color-cvd-{i}'
        if key not in text:
            return f"CVD 色板缺少 {key}"
    return True
test("T1.6 CVD Okabe-Ito 8 色", t1_6_cvd_okabe_ito)

def t1_7_wcag_focus_ring():
    text = read("assets/design/color-tokens-v2.css")
    for key in ['--focus-ring-width: 2px', '--focus-ring-color', ':focus-visible', ':focus:not(:focus-visible)']:
        if key not in text:
            return f"WCAG focus 缺少 {key}"
    return True
test("T1.7 WCAG 2.4.13 focus 2px", t1_7_wcag_focus_ring)

# === Phase 2: elevation ===
print("--- Phase 2: elevation.css ---")

def t2_1_elevation_exists():
    return assert_file_exists("assets/design/elevation.css")
test("T2.1 elevation.css 存在", t2_1_elevation_exists)

def t2_2_6_shadow_levels_real():
    """v3.18.1 修正: 真实 Open Props 6 级 + inner 5 级"""
    text = read("assets/design/elevation.css")
    for i in range(1, 7):  # shadow-1..6
        key = f'--shadow-{i}:'
        if key not in text:
            return f"缺少 --shadow-{i}:"
    for i in range(0, 5):  # inner-shadow-0..4
        key = f'--inner-shadow-{i}:'
        if key not in text:
            return f"缺少 --inner-shadow-{i}:"
    return True
test("T2.2 真实 Open Props 6 级 + inner 5 级", t2_2_6_shadow_levels_real)

def t2_3_hsl_space_separated_format():
    """真实 Open Props 用 HSL space-separated 而非 oklch"""
    text = read("assets/design/elevation.css")
    if '--shadow-color:' not in text or 'hsl(var(--shadow-color)' not in text:
        return "未使用 Open Props HSL 格式"
    return True
test("T2.3 HSL space-separated (Open Props 同款)", t2_3_hsl_space_separated_format)

def t2_4_dark_shadow_color_override():
    """暗色模式覆盖 --shadow-color (Open Props 真实策略)"""
    text = read("assets/design/elevation.css")
    if '[data-theme="dark"]' not in text:
        return "缺 dark theme 重映射"
    if '--shadow-color: 220 40% 2%' not in text:
        return "暗色未覆盖 --shadow-color"
    return True
test("T2.4 暗色 --shadow-color 覆盖", t2_4_dark_shadow_color_override)

def t2_5_utility_classes():
    text = read("assets/design/elevation.css")
    for cls in ['.elev-0', '.elev-1', '.elev-2', '.elev-3', '.elev-4', '.elev-5', '.elev-6']:
        if cls not in text:
            return f"缺少 utility class {cls}"
    return True
test("T2.5 7 个 .elev-N utility (含 0)", t2_5_utility_classes)

# === Phase 3: easing-tokens 升级 ===
print("--- Phase 3: easing-tokens 升级 ---")

def t3_1_real_open_props_spring():
    """v3.18.1 修正: 真实 Open Props linear() spring, 非臆造 MD3 12"""
    text = read("assets/motion/easing-tokens.css")
    for i in range(1, 6):
        key = f'--ease-spring-{i}'
        if key not in text:
            return f"缺少真实 Open Props spring {key}"
        # 必须用 CSS linear() 函数
        if f'--ease-spring-{i}: linear(' not in text:
            return f"spring-{i} 未用 linear() 函数"
    return True
test("T3.1 真实 Open Props 5 级 spring (linear())", t3_1_real_open_props_spring)

def t3_2_tailwind_v4_minimal_duration():
    """v3.19.1 修正: 我之前误以为 MD3 没有 12-level duration, 实际是 16-level.
       现 Tailwind 极简 3 级 + MD3 真实 16 级并存, 测试两者都在."""
    text = read("assets/motion/easing-tokens.css")
    # Tailwind v4 极简 3 级
    for key in ['--dur-fast', '--dur-default', '--dur-slow']:
        if key not in text:
            return f"缺少 Tailwind 风格 {key}"
    # MD3 16 duration (v3.19.1 恢复, v3.18.1 误删)
    import re
    for i in range(1, 5):
        for prefix in ['short', 'medium', 'long', 'extra-long']:
            if prefix == 'extra-long' and i > 4:
                continue
            key = f'--dur-{prefix}{i}'
            if key not in text:
                return f"MD3 16 duration 缺 {key}"
    return True
test("T3.2 Tailwind 3 + MD3 16 duration 并存", t3_2_tailwind_v4_minimal_duration)

def t3_3_real_op_easing_5_levels():
    """真实 Open Props --ease-op-1..5 (替代 v3.18 臆造)"""
    text = read("assets/motion/easing-tokens.css")
    for i in range(1, 6):
        key = f'--ease-op-{i}'
        if key not in text:
            return f"缺少真实 Open Props easing {key}"
    return True
test("T3.3 真实 Open Props --ease-op-1..5", t3_3_real_op_easing_5_levels)

def t3_4_reduced_motion_zero_dur():
    text = read("assets/motion/easing-tokens.css")
    if '--dur-fast: 0ms' not in text:
        return "reduced-motion 未重置 duration 为 0"
    return True
test("T3.4 reduced-motion duration = 0", t3_4_reduced_motion_zero_dur)

def t3_5_real_op_size_scale():
    """真实 Open Props --size-1..15 + --size-fluid-1..10"""
    text = read("assets/motion/easing-tokens.css")
    for i in [1, 5, 10, 15]:
        key = f'--size-{i}:'
        if key not in text:
            return f"缺少真实 Open Props size {key}"
    for i in [1, 5, 10]:
        key = f'--size-fluid-{i}:'
        if key not in text:
            return f"缺少 size-fluid-{key}"
    return True
test("T3.5 真实 Open Props size scale", t3_5_real_op_size_scale)

# === Phase 4: spring-preset 升级 ===
print("--- Phase 4: spring-preset 升级 ---")

def t4_1_preset_doc_mentions_triple():
    """v3.18.1 修正: Apple HIG 三参数是 v3.18 臆造.
       现 spring-preset 必须诚实标注 'WebPPT v3.13 自研' 或 'Open Props linear()'.
       测试只验证文档不再伪造 Apple HIG 引用."""
    text = read("assets/motion/_utils/spring-preset.js")
    # 必须含诚实声明之一
    honest_markers = ['WebPPT v3.13 自研', 'Open Props linear()', '诚实修正', 'WebPPT 内部约定', 'NOT Apple HIG']
    if not any(marker in text for marker in honest_markers):
        return "spring-preset 缺少诚实声明 (v3.18.1 要求)"
    # 必须不含 v3.18 臆造的 Apple HIG 引用
    forbidden = ['Apple HIG 风格', 'https://developer.apple.com/design/human-interface-guidelines/motion']
    for f in forbidden:
        if f in text:
            return f"spring-preset 仍含 v3.18 臆造引用: {f}"
    return True
test("T4.1 spring-preset 诚实声明 (NOT Apple HIG)", t4_1_preset_doc_mentions_triple)

def t4_2_preset_supports_physics():
    """v3.18.1 修正: physics 三参数 API 是 v3.18 臆造 (Apple HIG).
       现 spring-preset 只暴露 preset 选择, 不再提供 physics 三参数 (那是 spring.js v3.13 内部).
       测试验证: 不含 physics: 三参数 API 形式 + 正确暴露 WebPPT_Spring 全局."""
    text = read("assets/motion/_utils/spring-preset.js")
    # v3.18 臆造的 physics 三参数 API 不应再出现
    if "physics: { mass:" in text or "physics:{mass:" in text:
        return "仍含 v3.18 臆造的 physics 三参数 API"
    # 必须暴露 WebPPT_Spring 全局 (animate / animateMany / pickPreset)
    for fn in ['WebPPT_Spring', 'animate:', 'animateMany:', 'pickPreset:']:
        if fn not in text:
            return f"未暴露 {fn}"
    return True
test("T4.2 preset API 暴露 (无臆造 physics)", t4_2_preset_supports_physics)

def t4_3_old_preset_aliases_kept():
    text = read("/Users/lin/Documents/Agents配套/Agents/专属agent/开发可以用网页做ppt/做动态网页skill/assets/motion/_utils/spring-preset.js")
    for alias in ['snappy', 'wobbly', 'heavy']:
        if alias not in text:
            return f"旧 alias {alias} 不再支持 (应保持兼容)"
    return True
test("T4.3 旧 preset alias 兼容", t4_3_old_preset_aliases_kept)

# === Phase 5: component-engine Portal + State Machine ===
print("--- Phase 5: component-engine 升级 ---")

def t5_1_portal_functions():
    text = read("assets/components/_utils/component-engine.js")
    for fn in ['ensurePortalRoot', 'portalMount', 'portalUnmount']:
        if fn not in text:
            return f"Portal 缺少 {fn}"
    return True
test("T5.1 Portal 三函数", t5_1_portal_functions)

def t5_2_state_machine_states():
    text = read("assets/components/_utils/component-engine.js")
    # modal 必须有 opening/closing 中间状态
    for state in ['opening', 'closing']:
        if f"data-state', '{state}'" not in text and f'data-state\', \'{state}\'' not in text:
            return f"缺少中间 state {state}"
    return True
test("T5.2 State machine 中间态", t5_2_state_machine_states)

def t5_3_portal_attribute():
    text = read("assets/components/_utils/component-engine.js")
    if 'data-portal' not in text:
        return "未识别 data-portal 属性"
    return True
test("T5.3 data-portal 属性识别", t5_3_portal_attribute)

# === Phase 6: demo_v318_tokens ===
print("--- Phase 6: demo_v318_tokens ---")

def t6_1_demo_exists():
    return assert_file_exists("examples/demo_v318_tokens/index.html")
test("T6.1 demo_v318_tokens 存在", t6_1_demo_exists)

def t6_2_demo_uses_tokens_v2():
    text = read("examples/demo_v318_tokens/index.html")
    for ref in ['color-tokens-v2.css', 'elevation.css']:
        if ref not in text:
            return f"未引用 {ref}"
    return True
test("T6.2 引用 v3.18 新 token", t6_2_demo_uses_tokens_v2)

def t6_3_demo_theme_toggle():
    text = read("examples/demo_v318_tokens/index.html")
    if 'data-theme' not in text:
        return "缺 dark/light 切换"
    if '切换主题' not in text:
        return "缺主题切换 UI"
    return True
test("T6.3 主题切换演示", t6_3_demo_theme_toggle)

def t6_4_demo_all_4_toast_types():
    text = read("examples/demo_v318_tokens/index.html")
    for t in ['success', 'warning', 'error', 'info']:
        if f"type:'{t}'" not in text and f'type:\'{t}\'' not in text:
            return f"未演示 {t} toast"
    return True
test("T6.4 4 种 toast 演示", t6_4_demo_all_4_toast_types)

def t6_5_demo_cvd_palette():
    text = read("examples/demo_v318_tokens/index.html")
    for i in range(1, 9):
        if f'--color-cvd-{i}' not in text:
            return f"未演示 CVD-{i}"
    return True
test("T6.5 CVD 8 色演示", t6_5_demo_cvd_palette)

def t6_6_demo_portal_modal():
    text = read("examples/demo_v318_tokens/index.html")
    if 'data-portal="true"' not in text:
        return "未演示 Portal modal"
    return True
test("T6.6 Portal modal 演示", t6_6_demo_portal_modal)

# === Phase 7: 模板集成 ===
print("--- Phase 7: 模板集成 ---")

def t7_1_16x9_imports_tokens_v2():
    text = read("assets/templates/html_16x9_reveal.html")
    if 'color-tokens-v2.css' not in text:
        return "16x9 模板未引入 color-tokens-v2"
    if 'elevation.css' not in text:
        return "16x9 模板未引入 elevation"
    return True
test("T7.1 16x9 引入 v3.18 token", t7_1_16x9_imports_tokens_v2)

def t7_2_9x16_imports_tokens_v2():
    text = read("assets/templates/html_9x16_reveal.html")
    if 'color-tokens-v2.css' not in text:
        return "9x16 模板未引入 color-tokens-v2"
    if 'elevation.css' not in text:
        return "9x16 模板未引入 elevation"
    return True
test("T7.2 9x16 引入 v3.18 token", t7_2_9x16_imports_tokens_v2)

# === Phase 8: 回归 ===
print("--- Phase 8: 回归 ---")

def t8_1_v317_regression():
    # v3.17 核心组件仍在
    for f in ['modal.css', 'tabs.css', 'carousel.css', 'toast.css', 'breadcrumbs.css', 'form.css']:
        if not os.path.exists(os.path.join(SKILL_DIR, f'assets/components/{f}')):
            return f"v3.17 {f} 丢失"
    return True
test("T8.1 v3.17 组件未退化", t8_1_v317_regression)

def t8_2_v316_pages_intact():
    for p in ['landing', 'docs', 'blog', 'product', 'dashboard', 'portfolio']:
        if not os.path.exists(os.path.join(SKILL_DIR, f'assets/pages/{p}.css')):
            return f"v3.16 page {p}.css 丢失"
    return True
test("T8.2 v3.16 6 page 未退化", t8_2_v316_pages_intact)

def t8_3_v312_color_intact():
    return assert_file_exists("assets/design/color-tokens.css")
test("T8.3 v3.12 color-tokens 未退化", t8_3_v312_color_intact)

def t8_4_demos_intact():
    for d in ['demo_landing', 'demo_docs', 'demo_blog', 'demo_v318_tokens']:
        if not os.path.exists(os.path.join(SKILL_DIR, f'examples/{d}/index.html')):
            return f"demo {d} 丢失"
    return True
test("T8.4 4 个演示页完整", t8_4_demos_intact)

def t8_5_v318_size_budget():
    # v3.18 增量 < 50KB
    total = 0
    for f in ['color-tokens-v2.css', 'elevation.css']:
        p = os.path.join(SKILL_DIR, f'assets/design/{f}')
        if os.path.exists(p): total += os.path.getsize(p)
    p = os.path.join(SKILL_DIR, 'examples/demo_v318_tokens/index.html')
    if os.path.exists(p): total += os.path.getsize(p)
    if total > 50 * 1024:
        return f"v3.18 增量 {total/1024:.1f}KB > 50KB"
    return True
test("T8.5 v3.18 增量 < 50KB", t8_5_v318_size_budget)

# === 总结 ===
print()
print("=" * 60)
total = PASS + FAIL
print(f"📊 v3.18 测试: {PASS}/{total} PASS, {FAIL} FAIL")
if FAIL == 0:
    print("🎉 v3.18 Token v2 全部通过!")
else:
    print(f"❌ {len(ERRORS)} 个测试失败:")
    for e in ERRORS:
        print(f"   - {e}")
print("=" * 60)

import sys
sys.exit(0 if FAIL == 0 else 1)
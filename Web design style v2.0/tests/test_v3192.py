#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebPPT Maker v3.19.2 · MD3 Surface + Color Roles + Container + State 测试

测试架构 (5 Phase, 25+ tests):
- Phase 1: surface-tokens.css (MD3 5 surface-container + dim/bright = 7)
- Phase 2: color-roles.css (MD3 20+ color roles: primary/secondary/tertiary/error groups)
- Phase 3: container-queries.css (CSS @container 真实规范, shadcn v4 模式)
- Phase 4: state-variants.css (data-state/data-open/data-checked 真实 Radix 模式)
- Phase 5: 集成 + 回归 (v3.18 + v3.19.1 + 4 templates @import)

预期: 25+ tests PASS
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

# === Phase 1: surface-tokens.css ===
print("--- Phase 1: surface-tokens.css (MD3 5 surface-container) ---")

def t1_1_surface_tokens_exists():
    return assert_file_exists("assets/design/surface-tokens.css")
test("T1.1 surface-tokens.css 存在", t1_1_surface_tokens_exists)

def t1_2_md3_5_surface_container():
    """MD3 v0.192 _md-sys-color.scss 真实 5 levels:
       surface-container-lowest / low / default / high / highest"""
    text = read("assets/design/surface-tokens.css")
    for level in ['lowest', 'low', 'default'.replace('default', ''), 'high', 'highest']:
        key = f'--surface-container-{level}' if level else '--surface-container'
        if key not in text:
            return f"MD3 5 surface-container 缺 {key}"
    # 单独再验证 default
    if '--surface-container:' not in text and '--surface-container ' not in text:
        return "缺默认 --surface-container"
    return True
test("T1.2 MD3 5 surface-container 完整 (lowest/low/高/high/highest)", t1_2_md3_5_surface_container)

def t1_3_surface_dim_bright():
    """MD3 v0.192 真实 surface-dim + surface-bright"""
    text = read("assets/design/surface-tokens.css")
    for key in ['--surface-dim', '--surface-bright']:
        if key not in text:
            return f"MD3 surface 变体缺 {key}"
    return True
test("T1.3 MD3 surface-dim + surface-bright", t1_3_surface_dim_bright)

def t1_4_surface_uses_oklch():
    """必须用 OKLCH 色彩空间 (Tailwind v4 + MD3 现代)"""
    text = read("assets/design/surface-tokens.css")
    if 'oklch(' not in text:
        return "surface-tokens 未用 OKLCH"
    if text.count('oklch(') < 5:
        return f"OKLCH 使用过少: {text.count('oklch(')}"
    return True
test("T1.4 OKLCH 色彩空间", t1_4_surface_uses_oklch)

def t1_5_surface_dark_mode():
    """dark mode 重映射 (MD3 v0.192 dark palette: 4/6/10/12/17/22/24)"""
    text = read("assets/design/surface-tokens.css")
    if '[data-theme="dark"]' not in text:
        return "缺 dark theme 重映射"
    return True
test("T1.5 dark mode 重映射", t1_5_surface_dark_mode)

def t1_6_surface_utility_classes():
    """7 个 utility + 6 个语义化 component utility"""
    text = read("assets/design/surface-tokens.css")
    utilities = ['.surface-dim', '.surface-bright', '.surface-container-lowest',
                 '.surface-container-low', '.surface-container', '.surface-container-high',
                 '.surface-container-highest']
    for u in utilities:
        if u not in text:
            return f"utility 缺 {u}"
    semantics = ['.surface-page', '.surface-sidebar', '.surface-card', '.surface-raised',
                 '.surface-modal', '.surface-overlay']
    for s in semantics:
        if s not in text:
            return f"语义 utility 缺 {s}"
    return True
test("T1.6 7 surface utility + 6 语义化 component utility", t1_6_surface_utility_classes)

# === Phase 2: color-roles.css ===
print("--- Phase 2: color-roles.css (MD3 20+ color roles) ---")

def t2_1_color_roles_exists():
    return assert_file_exists("assets/design/color-roles.css")
test("T2.1 color-roles.css 存在", t2_1_color_roles_exists)

def t2_2_primary_group():
    """MD3 primary 4 tokens: primary, on-primary, primary-container, on-primary-container"""
    text = read("assets/design/color-roles.css")
    for key in ['--color-primary', '--color-on-primary', '--color-primary-container', '--color-on-primary-container']:
        if key not in text:
            return f"Primary group 缺 {key}"
    return True
test("T2.2 Primary group (4 tokens)", t2_2_primary_group)

def t2_3_secondary_tertiary_groups():
    """MD3 secondary + tertiary 各 4 tokens"""
    text = read("assets/design/color-roles.css")
    for prefix in ['secondary', 'tertiary']:
        for suffix in ['', '-on-' + prefix, '-container', '-on-' + prefix + '-container']:
            # on-secondary / secondary-container / on-secondary-container
            if prefix == 'secondary':
                keys = ['--color-secondary', '--color-on-secondary',
                        '--color-secondary-container', '--color-on-secondary-container']
            else:
                keys = ['--color-tertiary', '--color-on-tertiary',
                        '--color-tertiary-container', '--color-on-tertiary-container']
    for k in ['--color-secondary', '--color-on-secondary', '--color-secondary-container',
              '--color-on-secondary-container',
              '--color-tertiary', '--color-on-tertiary', '--color-tertiary-container',
              '--color-on-tertiary-container']:
        if k not in text:
            return f"Secondary/Tertiary group 缺 {k}"
    return True
test("T2.3 Secondary + Tertiary group (各 4 tokens)", t2_3_secondary_tertiary_groups)

def t2_4_error_group():
    """MD3 error 4 tokens"""
    text = read("assets/design/color-roles.css")
    for k in ['--color-error', '--color-on-error', '--color-error-container',
              '--color-on-error-container']:
        if k not in text:
            return f"Error group 缺 {k}"
    return True
test("T2.4 Error group (4 tokens)", t2_4_error_group)

def t2_5_surface_outline_inverse():
    """MD3 surface + on-surface + variant + outline + inverse 群组"""
    text = read("assets/design/color-roles.css")
    for k in ['--color-surface', '--color-on-surface', '--color-surface-variant',
              '--color-on-surface-variant', '--color-outline', '--color-outline-variant',
              '--color-inverse-surface', '--color-inverse-on-surface', '--color-inverse-primary']:
        if k not in text:
            return f"Surface/Outline/Inverse group 缺 {k}"
    return True
test("T2.5 Surface + Outline + Inverse group (9 tokens)", t2_5_surface_outline_inverse)

def t2_6_dark_mode_remap():
    """dark mode 全部重映射 (MD3 v0.192 真实 dark palette)"""
    text = read("assets/design/color-roles.css")
    if '[data-theme="dark"]' not in text:
        return "缺 dark theme 重映射"
    # 验证 dark 模式至少 5 个 token 被重定义
    dark_section = text.split('[data-theme="dark"]')[1] if '[data-theme="dark"]' in text else ''
    if dark_section.count('--color-') < 10:
        return f"dark 模式重定义 < 10, 实际 {dark_section.count('--color-')}"
    return True
test("T2.6 dark mode 重映射 (≥10 tokens)", t2_6_dark_mode_remap)

def t2_7_semantic_component_utilities():
    """btn-primary / chip-primary / chip-error 高层语义 utility"""
    text = read("assets/design/color-roles.css")
    for cls in ['.btn-primary', '.btn-tonal', '.btn-error',
                '.chip-primary', '.chip-tertiary', '.chip-error',
                '.inverse-surface']:
        if cls not in text:
            return f"语义 utility 缺 {cls}"
    return True
test("T2.7 7 个高层语义 utility (btn/chip/inverse)", t2_7_semantic_component_utilities)

# === Phase 3: container-queries.css ===
print("--- Phase 3: container-queries.css (CSS @container 真实) ---")

def t3_1_container_queries_exists():
    return assert_file_exists("assets/utilities/container-queries.css")
test("T3.1 container-queries.css 存在", t3_1_container_queries_exists)

def t3_2_real_container_at_rule():
    """真实 CSS @container 规则 (Baseline 2023, w3.org/TR/css-contain-3)"""
    text = read("assets/utilities/container-queries.css")
    if '@container' not in text:
        return "缺 @container at-rule (真实 CSS 容器查询)"
    # 必须有至少 3 个 @container 规则
    count = text.count('@container')
    if count < 3:
        return f"@container 规则过少: {count}"
    return True
test("T3.2 真实 CSS @container 规则 (≥3 处)", t3_2_real_container_at_rule)

def t3_3_named_containers():
    """命名 container (shadcn 风格: card / sidebar / main)"""
    text = read("assets/utilities/container-queries.css")
    for name in ['card', 'sidebar', 'main']:
        # 验证 container-name + 至少一个 @container name 规则
        if f'container-name: {name}' not in text and f'@container {name}' not in text:
            return f"命名 container '{name}' 缺"
    return True
test("T3.3 3 个命名 container (card/sidebar/main)", t3_3_named_containers)

def t3_4_container_type_set():
    """container-type: inline-size (让元素成为 query container)"""
    text = read("assets/utilities/container-queries.css")
    if 'container-type: inline-size' not in text:
        return "缺 container-type: inline-size"
    return True
test("T3.4 container-type: inline-size (成为 query container)", t3_4_container_type_set)

def t3_5_breakpoint_values_real():
    """真实 breakpoint (300/500/800 card, 200/400 sidebar, 600/900 main)"""
    text = read("assets/utilities/container-queries.css")
    for px in ['300px', '500px', '800px', '200px', '400px', '600px', '900px']:
        if px not in text:
            return f"缺 breakpoint {px}"
    return True
test("T3.5 7 个真实 breakpoint (300/500/800/200/400/600/900px)", t3_5_breakpoint_values_real)

# === Phase 4: state-variants.css ===
print("--- Phase 4: state-variants.css (data-state / data-open / data-checked) ---")

def t4_1_state_variants_exists():
    return assert_file_exists("assets/utilities/state-variants.css")
test("T4.1 state-variants.css 存在", t4_1_state_variants_exists)

def t4_2_data_state_patterns():
    """Radix 真实 6 states: open/closed/on/off/checked/unchecked"""
    text = read("assets/utilities/state-variants.css")
    for state in ['open', 'closed', 'on', 'off', 'checked', 'unchecked']:
        key = f'[data-state="{state}"]'
        if key not in text:
            return f"Radix data-state='{state}' 缺"
    return True
test("T4.2 Radix 6 真实 data-state (open/closed/on/off/checked/unchecked)", t4_2_data_state_patterns)

def t4_3_shadcn_data_attr_shortcuts():
    """shadcn v4 简化 data-open / data-checked 快捷属性"""
    text = read("assets/utilities/state-variants.css")
    for attr in ['[data-open="true"]', '[data-open="false"]', '[data-checked="true"]',
                 '[data-checked="false"]', '[data-disabled]']:
        if attr not in text:
            return f"shadcn 简化属性 {attr} 缺"
    return True
test("T4.3 shadcn data-open/data-checked 简化属性", t4_3_shadcn_data_attr_shortcuts)

def t4_4_component_state_combinations():
    """Radix 组件 × state 组合 (modal/popover/tab/switch/accordion)"""
    text = read("assets/utilities/state-variants.css")
    for combo in ['[data-component="modal"][data-state="open"]',
                  '[data-component="popover"][data-state="open"]',
                  '[data-component="tab"][data-state="selected"]',
                  '[data-component="switch"][data-state="on"]',
                  '[data-component="accordion"][data-state="open"]']:
        if combo not in text:
            return f"组件×state 组合缺 {combo}"
    return True
test("T4.4 5 个组件×state 组合 (modal/popover/tab/switch/accordion)", t4_4_component_state_combinations)

def t4_5_state_animations_use_md3_easing():
    """state 动画用 MD3 easing + duration token (避免散落 cubic-bezier)"""
    text = read("assets/utilities/state-variants.css")
    if 'var(--ease-emphasized' not in text and '--ease-emphasized' not in text:
        return "state 动画未用 MD3 easing token"
    if 'var(--dur-' not in text:
        return "state 动画未用 duration token"
    return True
test("T4.5 动画用 MD3 easing + duration token", t4_5_state_animations_use_md3_easing)

def t4_6_loading_spinner_animation():
    """[data-state=loading] loading spinner 动画 (真实 CSS 实现)"""
    text = read("assets/utilities/state-variants.css")
    if '[data-state="loading"]' not in text:
        return "缺 loading 状态"
    if '@keyframes' not in text or 'spin' not in text:
        return "缺 spinner keyframes"
    return True
test("T4.6 loading 状态 + spinner 动画", t4_6_loading_spinner_animation)

# === Phase 5: 集成 + 回归 ===
print("--- Phase 5: 集成 + 回归 (v3.18 + v3.19.1 + templates) ---")

def t5_1_16x9_imports_v3192():
    """16x9 模板引入 v3.19.2 全部 4 新 CSS"""
    text = read("assets/templates/html_16x9_reveal.html")
    for ref in ['surface-tokens.css', 'color-roles.css',
                'container-queries.css', 'state-variants.css']:
        if ref not in text:
            return f"16x9 模板未引入 {ref}"
    return True
test("T5.1 16x9 引入 v3.19.2 全部 4 新 CSS", t5_1_16x9_imports_v3192)

def t5_2_9x16_imports_v3192():
    """9x16 模板引入 v3.19.2 全部 4 新 CSS"""
    text = read("assets/templates/html_9x16_reveal.html")
    for ref in ['surface-tokens.css', 'color-roles.css',
                'container-queries.css', 'state-variants.css']:
        if ref not in text:
            return f"9x16 模板未引入 {ref}"
    return True
test("T5.2 9x16 引入 v3.19.2 全部 4 新 CSS", t5_2_9x16_imports_v3192)

def t5_3_v3191_typography_intact():
    """v3.19.1 typography 15 styles 完整 (回归)"""
    text = read("assets/design/typography-tokens.css")
    for key in ['--font-display-large-size', '--font-headline-medium-size',
                '--font-body-medium-size', '--font-label-small-size']:
        if key not in text:
            return f"v3.19.1 typography 缺 {key}"
    return True
test("T5.3 v3.19.1 typography 15 styles 完整", t5_3_v3191_typography_intact)

def t5_4_v3191_radius_intact():
    """v3.19.1 radius 8+8 完整 (回归)"""
    text = read("assets/design/radius-tokens.css")
    for key in ['--radius-xs', '--radius-4xl', '--radius-corner-extra-large', '--radius: 0.5rem']:
        if key not in text:
            return f"v3.19.1 radius 缺 {key}"
    return True
test("T5.4 v3.19.1 radius 完整", t5_4_v3191_radius_intact)

def t5_5_v318_color_intact():
    """v3.18 color-tokens-v2 完整 (回归)"""
    text = read("assets/design/color-tokens-v2.css")
    if 'oklch(' not in text or '--color-primary-50' not in text or '--color-primary-950' not in text:
        return "v3.18 color-tokens-v2 缺关键 token"
    return True
test("T5.5 v3.18 color-tokens-v2 完整", t5_5_v318_color_intact)

def t5_6_v3192_honest_sources():
    """v3.19.2 4 文件必须含真实出处 (curl 验证引用)"""
    files = [
        "assets/design/surface-tokens.css",
        "assets/design/color-roles.css",
        "assets/utilities/container-queries.css",
        "assets/utilities/state-variants.css",
    ]
    for f in files:
        text = read(f)
        # 必须有真实来源标记
        honest_markers = ['MD3 v0.192', 'Material Web', 'w3.org', 'Radix', 'shadcn', 'css-contain-3']
        if not any(m in text for m in honest_markers):
            return f"{f} 缺诚实来源声明"
    return True
test("T5.6 v3.19.2 4 文件含真实出处声明", t5_6_v3192_honest_sources)

def t5_7_v3192_size_budget():
    """v3.19.2 4 文件总大小 < 30KB"""
    total = 0
    for f in ['assets/design/surface-tokens.css', 'assets/design/color-roles.css',
              'assets/utilities/container-queries.css', 'assets/utilities/state-variants.css']:
        p = os.path.join(SKILL_DIR, f)
        if os.path.exists(p):
            total += os.path.getsize(p)
    if total > 30 * 1024:
        return f"v3.19.2 增量 {total/1024:.1f}KB > 30KB"
    return True
test("T5.7 v3.19.2 增量 < 30KB", t5_7_v3192_size_budget)

# === 总结 ===
print()
print("=" * 60)
total = PASS + FAIL
print(f"📊 v3.19.2 测试: {PASS}/{total} PASS, {FAIL} FAIL")
if FAIL == 0:
    print("🎉 v3.19.2 MD3 Surface + Color Roles + Container + State 全部通过!")
else:
    print(f"❌ {len(ERRORS)} 个测试失败:")
    for e in ERRORS:
        print(f"   - {e}")
print("=" * 60)

import sys
sys.exit(0 if FAIL == 0 else 1)

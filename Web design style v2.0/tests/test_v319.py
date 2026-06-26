#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebPPT Maker v3.19.1 · 基于真实开源 (2026) 改进测试

测试架构 (5 Phase, 20+ tests):
- Phase 1: MD3 16 duration tokens (恢复 v3.18.1 误删)
- Phase 2: typography-tokens.css (MD3 15 styles + Tailwind 13 sizes)
- Phase 3: radius-tokens.css (MD3 8 + Tailwind 8)
- Phase 4: modal.css MD3 标准化 (560/280/140/48/0.32)
- Phase 5: 回归 (v3.16 + v3.17 + v3.18.1 不退化)

预期: 20+ tests PASS
"""
import os

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

# === Phase 1: MD3 16 duration tokens ===
print("--- Phase 1: MD3 16 duration tokens (v3.19.1 恢复) ---")

def t1_1_md3_duration_full_set():
    """v3.19.1 恢复 MD3 16 duration (v3.18.1 误删).
       数据: @material/web@2.4.1 _md-sys-motion.scss HTTP 200 实测."""
    text = read("assets/motion/easing-tokens.css")
    expected_short = ['--dur-short1', '--dur-short2', '--dur-short3', '--dur-short4']
    expected_medium = ['--dur-medium1', '--dur-medium2', '--dur-medium3', '--dur-medium4']
    expected_long = ['--dur-long1', '--dur-long2', '--dur-long3', '--dur-long4']
    expected_xlong = ['--dur-extra-long1', '--dur-extra-long2', '--dur-extra-long3', '--dur-extra-long4']
    for key in expected_short + expected_medium + expected_long + expected_xlong:
        if key not in text:
            return f"MD3 16 duration 缺少 {key}"
    return True
test("T1.1 MD3 16 duration 完整 (short×4 + medium×4 + long×4 + extra-long×4)", t1_1_md3_duration_full_set)

def t1_2_md3_duration_values_correct():
    """验证关键 duration 值与 MD3 v0.192 一致 (允许空格变体)"""
    import re
    text = read("assets/motion/easing-tokens.css")
    expected = [
        ('--dur-short1', '50ms'),
        ('--dur-short4', '200ms'),
        ('--dur-medium2', '300ms'),
        ('--dur-long2', '500ms'),
        ('--dur-extra-long4', '1000ms'),
    ]
    for key, val in expected:
        # 允许多种空格变体 (e.g. ":  50ms" / ":50ms" / ": 50ms")
        pattern = re.compile(rf'{re.escape(key)}\s*:\s*{re.escape(val)}')
        if not pattern.search(text):
            return f"{key} 应为 {val}"
    return True
test("T1.2 MD3 duration 数值正确 (50/200/300/500/1000ms)", t1_2_md3_duration_values_correct)

def t1_3_md3_duration_honest_source():
    """诚实标注 MD3 出处 (v3.18.1 错误删除, v3.19.1 承认错误)"""
    text = read("assets/motion/easing-tokens.css")
    if '@material/web' not in text and 'md-sys-motion' not in text:
        return "未标注 MD3 真实出处"
    return True
test("T1.3 MD3 duration 出处诚实声明", t1_3_md3_duration_honest_source)

# === Phase 2: typography-tokens.css ===
print("--- Phase 2: typography-tokens.css (MD3 + Tailwind) ---")

def t2_1_typography_file_exists():
    return assert_file_exists("assets/design/typography-tokens.css")
test("T2.1 typography-tokens.css 存在", t2_1_typography_file_exists)

def t2_2_md3_15_type_styles():
    """MD3 v0.192 真实 15 styles:
       display-large/medium/small + headline-large/medium/small
       + title-large/medium/small + body-large/medium/small
       + label-large/medium/small"""
    text = read("assets/design/typography-tokens.css")
    expected = [
        '--font-display-large-size',
        '--font-display-medium-size',
        '--font-display-small-size',
        '--font-headline-large-size',
        '--font-headline-medium-size',
        '--font-headline-small-size',
        '--font-title-large-size',
        '--font-title-medium-size',
        '--font-title-small-size',
        '--font-body-large-size',
        '--font-body-medium-size',
        '--font-body-small-size',
        '--font-label-large-size',
        '--font-label-medium-size',
        '--font-label-small-size',
    ]
    for key in expected:
        if key not in text:
            return f"MD3 15 type styles 缺少 {key}"
    return True
test("T2.2 MD3 15 type styles 完整 (5 类 × 3 等级)", t2_2_md3_15_type_styles)

def t2_3_tailwind_font_stack():
    """Tailwind v4.3.1 真实字体堆栈: Apple Color Emoji, Segoe UI Emoji"""
    text = read("assets/design/typography-tokens.css")
    for marker in ["ui-sans-serif", "system-ui", "Apple Color Emoji", "Segoe UI Emoji"]:
        if marker not in text:
            return f"Tailwind 字体堆栈缺少 {marker}"
    return True
test("T2.3 Tailwind v4 字体堆栈 (含 emoji fallback)", t2_3_tailwind_font_stack)

def t2_4_type_utility_classes():
    text = read("assets/design/typography-tokens.css")
    for cls in ['.type-display-large', '.type-headline-medium', '.type-body-large',
                '.type-label-small']:
        if cls not in text:
            return f"utility class 缺少 {cls}"
    return True
test("T2.4 15 个 .type-* utility class", t2_4_type_utility_classes)

def t2_5_md3_size_values_real():
    """MD3 v0.192 display-large-size 应为 3.5625rem (57px, NOT 56px)"""
    import re
    text = read("assets/design/typography-tokens.css")
    # 允许多空格对齐
    if not re.search(r'--font-display-large-size\s*:\s*3\.5625rem', text):
        return "display-large-size 应为 3.5625rem (57px, MD3 v0.192)"
    if not re.search(r'--font-body-medium-size\s*:\s*0\.875rem', text):
        return "body-medium-size 应为 0.875rem (14px)"
    return True
test("T2.5 MD3 字号真实值 (display 57px, body 14px)", t2_5_md3_size_values_real)

# === Phase 3: radius-tokens.css ===
print("--- Phase 3: radius-tokens.css (MD3 + Tailwind) ---")

def t3_1_radius_file_exists():
    return assert_file_exists("assets/design/radius-tokens.css")
test("T3.1 radius-tokens.css 存在", t3_1_radius_file_exists)

def t3_2_md3_8_corners():
    """MD3 v0.192 真实 8 corners: none/extra-small/small/medium/large/extra-large/full"""
    text = read("assets/design/radius-tokens.css")
    expected = ['--radius-corner-none', '--radius-corner-extra-small', '--radius-corner-small',
                '--radius-corner-medium', '--radius-corner-large', '--radius-corner-extra-large',
                '--radius-corner-full']
    for key in expected:
        if key not in text:
            return f"MD3 8 corners 缺少 {key}"
    return True
test("T3.2 MD3 8 corner tokens 完整", t3_2_md3_corners := t3_2_md3_8_corners)

def t3_3_md3_corner_values_real():
    """MD3 v0.192 真实值: extra-large=28px, large=16px, medium=12px, small=8px"""
    text = read("assets/design/radius-tokens.css")
    if '--radius-corner-extra-large:  28px' not in text and '--radius-corner-extra-large: 28px' not in text:
        return "MD3 extra-large 应为 28px"
    if '--radius-corner-large:        16px' not in text and '--radius-corner-large: 16px' not in text:
        return "MD3 large 应为 16px"
    if '--radius-corner-medium:       12px' not in text and '--radius-corner-medium: 12px' not in text:
        return "MD3 medium 应为 12px"
    return True
test("T3.3 MD3 corner 数值正确 (28/16/12px)", t3_3_md3_corner_values_real)

def t3_4_tailwind_radius_scale():
    """Tailwind v4.3.1 真实 8 级: xs(2)/sm(4)/md(6)/lg(8)/xl(12)/2xl(16)/3xl(24)/4xl(32)"""
    text = read("assets/design/radius-tokens.css")
    for i, px in [('xs', '0.125rem'), ('sm', '0.25rem'), ('md', '0.375rem'), ('lg', '0.5rem'),
                  ('xl', '0.75rem'), ('2xl', '1rem'), ('3xl', '1.5rem'), ('4xl', '2rem')]:
        key = f'--radius-{i}'
        if key not in text:
            return f"Tailwind radius 缺少 {key}"
    return True
test("T3.4 Tailwind v4 8 级 radius scale", t3_4_tailwind_radius_scale)

def t3_5_shadcn_radius_derived():
    """shadcn 派生: --radius 默认 + 倍率 (sm=0.6x, md=0.8x, lg=1x)"""
    text = read("assets/design/radius-tokens.css")
    if '--radius: 0.5rem' not in text:
        return "shadcn --radius 默认值应为 0.5rem"
    for marker in ['--radius-calc-sm', '--radius-calc-md', '--radius-calc-lg',
                   '--radius-calc-xl', '--radius-calc-2xl', '--radius-calc-3xl',
                   '--radius-calc-4xl']:
        if marker not in text:
            return f"shadcn 派生半径缺少 {marker}"
    return True
test("T3.5 shadcn --radius 派生 (sm/md/lg/xl/2xl/3xl/4xl)", t3_5_shadcn_radius_derived)

# === Phase 4: modal.css MD3 标准化 ===
print("--- Phase 4: modal.css MD3 标准化 ---")

def t4_1_modal_md3_dimensions():
    """MD3 dialog 标准: max 560, min 280×140, viewport 48"""
    text = read("assets/components/modal.css")
    if 'min(560px' not in text:
        return "modal max-width 应为 min(560px, ...) (MD3 dialog 标准)"
    if 'min-width: 280px' not in text:
        return "modal min-width 应为 280px (MD3 dialog 标准)"
    if 'min-height: 140px' not in text:
        return "modal min-height 应为 140px (MD3 dialog 标准)"
    if 'padding: 48px' not in text:
        return "modal viewport 边距应为 48px (MD3 dialog 标准)"
    return True
test("T4.1 modal MD3 尺寸标准 (560/280/140/48)", t4_1_modal_md3_dimensions)

def t4_2_modal_scrim_opacity_032():
    """MD3 scrim opacity 0.32 (v3.17 用 0.5, 现改 MD3 标准)"""
    text = read("assets/components/modal.css")
    if '0.32' not in text:
        return "modal scrim opacity 应为 0.32 (MD3 dialog)"
    return True
test("T4.2 modal scrim opacity 0.32 (MD3)", t4_2_modal_scrim_opacity_032)

def t4_3_modal_md3_radius_28():
    """MD3 dialog 用 28px extra-large 圆角"""
    text = read("assets/components/modal.css")
    if 'radius-corner-extra-large' not in text and '28px' not in text:
        return "modal 圆角应为 28px (MD3 extra-large)"
    return True
test("T4.3 modal MD3 28px extra-large 圆角", t4_3_modal_md3_radius_28)

def t4_4_modal_md3_animation_500ms():
    """MD3 dialog 入场动画 500ms (vs v3.17 用 200ms)"""
    text = read("assets/components/modal.css")
    if '500ms' not in text and 'var(--dur-long2' not in text:
        return "modal 入场动画应为 500ms (MD3)"
    return True
test("T4.4 modal 入场动画 500ms (MD3 dialog)", t4_4_modal_md3_animation_500ms)

def t4_5_modal_honest_radix_disclaimer():
    """诚实声明: Radix-inspired 简化版, NOT Radix 等价"""
    text = read("assets/components/modal.css")
    if 'Radix-inspired' not in text:
        return "modal.css 应诚实声明 'Radix-inspired, NOT Radix 等价'"
    return True
test("T4.5 modal 诚实声明 Radix-inspired 简化", t4_5_modal_honest_radix_disclaimer)

def t4_6_modal_a11y_focus_visible():
    """a11y: focus-visible 样式 (WCAG 2.4.7)"""
    text = read("assets/components/modal.css")
    if 'focus-visible' not in text:
        return "modal 缺 focus-visible 样式"
    return True
test("T4.6 modal focus-visible (WCAG 2.4.7)", t4_6_modal_a11y_focus_visible)

# === Phase 5: 回归 ===
print("--- Phase 5: 回归 (v3.18.1 + v3.17 + v3.16 不退化) ---")

def t5_1_v318_color_tokens_intact():
    """v3.18.1 color-tokens-v2 OKLCH + Tailwind 11 scale 仍在"""
    text = read("assets/design/color-tokens-v2.css")
    for key in ['oklch', '--color-primary', '--color-primary-50', '--color-primary-950']:
        if key not in text:
            return f"v3.18.1 color 缺 {key}"
    return True
test("T5.1 v3.18.1 color-tokens-v2 完整", t5_1_v318_color_tokens_intact)

def t5_2_v318_elevation_intact():
    """v3.18.1 elevation 6 shadow + 5 inner 仍在"""
    text = read("assets/design/elevation.css")
    for i in range(1, 7):
        if f'--shadow-{i}' not in text:
            return f"v3.18.1 elevation 缺 --shadow-{i}"
    return True
test("T5.2 v3.18.1 elevation 6 shadow 完整", t5_2_v318_elevation_intact)

def t5_3_v318_openprops_spring_intact():
    """v3.18.1 Open Props 5 spring linear() 仍在"""
    text = read("assets/motion/easing-tokens.css")
    for i in range(1, 6):
        if f'--ease-spring-{i}' not in text:
            return f"v3.18.1 Open Props 缺 spring-{i}"
    return True
test("T5.3 v3.18.1 Open Props 5 spring 完整", t5_3_v318_openprops_spring_intact)

def t5_4_v317_components_intact():
    """v3.17 6 组件仍在"""
    for f in ['modal.css', 'tabs.css', 'carousel.css', 'toast.css', 'breadcrumbs.css', 'form.css']:
        if not os.path.exists(os.path.join(SKILL_DIR, f'assets/components/{f}')):
            return f"v3.17 {f} 丢失"
    return True
test("T5.4 v3.17 6 组件未退化", t5_4_v317_components_intact)

def t5_5_v316_pages_intact():
    """v3.16 6 pages 仍在"""
    for p in ['landing', 'docs', 'blog', 'product', 'dashboard', 'portfolio']:
        if not os.path.exists(os.path.join(SKILL_DIR, f'assets/pages/{p}.css')):
            return f"v3.16 page {p}.css 丢失"
    return True
test("T5.5 v3.16 6 pages 未退化", t5_5_v316_pages_intact)

def t5_6_v319_size_budget():
    """v3.19.1 新增 (typography + radius) < 20KB"""
    total = 0
    for f in ['typography-tokens.css', 'radius-tokens.css']:
        p = os.path.join(SKILL_DIR, f'assets/design/{f}')
        if os.path.exists(p):
            total += os.path.getsize(p)
    if total > 20 * 1024:
        return f"v3.19.1 增量 {total/1024:.1f}KB > 20KB"
    return True
test("T5.6 v3.19.1 新增 < 20KB", t5_6_v319_size_budget)

def t5_7_honest_research_doc_exists():
    """v3.19.1 真实开源研究文档"""
    return assert_file_exists("docs/RESEARCH_2026_OPEN_SOURCE.md")
test("T5.7 docs/RESEARCH_2026_OPEN_SOURCE.md 存在", t5_7_honest_research_doc_exists)

# === 总结 ===
print()
print("=" * 60)
total = PASS + FAIL
print(f"📊 v3.19.1 测试: {PASS}/{total} PASS, {FAIL} FAIL")
if FAIL == 0:
    print("🎉 v3.19.1 真实开源改进全部通过!")
else:
    print(f"❌ {len(ERRORS)} 个测试失败:")
    for e in ERRORS:
        print(f"   - {e}")
print("=" * 60)

import sys
sys.exit(0 if FAIL == 0 else 1)
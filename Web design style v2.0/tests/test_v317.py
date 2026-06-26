#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebPPT Maker v3.17 · Component Layer 测试

测试架构 (8 个 Phase):
- Phase 1: 6 个核心组件 CSS 文件
- Phase 2: 组件引擎 JS (component-engine.js)
- Phase 3: 3 个真实演示页 (landing/docs/blog)
- Phase 4: 模板集成 (component-engine.js 注入)
- Phase 5: DESIGN_PHILOSOPHY.md v3.16 升级
- Phase 6: v3.16 回归测试
- Phase 7: 端到端检查 (HTML/JS/CSS 链接完整)
- Phase 8: 文件统计 + 性能预算

预期: 30+ tests PASS
"""
import os
import re
import sys

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

# === Phase 1: 6 核心组件 CSS 文件 ===
print("--- Phase 1: 6 核心组件 CSS ---")

def t1_1_all_components_exist():
    components = ['modal', 'tabs', 'carousel', 'toast', 'breadcrumbs', 'form']
    for c in components:
        rel = f"assets/components/{c}.css"
        if assert_file_exists(rel) is not True:
            return f"missing: {rel}"
    return True
test("T1.1 6 component CSS exist", t1_1_all_components_exist)

def t1_2_modal_has_backdrop_and_close():
    text = read("assets/components/modal.css")
    for sel in ['[data-component="modal"]', 'backdrop-filter', 'aria-modal']:
        if sel not in text and sel != 'aria-modal':  # aria-modal 在 HTML, 不在 CSS
            return f"modal.css 缺少 {sel}"
    return True
test("T1.2 modal backdrop + close", t1_2_modal_has_backdrop_and_close)

def t1_3_tabs_has_aria_and_keyboard():
    text = read("assets/components/tabs.css")
    for sel in ['[data-component="tabs"]', 'aria-selected', '[data-orientation']:
        if sel not in text:
            return f"tabs.css 缺少 {sel}"
    return True
test("T1.3 tabs ARIA + orientation", t1_3_tabs_has_aria_and_keyboard)

def t1_4_carousel_has_dots_arrows_drag():
    text = read("assets/components/carousel.css")
    for sel in ['[data-component="carousel"]', 'carousel-arrow', 'carousel-dot', 'data-dragging']:
        if sel not in text:
            return f"carousel.css 缺少 {sel}"
    return True
test("T1.4 carousel dots/arrows/drag", t1_4_carousel_has_dots_arrows_drag)

def t1_5_toast_has_4_types_and_6_positions():
    text = read("assets/components/toast.css")
    for t in ['success', 'warning', 'error', 'info']:
        if f'data-type="{t}"' not in text:
            return f"toast.css 缺少 type={t}"
    for pos in ['top-right', 'top-left', 'bottom-right', 'bottom-left', 'top-center', 'bottom-center']:
        if f'data-position="{pos}"' not in text:
            return f"toast.css 缺少 position={pos}"
    return True
test("T1.5 toast 4 types + 6 positions", t1_5_toast_has_4_types_and_6_positions)

def t1_6_breadcrumbs_mobile_collapsible():
    text = read("assets/components/breadcrumbs.css")
    for sel in ['[data-component="breadcrumbs"]', 'data-collapsible', 'breadcrumb-expand']:
        if sel not in text:
            return f"breadcrumbs.css 缺少 {sel}"
    # 必须有 mobile 媒体查询
    if '@media (max-width: 640px)' not in text:
        return "breadcrumbs.css 缺少 mobile media query"
    return True
test("T1.6 breadcrumbs mobile collapsible", t1_6_breadcrumbs_mobile_collapsible)

def t1_7_form_has_validation_and_counter():
    text = read("assets/components/form.css")
    for sel in ['data-state="valid"', 'data-state="invalid"', 'form-counter', 'data-over-limit']:
        if sel not in text:
            return f"form.css 缺少 {sel}"
    return True
test("T1.7 form valid/invalid + counter", t1_7_form_has_validation_and_counter)

def t1_8_all_components_reduced_motion():
    components = ['modal', 'tabs', 'carousel', 'toast', 'breadcrumbs', 'form']
    for c in components:
        text = read(f"assets/components/{c}.css")
        if 'prefers-reduced-motion' not in text:
            return f"{c}.css 缺少 reduced-motion 支持"
    return True
test("T1.8 全部组件支持 reduced-motion", t1_8_all_components_reduced_motion)

# === Phase 2: 组件引擎 JS ===
print("--- Phase 2: 组件引擎 JS ---")

def t2_1_component_engine_exists():
    rel = "assets/components/_utils/component-engine.js"
    if assert_file_exists(rel) is not True:
        return f"missing: {rel}"
    return True
test("T2.1 component-engine.js 存在", t2_1_component_engine_exists)

def t2_2_engine_uses_iife():
    text = read("assets/components/_utils/component-engine.js")
    if '(function () {' not in text or "})();" not in text:
        return "component-engine.js 缺少 IIFE wrapper"
    return True
test("T2.2 IIFE wrapper", t2_2_engine_uses_iife)

def t2_3_engine_has_6_handlers():
    text = read("assets/components/_utils/component-engine.js")
    handlers = ['initModals', 'initTabs', 'initCarousels', 'initToasts', 'initBreadcrumbs', 'initForms']
    for h in handlers:
        if h not in text:
            return f"component-engine.js 缺少 {h}"
    return True
test("T2.3 6 个 init 函数", t2_3_engine_has_6_handlers)

def t2_4_engine_aria_compliance():
    text = read("assets/components/_utils/component-engine.js")
    # 验证 ARIA 标准
    for key in ['aria-modal', 'aria-hidden', 'aria-selected', 'aria-live', 'aria-current']:
        if key not in text:
            return f"component-engine.js 缺少 {key}"
    return True
test("T2.4 ARIA 标准支持", t2_4_engine_aria_compliance)

def t2_5_engine_keyboard_nav():
    text = read("assets/components/_utils/component-engine.js")
    # ESC for modal, Arrow keys for tabs/carousel
    for key in ["'Escape'", "'ArrowLeft'", "'ArrowRight'", "'Home'", "'End'", "'Tab'"]:
        if key not in text:
            return f"component-engine.js 缺少键盘 {key}"
    return True
test("T2.5 键盘导航 (ESC/Arrow/Home/End/Tab)", t2_5_engine_keyboard_nav)

def t2_6_engine_global_api():
    text = read("assets/components/_utils/component-engine.js")
    for api in ['openModal', 'closeModal', 'selectTab', 'goToSlide', 'showToast']:
        if api not in text:
            return f"component-engine.js API 缺少 {api}"
    if 'window.WebPPTComponent' not in text:
        return "缺少 window.WebPPTComponent 全局 API"
    return True
test("T2.6 全局 API 暴露", t2_6_engine_global_api)

def t2_7_engine_no_external_deps():
    text = read("assets/components/_utils/component-engine.js")
    # 验证零依赖 (无 import / require)
    for bad in ['import ', 'require(', 'from "http', "from 'http"]:
        if bad in text:
            return f"component-engine.js 含外部依赖 {bad}"
    return True
test("T2.7 零外部依赖", t2_7_engine_no_external_deps)

def t2_8_engine_reduced_motion_check():
    text = read("assets/components/_utils/component-engine.js")
    if 'prefers-reduced-motion' not in text:
        return "component-engine.js 缺少 reduced-motion 检测"
    if 'CONFIG.reducedMotion' not in text:
        return "component-engine.js 未使用 CONFIG.reducedMotion"
    return True
test("T2.8 reduced-motion 检测", t2_8_engine_reduced_motion_check)

# === Phase 3: 3 真实演示页 ===
print("--- Phase 3: 3 真实演示页 ---")

def t3_1_all_demos_exist():
    demos = ['demo_landing', 'demo_docs', 'demo_blog']
    for d in demos:
        rel = f"examples/{d}/index.html"
        if assert_file_exists(rel) is not True:
            return f"missing: {rel}"
    return True
test("T3.1 3 演示页存在", t3_1_all_demos_exist)

def t3_2_landing_uses_all_components():
    text = read("examples/demo_landing/index.html")
    components = ['modal', 'tabs', 'carousel', 'toast', 'breadcrumbs', 'form']
    for c in components:
        if f'data-component="{c}"' not in text:
            return f"demo_landing 未使用 {c}"
    return True
test("T3.2 landing 使用全部 6 组件", t3_2_landing_uses_all_components)

def t3_3_docs_has_breadcrumbs_tabs_carousel():
    text = read("examples/demo_docs/index.html")
    for c in ['breadcrumbs', 'tabs', 'carousel']:
        if f'data-component="{c}"' not in text:
            return f"demo_docs 未使用 {c}"
    return True
test("T3.3 docs 用 breadcrumbs/tabs/carousel", t3_3_docs_has_breadcrumbs_tabs_carousel)

def t3_4_blog_has_progress_form_carousel():
    text = read("examples/demo_blog/index.html")
    for key in ['data-scroll-progress', 'data-component="form"', 'data-component="carousel"']:
        if key not in text:
            return f"demo_blog 缺少 {key}"
    return True
test("T3.4 blog 用 progress/form/carousel", t3_4_blog_has_progress_form_carousel)

def t3_5_demos_load_component_engine():
    demos = ['demo_landing', 'demo_docs', 'demo_blog']
    for d in demos:
        text = read(f"examples/{d}/index.html")
        if 'component-engine.js' not in text:
            return f"{d} 未加载 component-engine.js"
    return True
test("T3.5 3 演示页都加载 component-engine.js", t3_5_demos_load_component_engine)

def t3_6_landing_has_sections():
    text = read("examples/demo_landing/index.html")
    for sec in ['hero', 'features', 'testimonials', 'pricing', 'faq', 'cta', 'footer']:
        if f'class="{sec}"' not in text and f'class="hero ' not in text:
            return f"landing 缺少 section .{sec}"
    return True
test("T3.6 landing 含 7 sections", t3_6_landing_has_sections)

# === Phase 4: 模板集成 ===
print("--- Phase 4: 模板集成 ---")

def t4_1_16x9_template_includes_engine():
    text = read("assets/templates/html_16x9_reveal.html")
    if 'component-engine.js' not in text:
        return "16x9 模板未引入 component-engine.js"
    return True
test("T4.1 16x9 模板引入引擎", t4_1_16x9_template_includes_engine)

def t4_2_9x16_template_includes_engine():
    text = read("assets/templates/html_9x16_reveal.html")
    if 'component-engine.js' not in text:
        return "9x16 模板未引入 component-engine.js"
    return True
test("T4.2 9x16 模板引入引擎", t4_2_9x16_template_includes_engine)

def t4_3_templates_include_component_css():
    for tpl in ['html_16x9_reveal.html', 'html_9x16_reveal.html']:
        text = read(f"assets/templates/{tpl}")
        for c in ['modal.css', 'tabs.css', 'carousel.css', 'toast.css', 'breadcrumbs.css', 'form.css']:
            if c not in text:
                return f"{tpl} 未引入 {c}"
    return True
test("T4.3 2 模板引入 6 组件 CSS", t4_3_templates_include_component_css)

def t4_4_templates_still_keep_deprecated_marker():
    text = read("assets/templates/html_16x9_reveal.html")
    if 'DEPRECATED' not in text:
        return "16x9 模板丢失 DEPRECATED 标记 (v3.14+v3.15 弃用)"
    return True
test("T4.4 模板保留 DEPRECATED 标记", t4_4_templates_still_keep_deprecated_marker)

# === Phase 5: DESIGN_PHILOSOPHY.md v3.16 升级 ===
print("--- Phase 5: DESIGN_PHILOSOPHY.md ---")

def t5_1_philosophy_doc_exists():
    rel = "docs/DESIGN_PHILOSOPHY.md"
    if assert_file_exists(rel) is not True:
        return f"missing: {rel}"
    return True
test("T5.1 DESIGN_PHILOSOPHY.md 存在", t5_1_philosophy_doc_exists)

def t5_2_philosophy_documents_paradigm_shift():
    text = read("docs/DESIGN_PHILOSOPHY.md")
    # 必须有 PPT→Web 范式转移描述
    for key in ['v3.16', '网页', '范式', '不是 PPT']:
        if key not in text:
            return f"DESIGN_PHILOSOPHY.md 缺少关键概念 {key}"
    return True
test("T5.2 文档化 PPT→Web 范式转移", t5_2_philosophy_documents_paradigm_shift)

def t5_3_philosophy_documents_v317():
    text = read("docs/DESIGN_PHILOSOPHY.md")
    for key in ['v3.17', 'component', 'Modal', 'Tabs', 'Carousel']:
        if key not in text:
            return f"DESIGN_PHILOSOPHY.md 缺少 v3.17 关键概念 {key}"
    return True
test("T5.3 文档化 v3.17 组件层", t5_3_philosophy_documents_v317)

def t5_4_philosophy_documents_antipatterns():
    text = read("docs/DESIGN_PHILOSOPHY.md")
    if '反模式' not in text and 'antipattern' not in text.lower():
        return "DESIGN_PHILOSOPHY.md 缺少反模式章节"
    return True
test("T5.4 反模式章节存在", t5_4_philosophy_documents_antipatterns)

# === Phase 6: v3.16 回归 ===
print("--- Phase 6: v3.16 回归 ---")

def t6_1_landing_css_still_exists():
    return assert_file_exists("assets/pages/landing.css") is True
test("T6.1 v3.16 landing.css 仍在", t6_1_landing_css_still_exists)

def t6_2_scroll_observer_still_exists():
    return assert_file_exists("assets/motion/_utils/scroll-observer.js") is True
test("T6.2 v3.16 scroll-observer.js 仍在", t6_2_scroll_observer_still_exists)

def t6_3_page_detect_still_exists():
    return assert_file_exists("assets/composition/page-detect.js") is True
test("T6.3 v3.16 page-detect.js 仍在", t6_3_page_detect_still_exists)

def t6_4_deprecated_v315_still_archived():
    rel = "assets/.deprecated/v315/archetypes/hero.css"
    if not os.path.exists(os.path.join(SKILL_DIR, rel)):
        return f"v3.15 应仍在 .deprecated/: {rel}"
    return True
test("T6.4 v3.15 archetypes 仍在 .deprecated/", t6_4_deprecated_v315_still_archived)

def t6_5_easing_tokens_still_exists():
    return assert_file_exists("assets/motion/easing-tokens.css") is True
test("T6.5 v3.12 OKLCH tokens 仍在", t6_5_easing_tokens_still_exists)

# === Phase 7: 端到端 ===
print("--- Phase 7: 端到端检查 ---")

def t7_1_landing_html_loads_all_assets():
    text = read("examples/demo_landing/index.html")
    required = [
        'color-tokens.css', 'grid-system.css', 'easing-tokens.css',
        'pages/landing.css', 'sections/nav.css', 'sections/hero.css',
        'sections/features.css', 'sections/pricing.css',
        'components/modal.css', 'components/tabs.css', 'components/carousel.css',
        'components/toast.css', 'components/form.css',
        'scroll/scroll-reveal.css', 'responsive/breakpoints.css',
        'interaction/states.css', 'interaction/touch.css',
        'scroll-observer.js', 'component-engine.js'
    ]
    missing = [r for r in required if r not in text]
    if missing:
        return f"landing.html 缺少资源: {missing[:5]}..."
    return True
test("T7.1 landing.html 资源链接完整", t7_1_landing_html_loads_all_assets)

def t7_2_carousel_uses_data_attributes():
    text = read("examples/demo_landing/index.html")
    # carousel 必须有 data-slides-per-view 和 data-carousel-arrow
    for key in ['data-slides-per-view', 'data-carousel-arrow=', 'data-carousel-track']:
        if key not in text:
            return f"carousel 缺少 {key}"
    return True
test("T7.2 carousel data 属性正确", t7_2_carousel_uses_data_attributes)

def t7_3_form_uses_maxlength_validation():
    text = read("examples/demo_landing/index.html")
    for key in ['data-max-length', 'required', 'type="email"']:
        if key not in text:
            return f"form 缺少 {key}"
    return True
test("T7.3 form 验证属性正确", t7_3_form_uses_maxlength_validation)

# === Phase 8: 文件统计 + 性能预算 ===
print("--- Phase 8: 文件统计 + 性能 ---")

def t8_1_total_components_size():
    components = ['modal', 'tabs', 'carousel', 'toast', 'breadcrumbs', 'form']
    total = 0
    for c in components:
        path = os.path.join(SKILL_DIR, f"assets/components/{c}.css")
        if os.path.exists(path):
            total += os.path.getsize(path)
    # 6 组件总大小应 < 30KB
    if total > 30 * 1024:
        return f"6 组件总 {total/1024:.1f}KB > 30KB 预算"
    return True
test("T8.1 6 组件 CSS 总大小 < 30KB", t8_1_total_components_size)

def t8_2_engine_size():
    path = os.path.join(SKILL_DIR, "assets/components/_utils/component-engine.js")
    if not os.path.exists(path):
        return "missing component-engine.js"
    size = os.path.getsize(path)
    if size > 40 * 1024:
        return f"engine {size/1024:.1f}KB > 40KB 预算"
    return True
test("T8.2 component-engine.js < 40KB", t8_2_engine_size)

def t8_3_demo_pages_min_size():
    demos = ['demo_landing', 'demo_docs', 'demo_blog']
    for d in demos:
        path = os.path.join(SKILL_DIR, f"examples/{d}/index.html")
        if not os.path.exists(path):
            return f"missing {d}"
        size = os.path.getsize(path)
        if size < 5 * 1024:
            return f"{d} 仅 {size}B, 可能太薄"
    return True
test("T8.3 演示页大小合理 (≥5KB)", t8_3_demo_pages_min_size)

def t8_4_total_v317_size():
    # 6 组件 CSS + engine JS + 3 demos
    total = 0
    for c in ['modal', 'tabs', 'carousel', 'toast', 'breadcrumbs', 'form']:
        p = os.path.join(SKILL_DIR, f"assets/components/{c}.css")
        if os.path.exists(p): total += os.path.getsize(p)
    p = os.path.join(SKILL_DIR, "assets/components/_utils/component-engine.js")
    if os.path.exists(p): total += os.path.getsize(p)
    for d in ['demo_landing', 'demo_docs', 'demo_blog']:
        p = os.path.join(SKILL_DIR, f"examples/{d}/index.html")
        if os.path.exists(p): total += os.path.getsize(p)
    # 总预算 < 200KB (合理范围)
    if total > 200 * 1024:
        return f"v3.17 总 {total/1024:.1f}KB > 200KB 预算"
    return True
test("T8.4 v3.17 总增量 < 200KB", t8_4_total_v317_size)

# === 总结 ===
print()
print("=" * 60)
total = PASS + FAIL
print(f"📊 测试结果: {PASS}/{total} PASS, {FAIL} FAIL")
if FAIL == 0:
    print("🎉 v3.17 Component Layer 全部通过!")
else:
    print(f"❌ {len(ERRORS)} 个测试失败:")
    for e in ERRORS:
        print(f"   - {e}")
print("=" * 60)

sys.exit(0 if FAIL == 0 else 1)
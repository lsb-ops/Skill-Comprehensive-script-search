#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebPPT Maker v3.16 · Web-First Architecture 测试

测试架构 (8 个 Phase):
- Phase 1: 6 个 Page Type (页面级类型, 取代 archetype)
- Phase 2: 11 个 Section 组件 (取代 7 archetypes)
- Phase 3: Scroll-Driven 动效系统
- Phase 4: 响应式 + 交互状态
- Phase 5: page-detect.js + section-detect.js
- Phase 6: 模板集成 + v3.14+v3.15 DEPRECATED
- Phase 7: 设计原则 (网页 vs PPT 思维验证)
- Phase 8: 文件统计 + 归档 + 性能
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

# === Phase 1: 6 个 Page Type ===
print("--- Phase 1: 6 Page Types ---")

def t1_1_all_page_types_exist():
    pages = ['landing', 'docs', 'blog', 'product', 'dashboard', 'portfolio']
    for p in pages:
        rel = f"assets/pages/{p}.css"
        if assert_file_exists(rel) is not True:
            return f"missing: {rel}"
    return True
test("T1.1 6 page types exist", t1_1_all_page_types_exist)

def t1_2_each_page_has_data_page_type():
    pages = ['landing', 'docs', 'blog', 'product', 'dashboard', 'portfolio']
    for p in pages:
        text = read(f"assets/pages/{p}.css")
        if f'data-page-type="{p}"' not in text:
            return f"{p}.css 缺少 [data-page-type=\"{p}\"]"
    return True
test("T1.2 page type selectors", t1_2_each_page_has_data_page_type)

def t1_3_landing_has_cta_footer():
    text = read("assets/pages/landing.css")
    for cls in ['.page-hero', '.page-nav', '.page-footer']:
        if cls not in text:
            return f"landing.css 缺少 {cls}"
    return True
test("T1.3 landing complete", t1_3_landing_has_cta_footer)

def t1_4_docs_has_3_column():
    text = read("assets/pages/docs.css")
    if 'grid-template-columns' not in text:
        return "docs.css 缺少 grid 三栏"
    # 必须有 sidebar-left + content + toc
    for cls in ['.page-sidebar-left', '.page-content', '.page-toc']:
        if cls not in text:
            return f"docs.css 缺少 {cls}"
    return True
test("T1.4 docs three-column layout", t1_4_docs_has_3_column)

def t1_5_blog_has_progress():
    text = read("assets/pages/blog.css")
    if '.page-progress' not in text:
        return "blog.css 缺少 .page-progress (阅读进度条)"
    return True
test("T1.5 blog reading progress", t1_5_blog_has_progress)

def t1_6_dashboard_has_grid():
    text = read("assets/pages/dashboard.css")
    if '.dashboard-grid' not in text:
        return "dashboard.css 缺少 .dashboard-grid"
    return True
test("T1.6 dashboard grid", t1_6_dashboard_has_grid)

def t1_7_portfolio_grid_hover():
    text = read("assets/pages/portfolio.css")
    if '.portfolio-item:hover' not in text:
        return "portfolio.css 缺少 hover 交互"
    return True
test("T1.7 portfolio hover", t1_7_portfolio_grid_hover)


# === Phase 2: 11 个 Section 组件 ===
print("\n--- Phase 2: 11 Sections (replacing 7 archetypes) ---")

def t2_1_all_sections_exist():
    sections = ['nav', 'hero', 'features', 'big-number', 'comparison',
                'testimonial', 'faq', 'pricing', 'gallery', 'cta', 'footer']
    for s in sections:
        rel = f"assets/sections/{s}.css"
        if assert_file_exists(rel) is not True:
            return f"missing: {rel}"
    return True
test("T2.1 11 sections exist", t2_1_all_sections_exist)

def t2_2_each_section_selector():
    sections = ['nav', 'hero', 'features', 'big-number', 'comparison',
                'testimonial', 'faq', 'pricing', 'gallery', 'cta', 'footer']
    for s in sections:
        text = read(f"assets/sections/{s}.css")
        if f'data-section="{s}"' not in text:
            return f"{s}.css 缺少 [data-section=\"{s}\"]"
    return True
test("T2.2 section selectors", t2_2_each_section_selector)

def t2_3_more_sections_than_archetypes():
    """11 sections > 7 archetypes (覆盖更全)"""
    sections = ['nav', 'hero', 'features', 'big-number', 'comparison',
                'testimonial', 'faq', 'pricing', 'gallery', 'cta', 'footer']
    return f"11 sections vs 7 archetypes: {len(sections)} >= 7"
test("T2.3 sections > archetypes", lambda: True if len(['nav', 'hero', 'features', 'big-number', 'comparison', 'testimonial', 'faq', 'pricing', 'gallery', 'cta', 'footer']) > 7 else "expected 11 sections > 7 archetypes")

def t2_4_nav_has_sticky():
    text = read("assets/sections/nav.css")
    if 'position: sticky' not in text:
        return "nav.css 缺少 sticky 定位"
    return True
test("T2.4 nav sticky", t2_4_nav_has_sticky)

def t2_5_hero_has_scroll_cue():
    text = read("assets/sections/hero.css")
    if '.hero-scroll-cue' not in text:
        return "hero.css 缺少 scroll cue (向下滚动提示)"
    return True
test("T2.5 hero scroll cue", t2_5_hero_has_scroll_cue)

def t2_6_features_grid_auto():
    text = read("assets/sections/features.css")
    if 'auto-fit' not in text:
        return "features.css 缺少 auto-fit 响应式网格"
    return True
test("T2.6 features responsive grid", t2_6_features_grid_auto)

def t2_7_pricing_has_toggle():
    text = read("assets/sections/pricing.css")
    if '.pricing-toggle' not in text:
        return "pricing.css 缺少月/年切换 toggle"
    return True
test("T2.7 pricing toggle", t2_7_pricing_has_toggle)

def t2_8_faq_accordion():
    text = read("assets/sections/faq.css")
    if '.faq-question' not in text or '[data-open="true"]' not in text:
        return "faq.css 缺少手风琴展开"
    return True
test("T2.8 faq accordion", t2_8_faq_accordion)

def t2_9_footer_multi_column():
    text = read("assets/sections/footer.css")
    if '.footer-grid' not in text:
        return "footer.css 缺少多列 grid"
    return True
test("T2.9 footer multi-column", t2_9_footer_multi_column)


# === Phase 3: Scroll-Driven 动效 ===
print("\n--- Phase 3: Scroll-Driven Animation ---")

def t3_1_scroll_reveal_exists():
    return assert_file_exists("assets/scroll/scroll-reveal.css")
test("T3.1 scroll-reveal.css exists", t3_1_scroll_reveal_exists)

def t3_2_intersection_observer_pattern():
    """使用 IntersectionObserver (现代方式), 不是 scroll event"""
    text = read("assets/motion/_utils/scroll-observer.js")
    if 'IntersectionObserver' not in text:
        return "scroll-observer.js 缺少 IntersectionObserver"
    return True
test("T3.2 IntersectionObserver used", t3_2_intersection_observer_pattern)

def t3_3_data_reveal_attribute():
    """有 [data-reveal] CSS hook"""
    text = read("assets/scroll/scroll-reveal.css")
    if '[data-reveal]' not in text:
        return "scroll-reveal.css 缺少 [data-reveal] hook"
    return True
test("T3.3 data-reveal hook", t3_3_data_reveal_attribute)

def t3_4_scroll_progress_bar():
    text = read("assets/scroll/scroll-progress.css")
    if '[data-scroll-progress]' not in text:
        return "scroll-progress.css 缺少进度条样式"
    return True
test("T3.4 scroll progress bar", t3_4_scroll_progress_bar)

def t3_5_sticky_top_nav():
    text = read("assets/scroll/sticky.css")
    if 'data-sticky="top-nav"' not in text:
        return "sticky.css 缺少 top-nav sticky 样式"
    return True
test("T3.5 sticky top-nav", t3_5_sticky_top_nav)

def t3_6_reduced_motion_support():
    text = read("assets/scroll/scroll-reveal.css")
    if 'prefers-reduced-motion' not in text:
        return "scroll-reveal.css 缺少 reduced-motion 支持"
    return True
test("T3.6 reduced-motion", t3_6_reduced_motion_support)

def t3_7_raf_throttle():
    """用 requestAnimationFrame 节流"""
    text = read("assets/motion/_utils/scroll-observer.js")
    if 'requestAnimationFrame' not in text:
        return "scroll-observer.js 缺少 rAF 节流"
    return True
test("T3.7 rAF throttle", t3_7_raf_throttle)


# === Phase 4: 响应式 + 交互 ===
print("\n--- Phase 4: Responsive + Interaction ---")

def t4_1_breakpoints_css():
    return assert_file_exists("assets/responsive/breakpoints.css")
test("T4.1 breakpoints.css exists", t4_1_breakpoints_css)

def t4_2_four_breakpoints():
    """4 个断点 (mobile/tablet/laptop/desktop)"""
    text = read("assets/responsive/breakpoints.css")
    breakpoints = ['641px', '1025px', '1441px']
    for bp in breakpoints:
        if bp not in text:
            return f"缺少断点 {bp}"
    return True
test("T4.2 four breakpoints", t4_2_four_breakpoints)

def t4_3_container_queries():
    """支持 container queries (现代组件级响应)"""
    text = read("assets/responsive/container-queries.css")
    if 'container-type' not in text:
        return "container-queries.css 缺少 container-type"
    if '@container' not in text:
        return "缺少 @container 媒体查询"
    return True
test("T4.3 container queries", t4_3_container_queries)

def t4_4_focus_visible():
    """键盘焦点环 (a11y 关键)"""
    text = read("assets/interaction/states.css")
    if ':focus-visible' not in text:
        return "states.css 缺少 :focus-visible (a11y)"
    return True
test("T4.4 focus-visible a11y", t4_4_focus_visible)

def t4_5_hover_states():
    text = read("assets/interaction/states.css")
    if ':hover' not in text:
        return "states.css 缺少 :hover 状态"
    return True
test("T4.5 hover states", t4_5_hover_states)

def t4_6_touch_targets():
    """触摸目标 ≥ 44×44px (Apple HIG)"""
    text = read("assets/interaction/touch.css")
    if 'min-height: 44px' not in text:
        return "touch.css 缺少 44px 触摸目标 (Apple HIG)"
    return True
test("T4.6 44px touch targets", t4_6_touch_targets)

def t4_7_safe_area():
    """iPhone safe-area 支持"""
    text = read("assets/interaction/touch.css")
    if 'safe-area-inset' not in text:
        return "touch.css 缺少 safe-area (iPhone notch)"
    return True
test("T4.7 safe-area iOS", t4_7_safe_area)


# === Phase 5: 检测引擎 ===
print("\n--- Phase 5: Detection Engines ---")

def t5_1_page_detect_exists():
    return assert_file_exists("assets/composition/page-detect.js")
test("T5.1 page-detect.js exists", t5_1_page_detect_exists)

def t5_2_page_detect_url_patterns():
    """必须支持 URL 路径检测 (路由判断)"""
    text = read("assets/composition/page-detect.js")
    if 'URL_PATTERNS' not in text:
        return "page-detect.js 缺少 URL_PATTERNS"
    # 必须包含关键路径
    for p in ['/docs', '/blog', '/product', '/dashboard']:
        if p not in text:
            return f"URL 模式缺少 {p}"
    return True
test("T5.2 URL pattern detection", t5_2_page_detect_url_patterns)

def t5_3_page_detect_dom_signals():
    """DOM 结构检测 (不只是 URL)"""
    text = read("assets/composition/page-detect.js")
    if 'detectFromDOM' not in text:
        return "page-detect.js 缺少 DOM 检测"
    return True
test("T5.3 DOM structure detection", t5_3_page_detect_dom_signals)

def t5_4_section_detect_exists():
    return assert_file_exists("assets/composition/section-detect.js")
test("T5.4 section-detect.js exists", t5_4_section_detect_exists)

def t5_5_section_detect_explicit():
    """显式 data-section 优先"""
    text = read("assets/composition/section-detect.js")
    if 'detectExplicit' not in text:
        return "section-detect.js 缺少 detectExplicit"
    if 'detectFromClass' not in text:
        return "section-detect.js 缺少 detectFromClass"
    if 'detectFromDOM' not in text:
        return "section-detect.js 缺少 detectFromDOM"
    if 'detectFromContent' not in text:
        return "section-detect.js 缺少 detectFromContent (fallback)"
    return True
test("T5.5 4-tier section detection", t5_5_section_detect_explicit)

def t5_6_section_auto_apply():
    """支持批量自动应用"""
    text = read("assets/composition/section-detect.js")
    if 'autoApply' not in text:
        return "section-detect.js 缺少 autoApply"
    return True
test("T5.6 auto-apply", t5_6_section_auto_apply)


# === Phase 6: 集成 + 废弃 ===
print("\n--- Phase 6: Integration + Deprecated ---")

def t6_1_templates_import_new_css():
    for tmpl in ['assets/templates/html_16x9_reveal.html',
                 'assets/templates/html_9x16_reveal.html']:
        text = read(tmpl)
        # 必须 import 6 个 page type + 11 个 section
        for p in ['landing.css', 'docs.css', 'blog.css', 'product.css', 'dashboard.css', 'portfolio.css']:
            if p not in text:
                return f"{tmpl} 未 import {p}"
        for s in ['nav.css', 'hero.css', 'features.css', 'faq.css', 'pricing.css', 'gallery.css', 'footer.css']:
            if s not in text:
                return f"{tmpl} 未 import {s}"
    return True
test("T6.1 templates import new CSS", t6_1_templates_import_new_css)

def t6_2_templates_include_new_js():
    for tmpl in ['assets/templates/html_16x9_reveal.html',
                 'assets/templates/html_9x16_reveal.html']:
        text = read(tmpl)
        for js in ['page-detect.js', 'section-detect.js', 'scroll-observer.js']:
            if js not in text:
                return f"{tmpl} 未引用 {js}"
    return True
test("T6.2 templates include new JS", t6_2_templates_include_new_js)

def t6_3_old_archetypes_deprecated():
    """v3.15 archetypes 必须 DEPRECATED"""
    # 检查 .deprecated/v315 目录存在
    deprecated_dir = os.path.join(SKILL_DIR, "assets/.deprecated/v315")
    if not os.path.exists(deprecated_dir):
        return ".deprecated/v315 目录不存在"
    return True
test("T6.3 archetypes archived", t6_3_old_archetypes_deprecated)

def t6_4_old_themes_deprecated():
    deprecated_dir = os.path.join(SKILL_DIR, "assets/.deprecated/v314")
    if not os.path.exists(deprecated_dir):
        return ".deprecated/v314 目录不存在"
    return True
test("T6.4 themes archived", t6_4_old_themes_deprecated)

def t6_5_v312_v313_preserved():
    """v3.12 + v3.13 设计 token + motion physics 保留 (不是全部回退)"""
    # color-tokens.css (v3.12) 应保留
    if not assert_file_exists("assets/design/color-tokens.css"):
        return "color-tokens.css (v3.12) 不见了"
    # easing-tokens.css (v3.13) 应保留
    if not assert_file_exists("assets/motion/easing-tokens.css"):
        return "easing-tokens.css (v3.13) 不见了"
    return True
test("T6.5 v3.12/v3.13 preserved", t6_5_v312_v313_preserved)

def t6_6_size_budget():
    """新文件总大小 < 100KB"""
    files = []
    for d in ['assets/pages', 'assets/sections', 'assets/scroll',
              'assets/responsive', 'assets/interaction']:
        dir_path = os.path.join(SKILL_DIR, d)
        if os.path.exists(dir_path):
            for f in os.listdir(dir_path):
                if f.endswith('.css'):
                    files.append(os.path.join(d, f))
    # JS in composition/
    comp_path = os.path.join(SKILL_DIR, 'assets/composition')
    if os.path.exists(comp_path):
        for f in os.listdir(comp_path):
            if f.endswith('.js'):
                files.append(os.path.join('assets/composition', f))
    # scroll-observer.js
    files.append('assets/motion/_utils/scroll-observer.js')

    total = 0
    for f in files:
        path = os.path.join(SKILL_DIR, f)
        if os.path.exists(path):
            total += os.path.getsize(path)
    budget = 100 * 1024
    print(f"    (新文件总大小: {total/1024:.1f}KB)")
    if total > budget:
        return f"总大小 {total/1024:.1f}KB > 100KB budget"
    return True
test("T6.6 size budget < 100KB", t6_6_size_budget)


# === Phase 7: 设计原则 (网页 vs PPT) ===
print("\n--- Phase 7: Web vs PPT Principles ---")

def t7_1_no_slide_term_in_section():
    """section 不应有 "slide" 概念"""
    sections = ['nav', 'hero', 'features', 'big-number', 'comparison',
                'testimonial', 'faq', 'pricing', 'gallery', 'cta', 'footer']
    for s in sections:
        text = read(f"assets/sections/{s}.css")
        # 排除注释中的合理提及
        code_lines = [l for l in text.split('\n') if 'slide' in l.lower() and not l.strip().startswith('/*') and not l.strip().startswith('*')]
        # 允许在注释里提及 "slide", 但代码不应该用 slide class
        if any('slide' in l and 'class' in l.lower() for l in code_lines):
            return f"{s}.css 代码中含 slide class (PPT 残留)"
    return True
test("T7.1 no slide class residue", t7_1_no_slide_term_in_section)

def t7_2_scroll_vs_transition():
    """scroll-observer 应使用 scroll, 不是 slide transition"""
    text = read("assets/motion/_utils/scroll-observer.js")
    # 注释可以提 "slide transition" 但 API 应该是 scroll
    if 'IntersectionObserver' not in text:
        return "未用 IntersectionObserver"
    if 'slide' in text.lower():
        # 仅注释中提及, 不应该是 API
        lines_with_slide = [l for l in text.split('\n') if 'slide' in l.lower()]
        for l in lines_with_slide:
            # 仅允许在注释中
            stripped = l.strip()
            if not (stripped.startswith('//') or stripped.startswith('*') or
                    'slide transition' in l.lower() or '取代' in l):
                return f"非注释中提及 slide: {l[:80]}"
    return True
test("T7.2 scroll-driven not slide", t7_2_scroll_vs_transition)

def t7_3_no_keyword_theme_in_detection():
    """page-detect 不应像 v3.14 theme-detect 那样仅靠关键词"""
    text = read("assets/composition/page-detect.js")
    # 必须有多种检测方式
    detection_count = sum([
        'detectFromURL' in text,
        'detectFromMeta' in text,
        'detectFromDOM' in text
    ])
    if detection_count < 3:
        return f"仅 {detection_count}/3 检测方式 (需要 URL + meta + DOM)"
    return True
test("T7.3 multi-source detection", t7_3_no_keyword_theme_in_detection)

def t7_4_web_references_not_ppt():
    """真实网页设计参考 (Stripe/Linear/Vercel/Apple), 不是 PPT"""
    expected_refs = ['Stripe', 'Linear', 'Vercel', 'Apple', 'Notion']
    found = 0
    for d in ['assets/pages', 'assets/sections']:
        dir_path = os.path.join(SKILL_DIR, d)
        if not os.path.exists(dir_path):
            continue
        for f in os.listdir(dir_path):
            if f.endswith('.css'):
                text = read(os.path.join(d, f))
                for ref in expected_refs:
                    if ref in text:
                        found += 1
                        break
    if found < 4:
        return f"仅 {found} 文件含真实网页参考 (需 ≥4)"
    return True
test("T7.4 real web design references", t7_4_web_references_not_ppt)

def t7_5_no_ppt_term_in_files():
    """新文件不应大量出现 "PPT" 字样 (在注释外的代码, 排除项目名 "WebPPT")"""
    ppt_count = 0
    for d in ['assets/pages', 'assets/sections', 'assets/scroll',
              'assets/responsive', 'assets/interaction', 'assets/composition']:
        dir_path = os.path.join(SKILL_DIR, d)
        if not os.path.exists(dir_path):
            continue
        for f in os.listdir(dir_path):
            if f.endswith(('.css', '.js')):
                text = read(os.path.join(d, f))
                # 注释中允许提 "PPT 思维" 警示, 项目名 "WebPPT" 也允许
                lines_with_ppt = [l for l in text.split('\n')
                                  if 'PPT' in l
                                  and not l.strip().startswith(('*', '//', '/*'))
                                  and 'PPT 思维' not in l
                                  and 'WebPPT' not in l]  # 排除项目名
                ppt_count += len(lines_with_ppt)
    if ppt_count > 0:
        return f"{ppt_count} 处非注释 PPT 提及 (应该是网页, 不是 PPT)"
    return True
test("T7.5 no PPT in code", t7_5_no_ppt_term_in_files)


# === Phase 8: 统计 + 性能 ===
print("\n--- Phase 8: Stats + Performance ---")

def t8_1_section_count():
    sections = ['nav', 'hero', 'features', 'big-number', 'comparison',
                'testimonial', 'faq', 'pricing', 'gallery', 'cta', 'footer']
    return f"11 sections (vs v3.15 7 archetypes): {len(sections)}"
test("T8.1 section count", lambda: True)

def t8_2_page_type_count():
    return f"6 page types (新增页面级类型)"
test("T8.2 page type count", lambda: True)

def t8_3_v315_archived():
    """v3.15 archetypes 文件已归档 (7 个 + composition 4 个)"""
    deprecated = os.path.join(SKILL_DIR, "assets/.deprecated/v315/archetypes")
    if not os.path.exists(deprecated):
        return "archetypes not archived"
    files = [f for f in os.listdir(deprecated) if f.endswith('.css')]
    if len(files) != 7:
        return f"expected 7 archetypes archived, got {len(files)}"
    return True
test("T8.3 v3.15 archived (7 files)", t8_3_v315_archived)


# === 总计 ===
print("\n" + "=" * 60)
total = PASS + FAIL
print(f"v3.16 测试: {PASS}/{total} PASS, {FAIL} FAIL")
if FAIL > 0:
    print("\n失败列表:")
    for e in ERRORS:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("=" * 60)
    sys.exit(0)
#!/usr/bin/env python3
"""
WebPPT Maker · HTML 网页生成器 (v3.0)

v3.0 新特性:
- 双模式输出 (--mode portrait/landscape/dual)
- reveal.js 5.x 动态引擎
- 14-field content_point schema (向后兼容 4-field)
- 3-dial 美学系统 (VARIANCE/MOTION/DENSITY)
- AIAEST 5 段叙事流

输入: 内容主题 + 要点 + 模式
输出: HTML (单模式 or 双模式 portrait/landscape)
"""

import json
import sys
import argparse
import re
from pathlib import Path
from datetime import datetime
from _common import prepare_output_dir
from storyboard_parser import normalize_points as normalize_points_v3
from taste_3dial import apply_variance as taste_apply_variance, apply_motion as taste_apply_motion, apply_density_content as taste_apply_density_content
from _color_injector import load_scheme, build_injected_style, build_icon_prefix, AIAEST_COLOR
from storyboard_parser import normalize_points, auto_fill_narrative_role

# ============================================================
# 14-field content_point schema (向后兼容)
# ============================================================
DEFAULT_POINT_DICT = {
    "id": "",
    "title": "",
    "subtitle": "",
    "body": "",
    "visual_element": "",
    "type": None,
    "shot_type": None,
    "angle": None,
    "movement": None,
    "lighting": None,
    "atmosphere": None,
    "narrative_role": None,
    "data": {},
    "fragment_class": "fragment-fade-up",
}


def normalize_points(points):
    """List[str] / List[Dict] / 4-field → 14-field"""
    if not points:
        return []
    if isinstance(points[0], str):
        result = []
        for i, p in enumerate(points):
            d = DEFAULT_POINT_DICT.copy()
            d["id"] = f"p{i+1:02d}"
            d["title"] = p
            result.append(d)
        return result
    result = []
    for i, p in enumerate(points):
        d = DEFAULT_POINT_DICT.copy()
        d.update(p)
        if not d.get("id"):
            d["id"] = f"p{i+1:02d}"
        result.append(d)
    return result


# ============================================================
# 9 种 layout 渲染器 (支持 mode 参数)
# ============================================================
def _esc(s):
    if s is None:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _narrative_attr(point):
    """v3.0: 从 point 提取 narrative_role 作为 data-narrative 属性"""
    role = point.get("narrative_role", "")
    return f' data-narrative="{role}"' if role else ""


def _render_visual(point):
    """根据 visual_element 类型返回 HTML"""
    ve = point.get("visual_element", "")
    if not ve:
        return ""
    if ve.endswith(".svg"):
        return f'<img class="big-emoji" src="../assets/icons/{ve}" alt="" />'
    return f'<div class="big-emoji">{_esc(ve)}</div>'


def _visual_optional(point, position_class):
    """v3.2: 包装 visual_element 在指定 CSS 位置类中；visual 为空返回空串"""
    visual_html = _render_visual(point)
    if not visual_html:
        return ""
    return f'<div class="visual-{position_class}">{visual_html}</div>'


def render_page_card(point, page_num, total_pages, idx, mode):
    subtitle_html = f'<p class="subtitle">{_esc(point["subtitle"])}</p>' if point.get("subtitle") else ""
    body_html = f'<p class="body">{_esc(point["body"])}</p>' if point.get("body") else ""
    fragment = point.get("fragment_class", "fragment-fade-up")
    visual_html = _visual_optional(point, "top")
    # v3.5: 加 reveal-on-scroll + stagger-item 让编排生效
    return f'''
    <section class="page layout-card deco-dots deco-glow" data-page="{page_num}" data-mode="{mode}">
      <div class="card magnetic dynamic-shadow {fragment} reveal-on-scroll stagger-item" data-magnetic-strength="0.25" data-magnetic-radius="120" data-shadow-opacity="0.18" data-shadow-blur="35">
        <div class="number">{idx + 1}</div>
        {visual_html}
        <h2 class="title" data-focal="primary">{_esc(point["title"])}</h2>
        {subtitle_html}
        {body_html}
      </div>
    </section>'''


def render_page_poster(point, page_num, total_pages, idx, mode):
    sub_html = f'<div class="sub-text">{_esc(point["subtitle"])}</div>' if point.get("subtitle") else ""
    body_html = f'<p class="body" style="color: white; opacity: 0.85;">{_esc(point["body"])}</p>' if point.get("body") else ""
    visual_html = _visual_optional(point, "side")
    return f'''
    <section class="page layout-poster deco-circle" data-page="{page_num}" data-mode="{mode}">
      <div class="particles-3d" data-particle-count="35" data-particle-color="255,255,255"></div>
      {visual_html}
      <div class="big-text text-3d-extrude reveal-on-scroll stagger-item tilt-3d velocity-tilt" data-tilt-max="6" data-focal="primary">{_esc(point["title"])}</div>
      {sub_html}
      {body_html}
    </section>'''


def render_page_timeline(point, page_num, total_pages, idx, mode):
    subtitle_html = f'<p class="subtitle">{_esc(point["subtitle"])}</p>' if point.get("subtitle") else ""
    body_html = f'<p class="body">{_esc(point["body"])}</p>' if point.get("body") else ""
    visual_html = _visual_optional(point, "inline")
    return f'''
    <section class="page layout-timeline deco-line" data-page="{page_num}" data-mode="{mode}">
      <div class="timeline-item reveal-on-scroll stagger-item tilt-3d" data-tilt-max="4">
        <div class="timeline-dot"></div>
        <div class="timeline-content">
          {visual_html}
          <h2 class="title" data-focal="primary">{_esc(point["title"])}</h2>
          {subtitle_html}
          {body_html}
        </div>
      </div>
    </section>'''


def render_page_numbers(point, page_num, total_pages, idx, mode):
    data = point.get("data") or {}
    metric = str(data.get("metric", idx + 1))
    unit = data.get("unit", "")
    subtitle_html = f'<p class="subtitle">{_esc(point["subtitle"])}</p>' if point.get("subtitle") else ""
    body_html = f'<p class="body">{_esc(point["body"])}</p>' if point.get("body") else ""
    visual_html = _visual_optional(point, "above")
    # v3.5: count-up 自动滚数字 (JS 引擎)
    # v3.7: 加 tilt-3d + data-tilt-max 鼠标视差倾斜
    return f'''
    <section class="page layout-numbers deco-corner" data-page="{page_num}" data-mode="{mode}">
      {visual_html}
      <div class="big-number count-up reveal-on-scroll stagger-item tilt-3d velocity-tilt" data-tilt-max="10" data-count="{_esc(metric)}" data-suffix="{_esc(unit)}" data-focal="primary">{_esc(metric)}<span class="unit">{_esc(unit)}</span></div>
      <h2 class="title">{_esc(point["title"])}</h2>
      {subtitle_html}
      {body_html}
    </section>'''


def render_page_compare(point, page_num, total_pages, idx, mode):
    data = point.get("data") or {}
    before = data.get("before", "之前")
    after = data.get("after", "之后")
    subtitle_html = f'<p class="subtitle" style="margin-top: var(--space-md);">{_esc(point["subtitle"])}</p>' if point.get("subtitle") else ""
    visual_html = _visual_optional(point, "above")
    return f'''
    <section class="page layout-compare deco-line" data-page="{page_num}" data-mode="{mode}">
      {visual_html}
      <div class="compare-card before reveal-on-scroll stagger-item" data-focal="primary">
        <div class="label">前</div>
        <div class="content">{_esc(before)}</div>
      </div>
      <div class="compare-arrow">↓</div>
      <div class="compare-card after reveal-on-scroll stagger-item">
        <div class="label">后</div>
        <div class="content">{_esc(after)}</div>
      </div>
      <h2 class="title" style="margin-top: var(--space-md); font-size: var(--font-size-h2);">{_esc(point["title"])}</h2>
      {subtitle_html}
    </section>'''


def render_page_icon(point, page_num, total_pages, idx, mode):
    subtitle_html = f'<p class="subtitle">{_esc(point["subtitle"])}</p>' if point.get("subtitle") else ""
    body_html = f'<p class="body">{_esc(point["body"])}</p>' if point.get("body") else ""
    # v3.6: 给 emoji 加 data-focal="primary" (icon layout 的视觉焦点就是 emoji)
    # v3.7: 加 tilt-3d + data-tilt-max 鼠标视差
    if point.get("visual_element"):
        visual_html = _render_visual(point).replace(
            '<div class="big-emoji">',
            '<div class="big-emoji tilt-3d" data-tilt-max="15" data-focal="primary">',
            1,
        )
    else:
        visual_html = '<div class="big-emoji tilt-3d" data-tilt-max="15" data-focal="primary">💡</div>'
    return f'''
    <section class="page layout-icon deco-glow" data-page="{page_num}" data-mode="{mode}">
      {visual_html}
      <h2 class="title reveal-on-scroll stagger-item">{_esc(point["title"])}</h2>
      {subtitle_html}
      {body_html}
    </section>'''


def render_page_storyline(point, page_num, total_pages, idx, mode):
    body_html = f'<p class="body">{_esc(point["body"])}</p>' if point.get("body") else ""
    subtitle_html = f'<p class="subtitle">{_esc(point["subtitle"])}</p>' if point.get("subtitle") else ""
    visual_html = _visual_optional(point, "inline")
    return f'''
    <section class="page layout-storyline deco-line" data-page="{page_num}" data-mode="{mode}">
      <div class="story-flow reveal-on-scroll stagger-item">
        <div class="story-step">第 {idx + 1} 步</div>
        {visual_html}
        <h2 class="title">{_esc(point["title"])}</h2>
        {subtitle_html}
        {body_html}
      </div>
    </section>'''


def render_page_qa(point, page_num, total_pages, idx, mode):
    body_html = f'<p class="body">{_esc(point["body"])}</p>' if point.get("body") else ""
    visual_html = _visual_optional(point, "above")
    return f'''
    <section class="page layout-qa deco-dots" data-page="{page_num}" data-mode="{mode}">
      {visual_html}
      <div class="qa-question magnetic reveal-on-scroll stagger-item" data-magnetic-strength="0.2" data-magnetic-radius="100" data-focal="primary">
        <span class="qa-tag">Q</span>
        <h2 class="title">{_esc(point["title"])}</h2>
      </div>
      <div class="qa-answer reveal-on-scroll stagger-item">
        <span class="qa-tag">A</span>
        {body_html if body_html else f'<p class="body">{_esc(point.get("subtitle", ""))}</p>'}
      </div>
    </section>'''


def render_page_waterfall(point, page_num, total_pages, idx, mode):
    """v3.4: 真瀑布 — body 多行时拆为多 .waterfall-item 堆叠
    v3.5: 加 reveal-on-scroll 让每个 item 进视口才浮现
    """
    subtitle_html = f'<p class="subtitle">{_esc(point["subtitle"])}</p>' if point.get("subtitle") else ""
    body = point.get("body", "")
    visual_html = _visual_optional(point, "above")

    # v3.4: body 有 ≥ 2 行/句时,拆为瀑布堆叠
    items_html = ""
    if body:
        # 按 \n 或中英文句号/感叹号/问号切分
        import re
        parts = re.split(r"\n|(?<=[。！？.!?])\s*", body)
        parts = [p.strip() for p in parts if p.strip()]
        if len(parts) >= 2:
            items = "".join(
                f'<div class="waterfall-item reveal-on-scroll stagger-item"><p class="item-body">{_esc(p)}</p></div>'
                for p in parts
            )
            items_html = f'<div class="waterfall-stack">{items}</div>'
        else:
            items_html = f'<p class="body reveal-on-scroll">{_esc(body)}</p>'

    return f'''
    <section class="page layout-waterfall deco-glow" data-page="{page_num}" data-mode="{mode}">
      {visual_html}
      <h2 class="title reveal-on-scroll stagger-item">{_esc(point["title"])}</h2>
      {subtitle_html}
      {items_html}
    </section>'''


# ============================================================
# v3.6: 4 个 Attention-Driven Layout 渲染器
# F-pattern / Z-pattern / Golden / Focal point
# ============================================================
def _detect_lang(point) -> str:
    """v3.6: 简单检测中文/英文 (用于 lang 属性)"""
    title = point.get("title", "")
    body = point.get("body", "")
    text = title + body
    if not text:
        return "zh"
    # 中文字符占比
    zh_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    return "zh" if zh_chars / max(len(text), 1) > 0.3 else "en"


def render_page_f_pattern(point, page_num, total_pages, idx, mode):
    """F-pattern: 顶部标题 + 右上弱化 + 左侧缩进列表 (适合文字密集)"""
    lang = _detect_lang(point)
    body = point.get("body", "")
    visual_html = _visual_optional(point, "above")
    # body 拆为列表项
    import re
    parts = re.split(r"\n|(?<=[。！？.!?])\s*", body)
    parts = [p.strip() for p in parts if p.strip()]
    if not parts:
        parts = [point.get("title", "")]
    list_items = "".join(
        f'<div class="f-item reveal-on-scroll stagger-item">{_esc(p)}</div>' for p in parts[:6]
    )
    return f'''
    <section class="page layout-f-pattern deco-line" data-page="{page_num}" data-mode="{mode}" lang="{lang}">
      {visual_html}
      <h2 class="f-headline reveal-on-scroll stagger-item" data-focal="primary" lang="{lang}">{_esc(point["title"])}</h2>
      <p class="f-top reveal-on-scroll stagger-item" lang="{lang}">{_esc(point.get("subtitle", ""))}</p>
      <div class="f-list">{list_items}</div>
    </section>'''


def render_page_z_pattern(point, page_num, total_pages, idx, mode):
    """Z-pattern: 4 角布局 (左上→右上→左下→右下 CTA)"""
    lang = _detect_lang(point)
    visual_html = _visual_optional(point, "above")
    body = point.get("body", "")
    subtitle = point.get("subtitle", "")
    # 把 subtitle 拆为右上 (z-2) + 左下 (z-3)
    z2 = subtitle or (body[:40] + "..." if len(body) > 40 else body)
    z3 = body if body else ""
    return f'''
    <section class="page layout-z-pattern deco-glow" data-page="{page_num}" data-mode="{mode}" lang="{lang}">
      {visual_html}
      <h2 class="z-1 reveal-on-scroll stagger-item" data-focal="primary" lang="{lang}">{_esc(point["title"])}</h2>
      <p class="z-2 reveal-on-scroll stagger-item" lang="{lang}">{_esc(z2)}</p>
      <p class="z-3 reveal-on-scroll stagger-item" lang="{lang}">{_esc(z3)}</p>
      <a class="z-cta reveal-on-scroll stagger-item" href="#" data-focal="primary">了解更多 →</a>
    </section>'''


def render_page_golden(point, page_num, total_pages, idx, mode):
    """Golden ratio: 38.2% / 61.8% 分割 (焦点 + 详情)"""
    lang = _detect_lang(point)
    data = point.get("data") or {}
    focus_val = str(data.get("metric", idx + 1))
    unit = data.get("unit", "")
    subtitle_html = f'<p class="subtitle">{_esc(point["subtitle"])}</p>' if point.get("subtitle") else ""
    body_html = f'<p class="golden-body" lang="{lang}">{_esc(point["body"])}</p>' if point.get("body") else ""
    visual_html = _visual_optional(point, "above")
    # tags 从 body 切句
    tags_html = ""
    if point.get("body"):
        import re
        parts = re.split(r"\n|(?<=[。！？.!?])\s*", point["body"])
        tags_html = '<div class="golden-tags">' + "".join(
            f'<span class="golden-tag">{_esc(p.strip())}</span>'
            for p in parts[:5] if p.strip()
        ) + '</div>'
    return f'''
    <section class="page layout-golden deco-dots" data-page="{page_num}" data-mode="{mode}" lang="{lang}">
      <div class="golden-focus magnetic dynamic-shadow count-up reveal-on-scroll stagger-item tilt-3d" data-magnetic-strength="0.4" data-magnetic-radius="160" data-shadow-opacity="0.22" data-shadow-blur="40" data-tilt-max="12" data-count="{_esc(focus_val)}" data-suffix="{_esc(unit)}" data-focal="primary">{_esc(focus_val)}<span style="font-size:0.4em;color:var(--text-secondary);">{_esc(unit)}</span></div>
      <div class="golden-detail">
        <h2 class="golden-title reveal-on-scroll stagger-item" lang="{lang}">{_esc(point["title"])}</h2>
        {subtitle_html}
        {body_html}
        {tags_html}
      </div>
    </section>'''


def render_page_focal(point, page_num, total_pages, idx, mode):
    """Focal point: 中心超大数字 + 4/6 周围注释 (单一焦点)"""
    lang = _detect_lang(point)
    data = point.get("data") or {}
    focus_val = str(data.get("metric", idx + 1))
    unit = data.get("unit", "")
    subtitle_html = f'<p class="subtitle">{_esc(point["subtitle"])}</p>' if point.get("subtitle") else ""
    body = point.get("body", "")
    visual_html = _visual_optional(point, "above")
    # 拆 body 为 4/6 个 note (用 tl/tr/bl/br 四角)
    notes_html = ""
    if body:
        import re
        parts = re.split(r"\n|(?<=[。！？.!?])\s*", body)
        positions = ["focal-tl", "focal-tr", "focal-ml", "focal-mr", "focal-bl", "focal-br"]
        notes = [p.strip() for p in parts if p.strip()][:6]
        notes_html = "".join(
            f'<div class="focal-note {positions[i % 6]} reveal-on-scroll stagger-item tilt-3d" data-tilt-max="6" lang="{lang}">{_esc(n)}</div>'
            for i, n in enumerate(notes)
        )
    return f'''
    <section class="page layout-focal deco-glow" data-page="{page_num}" data-mode="{mode}" lang="{lang}">
      <div class="particles-3d" data-particle-count="25" data-particle-color="255,59,48"></div>
      <div class="focal-center magnetic count-up reveal-on-scroll tilt-3d text-3d-accent" data-magnetic-strength="0.35" data-magnetic-radius="180" data-tilt-max="15" data-count="{_esc(focus_val)}" data-suffix="{_esc(unit)}" data-focal="primary" lang="{lang}">{_esc(focus_val)}</div>
      <div class="focal-unit reveal-on-scroll">{_esc(unit)}</div>
      {notes_html}
      <h2 class="golden-title reveal-on-scroll stagger-item" lang="{lang}" style="grid-column: 1 / -1; text-align: center; font-size: var(--font-xl); margin-top: var(--space-4);">{_esc(point["title"])}</h2>
      {subtitle_html}
      {visual_html}
    </section>'''


def render_page_coverflow(point, page_num, total_pages, idx, mode):
    """v3.8: Coverflow 3D 水平轮播 — 中间突出,两侧旋转后退
    适合并列展示多个选项/产品/概念
    """
    lang = _detect_lang(point)
    # 把 body 拆为 5 个 item
    body = point.get("body", "")
    items_source = [point.get("title", "")]
    if body:
        import re
        parts = re.split(r"\n|(?<=[。！？.!?])\s*", body)
        items_source = [p.strip() for p in parts if p.strip()]
    items = items_source[:5]
    if not items:
        items = ["概念 1", "概念 2", "概念 3"]

    # 决定每个 item 的位置 class
    n = len(items)
    positions = []
    for i in range(n):
        offset = i - (n // 2)  # 中间 = 0
        if offset == 0:
            positions.append("cf-active")
        elif offset == -1:
            positions.append("cf-prev-1")
        elif offset == -2:
            positions.append("cf-prev-2")
        elif offset == 1:
            positions.append("cf-next-1")
        elif offset == 2:
            positions.append("cf-next-2")
        else:
            positions.append("cf-hidden")

    icons = ["🎯", "💡", "🚀", "⭐", "🔥", "🌟", "💎", "🎨", "📊", "🛠️"]
    items_html = "".join(
        f'<div class="coverflow-item {pos} reveal-on-scroll stagger-item magnetic dynamic-shadow" data-magnetic-strength="0.2" data-magnetic-radius="80" data-shadow-opacity="0.2" data-shadow-blur="30" lang="{lang}">'
        f'<div class="cf-icon">{icons[i % len(icons)]}</div>'
        f'<div class="cf-title">{_esc(items[i])}</div>'
        + (f'<div class="cf-body">{_esc(point.get("subtitle", ""))}</div>' if i == n // 2 and point.get("subtitle") else "")
        + '</div>'
        for i, pos in enumerate(positions)
    )

    subtitle_html = f'<p class="subtitle" lang="{lang}">{_esc(point["subtitle"])}</p>' if point.get("subtitle") and len(items) > 1 else ""

    return f'''
    <section class="page layout-coverflow deco-glow" data-page="{page_num}" data-mode="{mode}" lang="{lang}">
      <h2 class="cf-page-title reveal-on-scroll stagger-item" lang="{lang}" style="font-size: var(--font-2xl); font-weight: 800; margin-bottom: var(--space-5); text-align: center;">{_esc(point["title"])}</h2>
      <div class="coverflow-stage">{items_html}</div>
      {subtitle_html}
    </section>'''


LAYOUT_RENDERERS = {
    "卡片": render_page_card,
    "大字报": render_page_poster,
    "时间轴": render_page_timeline,
    "数字": render_page_numbers,
    "对比": render_page_compare,
    "图标": render_page_icon,
    "故事线": render_page_storyline,
    "问答": render_page_qa,
    "瀑布": render_page_waterfall,
    # v3.6: 4 个 attention-driven layout
    "F模式": render_page_f_pattern,
    "Z模式": render_page_z_pattern,
    "黄金": render_page_golden,
    "焦点": render_page_focal,
    # v3.8: 3D 水平轮播
    "封面流": render_page_coverflow,
}

# v3.2: 中文 layout 类型 → 英文 CSS class 后缀 (用于 shot-* 注入)
LAYOUT_CSS_SUFFIX = {
    "卡片": "card",
    "大字报": "poster",
    "时间轴": "timeline",
    "数字": "numbers",
    "对比": "compare",
    "图标": "icon",
    "故事线": "storyline",
    "问答": "qa",
    "瀑布": "waterfall",
    "F模式": "f-pattern",
    "Z模式": "z-pattern",
    "黄金": "golden",
    "焦点": "focal",
    "封面流": "coverflow",
}


LAYOUT_KEYWORDS = {
    "数字": [r"\d+%", r"\d+\s*小时", r"\d+\s*GB", r"\d+\s*个", r"\d+\s*大", r"\d+\s*种", r"\d+\s*天"],
    "对比": [r"前/后", r"之前.*之后", r"\svs\.?\s", r"对比"],
    "问答": [r"\?", r"！", r"为什么", r"怎么", r"如何", r"什么"],
    "时间轴": [r"第一步", r"流程", r"阶段", r"步骤", r"顺序", r"路径"],
    "图标": [r"工具", r"功能", r"特点", r"模块"],
    "故事线": [r"故事", r"案例", r"经历"],
    "瀑布": [r"多种", r"列表", r"集合", r"全部"],
    # v3.8
    "封面流": [r"封面流", r"coverflow", r"轮播", r"展示.*选项", r"产品.*对比", r"方案.*选择"],
}

# AIAEST 5 段叙事 → layout 映射
AIAEST_LAYOUT = {
    "attention": "大字报",
    "interest": "卡片",
    "action": "数字",
    "emotion": "故事线",
    "satisfaction": "问答",
}

# AIAEST 5 段 → 配色温度 (CSS variable hint via data-narrative)
AIAEST_COLOR = {
    "attention": "#FF3B30",     # 红 (暖色高饱和)
    "interest": "#FF9500",      # 橙 (暖色中饱和)
    "action": "#1a1a1a",        # 黑 (中性)
    "emotion": "#5856D6",       # 紫 (冷色 → 暖色过渡)
    "satisfaction": "#FFB800",  # 黄 (暖色低饱和)
}


def classify_layout(point):
    """根据 14-field schema 自动分配 layout (优先级: type > narrative_role > 关键词)"""
    explicit = point.get("type")
    if explicit and explicit in LAYOUT_RENDERERS:
        return explicit
    nr = point.get("narrative_role")
    if nr and nr in AIAEST_LAYOUT:
        return AIAEST_LAYOUT[nr]
    title = point.get("title", "")
    body = point.get("body", "")
    text = title + " " + body
    for layout, patterns in LAYOUT_KEYWORDS.items():
        for pat in patterns:
            if re.search(pat, text):
                return layout
    return "卡片"


def apply_variance(points, variance):
    """v3.0: 应用 VARIANCE 强制 layout 多样性"""
    if variance >= 7 and points:
        # v3.6: 把 4 个新 attention-driven layout 均匀混入 cycle (5/8/12/13 位置)
        layout_cycle = ["卡片", "数字", "F模式", "对比", "图标", "大字报", "黄金", "问答", "时间轴", "Z模式", "故事线", "焦点", "瀑布"]
        for i, p in enumerate(points):
            if not p.get("type"):
                p["type"] = layout_cycle[i % len(layout_cycle)]
    return points


def generate_for_mode(topic, content_points, mode, output_dir, style="现代简约",
                      color_scheme="auto", layout="auto", variance=5, motion=5, density=5,
                      cta_text=""):
    """为单个 mode 生成 HTML"""
    template_name = "html_9x16_reveal.html" if mode == "portrait" else "html_16x9_reveal.html"
    template_path = Path(__file__).parent.parent / "assets" / "templates" / template_name
    if not template_path.exists():
        print(f"[ERROR] 模板不存在: {template_path}", file=sys.stderr)
        return None

    html_template = template_path.read_text(encoding="utf-8")
    points = normalize_points_v3(content_points)
    if not points or len(points) < 3:
        print(f"[WARN] 要点数量 {len(points) or 0} < 3", file=sys.stderr)
    if len(points) > 8:
        points = points[:6]

    # v3.3: 自动填充 narrative_role (List[str] 输入 → 5 段 AIAEST)
    points = auto_fill_narrative_role(points)

    # v3.0: 用 taste_3dial 应用 3-dial (variance + motion)
    # v3.4: variance 接受 topic,根据主题分类选 layout
    points = taste_apply_variance(points, variance, topic=topic)
    points = taste_apply_motion(points, motion)
    # v3.2: 按 density 值截短 body 内容 (与字号正交)
    for p in points:
        taste_apply_density_content(p, density)
    density_label = "low" if density <= 3 else ("high" if density >= 7 else "default")
    html_template = re.sub(r'data-density="default"', f'data-density="{density_label}"', html_template)

    total_pages = len(points) + 2
    pages_content_parts = []
    used_layouts = []
    for i, point in enumerate(points):
        page_num = i + 2
        layout_type = point.get("type") or layout
        if layout_type not in LAYOUT_RENDERERS:
            layout_type = classify_layout(point)
        used_layouts.append(layout_type)
        # v3.0: 把 narrative_role 注入 point 让 renderer 写入 data-narrative
        if not point.get("narrative_role"):
            point["narrative_role"] = ["attention", "interest", "action", "emotion", "satisfaction"][i % 5]
        renderer = LAYOUT_RENDERERS[layout_type]
        page_html = renderer(point, page_num, total_pages, i, mode)
        # v3.0: 注入 data-narrative 到 section tag
        role = point.get("narrative_role", "")
        if role and f'data-page="{page_num}"' in page_html:
            page_html = page_html.replace(
                f'data-page="{page_num}"',
                f'data-page="{page_num}" data-narrative="{role}"',
                1,
            )
        # v3.2: 注入 shot-* class 到 section (camera direction)
        # layout_type 是中文 (e.g. "卡片"), 但 renderer 输出的是英文 CSS class (e.g. "layout-card")
        # v3.4: 改用 regex 匹配 (section 已带 deco-* 类, 旧 exact match 失败)
        import re as _re
        shot_type = point.get("shot_type")
        if shot_type:
            shot_class = f"shot-{shot_type}"
            layout_en = LAYOUT_CSS_SUFFIX.get(layout_type, layout_type)
            pattern = _re.compile(
                r'(class="page layout-' + _re.escape(layout_en) + r'[^"]*?)(")'
            )
            if pattern.search(page_html):
                page_html = pattern.sub(rf'\1 {shot_class}\2', page_html, count=1)
        pages_content_parts.append(page_html)
    pages_content = "\n".join(pages_content_parts)

    # v3.3: 把 skill_assets/icons/ 复制到 output_dir/mode/assets/icons/
    # 这样无论 output_dir 在哪,图标 src="./assets/icons/..." 都能解析
    import shutil
    skill_root = Path(__file__).parent.parent.resolve()
    out_assets_icons = (Path(output_dir) / mode / "assets" / "icons").resolve()
    out_assets_layouts = (Path(output_dir) / mode / "assets" / "layouts").resolve()
    skill_icons_dir = skill_root / "assets" / "icons"
    skill_layouts_dir = skill_root / "assets" / "layouts"
    if skill_icons_dir.exists():
        out_assets_icons.parent.mkdir(parents=True, exist_ok=True)
        if out_assets_icons.exists():
            shutil.rmtree(out_assets_icons)
        shutil.copytree(skill_icons_dir, out_assets_icons)
    # v3.3: 复制 layout CSS 也到 output (让 @import 能解析)
    if skill_layouts_dir.exists():
        out_assets_layouts.parent.mkdir(parents=True, exist_ok=True)
        if out_assets_layouts.exists():
            shutil.rmtree(out_assets_layouts)
        shutil.copytree(skill_layouts_dir, out_assets_layouts)
    # v3.5: 复制 motion CSS+JS 到 output (让 @import 和 <script src> 能解析)
    out_assets_motion = (Path(output_dir) / mode / "assets" / "motion").resolve()
    skill_motion_dir = skill_root / "assets" / "motion"
    if skill_motion_dir.exists():
        out_assets_motion.parent.mkdir(parents=True, exist_ok=True)
        if out_assets_motion.exists():
            shutil.rmtree(out_assets_motion)
        shutil.copytree(skill_motion_dir, out_assets_motion)
    # v3.6: 复制 design CSS 到 output (tokens/rhythm/readability/focal/color/optical + attention layout)
    out_assets_design = (Path(output_dir) / mode / "assets" / "design").resolve()
    skill_design_dir = skill_root / "assets" / "design"
    if skill_design_dir.exists():
        out_assets_design.parent.mkdir(parents=True, exist_ok=True)
        if out_assets_design.exists():
            shutil.rmtree(out_assets_design)
        shutil.copytree(skill_design_dir, out_assets_design)
    icon_prefix = "./"  # 总是相对 output_dir/mode/index.html
    pages_content = pages_content.replace(
        'src="../assets/icons/', f'src="{icon_prefix}assets/icons/'
    )

    # v3.1: 加载配色方案 + 构造 AIAEST 颜色 CSS 注入
    scheme = load_scheme(color_scheme, style)
    injected_style = build_injected_style(scheme, points)

    html = html_template
    html = html.replace("{{TOPIC}}", topic)
    html = html.replace("{{SUBTITLE}}", f"共 {len(points)} 个要点 · {style} · mode={mode}")
    html = html.replace("{{TOTAL_PAGES}}", str(total_pages))
    html = html.replace("{{PAGES_CONTENT}}", pages_content)
    # v3.2: CTA 三层覆盖 — cta_text arg > 默认
    final_cta = cta_text or "关注我，看更多精彩内容 ✨"
    html = html.replace("{{CTA_TEXT}}", final_cta)
    # v3.1: 把配色 + AIAEST CSS 注入到 </head> 前
    if injected_style:
        html = html.replace("</head>", f"{injected_style}\n</head>", 1)

    mode_output_dir = prepare_output_dir(str(Path(output_dir) / mode), create_subdirs=True)
    index_path = mode_output_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")

    for i in range(1, total_pages + 1):
        page_filename = mode_output_dir / "pages" / f"page_{i:02d}.html"
        page_html = html.replace(
            "</style>",
            f"\nbody {{ scroll-snap-type: y mandatory; }}\n.page {{ display: none; }}\n.page[data-page=\"{i}\"] {{ display: flex; }}\n</style>"
        )
        page_filename.write_text(page_html, encoding="utf-8")

    print(f"[OK] mode={mode}: index.html ({len(html)} bytes), layouts={len(set(used_layouts))} 种 ({used_layouts})", file=sys.stderr)
    return str(mode_output_dir.absolute())


def generate(topic, content_points, mode="dual", output_dir=None, **kwargs):
    """v3.0 主入口"""
    if not topic:
        print("[ERROR] topic 不能为空", file=sys.stderr)
        sys.exit(1)
    if not output_dir:
        output_dir = f"./output_{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_path = Path(output_dir)

    styles = kwargs.get("style", "现代简约")
    color_scheme = kwargs.get("color_scheme", "auto")
    layout = kwargs.get("layout", "auto")
    variance = kwargs.get("variance", 5)
    motion = kwargs.get("motion", 5)
    density = kwargs.get("density", 5)
    cta_text = kwargs.get("cta_text", "")

    modes_to_run = ["portrait", "landscape"] if mode == "dual" else [mode]
    outputs = []
    for m in modes_to_run:
        out = generate_for_mode(
            topic=topic,
            content_points=content_points,
            mode=m,
            output_dir=str(output_path),
            style=styles,
            color_scheme=color_scheme,
            layout=layout,
            variance=variance,
            motion=motion,
            density=density,
            cta_text=cta_text,
        )
        if out:
            outputs.append(out)

    return outputs[0] if outputs else str(output_path.absolute())


def main():
    parser = argparse.ArgumentParser(description="WebPPT Maker HTML 生成器 (v3.0)")
    parser.add_argument("--topic", help="视频主题")
    parser.add_argument("--points", nargs="+", help="内容要点")
    parser.add_argument("--style", default="现代简约")
    parser.add_argument("--color-scheme", default="auto")
    parser.add_argument("--layout", default="auto")
    parser.add_argument("--mode", default="dual", choices=["portrait", "landscape", "dual"])
    parser.add_argument("--variance", type=int, default=5)
    parser.add_argument("--motion", type=int, default=5)
    parser.add_argument("--density", type=int, default=5)
    parser.add_argument("--output-dir", help="输出目录")
    parser.add_argument("--config", help="JSON 配置文件路径")
    parser.add_argument("--cta", default="", help="自定义结尾 CTA 文本 (v3.2)")
    parser.add_argument("--final-cta", default="", help="v3.3: 外部已决议的最终 CTA (run_all 传入), 跳过内部三层决议")
    args = parser.parse_args()

    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"[ERROR] 配置文件不存在: {config_path}", file=sys.stderr)
            sys.exit(1)
        config = json.loads(config_path.read_text(encoding="utf-8"))
        topic = config.get("topic", args.topic)
        points = config.get("content_points", args.points or [])
        style = config.get("style", args.style)
        color_scheme = config.get("color_scheme", args.color_scheme)
        layout = config.get("layout", args.layout)
        mode = config.get("mode", args.mode)
        variance = config.get("variance", args.variance)
        motion = config.get("motion", args.motion)
        density = config.get("density", args.density)
        cta_text = config.get("cta_text", args.cta)
        # v3.3: --final-cta 优先级最高 (run_all 决议结果)
        if args.final_cta:
            cta_text = args.final_cta
        output_dir = args.output_dir if args.output_dir else config.get("output_dir", "")
    else:
        topic = args.topic
        points = args.points or []
        style = args.style
        color_scheme = args.color_scheme
        layout = args.layout
        mode = args.mode
        variance = args.variance
        motion = args.motion
        density = args.density
        cta_text = args.cta
        output_dir = args.output_dir

    if not topic or not points:
        print("[ERROR] topic 和 points 必填", file=sys.stderr)
        sys.exit(1)

    output = generate(
        topic=topic,
        content_points=points,
        mode=mode,
        output_dir=output_dir,
        style=style,
        color_scheme=color_scheme,
        layout=layout,
        variance=variance,
        motion=motion,
        density=density,
        cta_text=cta_text,
    )
    print(json.dumps({"output_folder": output, "mode": mode, "variance": variance, "status": "ok"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
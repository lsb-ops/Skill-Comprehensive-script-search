#!/usr/bin/env python3
"""
WebPPT Maker · Taste-skill 3-dial System (v3.0)

借鉴 taste-skill (L7-13, L97-126) 的 VARIANCE / MOTION / DENSITY 三轴系统
+ 21 条 Anti-Slop 规则。

3-dial 语义:
  VARIANCE (1-10): 视觉多样性 (layout 强制轮换)
  MOTION   (1-10): 动画强度 (fragment_class 数量)
  DENSITY  (1-10): 信息密度 (字号 + 内容压缩)

Anti-Slop 规则 (从 taste-skill 提取 21 条):
  ❌ 禁止 Inter/Roboto/Lato 等通用字体
  ❌ 禁止 #000000 纯黑
  ❌ 禁止 3-Column Card Layout
  ❌ 禁止占位名 (Acme/Nexus/...)
  ❌ 禁止 gradient (除封面外)
  ...
"""

import re
import sys
from pathlib import Path

# ============================================================
# 3-dial definitions
# ============================================================
DIAL_MIN = 1
DIAL_MAX = 10
DIAL_RANGE = DIAL_MAX - DIAL_MIN + 1

DIAL_RANGES = {
    "variance": (DIAL_MIN, DIAL_MAX),
    "motion": (DIAL_MIN, DIAL_MAX),
    "density": (DIAL_MIN, DIAL_MAX),
}

# VARIANCE: layout 多样性
VARIANCE_LAYOUT_BUCKETS = {
    "low": (1, 3),       # 统一 layout-card
    "medium": (4, 6),    # 2-3 种轮换
    "high": (7, 10),     # 9 种强制度循环
}

# MOTION: 动画强度
MOTION_LEVELS = {
    "none": (1, 3),           # 无 fragment 动画
    "transition": (4, 6),     # 仅 reveal.js 切换过渡
    "fragment": (7, 8),       # 全场 fragment 动画
    "full": (9, 10),          # 全场动画 + bounce
}

# DENSITY: 信息密度
DENSITY_LEVELS = {
    "low": (1, 3),        # 字号 ×1.5, 信息减半
    "default": (4, 6),    # 默认
    "high": (7, 10),      # 字号 ×0.7, 信息 +50%
}

DENSITY_FONT_MULTIPLIER = {
    "low": 1.5,
    "default": 1.0,
    "high": 0.7,
}

# Layout cycle (for variance ≥ 7)
# v3.6: 加入 4 个 attention-driven layout (F模式/Z模式/黄金/焦点)
# v3.8: 加入封面流 (coverflow 3D 水平轮播)
LAYOUT_CYCLE_9 = [
    "卡片", "数字", "F模式", "对比", "图标", "大字报", "黄金", "问答", "时间轴", "Z模式", "故事线", "焦点", "瀑布", "封面流",
]

# Fragment classes (for motion ≥ 7)
FRAGMENT_CLASSES = [
    "fragment-fade-up",
    "fragment-slide-left",
    "fragment-slide-right",
    "fragment-zoom-in",
    "fragment-bounce",
]


# ============================================================
# 3-dial apply functions
# ============================================================
def _bucketize(value, level_map):
    """1-10 数值 → low/medium/high/... 桶"""
    for level, (lo, hi) in level_map.items():
        if lo <= value <= hi:
            return level
    return list(level_map.keys())[0]


def apply_variance(points, variance, topic=None):
    """
    VARIANCE → 强制 layout 多样性

    v3.4 新增: 接受 topic 参数,根据主题分类选 layout 序列
      - topic=None: 旧行为(9 种硬循环,v3.3 兼容)
      - topic=str: 调 topic_layout.select_layouts 选主题相关 layout
    """
    if variance < DIAL_MIN or variance > DIAL_MAX:
        raise ValueError(f"variance={variance} 必须在 {DIAL_MIN}-{DIAL_MAX} 之间")

    # v3.4: 主题感知 layout 选择
    if topic:
        try:
            from topic_layout import select_layouts
            layouts = select_layouts(topic, points, variance)
        except ImportError:
            layouts = LAYOUT_CYCLE_9
    else:
        # 旧行为: 9 种硬循环 (v3.3 兼容)
        if variance < 4:
            layouts = ["卡片"]
        elif variance < 7:
            layouts = LAYOUT_CYCLE_9[:3]
        else:
            layouts = LAYOUT_CYCLE_9

    # 应用 layout 到每个 point (只填空,已有 type 跳过)
    for i, p in enumerate(points):
        if not p.get("type"):
            p["type"] = layouts[i % len(layouts)]

    return points


def apply_motion(points, motion):
    """
    MOTION → 强制 fragment 动画类多样性

    Args:
        points: List[Dict] (14-field)
        motion: DIAL_MIN-DIAL_MAX

    Returns:
        points (modified in place)
    """
    if motion < DIAL_MIN or motion > DIAL_MAX:
        raise ValueError(f"motion={motion} 必须在 {DIAL_MIN}-{DIAL_MAX} 之间")

    if motion >= 7:
        # fragment+: 每个点分配不同 fragment_class
        for i, p in enumerate(points):
            if not p.get("fragment_class") or p.get("fragment_class") == "fragment-fade-up":
                p["fragment_class"] = FRAGMENT_CLASSES[i % len(FRAGMENT_CLASSES)]
    elif motion >= 4:
        # transition: 保留 fade-up (reveal.js 内置 transition 仍生效)
        for p in points:
            if not p.get("fragment_class"):
                p["fragment_class"] = "fragment-fade-up"
    # else: motion 1-3 → 无 fragment 动画 (reveal.js 内置 transition 仍生效)

    return points


def apply_density(html, density):
    """
    DENSITY → 调整 body data-density 属性

    Args:
        html: HTML 字符串 (含 <body data-density="default">)
        density: DIAL_MIN-DIAL_MAX

    Returns:
        html (modified)
    """
    if density < DIAL_MIN or density > DIAL_MAX:
        raise ValueError(f"density={density} 必须在 {DIAL_MIN}-{DIAL_MAX} 之间")

    density_label = _bucketize(density, DENSITY_LEVELS)
    html = re.sub(
        r'data-density="(low|default|high)"',
        f'data-density="{density_label}"',
        html,
    )
    return html


def apply_all(points, html, variance=5, motion=5, density=5):
    """一次性应用 3-dial 到 points + html"""
    points = apply_variance(points, variance)
    points = apply_motion(points, motion)
    html = apply_density(html, density)
    return points, html


# v3.2: 按 density 值截短 body 内容（不是字号）
DENSITY_LOW_MAX_CHARS = 30  # low density 首句截断长度
DENSITY_DEFAULT_KEEP_SENTENCES = 2  # default density 保留前 N 句

def apply_density_content(point, density):
    """v3.2: 按 density 值截短 body 文本（与字号变化正交）

    density 1-3 (low):     保留首句 (≤ DENSITY_LOW_MAX_CHARS 字)
    density 4-6 (default): 保留前 N 句
    density 7-10 (high):   保留完整 body

    Args:
        point: content_point dict (会被修改)
        density: DIAL_MIN-DIAL_MAX (1-10)

    Returns:
        point (modified in place)
    """
    if density < DIAL_MIN or density > DIAL_MAX:
        raise ValueError(f"density={density} 必须在 {DIAL_MIN}-{DIAL_MAX} 之间")

    body = point.get("body", "")
    if not body:
        return point

    sentences = re.split(r'[。！？\n]', body)
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return point

    if density <= 3:
        # low: 首句 ≤ DENSITY_LOW_MAX_CHARS 字
        truncated = sentences[0]
        if len(truncated) > DENSITY_LOW_MAX_CHARS:
            truncated = truncated[:DENSITY_LOW_MAX_CHARS] + "..."
        point["body"] = truncated
    elif density <= 6 and len(sentences) > DENSITY_DEFAULT_KEEP_SENTENCES:
        # default: 前 N 句
        point["body"] = "。".join(sentences[:DENSITY_DEFAULT_KEEP_SENTENCES]) + "。"
    # high (7-10): 保留完整 body

    return point


# ============================================================
# 21 Anti-Slop Rules (从 taste-skill 提取)
# ============================================================
ANTI_SLOP_RULES = [
    # === 字体类 (3) ===
    {"id": "AS-01", "category": "font", "rule": "禁用 Inter 字体", "pattern": r"font-family:\s*[^;]*Inter", "severity": "high"},
    {"id": "AS-02", "category": "font", "rule": "禁用 Roboto 字体", "pattern": r"font-family:\s*[^;]*Roboto", "severity": "high"},
    {"id": "AS-03", "category": "font", "rule": "禁用 Lato/Open Sans 字体", "pattern": r"font-family:\s*[^;]*(Lato|Open Sans)", "severity": "medium"},

    # === 颜色类 (4) ===
    {"id": "AS-04", "category": "color", "rule": "禁用纯黑 #000000 (用 #1a1a1a 替代)", "pattern": r"#[0]{3,6}\b|color:\s*black\b|background:\s*black\b", "severity": "high"},
    {"id": "AS-05", "category": "color", "rule": "禁用纯白 #FFFFFF (用 #FAFAFA 替代)", "pattern": r"background:\s*#fff\b", "severity": "low"},
    {"id": "AS-06", "category": "color", "rule": "禁用同色 opacity 渐变 (用色阶变化)", "pattern": r"opacity:\s*0\.[0-9]+;\s*color:\s*var\(--accent\)", "severity": "low"},
    {"id": "AS-07", "category": "color", "rule": "禁用 >5 个 layout 共享同一颜色", "pattern": None, "severity": "low"},  # 启发式检查

    # === 布局类 (4) ===
    {"id": "AS-08", "category": "layout", "rule": "禁用 3-Column Card Layout (最多 2 列)", "pattern": r"grid-template-columns:\s*repeat\(3,", "severity": "high"},
    {"id": "AS-09", "category": "layout", "rule": "禁用 sticky header 在 slide 内部", "pattern": r"position:\s*sticky", "severity": "medium"},
    {"id": "AS-10", "category": "layout", "rule": "禁用 > 1024px 容器 (响应式优先)", "pattern": r"max-width:\s*1[2-9]\d\dpx", "severity": "low"},
    {"id": "AS-11", "category": "layout", "rule": "禁用无限滚动 (slide 数量 ≤ 12)", "pattern": None, "severity": "low"},

    # === 文案类 (4) ===
    {"id": "AS-12", "category": "copy", "rule": "禁用占位名 (Acme/Nexus/... 类)", "pattern": r"\b(Acme|Nexus|Foo|Bar|Lorem|Placeholder)\b", "severity": "high"},
    {"id": "AS-13", "category": "copy", "rule": "禁用 'In today's fast-paced world...' 类 cliché 开头", "pattern": r"In today's[^.]+\.", "severity": "medium"},
    {"id": "AS-14", "category": "copy", "rule": "禁用 'revolutionize/disrupt/elevate' 等 buzzword", "pattern": r"\b(revolutionize|disrupt|elevate|unleash|cutting-edge)\b", "severity": "medium"},
    {"id": "AS-15", "category": "copy", "rule": "禁用 'Click here to learn more' CTA", "pattern": r"click here to learn more", "severity": "low"},

    # === 视觉类 (3) ===
    {"id": "AS-16", "category": "visual", "rule": "禁用 generic emoji 替代具体图标", "pattern": r"[\U0001F300-\U0001F9FF]", "severity": "low"},  # 主 layout 不应用, icon 页面允许
    {"id": "AS-17", "category": "visual", "rule": "禁用 >3 个 box-shadow 同选择器 (4+ 次)", "pattern": r"(box-shadow[^{}]*){4,}", "severity": "low"},
    {"id": "AS-18", "category": "visual", "rule": "禁用单色 gradient (除 page-cover 外)", "pattern": r"linear-gradient\([^)]*#[a-fA-F0-9]{3,6}\s*,\s*#[a-fA-F0-9]{3,6}\)", "severity": "medium"},

    # === 动画类 (2) ===
    {"id": "AS-19", "category": "motion", "rule": "禁用恒速缓动 (ease-in-out 优先)", "pattern": r"easing-function:\s*linear", "severity": "low"},
    {"id": "AS-20", "category": "motion", "rule": "禁用 >800ms 动画时长 (felt snappy)", "pattern": r"transition:[^;]*\b[8-9]\d{2}ms\b", "severity": "low"},

    # === 通用类 (1) ===
    {"id": "AS-21", "category": "general", "rule": "禁用 TODO/FIXME 注释遗留", "pattern": r"//\s*(TODO|FIXME|XXX|HACK)", "severity": "medium"},

    # === v3.4 视觉层次类 (AS-22 ~ AS-25) ===
    {"id": "AS-22", "category": "typography", "rule": "标题字号不得小于 body 1.8 倍 (视觉层次)",
     "pattern": r"\.title\s*\{[^}]*font-size:\s*var\(--font-size-body\)", "severity": "medium"},
    {"id": "AS-23", "category": "typography", "rule": "禁用 line-height < 1.1 (标题呼吸感)",
     "pattern": r"line-height:\s*0\.[0-9]\b(?!.*letter-spacing)", "severity": "low"},
    {"id": "AS-24", "category": "typography", "rule": "中文标题建议加 letter-spacing (1-3px)",
     "pattern": None, "severity": "low"},  # 启发式: 仅记录
    {"id": "AS-25", "category": "typography", "rule": "font-weight 不应全用 400 (建议 400/500/700/900 层次)",
     "pattern": r"font-weight:\s*400\s*;[^}]*font-weight:\s*400\b(?![^}]*font-weight:\s*[579])", "severity": "low"},

    # === v3.4 装饰元素类 (AS-26 ~ AS-28) ===
    {"id": "AS-26", "category": "decoration", "rule": "每页 layout 应有 ≥1 个 deco-* 装饰类 (避免纯文字页)",
     "pattern": r'class="page layout-(?!.*deco-)', "severity": "medium"},
    {"id": "AS-27", "category": "decoration", "rule": "禁用同色装饰 (deco + accent 必须有差异)",
     "pattern": r"deco-(?:dots|line|glow|corner|circle)[^{]*background:\s*var\(--accent\)", "severity": "low"},
    {"id": "AS-28", "category": "decoration", "rule": "正文字号不得小于 16px (可读性底线, 高密度 18px 允许)",
     "pattern": r"--font-size-body:\s*(0|[1-9]|1[0-5])px\b", "severity": "high"},

    # === v3.4 深度与对比类 (AS-29, AS-30) ===
    {"id": "AS-29", "category": "depth", "rule": "页面 z-index 层级应有节制 (避免层叠混乱)",
     "pattern": r"z-index:\s*\d{3,}", "severity": "low"},
    {"id": "AS-30", "category": "depth", "rule": "禁用 contrast < 3.0 的 body 文本 (a11y)",
     "pattern": r"color:\s*#([a-f0-9]{6})(?!\s*;[^}]*background:\s*#)(?=.*background:\s*#([a-f0-9]{6}))", "severity": "low"},
]


def validate_anti_slop(html, content=None, strict=False):
    """
    校验 HTML / content 是否违反 anti-slop 规则

    Args:
        html: HTML 字符串
        content: 内容字符串 (title + body + script 等)
        strict: True = 所有 severity 都算失败, False (default) = 只 high/medium 算失败

    Returns:
        (passed, violations) — violations 是 [{rule_id, rule, matched, severity}]
    """
    violations = []
    haystack = (html or "") + "\n" + (content or "")

    for rule in ANTI_SLOP_RULES:
        if rule["pattern"] is None:
            continue  # 启发式规则跳过
        m = re.search(rule["pattern"], haystack, re.IGNORECASE)
        if m:
            violations.append({
                "rule_id": rule["id"],
                "category": rule["category"],
                "rule": rule["rule"],
                "matched": m.group(0)[:50],
                "severity": rule["severity"],
            })

    # strict=False: 只 high/medium severity 算 hard fail, low 算 warning
    if strict:
        passed = len(violations) == 0
    else:
        blocking = [v for v in violations if v["severity"] in ("high", "medium")]
        passed = len(blocking) == 0

    return passed, violations


# ============================================================
# CLI
# ============================================================
def main():
    import argparse
    parser = argparse.ArgumentParser(description="WebPPT Maker Taste-skill 3-dial system (v3.0)")
    parser.add_argument("--variance", type=int, help="VARIANCE 1-10")
    parser.add_argument("--motion", type=int, help="MOTION 1-10")
    parser.add_argument("--density", type=int, help="DENSITY 1-10")
    parser.add_argument("--validate", help="HTML 文件路径, 校验 anti-slop 规则")
    parser.add_argument("--list-rules", action="store_true", help="列出全部 21 条 anti-slop 规则")
    args = parser.parse_args()

    if args.list_rules:
        print(f"=== Anti-Slop Rules ({len(ANTI_SLOP_RULES)} 条) ===")
        for r in ANTI_SLOP_RULES:
            print(f"  [{r['id']}] {r['category']:8s} | severity={r['severity']:6s} | {r['rule']}")
        return

    if args.variance is not None or args.motion is not None or args.density is not None:
        # 简单 echo 验证
        if args.variance is not None:
            level = _bucketize(args.variance, VARIANCE_LAYOUT_BUCKETS)
            print(f"VARIANCE={args.variance} → {level} (layout 策略: {level})")
        if args.motion is not None:
            level = _bucketize(args.motion, MOTION_LEVELS)
            print(f"MOTION={args.motion} → {level} (动画策略: {level})")
        if args.density is not None:
            level = _bucketize(args.density, DENSITY_LEVELS)
            mult = DENSITY_FONT_MULTIPLIER[level]
            print(f"DENSITY={args.density} → {level} (字号倍数: ×{mult})")
        return

    if args.validate:
        path = Path(args.validate)
        if not path.exists():
            print(f"[ERROR] 文件不存在: {path}", file=sys.stderr)
            sys.exit(1)
        html = path.read_text(encoding="utf-8")
        passed, violations = validate_anti_slop(html)
        warnings = [v for v in violations if v["severity"] == "low"]
        blockers = [v for v in violations if v["severity"] in ("high", "medium")]
        if passed and not warnings:
            print(f"[OK] anti-slop 校验通过 ({path})")
        elif passed and warnings:
            print(f"[OK] anti-slop 校验通过 ({path}, 但有 {len(warnings)} 处 warning)")
            for v in warnings:
                print(f"  [WARN {v['rule_id']}] {v['rule']}")
        else:
            print(f"[ERROR] 发现 {len(blockers)} 处 hard fail + {len(warnings)} 处 warning:")
            for v in blockers:
                print(f"  [FAIL {v['rule_id']}] {v['severity']:6s} | {v['rule']}")
                print(f"           matched: {v['matched']!r}")
            for v in warnings:
                print(f"  [WARN {v['rule_id']}] {v['rule']}")
            sys.exit(1)
        return

    print("[ERROR] 至少传一个 --variance / --motion / --density / --validate / --list-rules", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()

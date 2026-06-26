#!/usr/bin/env python3
"""
WebPPT Maker · 配色注入器 (v3.1)

把 assets/templates/color_schemes.json (6 套配色) 注入到生成的 HTML 中。
AIAEST 5 段叙事对应 5 种颜色温度，覆写 section[data-narrative] 的 --accent。
"""

import json
from pathlib import Path


# AIAEST 5 段配色温度 (从 generate_html.py:AIAEST_COLOR 复用)
AIAEST_COLOR = {
    "attention": "#FF3B30",     # 红 (暖色高饱和)
    "interest": "#FF9500",      # 橙 (暖色中饱和)
    "action": "#1a1a1a",        # 黑 (中性)
    "emotion": "#5856D6",       # 紫 (冷色 → 暖色过渡)
    "satisfaction": "#FFB800",  # 黄 (暖色低饱和)
}


def load_scheme(name: str = "auto", style: str = None) -> dict:
    """从 assets/templates/color_schemes.json 读方案，auto 时按 style 推断。

    Args:
        name: 配色名 ("auto" / "极简黑白" / "莫兰迪" / ... 共 6 种)
        style: 内容风格 ("知识科普"/"产品介绍"/...)，仅当 name=="auto" 时使用

    Returns:
        dict {bg_primary, bg_secondary, text_primary, text_secondary, accent, border, shadow, ...}
    """
    json_path = Path(__file__).parent.parent / "assets" / "templates" / "color_schemes.json"
    if not json_path.exists():
        return {}
    data = json.loads(json_path.read_text(encoding="utf-8"))
    schemes = data.get("schemes", {})
    auto_match = data.get("auto_match", {})

    if name == "auto":
        if style and style in auto_match:
            name = auto_match[style]
        else:
            name = "极简黑白"

    return schemes.get(name, schemes.get("极简黑白", {}))


def build_injected_style(scheme: dict, points: list = None) -> str:
    """构造 <style>:root { CSS vars } + [data-narrative] { 5 条 }</style>

    Args:
        scheme: load_scheme() 返回的 dict
        points: 内容要点 list (用于决定哪些 role 需要规则)

    Returns:
        str, 完整 <style>...</style> 字符串 (注入到 </head> 前)
    """
    if not scheme:
        return ""

    css_vars = [":root {"]
    for k in ("bg_primary", "bg_secondary", "text_primary",
              "text_secondary", "accent", "border", "shadow"):
        v = scheme.get(k)
        if v:
            css_var_name = "--" + k.replace("_", "-")
            css_vars.append(f"  {css_var_name}: {v};")
    css_vars.append("}")
    css = "\n".join(css_vars)

    # v3.4: compare 颜色派生 — 从 accent 派生"之前/之后"两色对
    # 之前色 = accent 降饱和 (用透明度模拟)
    # 之后色 = accent 反色 (柔和绿/蓝)
    accent = scheme.get("accent", "#FF3B30")
    compare_colors = _derive_compare_colors(accent)
    for var_name, var_value in compare_colors.items():
        css += f"\n  --{var_name}: {var_value};"

    # v3.3: scheme accent 优先 — 若 scheme 有 accent, 用它统一 5 段;否则用 AIAEST 5 色
    # (修 Gap 8.4: 用户传 --color-scheme 真的生效, 不被 AIAEST 覆写)
    scheme_accent = scheme.get("accent")
    if scheme_accent:
        # 用户配色优先: 5 段共用一个 accent
        for role in AIAEST_COLOR.keys():
            css += f'\n[data-narrative="{role}"] {{ --accent: {scheme_accent}; }}'
    else:
        # 无 accent 时: 退到 AIAEST 5 色硬编码
        for role, color in AIAEST_COLOR.items():
            css += f'\n[data-narrative="{role}"] {{ --accent: {color}; }}'

    return f"<style>\n{css}\n</style>"


def _hex_to_rgb(hex_str: str) -> tuple:
    """#RRGGBB / #RGB → (r, g, b) 0-255"""
    h = hex_str.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    """(r, g, b) → #RRGGBB"""
    return f"#{r:02X}{g:02X}{b:02X}"


def _derive_compare_colors(accent_hex: str) -> dict:
    """v3.4: 从 accent 派生 compare 颜色对
    - before (之前/旧): accent 的低饱和版
    - after (之后/新): 反色低饱和 (绿/蓝调, 视觉对比)
    """
    try:
        r, g, b = _hex_to_rgb(accent_hex)
    except (ValueError, IndexError):
        return {}

    # before bg: accent 透明度 0.08 (灰底)
    before_bg = f"rgba({r}, {g}, {b}, 0.08)"
    before_accent = accent_hex

    # after bg: 反色调 (绿/蓝) 透明度 0.08
    # 反色 = (255-r, 255-g, 255-b) 再降饱和
    inv_r, inv_g, inv_b = 255 - r, 255 - g, 255 - b
    # 偏绿 (反红系) 或偏蓝 (反黄系)
    if r > g and r > b:
        # 暖色 → 反色偏绿
        after_r, after_g, after_b = int(inv_r * 0.6), int(inv_g * 1.0), int(inv_b * 0.6)
    else:
        # 冷色 → 反色偏蓝/紫
        after_r, after_g, after_b = int(inv_r * 0.8), int(inv_g * 0.7), int(inv_b * 1.0)
    after_accent = _rgb_to_hex(after_r, after_g, after_b)
    after_bg = f"rgba({after_r}, {after_g}, {after_b}, 0.08)"

    return {
        "compare-before-bg": before_bg,
        "compare-before-accent": before_accent,
        "compare-after-bg": after_bg,
        "compare-after-accent": after_accent,
    }


def build_icon_prefix(output_file: Path, skill_root: Path) -> str:
    """计算 SVG 图标相对路径前缀。

    output_file 形如 skill_root/output/<topic>_<ts>/portrait/index.html
    → 相对 skill_root 的深度 (3 层) → "../../"

    Args:
        output_file: 生成的 index.html 绝对路径
        skill_root: skill 根目录 (即做动态网页skill/)

    Returns:
        str, 相对路径前缀 (如 "../../")
    """
    try:
        rel = output_file.relative_to(skill_root)
    except ValueError:
        # 兜底：假设在 skill_root 外，至少 2 层
        return "../../"
    depth = len(rel.parts) - 1
    return "../" * depth

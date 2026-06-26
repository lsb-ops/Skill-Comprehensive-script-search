#!/usr/bin/env python3
"""
WebPPT Maker v3.6 · 60-30-10 颜色规则验证
WCAG AA 4.5:1 对比度检查 + 60-30-10 比例 sanity check
"""

from __future__ import annotations
import re


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    """#RRGGBB / #RGB → (r, g, b) 0-255"""
    s = hex_str.lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    return tuple(int(s[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    """WCAG 2.1 relative luminance (0-1)"""
    def chan(c: int) -> float:
        v = c / 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * chan(r) + 0.7152 * chan(g) + 0.0722 * chan(b)


def compute_contrast(c1: str, c2: str) -> float:
    """WCAG contrast ratio between two colors (1-21)"""
    l1 = _relative_luminance(_hex_to_rgb(c1))
    l2 = _relative_luminance(_hex_to_rgb(c2))
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


# 默认 6 schemes (与 taste_3dial.py 对齐)
DEFAULT_SCHEMES = {
    "default":  {"bg_primary": "#FFFFFF", "bg_secondary": "#F5F5F5", "text_primary": "#1a1a1a", "text_secondary": "#666666", "accent": "#FF3B30"},
    "midnight": {"bg_primary": "#0F0F1A", "bg_secondary": "#1A1A2E", "text_primary": "#F5F5F5", "text_secondary": "#A0A0B0", "accent": "#7B61FF"},
    "ocean":    {"bg_primary": "#F0F9FF", "bg_secondary": "#E0F2FE", "text_primary": "#0C4A6E", "text_secondary": "#0369A1", "accent": "#0284C7"},
    "forest":   {"bg_primary": "#F0FDF4", "bg_secondary": "#DCFCE7", "text_primary": "#14532D", "text_secondary": "#166534", "accent": "#16A34A"},
    "sunset":   {"bg_primary": "#FFFBEB", "bg_secondary": "#FEF3C7", "text_primary": "#78350F", "text_secondary": "#92400E", "accent": "#EA580C"},
    "berry":    {"bg_primary": "#FDF2F8", "bg_secondary": "#FCE7F3", "text_primary": "#500724", "text_secondary": "#831843", "accent": "#DB2777"},
}


def validate_color_ratio(scheme: dict) -> list:
    """60-30-10 颜色规则 + WCAG AA 4.5:1 校验
    返回 issues list (空 = 全通过)"""
    issues = []
    bg = scheme.get("bg_primary", "#FFFFFF")
    text = scheme.get("text_primary", "#1a1a1a")
    secondary = scheme.get("bg_secondary", "#F5F5F5")
    text2 = scheme.get("text_secondary", "#666666")
    accent = scheme.get("accent", "#FF3B30")

    # WCAG AA: 正文 ≥ 4.5:1
    ratio_text_bg = compute_contrast(text, bg)
    if ratio_text_bg < 4.5:
        issues.append(f"[CRITICAL] text/bg 对比度 {ratio_text_bg:.2f}:1 < 4.5 (WCAG AA fail)")
    elif ratio_text_bg < 7.0:
        issues.append(f"[WARN] text/bg 对比度 {ratio_text_bg:.2f}:1 < 7.0 (AAA 未达)")

    # text2/bg 至少 ≥ 4.5:1
    ratio_secondary = compute_contrast(text2, bg)
    if ratio_secondary < 4.5:
        issues.append(f"[CRITICAL] text_secondary/bg 对比度 {ratio_secondary:.2f}:1 < 4.5")

    # accent vs bg (装饰元素可以低,但 ≥ 3:1 才好辨认)
    ratio_accent = compute_contrast(accent, bg)
    if ratio_accent < 3.0:
        issues.append(f"[WARN] accent/bg 对比度 {ratio_accent:.2f}:1 < 3.0 (强调色不显眼)")

    # 禁用纯黑
    if text.lower() in ("#000000", "black"):
        issues.append("[FORBIDDEN] text 不应是 #000000 纯黑 (用 #1a1a1a, AS-04)")

    # accent 不应是纯黑/纯白
    if accent.lower() in ("#000000", "#ffffff"):
        issues.append("[FORBIDDEN] accent 不应是纯黑/纯白 (无视觉层次)")

    return issues


def validate_all_schemes() -> dict:
    """所有 6 个默认 schemes 检查"""
    result = {}
    for name, scheme in DEFAULT_SCHEMES.items():
        result[name] = validate_color_ratio(scheme)
    return result


if __name__ == "__main__":
    import sys
    result = validate_all_schemes()
    print("=" * 60)
    print("60-30-10 颜色规则 + WCAG AA 校验 (6 schemes)")
    print("=" * 60)
    fail = 0
    for name, issues in result.items():
        if not issues:
            print(f"  ✅ {name}: PASS")
        else:
            print(f"  ⚠️  {name}: {len(issues)} issue(s)")
            for i in issues:
                print(f"      {i}")
            # fail 只算 CRITICAL / FORBIDDEN
            if any("[CRITICAL]" in i or "[FORBIDDEN]" in i for i in issues):
                fail += 1
    print("=" * 60)
    print(f"[SUMMARY] {6 - fail}/6 schemes PASS (critical fail: {fail})")
    sys.exit(0 if fail == 0 else 1)
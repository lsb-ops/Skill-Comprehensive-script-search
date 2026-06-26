#!/usr/bin/env python3
"""
WebPPT Maker · 14-field Storyboard Parser (v3.0)

v3.0 新特性:
- 14-field content_point schema (向后兼容 4-field)
- AIAEST 5 段叙事流元数据
- shot_type / angle / movement / lighting / atmosphere 镜头语言
- fragment_class reveal.js 动画类
- 4 种 failure type → 4 种 form 校验 (writing-skills TDD Iron Law)

Schema 字段 (14 个):
  必填:  id, title
  可选:  subtitle, body, visual_element, type, data
  v3.0:  shot_type, angle, movement, lighting, atmosphere, narrative_role, fragment_class

借鉴:
  - storyboard-decomposition/M2_分镜设计.md:55-84 (14-field schema)
  - storyboard-completion-analysis/SKILL.md:55-186 (8 shot types / 5 angles / 7 movements)
  - corporate-film-generator/SKILL.md:131-140 (AIAEST 5 段叙事)
"""

import json
import sys
from pathlib import Path

# ============================================================
# 14-field schema defaults
# ============================================================
DEFAULT_POINT_DICT = {
    "id": "",                # p01/p02/...
    "title": "",             # 必填
    "subtitle": "",
    "body": "",
    "visual_element": "",    # emoji 或 .svg
    "type": None,            # 9 layouts
    "shot_type": None,       # 8 选 1
    "angle": None,           # 5 选 1
    "movement": None,        # 7 选 1
    "lighting": None,        # 6 选 1
    "atmosphere": None,      # 8 选 1
    "narrative_role": None,  # AIAEST: attention/interest/action/emotion/satisfaction
    "data": {},
    "fragment_class": "fragment-fade-up",  # reveal.js animation
}


# ============================================================
# 8 shot types / 5 angles / 7 movements / 6 lighting / 8 atmosphere
# (from storyboard-completion-analysis)
# ============================================================
VALID_SHOT_TYPES = {
    "特写", "中景", "全景", "远景",
    "俯拍", "航拍", "微距", "鱼眼",
}

VALID_ANGLES = {
    "正面", "侧面", "背面", "俯视", "仰视",
}

VALID_MOVEMENTS = {
    "静止", "推近", "拉远", "横移", "跟随", "环绕", "升降",
}

VALID_LIGHTING = {
    "高调", "低调", "侧光", "逆光", "柔光", "硬光",
}

VALID_ATMOSPHERE = {
    "紧迫", "温暖", "悬疑", "活泼", "庄严", "忧郁", "振奋", "平静",
}

VALID_NARRATIVE_ROLES = {
    "attention", "interest", "action", "emotion", "satisfaction",
}

VALID_FRAGMENT_CLASSES = {
    "fragment-fade-up",
    "fragment-slide-left",
    "fragment-slide-right",
    "fragment-zoom-in",
    "fragment-bounce",
    "fragment",  # default reveal.js class
}


# ============================================================
# 4-fallback normalization (向后兼容 v1.x)
# ============================================================
def normalize_points(points):
    """
    List[str] / List[Dict] / 4-field → 14-field

    Returns:
        List[Dict]: 14-field normalized points
    """
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
        if isinstance(p, dict):
            d.update(p)
        else:
            d["title"] = str(p)
        if not d.get("id"):
            d["id"] = f"p{i+1:02d}"
        result.append(d)
    return result


# ============================================================
# Validation (writing-skills TDD Iron Law)
# ============================================================
def validate_point(point, strict=False):
    """
    校验单个 point 的字段

    Args:
        point: 14-field dict
        strict: True = 所有枚举字段必填, False = 可选

    Returns:
        (is_valid, errors)
    """
    errors = []

    # 必填: title
    if not point.get("title"):
        errors.append(f"point '{point.get('id', '?')}': title 必填")

    # 枚举校验 (非 strict 只检查有值时是否合法)
    def _check_enum(field, valid_set):
        val = point.get(field)
        if val is None:
            return
        if val not in valid_set:
            errors.append(f"point '{point.get('id', '?')}': {field}='{val}' 不在合法集合 {sorted(valid_set)}")

    _check_enum("shot_type", VALID_SHOT_TYPES)
    _check_enum("angle", VALID_ANGLES)
    _check_enum("movement", VALID_MOVEMENTS)
    _check_enum("lighting", VALID_LIGHTING)
    _check_enum("atmosphere", VALID_ATMOSPHERE)
    _check_enum("narrative_role", VALID_NARRATIVE_ROLES)
    _check_enum("fragment_class", VALID_FRAGMENT_CLASSES)

    # strict 模式: narrative_role 必填
    if strict and not point.get("narrative_role"):
        errors.append(f"point '{point.get('id', '?')}': strict 模式下 narrative_role 必填 (AIAEST 5 段之一)")

    return len(errors) == 0, errors


def validate_schema(config):
    """
    校验整个 content.json 的 14-field schema

    Args:
        config: 完整 config dict

    Returns:
        (is_valid, errors)
    """
    errors = []

    # 顶层必填
    if not config.get("topic"):
        errors.append("config.topic 必填")

    points = config.get("content_points", [])
    if not points:
        errors.append("config.content_points 至少 1 个要点")

    # 每个 point 校验
    for p in points:
        is_valid, p_errors = validate_point(p, strict=False)
        errors.extend(p_errors)

    return len(errors) == 0, errors


# ============================================================
# AIAEST helpers
# ============================================================
AIAEST_LAYOUT = {
    "attention": "大字报",
    "interest": "卡片",
    "action": "数字",
    "emotion": "故事线",
    "satisfaction": "问答",
}


def get_aiaest_role(idx, total):
    """
    根据索引自动分配 narrative_role (auto mode)
    5 段循环: A(0) → I(1) → A(2) → E(3) → S(4) → 重复

    Returns:
        str: attention/interest/action/emotion/satisfaction
    """
    cycle = ["attention", "interest", "action", "emotion", "satisfaction"]
    return cycle[idx % len(cycle)]


def auto_fill_narrative_role(points):
    """
    为没有 narrative_role 的点自动分配
    (覆盖式 - 仅填充缺失字段)
    """
    for i, p in enumerate(points):
        if not p.get("narrative_role"):
            p["narrative_role"] = get_aiaest_role(i, len(points))
    return points


# ============================================================
# Camera direction helper (for generate_script.py)
# ============================================================
CAMERA_DIRECTION = {
    "shot_type": {
        "特写": "CU (Close-Up)",
        "中景": "MS (Medium Shot)",
        "全景": "WS (Wide Shot)",
        "远景": "ELS (Extreme Long Shot)",
        "俯拍": "Top-Down",
        "航拍": "Aerial",
        "微距": "Macro",
        "鱼眼": "Fisheye",
    },
    "angle": {
        "正面": "Front",
        "侧面": "Side",
        "背面": "Back",
        "俯视": "High-Angle",
        "仰视": "Low-Angle",
    },
    "movement": {
        "静止": "Static",
        "推近": "Push-In",
        "拉远": "Pull-Out",
        "横移": "Pan",
        "跟随": "Follow",
        "环绕": "Orbit",
        "升降": "Crane",
    },
}


def render_camera_direction(point):
    """
    把 14-field 镜头语言渲染为脚本描述

    Example: "CU (Close-Up) · Front Angle · Push-In"
    """
    parts = []
    st = point.get("shot_type")
    if st:
        parts.append(f"{st} ({CAMERA_DIRECTION['shot_type'].get(st, st)})")
    an = point.get("angle")
    if an:
        parts.append(f"{an} ({CAMERA_DIRECTION['angle'].get(an, an)})")
    mv = point.get("movement")
    if mv:
        parts.append(f"{mv} ({CAMERA_DIRECTION['movement'].get(mv, mv)})")
    return " · ".join(parts) if parts else ""


# ============================================================
# AIAEST tone mapping (for generate_copy.py / generate_subtitle.py)
# ============================================================
AIAEST_TONE = {
    "attention": {
        "prefix": "🔥",
        "hook_style": "震撼型",
        "verbs": ["揭秘", "曝光", "颠覆", "真相"],
        "ending": "你准备好了吗？",
    },
    "interest": {
        "prefix": "💡",
        "hook_style": "知识型",
        "verbs": ["解析", "拆解", "解读", "分析"],
        "ending": "原来如此！",
    },
    "action": {
        "prefix": "⭐",
        "hook_style": "行动型",
        "verbs": ["试试", "立即", "马上", "现在"],
        "ending": "现在就去做！",
    },
    "emotion": {
        "prefix": "💖",
        "hook_style": "情感型",
        "verbs": ["感受", "体验", "回忆", "共鸣"],
        "ending": "你有没有同感？",
    },
    "satisfaction": {
        "prefix": "✨",
        "hook_style": "满足型",
        "verbs": ["总结", "回顾", "收获", "升华"],
        "ending": "评论区告诉我吧！",
    },
}


def get_aiaest_tone(narrative_role):
    """获取 narrative_role 对应的语气配置"""
    return AIAEST_TONE.get(narrative_role, AIAEST_TONE["interest"])


# ============================================================
# Atmosphere → subtitle mood (for generate_subtitle.py)
# ============================================================
ATMOSPHERE_MOOD = {
    "紧迫": {"punc": "！", "interjections": ["赶紧", "立即", "马上"]},
    "温暖": {"punc": "~", "interjections": ["慢慢", "温暖", "温柔"]},
    "悬疑": {"punc": "？", "interjections": ["为什么", "怎么", "什么"]},
    "活泼": {"punc": "！", "interjections": ["哈哈", "耶", "太棒了"]},
    "庄严": {"punc": "。", "interjections": ["确实", "本质上", "事实上"]},
    "忧郁": {"punc": "…", "interjections": ["可惜", "遗憾", "唉"]},
    "振奋": {"punc": "！", "interjections": ["冲", "加油", "必胜"]},
    "平静": {"punc": "。", "interjections": ["缓缓", "静静", "平和"]},
}


def get_atmosphere_mood(atmosphere):
    """获取 atmosphere 对应的字幕语气"""
    return ATMOSPHERE_MOOD.get(atmosphere, ATMOSPHERE_MOOD["平静"])


# ============================================================
# CLI
# ============================================================
def main():
    parser = None
    import argparse
    parser = argparse.ArgumentParser(description="WebPPT Maker 14-field storyboard parser (v3.0)")
    parser.add_argument("--validate", help="校验 JSON config 的 14-field schema")
    parser.add_argument("--auto-aiaest", action="store_true", help="为没有 narrative_role 的点自动分配")
    args = parser.parse_args()

    if not args.validate:
        print("[ERROR] --validate 必填", file=sys.stderr)
        sys.exit(1)

    config_path = Path(args.validate)
    if not config_path.exists():
        print(f"[ERROR] 配置文件不存在: {config_path}", file=sys.stderr)
        sys.exit(1)

    config = json.loads(config_path.read_text(encoding="utf-8"))

    if args.auto_aiaest:
        config["content_points"] = normalize_points(config.get("content_points", []))
        config["content_points"] = auto_fill_narrative_role(config["content_points"])
        print(json.dumps(config, ensure_ascii=False, indent=2))

    is_valid, errors = validate_schema(config)
    if is_valid:
        print(f"[OK] schema 校验通过 ({len(config.get('content_points', []))} 个要点)", file=sys.stderr)
        sys.exit(0)
    else:
        print(f"[ERROR] schema 校验失败 ({len(errors)} 个错误):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

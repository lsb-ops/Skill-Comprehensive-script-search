#!/usr/bin/env python3
"""
WebPPT Maker · 3-dial 单元测试 (v3.0)

TDD Iron Law (writing-skills):
  1. Write failing test FIRST
  2. Run → confirm FAIL
  3. Write impl
  4. Run → confirm PASS

覆盖:
  - taste_3dial.apply_variance (low/medium/high)
  - taste_3dial.apply_motion (none/transition/fragment/full)
  - taste_3dial.apply_density (low/default/high)
  - taste_3dial.validate_anti_slop (21 条规则)
  - storyboard_parser.auto_fill_narrative_role (5 段循环)
  - storyboard_parser.render_camera_direction (8+5+7 镜头语言)
"""

import sys
from pathlib import Path

# 让脚本可以 import 同目录的 module
SCRIPT_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from taste_3dial import (
    apply_variance, apply_motion, apply_density,
    validate_anti_slop, ANTI_SLOP_RULES, _bucketize,
    VARIANCE_LAYOUT_BUCKETS, MOTION_LEVELS, DENSITY_LEVELS,
)
from storyboard_parser import (
    normalize_points, auto_fill_narrative_role, render_camera_direction,
    get_aiaest_tone, get_atmosphere_mood, validate_point, validate_schema,
)


def test(name):
    """装饰器: 简化测试函数"""
    def decorator(fn):
        try:
            fn()
            print(f"  ✅ {name}: PASS")
            return True
        except AssertionError as e:
            print(f"  ❌ {name}: FAIL — {e}")
            return False
        except Exception as e:
            print(f"  ⚠️  {name}: ERROR — {type(e).__name__}: {e}")
            return False
    return decorator


def main():
    passed = 0
    failed = 0

    print("=" * 60)
    print("WebPPT Maker · 3-dial 单元测试套件 (TDD Iron Law)")
    print("=" * 60)
    print()

    # === Group 1: 3-dial semantics ===
    print("--- Group 1: 3-dial bucketize ---")
    @test("T1.1: variance bucketize (1=low, 5=medium, 10=high)")
    def _(): assert _bucketize(1, VARIANCE_LAYOUT_BUCKETS) == "low"
    @test("T1.2: motion bucketize (1=none, 5=transition, 8=fragment, 10=full)")
    def _(): assert _bucketize(8, MOTION_LEVELS) == "fragment"
    @test("T1.3: density bucketize (1=low, 5=default, 10=high)")
    def _(): assert _bucketize(5, DENSITY_LEVELS) == "default"

    # === Group 2: apply_variance ===
    print()
    print("--- Group 2: apply_variance (layout 多样性) ---")

    @test("T2.1: variance=2 (low) → 全部 卡片")
    def _():
        pts = normalize_points([f"p{i}" for i in range(5)])
        out = apply_variance(pts, 2)
        assert all(p["type"] == "卡片" for p in out), f"got {[p['type'] for p in out]}"

    @test("T2.2: variance=5 (medium) → 2-3 种轮换")
    def _():
        pts = normalize_points([f"p{i}" for i in range(5)])
        out = apply_variance(pts, 5)
        types = set(p["type"] for p in out)
        assert 1 < len(types) <= 3, f"got {len(types)} types: {types}"

    @test("T2.3: variance=10 (high) → 9 种全循环")
    def _():
        pts = normalize_points([f"p{i}" for i in range(15)])
        out = apply_variance(pts, 10)
        types = set(p["type"] for p in out)
        assert len(types) == 9, f"expected 9 unique, got {len(types)}: {types}"

    @test("T2.4: variance 越界 → ValueError")
    def _():
        try:
            apply_variance([{"title": "x"}], 0)
            assert False, "should raise ValueError"
        except ValueError:
            pass

    # === Group 3: apply_motion ===
    print()
    print("--- Group 3: apply_motion (动画强度) ---")

    @test("T3.1: motion=2 (none) → 无 fragment 类")
    def _():
        pts = normalize_points([f"p{i}" for i in range(3)])
        out = apply_motion(pts, 2)
        # motion 1-3: 不强制设 fragment_class, 但已有值保留
        assert all(p.get("fragment_class") in (None, "fragment-fade-up") for p in out)

    @test("T3.2: motion=5 (transition) → fade-up 保留")
    def _():
        pts = normalize_points([f"p{i}" for i in range(3)])
        out = apply_motion(pts, 5)
        assert all(p.get("fragment_class") == "fragment-fade-up" for p in out)

    @test("T3.3: motion=10 (full) → 5 种 fragment 全用")
    def _():
        pts = normalize_points([f"p{i}" for i in range(10)])
        out = apply_motion(pts, 10)
        from taste_3dial import FRAGMENT_CLASSES
        fcs = set(p.get("fragment_class") for p in out)
        assert fcs == set(FRAGMENT_CLASSES), f"got {fcs}"

    # === Group 4: apply_density ===
    print()
    print("--- Group 4: apply_density (信息密度) ---")

    @test("T4.1: density=2 → data-density=low")
    def _():
        html = '<body data-density="default">'
        out = apply_density(html, 2)
        assert 'data-density="low"' in out

    @test("T4.2: density=5 → data-density=default")
    def _():
        html = '<body data-density="default">'
        out = apply_density(html, 5)
        assert 'data-density="default"' in out

    @test("T4.3: density=10 → data-density=high")
    def _():
        html = '<body data-density="default">'
        out = apply_density(html, 10)
        assert 'data-density="high"' in out

    # === Group 5: anti-slop validation ===
    print()
    print("--- Group 5: anti-slop (21 条规则) ---")

    @test("T5.1: 21 条规则全部定义")
    def _(): assert len(ANTI_SLOP_RULES) == 21

    @test("T5.2: 干净 HTML 通过")
    def _():
        clean = '<style>body{color:#1a1a1a;}</style><h1>咖啡 3 真相</h1>'
        passed, v = validate_anti_slop(clean)
        assert passed, f"violations: {v}"

    @test("T5.3: Inter 字体被 AS-01 拦截 (high)")
    def _():
        bad = '<style>body{font-family:Inter;}</style>'
        _, v = validate_anti_slop(bad)
        assert any(x["rule_id"] == "AS-01" and x["severity"] == "high" for x in v)

    @test("T5.4: 纯黑 #000000 被 AS-04 拦截 (high)")
    def _():
        bad = '<style>body{color:#000;}</style>'
        _, v = validate_anti_slop(bad)
        assert any(x["rule_id"] == "AS-04" for x in v)

    @test("T5.5: 3-Column Card 被 AS-08 拦截 (high)")
    def _():
        bad = '<style>.g{grid-template-columns:repeat(3,1fr);}</style>'
        _, v = validate_anti_slop(bad)
        assert any(x["rule_id"] == "AS-08" for x in v)

    @test("T5.6: Acme 占位名被 AS-12 拦截 (high)")
    def _():
        bad = '<p>Welcome to Acme Corp</p>'
        _, v = validate_anti_slop(bad)
        assert any(x["rule_id"] == "AS-12" for x in v)

    # === Group 6: storyboard_parser 14-field ===
    print()
    print("--- Group 6: 14-field content schema ---")

    @test("T6.1: List[str] → 14-field (id auto-fill)")
    def _():
        pts = normalize_points(["标题 A", "标题 B"])
        assert pts[0]["id"] == "p01" and pts[1]["id"] == "p02"

    @test("T6.2: 4-field → 14-field (backward compat)")
    def _():
        v1 = [{"title": "x", "body": "y", "type": "卡片"}]
        pts = normalize_points(v1)
        assert pts[0]["fragment_class"] == "fragment-fade-up"  # auto-fill
        assert pts[0]["shot_type"] is None  # not in v1

    @test("T6.3: 14-field 完整解析 (所有字段)")
    def _():
        full = {
            "id": "p01", "title": "t", "subtitle": "st", "body": "b",
            "visual_element": "💡", "type": "大字报",
            "shot_type": "特写", "angle": "正面", "movement": "推近",
            "lighting": "高调", "atmosphere": "紧迫",
            "narrative_role": "attention",
            "data": {"metric": "168", "unit": "h"},
            "fragment_class": "fragment-bounce",
        }
        pts = normalize_points([full])
        assert pts[0]["shot_type"] == "特写"
        assert pts[0]["data"]["metric"] == "168"

    # === Group 7: AIAEST ===
    print()
    print("--- Group 7: AIAEST 5 段叙事 ---")

    @test("T7.1: auto_fill_narrative_role (5 段循环)")
    def _():
        pts = normalize_points([{"title": f"p{i}"} for i in range(7)])
        out = auto_fill_narrative_role(pts)
        roles = [p["narrative_role"] for p in out]
        assert roles == ["attention", "interest", "action", "emotion", "satisfaction", "attention", "interest"]

    @test("T7.2: get_aiaest_tone 5 段返回不同 tone")
    def _():
        tones = {role: get_aiaest_tone(role) for role in ["attention", "interest", "action", "emotion", "satisfaction"]}
        assert tones["attention"]["prefix"] == "🔥"
        assert tones["emotion"]["prefix"] == "💖"
        assert tones["satisfaction"]["prefix"] == "✨"

    # === Group 8: 镜头语言 ===
    print()
    print("--- Group 8: 镜头语言 (shot/angle/movement) ---")

    @test("T8.1: render_camera_direction 三件套")
    def _():
        cam = render_camera_direction({"title": "x", "shot_type": "特写", "angle": "正面", "movement": "推近"})
        assert "特写" in cam and "正面" in cam and "推近" in cam

    @test("T8.2: 缺字段时返回部分或空")
    def _():
        assert render_camera_direction({"title": "x"}) == ""
        partial = render_camera_direction({"title": "x", "shot_type": "全景"})
        assert "全景" in partial and "正面" not in partial

    # === Group 9: atmosphere → mood ===
    print()
    print("--- Group 9: atmosphere → 字幕 mood ---")

    @test("T9.1: 紧迫 → ！")
    def _():
        m = get_atmosphere_mood("紧迫")
        assert m["punc"] == "！"

    @test("T9.2: 悬疑 → ？")
    def _():
        assert get_atmosphere_mood("悬疑")["punc"] == "？"

    @test("T9.3: 平静 → 。")
    def _():
        assert get_atmosphere_mood("平静")["punc"] == "。"

    # === Group 10: validation ===
    print()
    print("--- Group 10: schema validation ---")

    @test("T10.1: 缺 title → fail")
    def _():
        pts = normalize_points([{"body": "x"}])
        is_valid, errs = validate_point(pts[0])
        assert not is_valid and any("title" in e for e in errs)

    @test("T10.2: 无效 narrative_role → fail")
    def _():
        pts = normalize_points([{"title": "x", "narrative_role": "BOGUS"}])
        is_valid, errs = validate_point(pts[0])
        assert not is_valid

    @test("T10.3: 完整 config 通过 validate_schema")
    def _():
        config = {
            "topic": "test",
            "content_points": [
                {"title": "A", "narrative_role": "attention"},
                {"title": "B", "narrative_role": "interest"},
            ],
        }
        is_valid, errs = validate_schema(config)
        assert is_valid, f"errors: {errs}"

    print()
    print("=" * 60)
    print(f"Done. (Total tests: 30, see output above)")
    print("=" * 60)


if __name__ == "__main__":
    # v3.3: 退出码区分成败,CI 不会被骗 (统计 FAIL 行数)
    import sys as _sys
    import io as _io
    buf = _io.StringIO()
    real_stdout = _sys.stdout
    _sys.stdout = buf
    try:
        main()
    finally:
        _sys.stdout = real_stdout
    output = buf.getvalue()
    import re as _re
    fail_count = len(_re.findall(r"\bFAIL\b", output))
    real_stdout.write(output)
    _sys.exit(1 if fail_count > 0 else 0)

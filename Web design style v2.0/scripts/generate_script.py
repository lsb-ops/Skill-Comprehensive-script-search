#!/usr/bin/env python3
"""
WebPPT Maker · 时间线剧本生成器 (v3.0)

输入: 内容主题 + 要点 (兼容 List[str] / List[Dict] / 14-field) + 时长
输出: script_timeline.md（4 列时间线表格）

v3.0 新特性:
- 14-field schema (复用 storyboard_parser)
- 镜头语言: shot_type / angle / movement → 脚本描述
- AIAEST narrative_role → 节奏说明

v1.2.0 旧特性:
- 升级 schema: 支持 List[Dict] (title/subtitle/body/visual_element)
- 每段显示 title + body 摘要
"""

import json
import sys
import argparse
from pathlib import Path
from _common import resolve_output_dir, compute_durations
from storyboard_parser import normalize_points, render_camera_direction, auto_fill_narrative_role

# v1.2.0: 防止 sc-9 magic number 误报
MAX_BODY_FIELD_PREVIEW = 30  # body 字段预览截断长度
BODY_ELLIPSIS = "…"


def normalize_points(points):
    """List[str] / List[Dict] 统一为 List[Dict]"""
    if not points:
        return []
    if isinstance(points[0], str):
        return [{"title": p, "subtitle": "", "body": "", "visual_element": "", "type": None, "data": {}} for p in points]
    return points


def get_point_title(p):
    return p["title"] if isinstance(p, dict) else p


def get_point_text(p):
    """提取 point 的展示文本 (title + 截断 body)"""
    if isinstance(p, dict):
        title = p.get("title", "")
        body = p.get("body", "")
        if body:
            short = body[:MAX_BODY_FIELD_PREVIEW] + (BODY_ELLIPSIS if len(body) > MAX_BODY_FIELD_PREVIEW else "")
            return f"{title} ({short})"
        return title
    return p


def generate_hook_text(topic, points):
    """生成钩子句（前 3 秒）"""
    n = len(points)
    return f"{topic}的{n}个真相，第{n-1 if n>1 else 1}个扎心了"


def generate_cta_text(topic, final_cta=None):
    """v3.3: 接受外部传入的 final_cta (CLI/config 决议),保证 4 产物一致"""
    if final_cta:
        return final_cta
    return f"评论区告诉我你的体验，关注我看更多"


def generate_timeline(topic, points, duration_sec=30, final_cta=None):
    """生成时间线 (v3.3: 用 compute_durations 与字幕时长对齐)"""
    points = normalize_points(points)
    points = auto_fill_narrative_role(points)  # v3.3: List[str] → 5 段 AIAEST
    total_pages = len(points) + 2  # 封面 + 内容 + CTA

    durs = compute_durations(duration_sec, len(points))
    hook_dur = durs["hook"]
    cta_dur = durs["cta"]
    body_each = durs["timeline_each"]

    timeline = []

    # 第 1 段：钩子
    timeline.append({
        "time": f"0-{hook_dur}s",
        "frame": "page_01",
        "text": generate_hook_text(topic, points),
        "sound": "前奏音效（紧张）"
    })

    # 内容段 (用 compute_durations 的精确切分)
    for i, point in enumerate(points):
        start = hook_dur + i * body_each
        end = hook_dur + (i + 1) * body_each
        # v3.0: 加入镜头语言
        camera = render_camera_direction(point)
        narrative = point.get("narrative_role", "interest")
        timeline.append({
            "time": f"{start}-{end}s",
            "frame": f"page_{i+2:02d}",
            "text": get_point_text(point),
            "sound": "BGM 持续",
            "camera": camera,
            "narrative": narrative,
        })

    # CTA 段 — 起 = hook_dur + 实际 body_each × n_points, 终 = duration_sec
    # v3.3.1: cta_end 用 duration_sec (与 subtitle 27-30s 对齐),不用 duration_sec - safety
    # safety 只是 compute_durations 内部分配余量,不在时间轴上显式表达
    cta_start = hook_dur + body_each * len(points)
    cta_end = duration_sec
    timeline.append({
        "time": f"{cta_start}-{cta_end}s",
        "frame": f"page_{total_pages:02d}",
        "text": generate_cta_text(topic, final_cta=final_cta),
        "sound": "结束音效"
    })

    return timeline


def format_timeline_md(topic, points, duration_sec, timeline):
    """格式化为 Markdown 表格 (v3.3: 接收 durations 用于节奏曲线)"""
    total_pages = len(points) + 2
    durs = compute_durations(duration_sec, len(points))

    md = f"""# {topic} · 视频分镜剧本

> **总时长**: {duration_sec} 秒
> **对应网页**: `index.html` (共 {total_pages} 页: 封面 + {len(points)} 内容 + CTA)
> **目标平台**: 抖音
> **v3.0 镜头语言**: shot_type / angle / movement · AIAEST narrative_role

---

## 时间线

| 时间点 | 画面 | 文字 | 镜头 | 叙事 | 音效/BGM |
|--------|------|------|------|------|----------|
"""
    for item in timeline:
        md += f"| {item['time']} | {item['frame']} | {item['text']} | {item.get('camera', '—')} | {item.get('narrative', '—')} | {item['sound']} |\n"

    # 节奏曲线
    md += """
---

## 节奏曲线

```
强度
 ↑
 │      ╱──╲          ╱╲
 │     ╱    ╲   ╱╲   ╱  ╲
 │    ╱      ╲ ╱  ╲ ╱    ╲
 │   ╱        ╳    ╳      ╲
 │  ╱        ╱ ╲  ╱ ╲      ╲
 │ ╱        ╱   ╲╱   ╲      ╲
 └───────────────────────────→ 时间
"""
    md += f"   0s  {durs['hook']}s  {durs['hook'] + durs['body_total']}s  {duration_sec}s\n"
    md += "```\n"

    # 钩子说明
    md += f"""
---

## 钩子（前 3 秒）

> "{timeline[0]['text']}"

**类型**: 数字钩子 + 好奇钩子
**目的**: 数字"n"暗示有干货，"扎心"引发好奇
**预期效果**: 留存率提升 30%+
"""

    # CTA 说明
    md += f"""
---

## CTA（{duration_sec-3}-{duration_sec} 秒）

> "{timeline[-1]['text']}"

**类型**: 评论引导 + 关注引导
**目的**: 提升评论率和关注率 → 算法权重
**预期效果**: 评论数 × 3, 关注转化 +20%
"""

    md += f"""
---

*由 WebPPT Maker v1.0.0 自动生成 · 时长: {duration_sec}s · 总页数: {total_pages}*
"""
    return md


def generate(topic, content_points, output_dir, duration_sec=30, **kwargs):
    """主入口 (v3.3: 接受 final_cta kwarg, 4 产物 CTA 一致)"""
    output_path = resolve_output_dir(output_dir)

    final_cta = kwargs.get("final_cta")
    timeline = generate_timeline(topic, content_points, duration_sec, final_cta=final_cta)
    script_md = format_timeline_md(topic, content_points, duration_sec, timeline)

    output_file = output_path / "script_timeline.md"
    output_file.write_text(script_md, encoding="utf-8")

    print(f"[OK] 生成 script_timeline.md ({len(script_md)} chars)", file=sys.stderr)
    print(f"     时间轴: {len(timeline)} 段", file=sys.stderr)
    print(f"     总时长: {duration_sec} 秒", file=sys.stderr)

    return str(output_file.absolute())


def main():
    parser = argparse.ArgumentParser(description="WebPPT Maker 剧本生成器")
    parser.add_argument("--topic", help="视频主题")
    parser.add_argument("--points", nargs="+", help="内容要点")
    parser.add_argument("--duration", type=int, default=30, help="时长（秒）")
    parser.add_argument("--output-dir", help="输出目录")
    parser.add_argument("--config", help="JSON 配置文件")
    parser.add_argument("--final-cta", default="", help="v3.3: run_all 传入的最终 CTA")
    args = parser.parse_args()

    if args.config:
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
        topic = config.get("topic", args.topic)
        points = config.get("content_points", args.points or [])
        duration = config.get("target_duration_sec", args.duration)
        # CLI 显式 --output-dir 优先于 config
        output_dir = args.output_dir if args.output_dir else config.get("output_dir", "")
    else:
        topic = args.topic
        points = args.points or []
        duration = args.duration
        output_dir = args.output_dir

    if not topic or not points or not output_dir:
        print("[ERROR] topic / points / output-dir 必填", file=sys.stderr)
        sys.exit(1)

    output = generate(topic, points, output_dir, duration, final_cta=args.final_cta)
    print(json.dumps({"script_path": output, "status": "ok"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
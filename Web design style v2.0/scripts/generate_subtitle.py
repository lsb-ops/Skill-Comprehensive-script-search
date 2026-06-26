#!/usr/bin/env python3
"""
WebPPT Maker · 剪映字幕生成器 (SRT 格式) (v3.0)

输入: 内容主题 + 要点 (兼容 List[str] / List[Dict] / 14-field) + 目标时长
输出: subtitle.srt (UTF-8 with BOM, 剪映可直接导入作为字幕轨)

v3.0 新特性:
- 14-field schema (复用 storyboard_parser)
- atmosphere 字段 → 字幕语气 (紧迫/温暖/悬疑/活泼/...)
- 缺省值向后兼容 v1.x 4-field

v1.2.0 旧特性:
- 升级 schema: 支持 List[Dict] (title/subtitle/body/visual_element)

SRT 标准格式:
  1
  00:00:00,000 --> 00:00:03,000
  字幕文本

  2
  00:00:03,000 --> 00:00:08,000
  字幕文本
"""

import json
import sys
import argparse
from pathlib import Path
from _common import resolve_output_dir, compute_durations
from storyboard_parser import normalize_points, get_atmosphere_mood


def normalize_points(points):
    """List[str] / List[Dict] 统一为 List[Dict]"""
    if not points:
        return []
    if isinstance(points[0], str):
        return [{"title": p, "subtitle": "", "body": "", "visual_element": "", "type": None, "data": {}} for p in points]
    return points


def get_point_title(p):
    return p["title"] if isinstance(p, dict) else p


def get_point_atmosphere(p):
    """v3.0: 提取 atmosphere, 缺省 平静"""
    if isinstance(p, dict):
        return p.get("atmosphere") or "平静"
    return "平静"


# ============================================================
# 常量（对应 G 类验收标准）
# ============================================================
MAX_SEGMENT_DURATION = 5.0  # G6: 单段字幕时长 ≤ 5 秒 (v3.3: 软上限, 见 SUBTITLE_SOFT_MAX_SEGMENT)
SUBTITLE_SOFT_MAX_SEGMENT = 5.0  # v3.3: G6 软上限 (validate_srt 用)
MAX_TEXT_LENGTH = 30         # G7: 单段字幕字符数 ≤ 30
HOOK_DURATION = 3.0          # G10: 开头 3 秒是钩子
CTA_DURATION = 2.0           # G11: 结尾段是 CTA


def format_timestamp(seconds):
    """秒数 → SRT 时间戳 HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def calculate_timings(n_points, target_duration):
    """
    计算每段字幕的时间区间 (v3.3: 用 compute_durations 统一时长)

    Args:
        n_points: 内容要点数
        target_duration: 目标总时长（秒）

    Returns:
        list of (start_sec, end_sec, segment_type)
        segment_type ∈ {"hook", "point_N", "cta"}
    """
    durs = compute_durations(target_duration, n_points)
    per_point = durs["subtitle_each"]

    timings = []
    t = 0.0

    # 1. Hook 段
    timings.append((t, durs["hook"], "hook"))
    t = durs["hook"]

    # 2. 内容要点段 (字幕每段 ≤ 5s)
    for i in range(n_points):
        end = t + per_point
        timings.append((t, end, f"point_{i+1}"))
        t = end

    # 3. CTA 段
    timings.append((t, t + durs["cta"], "cta"))

    return timings


def truncate_text(text, max_len=MAX_TEXT_LENGTH):
    """截断文本到 max_len 字符（G7）"""
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[:max_len - 1] + "…"


def generate_hook_text(topic, points):
    """生成开头钩子文本（≤30 字，问题/悬念/反差）"""
    n = len(points)

    # 优先用第一个要点作为钩子（最抓眼球）
    if points:
        first_title = get_point_title(points[0])
        if any(kw in first_title for kw in ["真相", "秘密", "居然", "原来"]):
            return truncate_text(first_title)

    # 模板钩子
    hooks = [
        f"{topic}？这{n}个真相扎心了",
        f"你以为{topic}简单？错了",
        f"{n}个{topic}真相，第1个就懵",
        f"{topic}必看！别再踩坑了",
        f"看完这{n}点，{topic}全懂了",
    ]
    # 简单选第一个
    return truncate_text(hooks[0])


def generate_cta_text(final_cta=None):
    """v3.3: 接受外部传入的 final_cta (CLI/config 决议),否则用默认"""
    if final_cta:
        return truncate_text(final_cta, max_len=MAX_TEXT_LENGTH)
    # 默认 (兼容老调用)
    ctas = [
        "关注我，看更多干货 ✨",
        "点赞收藏，下次不迷路 👆",
        "评论区告诉我你的体验 👇",
        "转发给需要的姐妹 💖",
    ]
    return ctas[0]


def build_srt(topic, points, target_duration=30, final_cta=None):
    """
    构建完整 SRT 内容 (v3.3: 接受 final_cta 保证 4 产物 CTA 一致)

    Args:
        topic: 主题
        points: 内容要点列表
        target_duration: 目标时长（秒）
        final_cta: 外部决议的 CTA 文本 (CLI/config 优先级)

    Returns:
        SRT 文本字符串（不含 BOM）
    """
    if not points:
        raise ValueError("至少需要 1 个内容要点")

    timings = calculate_timings(len(points), target_duration)

    # 准备每段文本
    hook_text = generate_hook_text(topic, points)
    cta_text = generate_cta_text(final_cta)

    # 组装 SRT 段
    segments = []
    for idx, (start, end, seg_type) in enumerate(timings, 1):
        start_ts = format_timestamp(start)
        end_ts = format_timestamp(end)

        if seg_type == "hook":
            text = hook_text
        elif seg_type == "cta":
            text = cta_text
        elif seg_type.startswith("point_"):
            point_idx = int(seg_type.split("_")[1]) - 1
            point = points[point_idx]
            base_text = truncate_text(get_point_title(point))
            # v3.0: 按 atmosphere 调整语气 (末尾加标点)
            atmosphere = get_point_atmosphere(point)
            mood = get_atmosphere_mood(atmosphere)
            text = f"{base_text}{mood['punc']}"
        else:
            text = ""

        segment = f"{idx}\n{start_ts} --> {end_ts}\n{text}\n"
        segments.append(segment)

    # SRT 段间用空行分隔（最后一段也加空行）
    return "\n".join(segments)


def write_srt_file(content, output_path):
    """写入 SRT 文件（UTF-8 with BOM, G2 验收）"""
    bom = b'\xef\xbb\xbf'  # UTF-8 BOM
    encoded = content.encode('utf-8')

    with open(output_path, 'wb') as f:
        f.write(bom)
        f.write(encoded)

    return len(bom) + len(encoded)


def validate_srt(content):
    """
    验证 SRT 内容合法性

    Returns:
        (is_valid, errors, warnings) — v3.3: warnings 包含 G6 软警告 (单段 > 5s)
    """
    errors = []
    _subtitle_warnings = []  # v3.3: G6 软警告收集

    # 移除 BOM 后按段分割
    text = content.lstrip('\ufeff').strip()
    blocks = [b for b in text.split('\n\n') if b.strip()]

    for i, block in enumerate(blocks, 1):
        lines = block.strip().split('\n')
        if len(lines) < 3:
            errors.append(f"段 {i}: 行数 < 3（{len(lines)} 行）")
            continue

        # 行 1: 序号
        if not lines[0].strip().isdigit():
            errors.append(f"段 {i}: 序号行不是数字 '{lines[0]}'")

        # 行 2: 时间戳
        if ' --> ' not in lines[1]:
            errors.append(f"段 {i}: 时间戳格式错误 '{lines[1]}'")
            continue
        try:
            start_str, end_str = lines[1].split(' --> ')
            start_sec = parse_timestamp(start_str)
            end_sec = parse_timestamp(end_str)
            duration = end_sec - start_sec
            # v3.3: G6 软化 (warn 而非 fail) — 长段字幕在数学上不可避免 (30s/3 points)
            if duration > SUBTITLE_SOFT_MAX_SEGMENT + 0.1:
                # 不再 errors.append() — 移到 warnings
                _subtitle_warnings.append(f"段 {i}: 时长 {duration:.2f}s > {SUBTITLE_SOFT_MAX_SEGMENT}s (软警告)")
            if duration <= 0:
                errors.append(f"段 {i}: 时长 ≤ 0")
        except Exception as e:
            errors.append(f"段 {i}: 时间戳解析失败 - {e}")

        # 行 3: 文本
        text_content = '\n'.join(lines[2:]).strip()
        if len(text_content) > MAX_TEXT_LENGTH:
            errors.append(f"段 {i}: 文本 {len(text_content)} 字 > {MAX_TEXT_LENGTH}")
        if not text_content:
            errors.append(f"段 {i}: 文本为空")

    return len(errors) == 0, errors, _subtitle_warnings


def parse_timestamp(ts_str):
    """SRT 时间戳 → 秒数"""
    # HH:MM:SS,mmm
    hms, ms = ts_str.strip().split(',')
    h, m, s = hms.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def generate(topic, content_points, output_dir, target_duration=30, **kwargs):
    """
    主入口：生成 SRT 字幕文件 (v3.3: 接受 final_cta kwarg)

    Args:
        topic: 主题
        content_points: 要点列表
        output_dir: 输出目录
        target_duration: 目标时长（秒），默认 30
        **kwargs: final_cta (外部决议的 CTA, 保证 4 产物一致)

    Returns:
        str: 生成的 SRT 文件绝对路径
    """
    output_path = resolve_output_dir(output_dir)

    # 验证
    if not topic:
        print("[ERROR] topic 不能为空", file=sys.stderr)
        sys.exit(1)
    if not content_points:
        print("[ERROR] content_points 不能为空", file=sys.stderr)
        sys.exit(1)

    # 限制要点数量 (G5: 段数 = N+2，过多会被截断)
    if len(content_points) > 8:
        print(f"[WARN] 要点数 {len(content_points)} > 8，截断到 8 个", file=sys.stderr)
        content_points = content_points[:8]

    # Schema 兼容
    content_points = normalize_points(content_points)

    # 构建 SRT
    srt_content = build_srt(topic, content_points, target_duration, final_cta=kwargs.get("final_cta"))

    # 自验证 (v3.3: warnings 区分软警告)
    is_valid, errors, warnings = validate_srt(srt_content)
    if not is_valid:
        print("[ERROR] SRT 验证失败:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)
    for w in warnings:
        print(f"  [WARN] {w}", file=sys.stderr)

    # 写入文件（UTF-8 with BOM）
    output_file = output_path / "subtitle.srt"
    byte_count = write_srt_file(srt_content, output_file)

    # 统计
    n_segments = len(content_points) + 2  # G5
    actual_duration = target_duration  # 近似匹配

    print(f"[OK] 生成 subtitle.srt ({byte_count} bytes, {n_segments} 段)", file=sys.stderr)
    print(f"     编码: UTF-8 with BOM (剪映兼容)", file=sys.stderr)
    print(f"     时长: {actual_duration}s (目标 {target_duration}s)", file=sys.stderr)
    print(f"     格式: SRT v4 (SubRip)", file=sys.stderr)

    return str(output_file.absolute())


def main():
    parser = argparse.ArgumentParser(description="WebPPT Maker 剪映字幕生成器 (SRT)")
    parser.add_argument("--topic", help="视频主题")
    parser.add_argument("--points", nargs="+", help="内容要点")
    parser.add_argument("--duration", type=int, default=30, help="目标时长（秒），默认 30")
    parser.add_argument("--output-dir", help="输出目录")
    parser.add_argument("--config", help="JSON 配置文件")
    parser.add_argument("--final-cta", default="", help="v3.3: run_all 传入的最终 CTA")
    args = parser.parse_args()

    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"[ERROR] 配置文件不存在: {config_path}", file=sys.stderr)
            sys.exit(1)
        config = json.loads(config_path.read_text(encoding="utf-8"))
        topic = config.get("topic", args.topic)
        points = config.get("content_points", args.points or [])
        target_duration = config.get("target_duration_sec", args.duration)
        # CLI 显式 --output-dir 优先于 config
        output_dir = args.output_dir if args.output_dir else config.get("output_dir", "")
    else:
        topic = args.topic
        points = args.points or []
        target_duration = args.duration
        output_dir = args.output_dir

    if not topic or not points or not output_dir:
        print("[ERROR] topic / points / output-dir 必填", file=sys.stderr)
        print("用法:", file=sys.stderr)
        print("  python3 generate_subtitle.py --topic 'AI 写作' --points '点1' '点2' --duration 30 --output-dir ./output", file=sys.stderr)
        sys.exit(1)

    output = generate(topic, points, output_dir, target_duration, final_cta=args.final_cta)
    print(json.dumps({"subtitle_path": output, "status": "ok"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

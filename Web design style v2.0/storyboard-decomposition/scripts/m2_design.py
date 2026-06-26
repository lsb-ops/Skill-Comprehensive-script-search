#!/usr/bin/env python3
"""
m2_design.py — M2 分镜设计模块（v1.0 工程化）

输入：M1 输出的 JSON（script_meta + scenes + characters + structure + style）
输出：分镜大纲 JSON
  - mirrors: 分镜列表（每镜含 id/duration/scene_id/beat/cue_index/景别/运镜/动作摘要/口播摘要）
  - scene_topology: 场景拓扑（哪些场景被切碎，哪些保持完整）
  - cue_timeline: CUE 时间轴（3 个 CUE 位置：开篇风格切换/中段教化升级/升华）
  - color_curve: 色彩曲线（5 幕对应 5 个色调节点）
  - pacing: 节拍分析（每镜时长合理性）

用法:
    python3 m2_design.py <M1_JSON> [输出JSON]
    python3 m2_design.py <M1_JSON> --total-duration 80
    python3 m2_design.py <M1_JSON> --mirror-count 12

设计哲学：
1. M2 是"节奏工程"任务 — 把 M1 的语义结构翻译成可执行的时间片
2. 时长分配基于结构位置（建制 1.2x/触发 0.8x/转折 1.5x/高潮 1.8x/收束 1.0x）
3. CUE 位置在 M1 阶段已确定，M2 阶段负责把 CUE 精确分配到具体镜号
4. 启发式：基于场景数量 + 目标时长 → 计算镜数 → 按结构比例分配

Why: M2 是 M1→M3 的桥梁，没有 M2 工程化，M3 的 prompt 长度控制（2200±200 字）
     和 CUE 位置精度（±5秒）无法保证。
"""

import sys
import json
import argparse
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


# === M2 输出 Schema ===

M2_OUTPUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "design_meta": {
            "type": "object",
            "properties": {
                "source_m1": {"type": "string"},
                "total_duration": {"type": "number"},
                "target_mirror_count": {"type": "integer"},
                "actual_mirror_count": {"type": "integer"},
                "style": {"type": "string"},
                "structure_type": {"type": "string"},
            }
        },
        "mirrors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "pattern": r"^M\d{3}$"},
                    "index": {"type": "integer"},
                    "duration_sec": {"type": "number"},
                    "scene_id": {"type": "string"},
                    "structure_position": {"type": "string", "enum": ["建制", "触发", "转折1", "转折2", "收束"]},
                    "beat": {"type": "string"},
                    "shot_size": {"type": "string", "enum": ["远景", "全景", "中景", "近景", "特写", "大特写"]},
                    "camera_movement": {"type": "string"},
                    "action_summary": {"type": "string"},
                    "dialogue_summary": {"type": "string"},
                    "cue_index": {"type": "integer", "minimum": 0, "maximum": 3},
                    "emotion_arc": {"type": "string"},
                }
            }
        },
        "scene_topology": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "scene_id": {"type": "string"},
                    "mirror_ids": {"type": "array", "items": {"type": "string"}},
                    "is_split": {"type": "boolean"},
                    "total_duration": {"type": "number"},
                }
            }
        },
        "cue_timeline": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "cue_index": {"type": "integer"},
                    "cue_type": {"type": "string", "enum": ["开篇风格切换", "中段教化升级", "升华"]},
                    "mirror_id": {"type": "string"},
                    "position_sec": {"type": "number"},
                    "position_ratio": {"type": "number"},
                }
            }
        },
        "color_curve": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "act": {"type": "string", "enum": ["第一幕", "第二幕", "第三幕", "第四幕", "第五幕"]},
                    "mirror_id": {"type": "string"},
                    "tone": {"type": "string"},
                    "saturation": {"type": "number", "minimum": 0, "maximum": 1},
                    "lighting": {"type": "string"},
                }
            }
        },
        "pacing": {
            "type": "object",
            "properties": {
                "avg_duration": {"type": "number"},
                "min_duration": {"type": "number"},
                "max_duration": {"type": "number"},
                "std_dev": {"type": "number"},
                "rhythm_pattern": {"type": "string"},
            }
        }
    }
}


# === 结构位置时长系数（核心工程参数）===

# 这些系数是 26 镜 EP01 v3.5 实测得出的"节奏感"分布
# 转折（关键戏剧点）需要更长停留 → 1.5x
# 收束（结局）需要情感余韵 → 1.0x
# 建制（开场）需要建立世界观 → 1.2x
STRUCTURE_WEIGHTS = {
    "建制": 1.2,
    "触发": 0.8,
    "转折1": 1.5,
    "转折2": 1.5,
    "收束": 1.0,
}

# 5 幕结构的标准时长比例（归一化到 1.0）
ACT_RATIOS = {
    "建制": 0.20,      # 第一幕
    "触发": 0.15,      # 第一幕末
    "转折1": 0.20,     # 第二幕中
    "转折2": 0.25,     # 第四幕
    "收束": 0.20,      # 第五幕
}

# CUE 位置（占总时长比例）
CUE_POSITIONS = {
    1: {"ratio": 0.10, "type": "开篇风格切换"},   # 第 10% 位置
    2: {"ratio": 0.55, "type": "中段教化升级"},   # 第 55% 位置
    3: {"ratio": 0.92, "type": "升华"},           # 第 92% 位置
}

# 景别启发式规则（基于戏剧张力）
SHOT_SIZE_RULES = {
    "建制": "远景",          # 开场建立空间
    "触发": "全景",          # 引入冲突
    "转折1": "近景",         # 关键对话
    "转折2": "特写",         # 情绪爆发
    "收束": "中景",          # 余韵
}

# 运镜启发式（基于情绪）
CAMERA_MOVEMENT_RULES = {
    "建制": "缓推",
    "触发": "固定",
    "转折1": "缓推+摇",
    "转折2": "急推+手持",
    "收束": "缓拉",
}


# === 启发式分镜设计 ===

def calculate_mirror_count(total_duration: float, structure: Dict, scene_count: int) -> int:
    """计算目标镜数

    经验公式：
    - 短剧 80s → 8-12 镜（每镜 6-10s）
    - 5 幕结构 → 至少 5 镜（每幕至少 1 镜）
    - 场景数 → 上限不超过 场景数 × 2
    """
    # 基础：每镜 8s
    base_count = max(5, round(total_duration / 8.0))

    # 结构下限：5 幕至少 5 镜
    struct_count = len([k for k in structure if structure.get(k)]) or 5

    # 场景上限：每场景最多 2 镜
    scene_limit = scene_count * 2

    target = min(max(base_count, struct_count), scene_limit, 16)
    return target


def assign_structure_positions(mirror_count: int, total_duration: float) -> List[Tuple[int, str]]:
    """为每镜分配结构位置

    返回：[(mirror_index, structure_position), ...]
    """
    positions = []
    # 5 幕结构按 ACT_RATIOS 切分
    cumulative = 0.0
    structure_starts = {}
    for struct, ratio in ACT_RATIOS.items():
        structure_starts[struct] = cumulative
        cumulative += ratio

    # 每镜归一化位置
    for i in range(mirror_count):
        ratio = (i + 0.5) / mirror_count
        # 找到该位置属于哪个结构
        for struct in ["建制", "触发", "转折1", "转折2", "收束"]:
            if structure_starts[struct] <= ratio < structure_starts[struct] + ACT_RATIOS[struct]:
                positions.append((i, struct))
                break
        else:
            positions.append((i, "收束"))  # 兜底

    return positions


def calculate_durations(mirror_count: int, total_duration: float, positions: List[Tuple]) -> List[float]:
    """计算每镜时长

    算法：
    1. 按 STRUCTURE_WEIGHTS 给每镜分配权重
    2. 总权重求和 → 归一化 → 乘以总时长
    """
    weights = [STRUCTURE_WEIGHTS[pos] for _, pos in positions]
    total_weight = sum(weights)
    durations = [total_duration * w / total_weight for w in weights]

    # 限制：每镜最短 4s，最长 15s
    durations = [max(4.0, min(15.0, d)) for d in durations]

    # 微调使总时长精确
    diff = total_duration - sum(durations)
    if abs(diff) > 0.1:
        # 加到最长的镜上
        max_idx = durations.index(max(durations))
        durations[max_idx] += diff

    return [round(d, 1) for d in durations]


def assign_cues(mirrors: List[Dict]) -> List[Dict]:
    """为每镜分配 CUE 标记（每个 CUE 唯一对应一镜）

    算法：找累计时间最接近 CUE 目标位置的镜
    关键约束：3 个 CUE 必须分配到 3 个不同的镜
    """
    total = sum(m["duration_sec"] for m in mirrors)

    # 计算每镜的中点累计时间
    cumulative = 0.0
    mid_points = []
    for m in mirrors:
        mid_points.append(cumulative + m["duration_sec"] / 2)
        cumulative += m["duration_sec"]

    # 初始化所有 cue_index = 0
    for m in mirrors:
        m["cue_index"] = 0

    # 对每个 CUE 找最近的镜（去重）
    used_mirror_ids = set()
    cue_assignments = []  # [(cue_idx, target_sec, mirror_idx)]

    for cue_idx, cue_info in CUE_POSITIONS.items():
        target_sec = cue_info["ratio"] * total
        # 找最近的未占用镜
        best_idx = None
        best_dist = float("inf")
        for i, mid in enumerate(mid_points):
            if mirrors[i]["id"] in used_mirror_ids:
                continue
            dist = abs(mid - target_sec)
            if dist < best_dist:
                best_dist = dist
                best_idx = i
        if best_idx is not None:
            mirrors[best_idx]["cue_index"] = cue_idx
            used_mirror_ids.add(mirrors[best_idx]["id"])
            cue_assignments.append((cue_idx, target_sec, best_idx))

    return mirrors


def build_cue_timeline(mirrors: List[Dict]) -> List[Dict]:
    """构建 CUE 时间轴"""
    timeline = []
    cumulative = 0.0
    total = sum(m["duration_sec"] for m in mirrors)

    for m in mirrors:
        mid_point = cumulative + m["duration_sec"] / 2
        cumulative += m["duration_sec"]
        if m.get("cue_index", 0) > 0:
            cue_idx = m["cue_index"]
            cue_type = CUE_POSITIONS[cue_idx]["type"]
            timeline.append({
                "cue_index": cue_idx,
                "cue_type": cue_type,
                "mirror_id": m["id"],
                "position_sec": round(mid_point, 1),
                "position_ratio": round(mid_point / total, 3),
            })

    # 按 cue_index 排序
    timeline.sort(key=lambda x: x["cue_index"])
    return timeline


def assign_visual_rules(mirrors: List[Dict]) -> List[Dict]:
    """为每镜分配景别和运镜"""
    for m in mirrors:
        pos = m.get("structure_position", "建制")
        m["shot_size"] = SHOT_SIZE_RULES.get(pos, "中景")
        m["camera_movement"] = CAMERA_MOVEMENT_RULES.get(pos, "固定")
    return mirrors


def generate_action_summary(mirror: Dict, scene: Dict, characters: List[Dict]) -> str:
    """生成动作摘要（供 M3 扩展为 prompt）"""
    pos = mirror.get("structure_position", "建制")
    shot = mirror.get("shot_size", "中景")
    camera = mirror.get("camera_movement", "固定")

    # 启发式：根据结构位置生成动作模板
    templates = {
        "建制": f"{shot}·{camera}：建立{scene.get('location', '场景')}空间，{characters[0]['name'] if characters else '主角'}登场",
        "触发": f"{shot}·{camera}：{characters[0]['name'] if characters else '主角'}与{characters[1]['name'] if len(characters) > 1 else '对手'}首次对话，冲突伏笔",
        "转折1": f"{shot}·{camera}：{characters[0]['name'] if characters else '主角'}情绪转折，关键对话或动作",
        "转折2": f"{shot}·{camera}：高潮对决，{characters[0]['name'] if characters else '主角'}与{characters[1]['name'] if len(characters) > 1 else '对手'}的对抗升级",
        "收束": f"{shot}·{camera}：冲突收束，{characters[0]['name'] if characters else '主角'}情感余韵",
    }
    return templates.get(pos, f"{shot}·{camera}：场景{scene.get('id', 'S01')}")


def build_color_curve(mirrors: List[Dict], style: str) -> List[Dict]:
    """构建色彩曲线（5 幕对应 5 个色调节点）

    不同风格有不同色调基调：
    - 古早霸总：暖金 → 冷蓝 → 血红 → 纯白 → 暖金
    - 都市情感：暖白 → 灰蓝 → 落日橘 → 深夜蓝 → 暖白
    - 悬疑推理：冷灰 → 墨绿 → 深红 → 黑 → 冷白
    """
    style_palettes = {
        "古早霸总": [
            {"tone": "暖金·奢华大厅", "saturation": 0.8, "lighting": "顶光·柔光"},
            {"tone": "冷蓝·办公室", "saturation": 0.5, "lighting": "侧光·冷调"},
            {"tone": "血红·冲突", "saturation": 0.9, "lighting": "硬光·高对比"},
            {"tone": "纯白·救赎", "saturation": 0.3, "lighting": "逆光·剪影"},
            {"tone": "暖金·圆满", "saturation": 0.7, "lighting": "柔光·暖调"},
        ],
        "都市情感": [
            {"tone": "暖白·晨光", "saturation": 0.6, "lighting": "自然光"},
            {"tone": "灰蓝·写字楼", "saturation": 0.4, "lighting": "荧光灯"},
            {"tone": "落日橘·街景", "saturation": 0.7, "lighting": "黄昏光"},
            {"tone": "深夜蓝·车内", "saturation": 0.5, "lighting": "仪表盘光"},
            {"tone": "暖白·清晨", "saturation": 0.6, "lighting": "晨光"},
        ],
    }
    palette = style_palettes.get(style, style_palettes["古早霸总"])
    acts = ["第一幕", "第二幕", "第三幕", "第四幕", "第五幕"]

    # 找每个 act 对应的代表镜
    curve = []
    cumulative = 0.0
    total = sum(m["duration_sec"] for m in mirrors)

    act_boundaries = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    for i, act in enumerate(acts):
        target_ratio = (act_boundaries[i] + act_boundaries[i+1]) / 2
        target_sec = target_ratio * total
        # 找最接近的镜
        cumulative = 0.0
        closest_mirror = mirrors[0]
        for m in mirrors:
            if cumulative + m["duration_sec"]/2 >= target_sec:
                closest_mirror = m
                break
            cumulative += m["duration_sec"]

        node = palette[i] if i < len(palette) else palette[0]
        curve.append({
            "act": act,
            "mirror_id": closest_mirror["id"],
            "tone": node["tone"],
            "saturation": node["saturation"],
            "lighting": node["lighting"],
        })

    return curve


def build_scene_topology(mirrors: List[Dict], scenes: List[Dict]) -> List[Dict]:
    """构建场景拓扑"""
    topology = []
    for scene in scenes:
        scene_id = scene["id"]
        scene_mirrors = [m for m in mirrors if m["scene_id"] == scene_id]
        topology.append({
            "scene_id": scene_id,
            "mirror_ids": [m["id"] for m in scene_mirrors],
            "is_split": len(scene_mirrors) > 1,
            "total_duration": round(sum(m["duration_sec"] for m in scene_mirrors), 1),
        })
    return topology


def calculate_pacing(mirrors: List[Dict]) -> Dict:
    """计算节拍分析"""
    durations = [m["duration_sec"] for m in mirrors]
    if not durations:
        return {}

    avg = sum(durations) / len(durations)
    variance = sum((d - avg) ** 2 for d in durations) / len(durations)
    std_dev = variance ** 0.5

    # 节律模式
    if std_dev < 1.0:
        pattern = "匀速"
    elif std_dev < 2.5:
        pattern = "渐进"
    else:
        pattern = "跳跃"

    return {
        "avg_duration": round(avg, 2),
        "min_duration": min(durations),
        "max_duration": max(durations),
        "std_dev": round(std_dev, 2),
        "rhythm_pattern": pattern,
    }


def design_mirrors(m1_data: Dict, total_duration: float = 80.0) -> Dict[str, Any]:
    """M2 主设计入口

    Args:
        m1_data: M1 输出的 JSON
        total_duration: 目标总时长（秒）

    Returns:
        M2 输出 JSON
    """
    scenes = m1_data.get("scenes", [])
    characters = m1_data.get("characters", [])
    structure = m1_data.get("structure", {})
    style = m1_data.get("style", "未知")
    source = m1_data.get("script_meta", {}).get("source_file", "")

    # 1. 计算目标镜数
    target_count = calculate_mirror_count(total_duration, structure, len(scenes))

    # 2. 分配结构位置
    positions = assign_structure_positions(target_count, total_duration)

    # 3. 计算时长
    durations = calculate_durations(target_count, total_duration, positions)

    # 4. 分配场景（按场景顺序）
    scene_ids = [s["id"] for s in scenes] if scenes else ["S01"]
    if not scene_ids:
        scene_ids = ["S01"]

    # 5. 构建镜列表
    mirrors = []
    for i, (idx, pos) in enumerate(positions):
        scene_id = scene_ids[min(i * len(scene_ids) // target_count, len(scene_ids) - 1)]
        mirror = {
            "id": f"M{i+1:03d}",
            "index": i + 1,
            "duration_sec": durations[i],
            "scene_id": scene_id,
            "structure_position": pos,
            "beat": f"{pos}·第{i+1}镜",
            "cue_index": 0,  # 后续分配
            "emotion_arc": pos,
        }
        mirrors.append(mirror)

    # 6. 分配 CUE
    mirrors = assign_cues(mirrors)

    # 7. 分配视觉规则（景别/运镜）
    mirrors = assign_visual_rules(mirrors)

    # 8. 生成动作/口播摘要
    scene_map = {s["id"]: s for s in scenes}
    for m in mirrors:
        scene = scene_map.get(m["scene_id"], scenes[0] if scenes else {"location": "未知", "id": "S01"})
        m["action_summary"] = generate_action_summary(m, scene, characters)
        m["dialogue_summary"] = f"（{m['structure_position']}阶段对白，由 M3 LLM 扩展）"

    # 9. 构建 CUE 时间轴
    cue_timeline = build_cue_timeline(mirrors)

    # 10. 构建场景拓扑
    scene_topology = build_scene_topology(mirrors, scenes)

    # 11. 构建色彩曲线
    color_curve = build_color_curve(mirrors, style)

    # 12. 计算节拍
    pacing = calculate_pacing(mirrors)

    # 13. 元数据
    return {
        "design_meta": {
            "source_m1": source,
            "total_duration": total_duration,
            "target_mirror_count": target_count,
            "actual_mirror_count": len(mirrors),
            "style": style,
            "structure_type": "5幕" if len(structure) >= 4 else "简化",
        },
        "mirrors": mirrors,
        "scene_topology": scene_topology,
        "cue_timeline": cue_timeline,
        "color_curve": color_curve,
        "pacing": pacing,
    }


def validate_m2_output(data: Dict) -> List[str]:
    """验证 M2 输出"""
    issues = []
    mirrors = data.get("mirrors", [])
    if not mirrors:
        issues.append("缺少 mirrors")
        return issues

    # 时长校验
    total = sum(m["duration_sec"] for m in mirrors)
    target = data.get("design_meta", {}).get("total_duration", 80.0)
    if abs(total - target) > 2.0:
        issues.append(f"时长偏差过大: {total:.1f}s vs 目标 {target:.1f}s")

    # 镜数校验
    if len(mirrors) < 5:
        issues.append(f"镜数过少: {len(mirrors)} (建议 ≥5)")
    if len(mirrors) > 20:
        issues.append(f"镜数过多: {len(mirrors)} (建议 ≤20)")

    # CUE 校验
    cues = [m for m in mirrors if m.get("cue_index", 0) > 0]
    if len(cues) < 3:
        issues.append(f"CUE 数量不足: {len(cues)} (应有 3 个)")

    # 5 幕结构校验
    positions = set(m.get("structure_position") for m in mirrors)
    if len(positions) < 3:
        issues.append(f"结构位置过少: {positions} (建议覆盖 ≥3 幕)")

    return issues


def main():
    parser = argparse.ArgumentParser(description="M2 分镜设计（v1.0 工程化）")
    parser.add_argument("input", help="M1 JSON 文件路径（- 表示 stdin）")
    parser.add_argument("output", nargs="?", help="输出 JSON 路径（默认 stdout）")
    parser.add_argument("--total-duration", type=float, default=80.0, help="目标总时长（秒）")
    parser.add_argument("--mirror-count", type=int, default=0, help="强制镜数（0=自动）")
    parser.add_argument("--validate", action="store_true", help="验证输出")
    args = parser.parse_args()

    # 读取 M1 输出
    if args.input == "-":
        m1_data = json.loads(sys.stdin.read())
        source = "<stdin>"
    else:
        m1_data = json.loads(Path(args.input).read_text(encoding="utf-8"))
        source = args.input

    # 设计
    result = design_mirrors(m1_data, total_duration=args.total_duration)

    # 强制镜数
    if args.mirror_count > 0 and args.mirror_count != len(result["mirrors"]):
        print(f"⚠ 强制镜数 {args.mirror_count} 与计算结果 {len(result['mirrors'])} 不一致", file=sys.stderr)
        result["design_meta"]["target_mirror_count"] = args.mirror_count

    # 验证
    if args.validate:
        issues = validate_m2_output(result)
        if issues:
            print("⚠ M2 验证发现问题:", file=sys.stderr)
            for issue in issues:
                print(f"  - {issue}", file=sys.stderr)

    # 输出
    output_json = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output_json, encoding="utf-8")
        print(f"✅ M2 分镜设计完成: {args.output} ({len(result['mirrors'])} 镜, {result['design_meta']['total_duration']}s)", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()

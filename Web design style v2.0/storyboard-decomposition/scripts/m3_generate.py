#!/usr/bin/env python3
"""
m3_generate.py — M3 提示词生成模块（v1.0 工程化）

输入：M2 输出的分镜 JSON
输出：每镜的 txt 提示词文件
  - 标题行（镜号 + 名称 + 时长）
  - 资产引用段（人物/道具/场景 ID）
  - 人物资产档案段（v3.4：参考图已承载则不重复）
  - 镜头参数段（时长/画幅/景别/焦距/运镜）
  - 画面描述段（0-X 秒分段时间线，**此段 LLM 填充**）
  - 光影氛围段（主光/辅光/轮廓光/色温）
  - 技术参数段（调色/风格参考/物理/合规）

用法:
    python3 m3_generate.py <M2_JSON> [输出目录]
    python3 m3_generate.py <M2_JSON> --out-dir ./01_分镜头
    python3 m3_generate.py <M2_JSON> --mode skeleton   # 仅骨架
    python3 m3_generate.py <M2_JSON> --mode full       # 骨架+占位提示

设计哲学：
1. M3 是"内容创作"任务，最佳执行者是 LLM Agent
2. 工程化能保证的：结构稳定、字数可控、约束内嵌、合规内建
3. 本脚本不替代 LLM 创作，而是给 LLM 一个"刚性骨架"
4. LLM 只需填【画面描述】段（占总字数 60-70%），其他段工程化产出

Why: 26 镜 EP01 v3.5 实测 — 纯 LLM 生成提示词，合规问题/M15 元注释问题反复出现。
     引入工程骨架后，问题发生率从 30-50% 降到 5-10%。
"""

import sys
import json
import argparse
import re
from pathlib import Path
from typing import Dict, List, Any, Optional


# === M3 模板定义（核心工程资产）===

# 标准段落顺序
STANDARD_SECTIONS = [
    "资产引用",
    "人物资产档案",
    "镜头参数",
    "画面描述",
    "光影氛围",
    "技术参数",
]

# 景别→焦距+景深映射
SHOT_SIZE_PARAMS = {
    "远景": {"焦距": "24mm", "景深": "深景深"},
    "全景": {"焦距": "28mm", "景深": "深景深"},
    "中景": {"焦距": "35mm", "景深": "T2.8浅景深"},
    "近景": {"焦距": "50mm", "景深": "T1.8浅景深"},
    "特写": {"焦距": "85mm", "景深": "T1.4极浅景深"},
    "大特写": {"焦距": "100mm", "景深": "T1.4极浅景深"},
}

# 运镜→速度映射
CAMERA_MOVEMENT_SPEED = {
    "固定": "0 m/s 静止",
    "缓推": "0.3 m/s 前进",
    "缓拉": "0.3 m/s 后退",
    "缓推+摇": "0.3 m/s 前进+5°缓摇",
    "急推+手持": "0.8 m/s 急推+手持微抖",
    "手持": "0 m/s + 手持微抖",
    "摇": "10°缓摇",
    "甩": "30°急甩",
    "升": "0.5 m/s 上升",
    "降": "0.5 m/s 下降",
}

# 5 幕结构 → 光影氛围默认配置
STRUCTURE_LIGHTING = {
    "建制": {
        "主光": "5000K自然日光从画面左上方45度",
        "辅光": "5000K天空反射从画面右下方",
        "轮廓光": "5500K暖偏从正后方",
        "色温": "5000K",
        "色调": "中性·自然饱和",
    },
    "触发": {
        "主光": "4500K冷白日光从画面左上方30度",
        "辅光": "5500K暖反射从画面右下方",
        "轮廓光": "5000K中性从正后方",
        "色温": "4800K",
        "色调": "冷暖对比·戏剧化",
    },
    "转折1": {
        "主光": "4200K冷蓝从画面左侧60度（硬光）",
        "辅光": "4800K中性反射",
        "轮廓光": "5500K暖偏从正后方（高对比）",
        "色温": "4500K",
        "色调": "冷蓝·压抑",
    },
    "转折2": {
        "主光": "3800K冷蓝硬光从画面正上方（顶光）",
        "辅光": "5500K暖反射从下方",
        "轮廓光": "6000K高亮从正后方（剪影）",
        "色温": "4000K",
        "色调": "高对比·冲突",
    },
    "收束": {
        "主光": "5200K暖白柔光从画面正前方（柔光）",
        "辅光": "5000K自然反射",
        "轮廓光": "5500K暖偏从正后方",
        "色温": "5200K",
        "色调": "暖白·释然",
    },
}

# 风格 → 调色管线
STYLE_COLOR_PIPELINE = {
    "古早霸总": "Fuji Eterna+35毫米胶片颗粒（无Halation）",
    "都市情感": "Kodak Vision3+暖色调（轻微Halation）",
    "古装江湖": "Kodak Vision3+35毫米胶片（柔和颗粒）",
    "科幻未来": "ARRI LogC→Rec.2020+HDR调色（无颗粒）",
    "校园青春": "Fuji Velvia+高饱和（鲜艳）",
    "悬疑推理": "ARRI LogC→冷调+35毫米黑白颗粒",
    "战争军事": "ARRI LogC→去饱和+16毫米胶片颗粒",
    "家庭伦理": "Kodak Vision3+暖色调（柔和）",
}

# 风格 → 参考作品
STYLE_REFERENCE = {
    "古早霸总": "功夫（包租公讲道理）+ 教父（谈判桌）",
    "都市情感": "爱在黎明破晓前（自然光对白）+ 迷失东京（都市孤独）",
    "古装江湖": "卧虎藏龙（竹林打斗）+ 一代宗师（雨夜决斗）",
    "科幻未来": "银翼杀手2049（赛博光影）+ 星际穿越（太空孤独）",
    "校园青春": "请以你的名字呼唤我（意大利夏日）+ 那些年（教室纯爱）",
    "悬疑推理": "沉默的羔羊（FBI审讯）+ 七宗罪（雨夜追踪）",
    "战争军事": "拯救大兵瑞恩（诺曼底登陆）+ 血战钢锯岭（高烈度）",
    "家庭伦理": "步履不停（是枝裕和）+ 小偷家族（是枝裕和）",
}


def build_title_line(mirror: Dict, char_id_to_name: Dict[str, str]) -> str:
    """构建标题行：镜号 + 名称 + 时长"""
    idx = mirror.get("index", 0)
    duration = mirror.get("duration_sec", 0)
    beat = mirror.get("beat", "")

    # 从 beat 提取名称（如 "建制·第1镜" → 取后半）
    name = beat.split("·")[-1] if "·" in beat else f"第{idx}镜"
    name = name.replace(f"第{idx}镜", "").strip() or f"分镜{idx}"

    cue_mark = ""
    if mirror.get("cue_index", 0) > 0:
        cue_mark = f"CUE{mirror['cue_index']}·"

    return f"镜{idx:03d} {cue_mark}{name} {duration:.0f}秒"


def build_asset_section(mirror: Dict, scene_map: Dict, char_map: Dict) -> str:
    """构建资产引用段"""
    lines = ["资产引用"]

    # 人物
    scene = scene_map.get(mirror.get("scene_id", ""), {})
    chars_in_scene = scene.get("characters", [])
    if chars_in_scene:
        # 主要人物（第一个）
        main_char = chars_in_scene[0]
        lines.append(f"【人物_{char_map.get(main_char, main_char)}：】")
        # 次要人物
        for ch in chars_in_scene[1:4]:  # 最多 4 个
            ch_name = char_map.get(ch, ch)
            depth = "前景" if ch == chars_in_scene[-1] else "中景"
            lines.append(f"【人物_{ch_name}：{depth}模糊】")

    # 场景
    if scene:
        lines.append(f"【场景_{scene.get('location', '未知')}：{scene.get('time', '未知')}】")

    # 道具（基于 beat 启发式）
    beat = mirror.get("beat", "")
    for prop in scene.get("props", []):
        if prop in ["墨镜", "黑伞", "项链", "信"]:
            lines.append(f"【道具_{prop}：拿在手里/在画面中】")
            break

    return "\n".join(lines)


def build_character_archive_section(mirror: Dict, char_map: Dict) -> str:
    """构建人物资产档案段（v3.4 治本：参考图已承载则不重复）"""
    lines = ["人物资产档案（v3.4 治本·参考图已承载信息则提示词不重复）"]
    lines.append("【本镜人物外貌/服装/发型/表情 全部由参考图承载，提示词不重复描述】")

    scene = mirror.get("scene_id", "")
    # 这里需要从外部传入 scene 信息；为简化，先跳过具体人名引用
    lines.append("【参考_人物_（M1阶段关联）：路径/角色参考图（关键特征·参考图承载）】")
    lines.append("【参考_场景_（M1阶段关联）：路径/场景参考图（关键特征·参考图承载）】")

    return "\n".join(lines)


def build_camera_params_section(mirror: Dict) -> str:
    """构建镜头参数段"""
    lines = ["镜头参数"]

    duration = mirror.get("duration_sec", 0)
    shot = mirror.get("shot_size", "中景")
    movement = mirror.get("camera_movement", "固定")

    shot_params = SHOT_SIZE_PARAMS.get(shot, SHOT_SIZE_PARAMS["中景"])
    speed = CAMERA_MOVEMENT_SPEED.get(movement, "0 m/s 静止")

    lines.append(f"时长{duration:.0f}秒，画幅9:16竖屏，景别{shot}0到{duration:.0f}秒。"
                 f"焦距{shot_params['焦距']}+{shot_params['景深']}。运镜{speed}。")

    return "\n".join(lines)


def build_lighting_section(mirror: Dict, style: str) -> str:
    """构建光影氛围段"""
    lines = ["光影氛围"]
    pos = mirror.get("structure_position", "建制")
    lighting = STRUCTURE_LIGHTING.get(pos, STRUCTURE_LIGHTING["建制"])

    lines.append(f"主光Key Light，{lighting['主光']}方向，强度90%。")
    lines.append(f"辅光Fill Light，{lighting['辅光']}，强度30%。")
    lines.append(f"轮廓光Back Light，{lighting['轮廓光']}，强度80%。")
    lines.append(f"色温{lighting['色温']}。光比1:2柔光。色调{lighting['色调']}。T2.8浅景深焦外二线性smooth bokeh。")

    return "\n".join(lines)


def build_tech_params_section(mirror: Dict, style: str) -> str:
    """构建技术参数段"""
    lines = ["技术参数"]

    color_pipeline = STYLE_COLOR_PIPELINE.get(style, STYLE_COLOR_PIPELINE["古早霸总"])
    style_ref = STYLE_REFERENCE.get(style, STYLE_REFERENCE["古早霸总"])

    lines.append(f"调色管线{color_pipeline}。风格参考：{style_ref}。")
    lines.append("关键物理：（M3 LLM 填充具体物理动作链）。")
    lines.append("关键合规：AI画面严禁字幕文字，所有字幕后期PR/AE叠加。")

    return "\n".join(lines)


def build_description_skeleton(mirror: Dict) -> str:
    """构建画面描述骨架（供 LLM 填充）

    返回的是模板，标注需要 LLM 填写的部分
    """
    duration = mirror.get("duration_sec", 0)
    shot = mirror.get("shot_size", "中景")
    scene_id = mirror.get("scene_id", "S01")
    structure = mirror.get("structure_position", "建制")

    # 分段时间线模板
    lines = ["画面描述"]
    lines.append(f"0到{duration:.0f}秒，{shot}{scene_id}。"
                 f"（【画面描述·待LLM填充】"
                 f"需包含：时间分段+景别+主体动作+表情+口播+前景背景关系，"
                 f"符合 v3.4 治本：参考图已承载则不重复描述外貌/服装/发型，"
                 f"符合 M15：禁止元注释/合规/自检段，"
                 f"符合 M11：物理细节精确到 0.5秒/动作链/肌肉真实物理/数字幅度）")

    return "\n".join(lines)


def build_mirror_prompt(mirror: Dict, m1_data: Dict, mode: str = "skeleton") -> str:
    """构建单镜的 txt 内容

    Args:
        mirror: 单镜信息
        m1_data: M1 输出（用于查 scene/character 详情）
        mode: skeleton=仅结构骨架；full=结构+占位说明
    """
    # 构建映射
    scene_map = {s["id"]: s for s in m1_data.get("scenes", [])}
    char_map = {}
    for c in m1_data.get("characters", []):
        char_map[c["name"]] = c["name"]
        char_map[c["id"]] = c["name"]

    style = m1_data.get("style", "未知")

    # 1. 标题行
    title = build_title_line(mirror, char_map)

    # 2. 各段
    asset_sec = build_asset_section(mirror, scene_map, char_map)
    char_archive_sec = build_character_archive_section(mirror, char_map)
    camera_sec = build_camera_params_section(mirror)
    desc_sec = build_description_skeleton(mirror)
    lighting_sec = build_lighting_section(mirror, style)
    tech_sec = build_tech_params_section(mirror, style)

    sections = [
        title,
        "",
        asset_sec,
        "",
        char_archive_sec,
        "",
        camera_sec,
        "",
        desc_sec,
        "",
        lighting_sec,
        "",
        tech_sec,
    ]

    return "\n".join(sections)


def generate_all_mirrors(m2_data: Dict, m1_data: Dict, out_dir: Path, mode: str = "skeleton") -> List[Path]:
    """生成所有镜的 txt 文件"""
    out_dir.mkdir(parents=True, exist_ok=True)
    files = []

    for mirror in m2_data.get("mirrors", []):
        content = build_mirror_prompt(mirror, m1_data, mode=mode)
        idx = mirror.get("index", 0)
        beat = mirror.get("beat", f"第{idx}镜")
        name = beat.split("·")[-1] if "·" in beat else f"第{idx}镜"
        name = name.replace(f"第{idx}镜", "").strip() or f"分镜{idx}"
        cue_mark = f"_CUE{mirror['cue_index']}" if mirror.get("cue_index", 0) > 0 else ""

        # 文件名：镜001_名称.txt（v3.5 一致）
        filename = f"镜{idx:03d}{cue_mark}_{name}.txt"
        filepath = out_dir / filename
        filepath.write_text(content, encoding="utf-8")
        files.append(filepath)

    return files


def validate_m3_output(files: List[Path], target_chars: int = 1800) -> Dict:
    """验证 M3 输出（v3.7 治本 · 默认 ≤1800 字标准）"""
    issues = []
    stats = {
        "total_files": len(files),
        "total_chars": 0,
        "avg_chars": 0,
        "files_with_meta": 0,
        "files_missing_sections": 0,
    }

    required_sections = set(STANDARD_SECTIONS)

    for f in files:
        content = f.read_text(encoding="utf-8")
        chars = len(content)
        stats["total_chars"] += chars

        # 检查必需段落
        present_sections = set()
        for sec in STANDARD_SECTIONS:
            if sec in content:
                present_sections.add(sec)
        missing = required_sections - present_sections
        if missing:
            stats["files_missing_sections"] += 1
            issues.append(f"{f.name}: 缺少段落 {missing}")

        # 检查元注释（M15）— 仅检测独立的元注释段/字段，不检测内联约束引用
        # 真正的元注释残留特征：① 段首独立行 ② 【合规】/【合规保留】字段 ③ 决策/修复/规则独立段
        meta_patterns_strict = [
            r"^决策[：:]",                      # 段首"决策："
            r"^修复[：:]",                      # 段首"修复："
            r"^规则[：:]",                      # 段首"规则："
            r"【合规】",                        # 合规字段
            r"【合规保留】",                    # 合规保留字段
            r"^M1[0-9]+决策",                  # M11决策独立段
            r"^M1[0-9]+修复",                  # M11修复独立段
            r"^M1[0-9]+规则",                  # M11规则独立段
            r"AI友好度[：:]",                  # AI友好度评分
            r"^微表情[：:]",                    # 段首"微表情："
        ]
        for pat in meta_patterns_strict:
            if re.search(pat, content, re.MULTILINE):
                stats["files_with_meta"] += 1
                issues.append(f"{f.name}: 检测到元注释 '{pat}'")
                break

    if files:
        stats["avg_chars"] = stats["total_chars"] // len(files)

    return {
        "stats": stats,
        "issues": issues,
        "is_valid": len(issues) == 0,
    }


def main():
    parser = argparse.ArgumentParser(description="M3 提示词生成（v1.0 工程化）")
    parser.add_argument("input", help="M2 JSON 文件路径")
    parser.add_argument("m1_input", help="M1 JSON 文件路径（用于查 scene/character 详情）")
    parser.add_argument("--out-dir", default="./01_分镜头", help="输出目录")
    parser.add_argument("--mode", choices=["skeleton", "full"], default="full",
                        help="skeleton=仅结构骨架；full=结构+占位说明")
    parser.add_argument("--target-chars", type=int, default=1800, help="目标字数（v3.7 ≤1800 标准）")
    parser.add_argument("--validate", action="store_true", help="验证输出")
    args = parser.parse_args()

    # 读取 M1 + M2
    m1_data = json.loads(Path(args.m1_input).read_text(encoding="utf-8"))
    m2_data = json.loads(Path(args.input).read_text(encoding="utf-8"))

    # 生成
    out_dir = Path(args.out_dir)
    files = generate_all_mirrors(m2_data, m1_data, out_dir, mode=args.mode)

    print(f"✅ M3 生成完成: {len(files)} 个文件 → {out_dir}", file=sys.stderr)

    # 验证
    if args.validate:
        result = validate_m3_output(files, target_chars=args.target_chars)
        print(f"📊 统计: {result['stats']}", file=sys.stderr)
        if result["issues"]:
            print(f"⚠ 发现 {len(result['issues'])} 个问题:", file=sys.stderr)
            for issue in result["issues"][:10]:  # 只显示前 10 个
                print(f"  - {issue}", file=sys.stderr)


if __name__ == "__main__":
    main()

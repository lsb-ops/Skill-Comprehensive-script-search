#!/usr/bin/env python3
"""
continuity_check.py — 多镜衔接校验

用法:
    python continuity_check.py <shot_dir>
    python continuity_check.py <shot_dir> --json

校验项:
    1. 站位一致性（180度轴线）
    2. 道具轨迹（跨镜位置连贯）
    3. CUE 节奏（时间点 + 效果）
    4. 字数校验（**≤1800 · v3.7 治本**）
    5. 风格一致性（色温/光比/视觉参考）
    6. v3.3 重构：场景空间坐标继承（坐标段末位置 → 下镜起点）
    7. v3.3 重构：道具状态继承（墨镜是否戴/手持）
    8. v3.3 重构：机位方向继承（朝北/朝南 持续）
"""

import sys
import json
import re
from pathlib import Path
from collections import defaultdict


def load_shots(shot_dir):
    """加载所有镜提示词

    支持多版本命名约定：
    - 镜001_v3.3_xxx.txt          (v3.3 单镜)
    - 镜002A_v3.3_xxx.txt         (v3.3 拆分后子镜)
    - 镜002B+003_v3.3_xxx.txt     (v3.3 合并镜: A/B + 后续镜号)
    - 镜007+008_v3.3_xxx.txt      (v3.3 合并镜: 无 A/B)
    - 镜010+011_v3.3_xxx.txt      (v3.3 合并镜: 无 A/B)
    - 镜001_xxx.txt               (v3.7 简化命名)

    匹配规则: 镜{N}{AB?}?{+\\d+}?(_v3\.3)?_xxx.txt
    """
    shot_dir = Path(shot_dir)
    shots = []

    # 匹配 v3.3 / v3.7 命名约定
    pattern = re.compile(r'镜(\d+)(?:([A-Z])?(?:\+(\d+))?)?(?:_v3\.3)?_.*\.txt')

    for file_path in sorted(shot_dir.glob("镜*.txt")):
        match = pattern.match(file_path.name)
        if match:
            shot_num = int(match.group(1))
            ab_suffix = match.group(2) or ""  # A / B / ''
            merge_num = match.group(3) or ""  # '003' / '008' / '011' / ''
            suffix = ab_suffix + (f"+{merge_num}" if merge_num else "")

            # 构造排序键：镜号 + 子镜权重（A=0.1, B=0.2, 合并+=0.5）
            sort_key = float(shot_num)
            if ab_suffix == "A":
                sort_key += 0.1
            elif ab_suffix == "B":
                sort_key += 0.2
            elif merge_num:
                # 合并镜放在主镜后
                sort_key += 0.5

            content = file_path.read_text(encoding="utf-8")
            shots.append({
                "num": shot_num,
                "suffix": suffix,
                "sort_key": sort_key,
                "name": file_path.stem,
                "content": content,
                "path": str(file_path),
            })

    shots.sort(key=lambda s: s["sort_key"])
    return shots


def extract_assets(content):
    """提取资产引用"""
    return re.findall(r'【([^】]+)】', content)


def extract_position(content, person_name):
    """提取人物位置"""
    # 兼容旧格式"资产人物XXX"和新格式"人物_XXX"
    patterns = [
        rf'(?:资产人物|人物_){person_name}[^，,。]*(在|从|位于)[^，,。]*(左|右|中)',
        rf'(?:资产人物|人物_){person_name}[^，,。]*(左侧|右侧|中间|居中)',
    ]

    for p in patterns:
        m = re.search(p, content)
        if m:
            return m.group(0)
    return None


def extract_color_temp(content):
    """提取色温"""
    pattern = r'(\d+)K'
    matches = re.findall(pattern, content)
    return [int(m) for m in matches]


def extract_cue(content):
    """提取 CUE 标记"""
    cues = []
    if "CUE①" in content or "CUE1" in content:
        cues.append("CUE①")
    if "CUE②" in content or "CUE2" in content:
        cues.append("CUE②")
    if "CUE③" in content or "CUE3" in content:
        cues.append("CUE③")
    return cues


def extract_duration(content):
    """提取时长"""
    m = re.search(r'时长(\d+(?:\.\d+)?)秒', content)
    if m:
        return float(m.group(1))
    return 0


def extract_lut(content):
    """提取 LUT"""
    luts = []
    for lut in ["Fuji Eterna", "Kodak 2383", "Warm Gold", "Bleach Bypass", "Teal & Orange"]:
        if lut in content:
            luts.append(lut)
    return luts


def count_chars(text):
    """计算字符数（去除空白）"""
    return len(re.sub(r'\s+', '', text))


def check_axis_continuity(shots):
    """检查站位一致性（v3.7 增强·识别跨镜承接标注）"""
    issues = []

    for i in range(1, len(shots)):
        prev = shots[i-1]
        curr = shots[i]

        # 提取人物位置（兼容旧格式"资产人物XXX"和新格式"人物_XXX"）
        # 仅对 prompt_body 生效（剥离本镜自检段）
        pattern = r'(?:资产人物|人物_)([一-龥]+)[^，,。]*(左侧|右侧|居中|中间)'
        prev_positions = re.findall(pattern, prev.get("prompt_body", prev["content"]))
        curr_positions = re.findall(pattern, curr.get("prompt_body", curr["content"]))

        # 比较相同人物的位置
        prev_dict = {p[0]: p[1] for p in prev_positions}
        curr_dict = {p[0]: p[1] for p in curr_positions}

        for person in prev_dict:
            if person in curr_dict:
                if prev_dict[person] != curr_dict[person]:
                    # v3.7 增强：识别跨镜承接标注
                    # 1. "轴线重建" / "跳轴"（v1.0 旧标注）
                    # 2. "承接镜00X" / "延续镜00X" / "位置重建"（v3.7 新标注）
                    # 3. 资产引用段含承接说明（v3.7 格式）
                    has_v37_inherit = bool(re.search(
                        r'(?:承接镜\d+|延续镜\d+|接镜\d+|位置重建|轴线重建|跳轴)',
                        curr["content"]
                    ))
                    # 检查资产引用段是否含承接说明
                    asset_inherit = re.search(
                        rf'(?:资产人物|人物_){person}[^】]*?(?:承接镜\d+|延续镜\d+|接镜\d+|位置重建)',
                        curr["content"]
                    )
                    has_asset_inherit = bool(asset_inherit)

                    if not (has_v37_inherit or has_asset_inherit):
                        issues.append({
                            "type": "axis_break",
                            "severity": "严重",
                            "shots": [prev["num"], curr["num"]],
                            "description": f"人物 {person} 位置跳变：{prev_dict[person]} → {curr_dict[person]}"
                        })

    return issues


def check_v37_position_inheritance(shots):
    """v3.7 治本·跨镜站位继承详细校验（KB04 第十三章强制约束）

    Why: 11 镜 v3.7 初版实测发现 4 处中重度站位问题（道具状态跳变/站位不明/角色离场无承接/位置漂移）。
         本校验作为 M4 衔接校验的强化版，从跨镜维度发现 v3.7 站位问题。

    校验项（4 子项）:
      1. 道具状态跳变（戴↔拿↔收 无过渡说明）
      2. 角色位置左↔右 跳变（潜在跳轴）
      3. 角色位置不明→明确（需补承接说明）
      4. 离场/入画无承接说明
    """
    issues = []

    for i in range(1, len(shots)):
        prev = shots[i-1]
        curr = shots[i]
        prev_body = prev.get("prompt_body", prev["content"])
        curr_body = curr.get("prompt_body", curr["content"])

        # === 1. 道具状态跳变检测 ===
        # 关键道具：墨镜、眼镜、名片、皮鞋
        key_props = ["墨镜", "眼镜", "名片", "皮鞋"]
        for prop in key_props:
            prev_state = _extract_prop_state(prev_body, prop)
            curr_state = _extract_prop_state(curr_body, prop)

            if prev_state and curr_state and prev_state != curr_state:
                # 检查是否标注了过渡说明（"戴回""收""拿出"等）
                has_transition = bool(re.search(
                    rf'道具_{prop}[^】]*?(戴上|戴回|摘下|收起|拿出|接过|手持|延续|→)',
                    curr_body
                ))
                if not has_transition:
                    issues.append({
                        "type": "v37_prop_state_jump",
                        "severity": "严重",
                        "shots": [prev["num"], curr["num"]],
                        "prop": prop,
                        "prev_state": prev_state,
                        "curr_state": curr_state,
                        "description": f"v3.7 治本·道具【{prop}】状态跳变：{prev_state} → {curr_state}（缺过渡动作说明）"
                    })

        # === 2. 角色位置左↔右 跳变检测（强化版） ===
        # 即使有"轴线重建"标注，但中间无重建镜头，仍然算潜在跳轴
        pattern_left_right = r'(?:资产人物|人物_)([一-龥]+)[^，,。]*?(左侧|左侧前景|前景左侧|右侧|右侧前景|前景右侧)'
        prev_lr = {m[0]: m[1] for m in re.findall(pattern_left_right, prev_body)}
        curr_lr = {m[0]: m[1] for m in re.findall(pattern_left_right, curr_body)}

        for person in prev_lr:
            if person in curr_lr:
                prev_side = "左" if "左" in prev_lr[person] else "右"
                curr_side = "左" if "左" in curr_lr[person] else "右"
                if prev_side != curr_side:
                    # 左↔右 跳变，且没有"位置重建""轴线重建"标注
                    has_rebuild = bool(re.search(r'位置重建|轴线重建|重建', curr_body))
                    if not has_rebuild:
                        issues.append({
                            "type": "v37_position_lr_jump",
                            "severity": "严重",
                            "shots": [prev["num"], curr["num"]],
                            "person": person,
                            "description": f"v3.7 治本·【人物_{person}】左右跳变：{prev_lr[person]} → {curr_lr[person]}（潜在跳轴风险，建议补'位置重建'说明）"
                        })

        # === 3. 角色位置不明→明确 检测 ===
        # 检测 002 末尾"前景模糊"+"镜003 明确位置" 类问题
        persons = ["刘一鸣", "小仇", "骆骆"]
        for person in persons:
            # 上镜"前景模糊"或"前景MCU模糊"位置不明
            prev_blur = bool(re.search(rf'(?:资产人物|人物_){person}[^】]*?前景(?:模糊|MCU模糊|CU模糊)', prev_body))
            # 本镜有明确位置（左/右/中）
            curr_clear = bool(re.search(rf'(?:资产人物|人物_){person}[^】]*?(?:左侧|右侧|居中|中|偏左|偏右)', curr_body))
            if prev_blur and curr_clear:
                # 检测承接说明
                has_inherit = bool(re.search(rf'(?:资产人物|人物_){person}[^】]*?(?:延续|承接|明确|继承)', curr_body))
                if not has_inherit:
                    issues.append({
                        "type": "v37_position_blur_to_clear",
                        "severity": "中等",
                        "shots": [prev["num"], curr["num"]],
                        "person": person,
                        "description": f"v3.7 治本·【人物_{person}】从'前景模糊'→'明确位置'，缺承接说明（建议补'明确左侧承接镜00X'类标注）"
                    })

        # === 4. 离场/入画无承接检测 ===
        # 上镜在场，本镜"画面外已离去"且无"承接镜"标注
        for person in persons:
            prev_in_scene = bool(re.search(rf'(?:资产人物|人物_){person}[^】]+', prev_body))
            # 排除"画面外"状态本身
            prev_off_screen = bool(re.search(rf'(?:资产人物|人物_){person}[^】]*?画面外', prev_body))
            curr_off_screen = bool(re.search(rf'(?:资产人物|人物_){person}[^】]*?画面外(?:已)?(?:离去|不在|离场)', curr_body))

            if prev_in_scene and not prev_off_screen and curr_off_screen:
                has_inherit_off = bool(re.search(rf'(?:资产人物|人物_){person}[^】]*?承接镜\d+', curr_body))
                if not has_inherit_off:
                    issues.append({
                        "type": "v37_off_screen_no_inherit",
                        "severity": "中等",
                        "shots": [prev["num"], curr["num"]],
                        "person": person,
                        "description": f"v3.7 治本·【人物_{person}】从在场→画面外离场，但缺'承接镜00X'标注"
                    })

    return issues


def _extract_prop_state(content, prop_name):
    """提取道具状态描述"""
    # 在【道具_XXX：...】中找状态关键词
    pattern = rf'道具_{prop_name}[：:]([^】]+)'
    m = re.search(pattern, content)
    if m:
        desc = m.group(1)
        # 提取状态关键词
        states = ["戴在脸上", "戴在", "戴回", "戴着", "拿在手里", "拿在", "手持",
                  "收于内袋", "收于", "收起", "接过", "拿住", "放在"]
        for state in states:
            if state in desc:
                return state
    return None


def check_word_counts(shots):
    """检查每镜字数（v3.7 治本 · ≤1800 标准）"""
    issues = []

    for shot in shots:
        # v3.3 字数检查只对 prompt_body 生效（剥离本镜自检段）
        prompt_body = shot.get("prompt_body", shot["content"])
        count = count_chars(prompt_body)
        if count < 1400:
            issues.append({
                "type": "word_count",
                "severity": "严重",
                "shots": [shot["num"]],
                "description": f"镜 {shot['num']:03d} 字数过少：{count}（< 1400 · v3.7 治本）"
            })
        elif count > 2400:
            issues.append({
                "type": "word_count",
                "severity": "严重",
                "shots": [shot["num"]],
                "description": f"镜 {shot['num']:03d} 字数过多：{count}（> 2400 · 失控）"
            })
        elif count < 1800:
            # 标准区间：1400-1800（v3.7 治本）
            pass  # 通过
        elif count <= 2200:
            issues.append({
                "type": "word_count",
                "severity": "一般",
                "shots": [shot["num"]],
                "description": f"镜 {shot['num']:03d} 字数偏多：{count}（v3.7 标准 ≤1800）"
            })
        else:
            issues.append({
                "type": "word_count",
                "severity": "严重",
                "shots": [shot["num"]],
                "description": f"镜 {shot['num']:03d} 字数过多：{count}（v3.7 强约束 ≤1800）"
            })

    return issues


def check_cue_rhythm(shots):
    """检查 CUE 节奏（v3.3 仅对 prompt_body 生效）

    v3.3 设计说明：v3.3 在剧本中标注了更多 CUE 节点（登场/相撞/摘墨镜/CUE①/CUE②/CUE③），
    这些是导演意图标记，不是 Style Switch 节点。
    因此 v3.3 模式下，CUE 节点上限提升到 12（剧本中 ~93s 内的合理密度）。
    """
    issues = []

    # 收集所有 CUE
    cue_shots = []
    cumulative_time = 0
    for shot in shots:
        # 使用 prompt_body 而非 content
        prompt_body = shot.get("prompt_body", shot["content"])
        cues = extract_cue(prompt_body)
        for cue in cues:
            cue_shots.append({
                "cue": cue,
                "shot_num": shot["num"],
                "time": cumulative_time,
                "duration": extract_duration(prompt_body),
            })
        cumulative_time += extract_duration(prompt_body)

    # 检查 CUE 数量（v3.3 模式上限 12）
    CUE_MAX_V33 = 12
    if len(cue_shots) > CUE_MAX_V33:
        issues.append({
            "type": "cue_count",
            "severity": "严重",
            "shots": [c["shot_num"] for c in cue_shots],
            "description": f"CUE 数量过多：{len(cue_shots)}（v3.3 上限 {CUE_MAX_V33}）"
        })

    # 检查 CUE 间隔（v3.3 模式 ≤ 20 秒为警告）
    for i in range(1, len(cue_shots)):
        prev = cue_shots[i-1]
        curr = cue_shots[i]
        gap = curr["time"] - prev["time"]
        if gap < 5:  # 5 秒内不允许 2 个 CUE
            issues.append({
                "type": "cue_gap",
                "severity": "一般",
                "shots": [prev["shot_num"], curr["shot_num"]],
                "description": f"CUE 间隔过短：{prev['cue']} → {curr['cue']} = {gap:.1f} 秒（< 5s）"
            })

    return cue_shots, issues


def check_color_temp_curve(shots):
    """检查色温曲线连贯性"""
    issues = []

    prev_temp = None
    for shot in shots:
        # 使用 prompt_body 避免自检段误判
        prompt_body = shot.get("prompt_body", shot["content"])
        temps = extract_color_temp(prompt_body)
        if not temps:
            continue

        # 取第一个色温作为代表
        curr_temp = temps[0]

        if prev_temp is not None:
            diff = abs(curr_temp - prev_temp)
            # 跳变 > 1500K 但无过渡说明
            if diff > 1500 and "色温跳变" not in shot["content"]:
                issues.append({
                    "type": "color_temp_jump",
                    "severity": "一般",
                    "shots": [shot["num"]],
                    "description": f"色温跳变过大但无说明：{prev_temp}K → {curr_temp}K"
                })

        prev_temp = curr_temp

    return issues


def check_asset_continuity(shots):
    """检查资产延续关系（仅对 prompt_body 生效）

    v3.3 设计：v3.3 用"场景空间坐标"段代替"延续"字样。
    资产引用段（在镜001后的镜）应使用"继承镜00X末"或"画面外"等标注。
    本检查同时扫描"资产引用"段和"场景空间坐标"段，确认有 继承/画面外 标注。
    """
    issues = []

    # 检查每镜是否标注了延续关系
    for shot in shots:
        prompt_body = shot.get("prompt_body", shot["content"])

        # 同时检查"资产引用"段和"场景空间坐标"段
        asset_section_match = re.search(r'资产引用\s*\n(.*?)(?=\n\n|镜头参数|画面描述|光影氛围|技术参数|$)',
                                          prompt_body, re.DOTALL)
        scene_section_match = re.search(r'场景空间坐标\s*\n(.*?)(?=\n\n|资产引用|镜头参数|画面描述|$)',
                                          prompt_body, re.DOTALL)

        combined_section = ""
        if asset_section_match:
            combined_section += asset_section_match.group(1)
        if scene_section_match:
            combined_section += scene_section_match.group(1)

        # 提取【人物_xxx】和【道具_xxx】格式的资产条目
        asset_entries = re.findall(r'【(?:人物|道具)_([^】]+)】', combined_section)
        for asset in asset_entries:
            # v3.3 不要求"延续"字样（已用"继承"+场景空间坐标段代替）
            # 但仍要求"继承"或"画面外"（任一段出现即可）
            if "继承" not in asset and "画面外" not in asset:
                # 检查是否为首镜
                if shot["num"] > 1:
                    issues.append({
                        "type": "asset_no_continuity",
                        "severity": "一般",
                        "shots": [shot["num"]],
                        "description": f"资产 {asset[:50]} 缺少继承/画面外标注"
                    })
                    break  # 每镜只报告一次

    return issues


def check_lut_consistency(shots):
    """检查 LUT 一致性"""
    issues = []

    all_luts = set()
    for shot in shots:
        luts = extract_lut(shot["content"])
        all_luts.update(luts)

    # 基础 LUT 应保持一致
    base_luts = {"Fuji Eterna", "Kodak 2383", "Teal & Orange", "Bleach Bypass"}
    found_base = base_luts & all_luts

    if len(found_base) > 1:
        issues.append({
            "type": "lut_inconsistent",
            "severity": "一般",
            "shots": [],
            "description": f"基础 LUT 不一致：{found_base}（建议统一）"
        })

    return issues


# 自检段分隔符：v3.3 txt 文件末尾的"本镜自检·M9+M12+M13"段是元注释
SELF_CHECK_MARKER = "【本镜自检"


def strip_self_check(content):
    """剥离本镜自检段（v3.3 元注释）

    为什么要剥离：v3.3 txt 文件末尾的"本镜自检·M9+M12+M13"段是元注释，
    包含"摘墨镜 CUE①"等修复声明，会被误判为 CUE 标记。
    返回实际提示词内容。
    """
    idx = content.find(SELF_CHECK_MARKER)
    if idx == -1:
        return content
    return content[:idx]


# ========================================
# v3.3 重构新增：场景空间坐标 / 道具状态 / 机位方向 继承校验
# ========================================

def extract_end_position(content):
    """提取本镜末位置（继承给下镜的坐标）"""
    # 从"上镜→本镜位移"段提取末位置
    end_positions = {}

    # 匹配 镜{NN}{A/B?}_ 末位置: 居中/左侧/右侧/前景/背景
    # 简化提取: 从资产引用段查找
    pattern = r'(?:资产人物|人物_)([一-龥]+)[^】]*?(居中|前景|背景|左侧|右侧|中央|左下|右下)'
    matches = re.findall(pattern, content)
    for person, pos in matches:
        end_positions[person] = pos

    return end_positions


def extract_start_position(content):
    """提取本镜起点位置（从上镜继承而来）"""
    # 从"场景空间坐标"段提取
    pattern = r'(?:人物|资产人物)_([一-龥]+)坐标[：:]\s*([^\n（(]+)'
    matches = re.findall(pattern, content)
    start_positions = {}
    for person, pos in matches:
        # 提取位置关键词
        pos_clean = pos.strip()
        for keyword in ["居中", "前景", "背景", "左侧", "右侧", "中央", "左下", "右下", "画面外"]:
            if keyword in pos_clean:
                start_positions[person] = keyword
                break
    return start_positions


def check_scene_space_inheritance(shots):
    """v3.3 校验：场景空间坐标段末位置 → 下镜起点位置 一致性"""
    issues = []

    for i in range(1, len(shots)):
        prev = shots[i-1]
        curr = shots[i]

        # 使用 prompt_body 而非 content（剥离本镜自检段）
        prev_body = prev.get("prompt_body", prev["content"])
        curr_body = curr.get("prompt_body", curr["content"])

        # 提取上镜末位置（从资产引用/画面描述）
        prev_end = extract_end_position(prev_body)
        # 提取本镜起点位置（从场景空间坐标段）
        curr_start = extract_start_position(curr_body)

        # 比较相同人物
        for person in prev_end:
            if person in curr_start:
                if prev_end[person] != curr_start[person]:
                    # 允许：上镜末"画面外" → 本镜"画面外"（保持画面外）
                    # 允许：上镜末"前景" → 本镜"居中"（位移合法）
                    # 严格校验：完全相同才通过
                    if "继承" in curr["content"] or prev_end[person] == "画面外":
                        continue
                    issues.append({
                        "type": "v33_position_break",
                        "severity": "一般",
                        "shots": [prev["num"], curr["num"]],
                        "person": person,
                        "description": f"v3.3 空间坐标断链：{person} 末位置={prev_end[person]} → 本镜起点={curr_start[person]}（应有继承说明）"
                    })

    return issues


def check_prop_state_inheritance(shots):
    """v3.3 校验：道具状态（墨镜/杯子/领带）跨镜一致（仅 prompt_body）

    改进：从"道具状态"段（场景空间坐标内的道具状态行）直接读取末状态。
    """
    issues = []

    # 关键道具：墨镜（戴/手持/无）
    for i in range(1, len(shots)):
        prev = shots[i-1]
        curr = shots[i]

        # 仅对 prompt_body 生效（剥离本镜自检段）
        prev_body = prev.get("prompt_body", prev["content"])
        curr_body = curr.get("prompt_body", curr["content"])

        # 上镜末墨镜状态（从"道具状态"段读取末状态）
        prev_end_state = extract_prop_state(prev_body, "墨镜", position="end")
        # 本镜墨镜状态（从"道具状态"段读取起点状态）
        curr_state = extract_prop_state(curr_body, "墨镜", position="start")

        if not prev_end_state or not curr_state:
            continue

        if prev_end_state != curr_state:
            # 允许的转换：戴→摘（CUE①摘墨镜镜004A）
            # 允许的转换：摘→手持（镜009A/镜010+011）
            # 允许的转换：手持→无（镜010+011 升华段）
            allowed_transitions = {
                ("戴", "摘"), ("戴", "无"),
                ("摘", "手持"), ("摘", "无"),
                ("手持", "无"),
            }
            if (prev_end_state, curr_state) in allowed_transitions:
                continue
            issues.append({
                "type": "v33_prop_state_break",
                "severity": "一般",
                "shots": [prev["num"], curr["num"]],
                "description": f"v3.3 道具状态断链：墨镜 {prev_end_state} → {curr_state}"
            })

    return issues


def extract_prop_state(content, prop_name, position="start"):
    """从"道具状态"段提取指定道具的状态

    position: "start" 提取本镜起点状态（默认）
              "end"   提取本镜末状态（从"本镜末X→Y"格式读取）

    支持格式:
    - 道具状态：墨镜戴在刘一鸣脸上（本镜末摘下→拿在手里）  →  start=戴, end=手持
    - 道具状态：墨镜戴在刘一鸣脸上（继承镜001）             →  start=戴, end=戴
    - 道具状态：墨镜拿在刘一鸣手里                            →  start=手持, end=手持
    - 道具状态：墨镜拿在刘一鸣手里（本镜无墨镜·传递到下镜） →  start=手持, end=手持（本镜无=本镜不戴=仍手持）

    关键修复：只有"本镜末X"格式的明确转换才提取末状态。
    "本镜无" 不被视为末状态转换（"无"在本镜上下文中意为"不戴"，仍持有）。
    """
    # 查找"道具状态"段
    m = re.search(r'道具状态[：:]\s*([^\n]+)', content)
    if not m:
        return None
    state_text = m.group(1)

    if prop_name not in state_text:
        return None

    # 拆分：起点描述 和 本镜末X→Y 描述
    if position == "end":
        # 关键：必须找到 "本镜末X→Y" 格式（X是状态变化前，Y是状态变化后）
        end_match = re.search(r'本镜末([^→\n]+)→([^)\n]+)', state_text)
        if end_match:
            # 取箭头后的末状态
            state_text = end_match.group(2)
        else:
            # 没有明确的本镜末X→Y 转换，末状态 = 起点状态
            state_text = state_text.split("（")[0]  # 取括号前的部分

    # 判断状态（按优先级：摘 > 手持 > 戴 > 无）
    if "摘下" in state_text or "摘掉" in state_text:
        return "摘"
    if "拿在" in state_text or "手持" in state_text:
        return "手持"
    if "戴在" in state_text or "戴着" in state_text:
        return "戴"
    # "无"判定需谨慎：本镜无X 在 v3.3 上下文意为"不戴"，仍持有
    # 只有 prop_name + 已离场 才视为真正"无"
    if prop_name + "已离场" in state_text:
        return "无"
    return None


def check_camera_direction_inheritance(shots):
    """v3.3 校验：机位方向（朝北/朝南）跨镜一致（仅 prompt_body）

    设计说明：
    - 镜001 设定基线机位（开篇贴地仰拍为朝南特殊设定）
    - 从镜002 起，基线为朝北
    - 镜006 反打机位是明文标注的机位跳转，必须有"反打"或"轴线重建"说明
    - 镜001 → 镜002 的朝南→朝北 切换为开篇→常规 切换，不需要反打标注
    """
    issues = []

    prev_direction = None
    for i, shot in enumerate(shots):
        # 仅对 prompt_body 生效
        prompt_body = shot.get("prompt_body", shot["content"])
        # 提取本镜机位方向
        m = re.search(r'机位方向[：:]\s*朝([东南西北])', prompt_body)
        curr_direction = m.group(1) if m else None

        # 镜001 设定基线，不检查（开篇贴地仰拍为常规设计）
        if i == 0:
            prev_direction = curr_direction
            continue

        if prev_direction and curr_direction and prev_direction != curr_direction:
            # 允许：机位切换必须有"反打"或"轴线重建"标注
            # 允许：镜001→镜002 的朝南→朝北 切换（开篇→常规）
            is_opening_transition = (i == 1 and prev_direction == "南" and curr_direction == "北")
            if is_opening_transition:
                prev_direction = curr_direction
                continue
            if "反打" not in shot["content"] and "轴线重建" not in shot["content"]:
                issues.append({
                    "type": "v33_camera_direction_break",
                    "severity": "一般",
                    "shots": [shot["num"]],
                    "description": f"v3.3 机位方向跳变：朝{prev_direction} → 朝{curr_direction}（缺少反打标注）"
                })

        if curr_direction:
            prev_direction = curr_direction

    return issues


def generate_report(shots):
    """生成完整校验报告"""
    all_issues = []

    # 剥离本镜自检段（v3.3 元注释），避免 CUE/道具状态误判
    for shot in shots:
        shot["prompt_body"] = strip_self_check(shot["content"])

    # v1.0 基础校验
    axis_issues = check_axis_continuity(shots)
    word_issues = check_word_counts(shots)
    cue_shots, cue_issues = check_cue_rhythm(shots)
    temp_issues = check_color_temp_curve(shots)
    asset_issues = check_asset_continuity(shots)
    lut_issues = check_lut_consistency(shots)

    # v3.3 重构新增校验
    v33_pos_issues = check_scene_space_inheritance(shots)
    v33_prop_issues = check_prop_state_inheritance(shots)
    v33_cam_issues = check_camera_direction_inheritance(shots)

    # v3.7 治本新增：跨镜站位继承详细校验（KB04 第十三章强制约束）
    v37_pos_inherit_issues = check_v37_position_inheritance(shots)

    all_issues.extend(axis_issues)
    all_issues.extend(word_issues)
    all_issues.extend(cue_issues)
    all_issues.extend(temp_issues)
    all_issues.extend(asset_issues)
    all_issues.extend(lut_issues)
    all_issues.extend(v33_pos_issues)
    all_issues.extend(v33_prop_issues)
    all_issues.extend(v33_cam_issues)
    all_issues.extend(v37_pos_inherit_issues)

    # 统计
    total_critical = sum(1 for i in all_issues if i["severity"] == "严重")
    total_warning = sum(1 for i in all_issues if i["severity"] == "一般")
    total = len(all_issues)

    return {
        "total_shots": len(shots),
        "total_cue": len(cue_shots),
        "v33_position_breaks": len(v33_pos_issues),
        "v33_prop_breaks": len(v33_prop_issues),
        "v33_camera_breaks": len(v33_cam_issues),
        "v37_position_inherit_breaks": len(v37_pos_inherit_issues),
        "issues": all_issues,
        "issue_count": {
            "total": total,
            "critical": total_critical,
            "warning": total_warning,
        },
        "pass_rate": max(0, 100 - total * 2),  # 每个问题扣 2 分
    }


def print_report(report, shots):
    """打印报告"""
    print("=" * 70)
    print("M4 衔接校验报告 v2.0（v3.3 重构增强）")
    print("=" * 70)

    print(f"\n基本信息：")
    print(f"  总镜数：{report['total_shots']}")
    print(f"  CUE 数：{report['total_cue']}")
    print(f"  通过率：{report['pass_rate']}%")

    print(f"\nv3.3 重构继承校验：")
    print(f"  空间坐标断链：{report['v33_position_breaks']}")
    print(f"  道具状态断链：{report['v33_prop_breaks']}")
    print(f"  机位方向跳变：{report['v33_camera_breaks']}")

    print(f"\nv3.7 治本·跨镜站位继承校验（KB04 第十三章强制约束）：")
    print(f"  站位继承断链：{report['v37_position_inherit_breaks']}")
    if report['v37_position_inherit_breaks'] > 0:
        v37_issues = [i for i in report['issues'] if i['type'].startswith('v37_')]
        for issue in v37_issues[:5]:
            print(f"    - [{issue['severity']}] {issue['description']}")
        if len(v37_issues) > 5:
            print(f"    ... 还有 {len(v37_issues) - 5} 个问题")

    print(f"\n问题统计：")
    print(f"  严重：{report['issue_count']['critical']}")
    print(f"  一般：{report['issue_count']['warning']}")
    print(f"  总计：{report['issue_count']['total']}")

    if report['issues']:
        print(f"\n详细问题：")
        # 按严重程度分组
        critical = [i for i in report['issues'] if i['severity'] == '严重']
        warning = [i for i in report['issues'] if i['severity'] == '一般']

        if critical:
            print(f"\n  严重问题：")
            for i, issue in enumerate(critical, 1):
                print(f"    {i}. {issue['description']}")
                if issue['shots']:
                    print(f"       涉及镜：{issue['shots']}")

        if warning:
            print(f"\n  一般问题：")
            for i, issue in enumerate(warning, 1):
                print(f"    {i}. {issue['description']}")
                if issue['shots']:
                    print(f"       涉及镜：{issue['shots']}")

    # 各镜摘要
    print(f"\n各镜摘要：")
    for shot in shots:
        count = count_chars(shot["content"])
        cues = extract_cue(shot["content"])
        cue_str = f" [{','.join(cues)}]" if cues else ""
        suffix_str = shot.get("suffix", "") or ""
        print(f"  镜{shot['num']:03d}{suffix_str}：{count} 字{cue_str}")


def main():
    if len(sys.argv) < 2:
        print("用法: python continuity_check.py <镜提示词目录>")
        sys.exit(1)

    shot_dir = Path(sys.argv[1])
    if not shot_dir.exists():
        print(f"错误: 目录不存在: {shot_dir}")
        sys.exit(1)

    shots = load_shots(shot_dir)
    if not shots:
        print(f"未找到镜提示词文件（应命名为 镜XXX_xxx.txt）")
        sys.exit(1)

    report = generate_report(shots)

    if "--json" in sys.argv:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_report(report, shots)


if __name__ == "__main__":
    main()

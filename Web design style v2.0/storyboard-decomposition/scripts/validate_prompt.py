#!/usr/bin/env python3
"""
validate_prompt.py v2.2 — 单镜提示词校验（M13 v3.3 重构自检 + M14 v3.4 治本 + M15 v3.5 治本 + v3.7 治本·跨镜站位继承）

用法:
    python validate_prompt.py <prompt_file>
    python validate_prompt.py <prompt_file> --json
    python validate_prompt.py <dir> --batch  # 批量校验目录下所有 txt

校验项:
  v1.0 基础 (8 项)
    1. 字数（v3.7 治本：1400-2400 警告 / ≤1800 标准）
    2. 5段式结构完整性
    3. 资产引用规范
    4. 镜头参数完整性（12 核心参数）
    5. 画面描述时序分段
    6. 光影氛围三点布光
    7. 负面约束（字幕）
    8. 剧本原词保留
  v2.0 M13 新增（6 项 · 约束 19-21）
    9.  物理细节数 ≤ 时长上限（≤5s ≤4 / 6s ≤6 / 7-8s ≤8 / 9-10s ≤8）
    10. 无"补充物理细节"段
    11. 无"延续镜00X"文字锚点
    12. 场景空间坐标段存在（6 字段）
    13. 机位方向行存在
    14. 无反作用力/抛物线/帧率切换/微距离黑名单词
  v2.1 M14 新增（1 项 · 约束 23 · v3.4 治本）
    15. 人物资产档案段不得重复描述参考图已承载信息（年龄/服装/发型/表情/道具外观/场景细节）
  v3.7 治本新增（1 项 · 约束 27 · 跨镜站位继承 · KB04 第十三章）
    16. 跨镜站位继承（4 子项：站位明确/跨镜延续标注/道具状态延续/离场入画承接）
"""

import sys
import json
import re
import os
from pathlib import Path


# 5段式结构的关键词标识
SECTION_KEYWORDS = {
    "资产引用": ["资产引用", "【资产人物", "【资产道具", "【场景图"],
    "镜头参数": ["镜头参数", "时长", "画幅", "景别", "焦距", "运镜"],
    "画面描述": ["画面描述", "0到"],
    "光影氛围": ["光影氛围", "主光", "辅光", "轮廓光", "色温", "光比"],
    "技术参数": ["技术参数", "调色管线", "Fuji", "风格参考", "关键合规", "严禁"],
}


# 12 核心参数
CORE_PARAMETERS = {
    "时长": r"时长\d+秒",
    "画幅": r"画幅\s*\d+[比:：]\d+",  # 接受 9比16 / 9:16 / 9：16
    "景别": r"(MS|CU|ECU|MCU|MLS|FS|LS|ELS|中景|近景|特写|远景|全景)",
    "焦距": r"\d+毫米",
    "运镜": r"(Dolly|Pan|固定|推|拉|摇|移|跟|升降)",
    "色温": r"\d+K",
    "光比": r"光比\s*\d+[比:：]\d+",  # 接受 1比3 / 1:3 / 1：3
}


# 负面约束关键词
NEGATIVE_CONSTRAINTS = [
    "AI画面严禁字幕文字",
    "严禁字幕",
    "后期PR",
    "后期AE",
]


# M13 v2.0 新增：物理细节数按时长分级
PHYSICAL_DETAIL_LIMITS = {
    "≤5s": 4,
    "6s": 6,
    "7-8s": 8,
    "9-10s": 8,
    "11-15s": 8,
}


# M13 v2.0 新增：黑名单词
BLACKLIST_WORDS = {
    "反作用力": r"反作用力",
    "抛物线": r"抛物线",
    "帧率切换": r"\d+fps\s*[→\->]+\s*\d+fps",
    "微距离_秒级": r"\d+\.\d+/\d+\.\d+秒",  # 如"0.05/0.1秒"
    "微距离_毫米": r"\d+mm\s*距离",  # 如"0.3cm眉骨距离"
}


# 自检段分隔符：跳过 【本镜自检·M9+M12+M13】 后的所有元注释
SELF_CHECK_MARKER = "【本镜自检"


def strip_self_check_section(text):
    """剥离本镜自检段（M13 校验只对实际提示词内容生效）

    为什么需要：v3.3 txt 文件末尾的 "本镜自检·M9+M12+M13" 段是元注释，
    包含反作用力/抛物线/延续镜00X 等字样的"删除声明"或"修复说明"，
    误判为违反约束。本函数返回实际提示词内容。
    """
    idx = text.find(SELF_CHECK_MARKER)
    if idx == -1:
        return text
    return text[:idx]


# 场景空间坐标段关键词
SCENE_SPACE_KEYWORDS = [
    "场景空间坐标",
    "场景拓扑",
    "坐标",
    "机位方向",
    "上镜→本镜位移",
    "道具状态",
]


def count_chars(text):
    """计算中文字符数（去除空白）"""
    text_no_space = re.sub(r'\s+', '', text)
    return len(text_no_space)


def extract_duration(text):
    """从镜{NN} {主题} {时长}秒 中提取时长"""
    # 匹配 "时长 X 秒" 或 "X秒" 模式
    match = re.search(r'时长\s*(\d+(?:\.\d+)?)\s*秒', text)
    if match:
        return float(match.group(1))
    # 备选：镜XXX 主题 X秒
    match = re.search(r'镜\d+[A-Za-z+]*\s+\S+\s+(?:\S+\s+)?(\d+(?:\.\d+)?)秒', text)
    if match:
        return float(match.group(1))
    return None


def get_physical_detail_limit(duration):
    """按时长返回物理细节上限"""
    if duration is None:
        return 8
    if duration <= 5:
        return 4
    elif duration <= 6:
        return 6
    elif duration <= 8:
        return 8
    elif duration <= 10:
        return 8
    else:
        return 8


def count_physical_details(text):
    """统计物理细节数

    规则：物理细节1、物理细节2...  编号
    """
    # 匹配 "物理细节N：" 或 "物理细节N "
    pattern = r'物理细节\s*\d+[：:、]'
    matches = re.findall(pattern, text)
    return len(matches)


def check_sections(text):
    """检查5段式结构完整性"""
    issues = []
    found_sections = {}

    for section, keywords in SECTION_KEYWORDS.items():
        found = any(kw in text for kw in keywords)
        found_sections[section] = found
        if not found:
            issues.append({
                "type": "section_missing",
                "section": section,
                "severity": "严重",
                "description": f"缺少段：{section}"
            })

    return found_sections, issues


def check_word_count(text):
    """检查字数（v3.7 治本 · ≤1800 标准）"""
    count = count_chars(text)
    issues = []

    if count < 1400:
        issues.append({
            "type": "word_count",
            "severity": "严重",
            "description": f"字数过少：{count}（< 1400）"
        })
    elif count < 1800:
        issues.append({
            "type": "word_count",
            "severity": "信息",
            "description": f"字数达标：{count}（≤1800 标准 · v3.7）"
        })
    elif count <= 2200:
        issues.append({
            "type": "word_count",
            "severity": "一般",
            "description": f"字数偏多：{count}（v3.7 标准 ≤1800）"
        })
    elif count <= 2400:
        issues.append({
            "type": "word_count",
            "severity": "严重",
            "description": f"字数过多：{count}（v3.7 强约束 ≤1800）"
        })
    else:
        issues.append({
            "type": "word_count",
            "severity": "严重",
            "description": f"字数严重过多：{count}（> 2400 · 失控）"
        })

    return count, issues


def check_core_parameters(text):
    """检查12核心参数"""
    issues = []
    found_params = {}

    for param, pattern in CORE_PARAMETERS.items():
        found = bool(re.search(pattern, text))
        found_params[param] = found
        if not found:
            issues.append({
                "type": "param_missing",
                "param": param,
                "severity": "一般",
                "description": f"缺少核心参数：{param}"
            })

    return found_params, issues


def check_time_sequence(text):
    """检查画面描述的时序分段"""
    issues = []

    pattern = r'0到\d+(\.\d+)?秒'
    matches = re.findall(pattern, text)

    if len(matches) < 3:
        issues.append({
            "type": "time_sequence",
            "severity": "一般",
            "description": f"时序分段过少：{len(matches)} 个（建议至少 3 个）"
        })

    return matches, issues


def check_three_point_lighting(text):
    """检查三点布光"""
    issues = []

    key_light = "主光" in text or "Key Light" in text
    fill_light = "辅光" in text or "Fill Light" in text
    back_light = "轮廓光" in text or "Back Light" in text or "Rim Light" in text

    if not key_light:
        issues.append({
            "type": "lighting",
            "severity": "一般",
            "description": "缺少主光 Key Light 描述"
        })
    if not fill_light:
        issues.append({
            "type": "lighting",
            "severity": "一般",
            "description": "缺少辅光 Fill Light 描述"
        })
    if not back_light:
        issues.append({
            "type": "lighting",
            "severity": "一般",
            "description": "缺少轮廓光 Back Light 描述"
        })

    return {
        "key_light": key_light,
        "fill_light": fill_light,
        "back_light": back_light,
    }, issues


def check_negative_constraints(text):
    """检查负面约束"""
    issues = []
    found = []

    for constraint in NEGATIVE_CONSTRAINTS:
        if constraint in text:
            found.append(constraint)

    if not found:
        issues.append({
            "type": "constraint",
            "severity": "严重",
            "description": "缺少字幕负面约束（如 'AI画面严禁字幕文字'）"
        })

    return found, issues


def check_asset_references(text):
    """检查资产引用规范"""
    issues = []

    new_format_pattern = r'【(人物|道具|场景)_([^：】]+)(：[^】]*)?】'
    new_format_matches = re.findall(new_format_pattern, text)

    old_format = re.findall(r'【资产[人物道具场景][^】]*】', text)
    all_brackets = re.findall(r'【([^】]+)】', text)

    if not all_brackets:
        issues.append({
            "type": "asset",
            "severity": "严重",
            "description": "缺少【类型_XXX】资产引用"
        })

    if old_format:
        issues.append({
            "type": "asset_legacy_format",
            "severity": "建议",
            "description": f"使用了已废弃的旧格式: {old_format}"
        })

    wrong_brackets = re.findall(r'\[(人物|道具|场景)_[^\]]+\]', text)
    if wrong_brackets:
        issues.append({
            "type": "asset_format",
            "severity": "一般",
            "description": f"资产引用使用了 [] 而非 【】: {wrong_brackets}"
        })

    asset_stats = {
        "人物": sum(1 for m in new_format_matches if m[0] == "人物"),
        "道具": sum(1 for m in new_format_matches if m[0] == "道具"),
        "场景": sum(1 for m in new_format_matches if m[0] == "场景"),
    }

    return {
        "all_brackets": all_brackets,
        "new_format_matches": new_format_matches,
        "old_format_uses": len(old_format),
        "asset_stats": asset_stats,
    }, issues


def check_original_text(text):
    """检查剧本原词标注"""
    issues = []

    if "剧本原词" not in text:
        issues.append({
            "type": "script_text",
            "severity": "一般",
            "description": "缺少 '剧本原词' 标注（用于保留对白/舞台指示）"
        })

    return "剧本原词" in text, issues


# ========================================
# M13 v2.0 新增校验项（约束 19-21）
# ========================================

def check_physical_details(text):
    """M13 约束 19：物理细节数 ≤ 时长上限"""
    issues = []
    duration = extract_duration(text)
    detail_count = count_physical_details(text)
    limit = get_physical_detail_limit(duration)

    if duration is None:
        issues.append({
            "type": "m13_duration_parse_failed",
            "severity": "警告",
            "description": "无法解析时长，跳过物理细节数校验"
        })
        return {
            "duration": None,
            "detail_count": detail_count,
            "limit": None,
            "passed": None
        }, issues

    passed = detail_count <= limit
    severity = "严重" if not passed else "通过"

    if not passed:
        issues.append({
            "type": "m13_physical_details_exceeded",
            "severity": severity,
            "description": f"物理细节数={detail_count} 超过上限 {limit}（时长={duration}s）"
        })

    return {
        "duration": duration,
        "detail_count": detail_count,
        "limit": limit,
        "passed": passed
    }, issues


def check_no_supplementary_section(text):
    """M13 约束 20：无'补充物理细节'段"""
    issues = []
    has_section = "补充物理细节" in text

    if has_section:
        issues.append({
            "type": "m13_supplementary_section_exists",
            "severity": "严重",
            "description": "存在'补充物理细节'段（M13 强制删除）"
        })

    return {"has_section": has_section, "passed": not has_section}, issues


def check_no_text_anchors(text):
    """M13 约束 20：无'延续镜00X'文字锚点"""
    issues = []
    pattern = r'延续镜\d+|承接镜\d+结尾|延续镜\d+到\d+'
    matches = re.findall(pattern, text)

    if matches:
        issues.append({
            "type": "m13_text_anchor_exists",
            "severity": "严重",
            "description": f"存在文字锚点: {matches}（AI 0% 识别）"
        })

    return {"matches": matches, "passed": len(matches) == 0}, issues


def check_scene_space_coordinates(text):
    """M13 约束 14：场景空间坐标段存在（6 字段）"""
    issues = []
    found_keywords = [kw for kw in SCENE_SPACE_KEYWORDS if kw in text]

    missing = [kw for kw in SCENE_SPACE_KEYWORDS if kw not in text]
    if missing:
        issues.append({
            "type": "m13_scene_space_incomplete",
            "severity": "严重",
            "description": f"场景空间坐标段缺少字段: {missing}"
        })

    return {
        "found": found_keywords,
        "missing": missing,
        "passed": len(missing) == 0
    }, issues


def check_camera_direction(text):
    """M13 约束 21：机位方向行存在"""
    issues = []
    # 多种机位方向关键词
    direction_patterns = [
        r'机位方向[：:]\s*朝[东南西北]',
        r'机位朝[东南西北]',
        r'反打机位[：:从]',
    ]
    found = any(re.search(p, text) for p in direction_patterns)

    if not found:
        issues.append({
            "type": "m13_camera_direction_missing",
            "severity": "严重",
            "description": "缺少机位方向标注（朝东/南/西/北 或 反打机位）"
        })

    return {"found": found, "passed": found}, issues


def check_blacklist_words(text):
    """M13 约束 21：黑名单词检查"""
    issues = []
    found_blacklist = {}

    for name, pattern in BLACKLIST_WORDS.items():
        matches = re.findall(pattern, text)
        if matches:
            found_blacklist[name] = matches

    if found_blacklist:
        issues.append({
            "type": "m13_blacklist_words_found",
            "severity": "严重",
            "description": f"存在黑名单词: {found_blacklist}"
        })

    return {"found": found_blacklist, "passed": len(found_blacklist) == 0}, issues


# M14 v2.1 新增：人物资产档案段去重检查（v3.4 治本·约束 23）
# 检测在"人物资产档案"段是否重复描述了参考图已承载的信息
M14_REDUNDANT_PATTERNS = {
    "年龄": r"\d{1,2}岁(男|女)性",
    "身高": r"1\d{2}cm",
    "服装颜色+品类": r"(全黑|全白|深蓝|浅蓝|浅蓝色|黑色|白色|红色|蓝色|绿色|银框|金色|棕色)(西装|衬衫|T恤|领带|外套|眼镜|短袖|皮鞋|墨镜|外套|夹克|连衣裙|裤子)",
    "发型描述": r"(黑色|棕色|金色|银白)(短发|长发|卷发|直发|寸头|马尾|披肩发|自然垂坠|自然)(垂坠|发型|短发|长发)?",
    "表情描述": r"表情(极度|非常|十分)?(夸张|冷漠|戏精|严肃|温柔|冷酷|无)",
    "道具外观": r"(锃亮|光亮|哑光|磨砂)(黑色|白色|银色|金色)(皮鞋|墨镜|眼镜|手表|手机|钱包|包|领带)",
    "场景细节": r"(上海|北京|广州|深圳|杭州|成都)(张园|石库门|弄堂|外滩|老街|胡同)(建筑群|青砖墙|石板路|复古路灯|藤蔓)",
}


def extract_asset_archive_section(text):
    """提取"人物资产档案"段内容（用于 M14 检查）

    返回：从"人物资产档案"开始到下一个标题段（## / ### / 镜头参数 / 画面描述 / 光影氛围 / 技术参数）的内容
    若找不到该段则返回空字符串。
    """
    start_match = re.search(r"人物资产档案", text)
    if not start_match:
        return ""

    start = start_match.start()
    # 找到下一个段标题
    next_section_patterns = [
        r"\n镜头参数\n",
        r"\n画面描述",
        r"\n光影氛围",
        r"\n技术参数",
        r"\n音效",
        r"\n台词",
        r"\n合规",
        r"\n【本镜自检",
        r"\n##\s+",
    ]
    end = len(text)
    for pat in next_section_patterns:
        m = re.search(pat, text[start + 1:])
        if m:
            candidate_end = start + 1 + m.start()
            if candidate_end < end:
                end = candidate_end

    return text[start:end]


def check_asset_archive_no_redundancy(text):
    """M14 约束 23：人物资产档案段不得重复描述参考图已承载信息（v3.4 治本）

    检测逻辑：
    1. 提取"人物资产档案"段
    2. 检测该段中是否出现 v3.3 风格的详细描述（年龄/身高/服装/发型/表情/道具外观/场景细节）
    3. v3.4 新格式允许多行参考图指针 + "（关键特征·参考图承载）" 简短标注

    关键豁免：
    - 若段首有 "v3.4 治本" 标注，说明已采用新格式
    - "（关键特征·参考图承载）" 中的简短描述（< 10 字）视为合规
    - 合规/禁忌信息（如"严禁字幕文字"）视为合规
    """
    issues = []
    archive = extract_asset_archive_section(text)

    if not archive:
        # 没有人物资产档案段，可能已优化删除 → 视为通过
        return {"section_exists": False, "passed": True, "redundant_items": []}, issues

    # v3.4 治本豁免：段首有"v3.4 治本"标注
    if "v3.4 治本" in archive or "v3.4治本" in archive:
        # 检查是否还有详细描述（v3.4 格式只允许"（关键特征·参考图承载）"括号注释）
        redundant_items = []
        for name, pattern in M14_REDUNDANT_PATTERNS.items():
            matches = re.findall(pattern, archive)
            # re.findall with groups returns tuples; convert to strings
            matches = [m if isinstance(m, str) else "".join(m) for m in matches]
            # 过滤掉括号内的简短标注（"（xxx·参考图承载）"）
            real_matches = []
            for m in matches:
                # 找到 match 所在行的上下文
                idx = archive.find(m)
                line_start = archive.rfind("\n", 0, idx) + 1
                line_end = archive.find("\n", idx)
                line = archive[line_start:line_end if line_end != -1 else len(archive)]
                # 如果在"（xxx·参考图承载）"括号内，视为合规
                if "参考图承载" in line and m in line.split("参考图承载")[0][-30:]:
                    continue
                real_matches.append(m)
            if real_matches:
                redundant_items.append({name: real_matches})

        if redundant_items:
            issues.append({
                "type": "m14_asset_archive_redundant",
                "severity": "一般",
                "description": f"v3.4 治本格式中存在未压缩的描述: {redundant_items}"
            })
            return {"section_exists": True, "passed": False, "redundant_items": redundant_items}, issues
        else:
            return {"section_exists": True, "passed": True, "redundant_items": []}, issues

    # v3.3 老格式：检测详细描述
    redundant_items = []
    for name, pattern in M14_REDUNDANT_PATTERNS.items():
        matches = re.findall(pattern, archive)
        matches = [m if isinstance(m, str) else "".join(m) for m in matches]
        if matches:
            redundant_items.append({name: matches})

    if redundant_items:
        issues.append({
            "type": "m14_asset_archive_redundant",
            "severity": "一般",
            "description": f"人物资产档案段存在 v3.3 老格式详细描述（参考图已承载）: {redundant_items}"
        })
        return {"section_exists": True, "passed": False, "redundant_items": redundant_items}, issues

    return {"section_exists": True, "passed": True, "redundant_items": []}, issues


# === v3.5 M15 元注释剥离校验（约束 24-26）===

# 约束 24：元注释零容忍
# 元注释模式（M11决策/M9 Gap/修正原版/AI友好/凭空 等）
M15_META_PATTERNS = [
    r'M11决策#?\d*',
    r'M9\s+Gap-?\d*',
    r'M12规则\d+',
    r'M13[^\s\u4e00-\u9fff]*',
    r'M14[^\s\u4e00-\u9fff]*',
    r'M15[^\s\u4e00-\u9fff]*',
    r'修正原版[^\s\u4e00-\u9fff]*',
    r'AI友好[^\s\u4e00-\u9fff]*',
    r'避免.{0,15}失败',
    r'避免.{0,15}双重',
    r'压缩原版\d*',
    r'🔴删[^\s\u4e00-\u9fff]*',
    r'凭空[^\s\u4e00-\u9fff]*',
    r'替代原版[^\s\u4e00-\u9fff]*',
    r'剧本未提[^\s\u4e00-\u9fff]*',
    r'9s长镜[^\s\u4e00-\u9fff]*',
    r'接近上限[^\s\u4e00-\u9fff]*',
    r'升华断点可接受[^\s\u4e00-\u9fff]*',
    r'场景突变[^\s\u4e00-\u9fff]*',
    r'\d+个微表情',
    r'微表情合并[^\s\u4e00-\u9fff]*',
    r'微表情压缩[^\s\u4e00-\u9fff]*',
    r'决策#\d+',
    r'Gap-\d+',
]


def check_no_meta_comments(text):
    """M15 约束 24：元注释零容忍（v3.5 治本）

    检测模式：决策标注/修复说明/AI友好说明/凭空/压缩原版 等元注释
    """
    issues = []
    found_items = []

    for pattern in M15_META_PATTERNS:
        matches = re.findall(pattern, text)
        matches = [m if isinstance(m, str) else "".join(m) for m in matches]
        if matches:
            found_items.extend(matches)

    if found_items:
        issues.append({
            "type": "m15_meta_comments",
            "severity": "一般",
            "description": f"v3.5 元注释残留: {found_items[:5]}{'...' if len(found_items) > 5 else ''}"
        })
        return {"passed": False, "found_items": found_items}, issues
    return {"passed": True, "found_items": []}, issues


def check_no_self_check_section(text):
    """M15 约束 25：自检段外置（v3.5 治本）

    【本镜自检·M9+M12+M13+M14】整段不应出现在提示词主体中，应由工具自动生成
    """
    issues = []
    pattern = r'【本镜自检[^\n]*'
    matches = re.findall(pattern, text)

    if matches:
        issues.append({
            "type": "m15_self_check_in_body",
            "severity": "一般",
            "description": f"v3.5 自检段残留: {matches[0][:50]}..."
        })
        return {"passed": False, "found": matches}, issues
    return {"passed": True, "found": []}, issues


def check_compliance_single_point(text):
    """M15 约束 26：合规信息单点化（v3.5 治本）

    【合规】/【合规保留】行应只出现 1 次。
    若出现多次 → 重复污染。
    """
    issues = []
    # 找所有 【合规】/【合规保留】行
    compliance_lines = re.findall(r'【合规(?:保留)?】[^\n]*', text)
    count = len(compliance_lines)

    if count > 1:
        issues.append({
            "type": "m15_compliance_duplicated",
            "severity": "一般",
            "description": f"v3.5 合规段出现 {count} 次（应单点化）"
        })
        return {"passed": False, "count": count, "lines": compliance_lines[:3]}, issues
    return {"passed": True, "count": count, "lines": compliance_lines}, issues


def check_position_continuity(text):
    """v3.7 治本·站位继承校验（KB04 第十三章强制约束）

    Why: 11 镜 v3.7 初版实测发现 4 处中重度站位问题（道具状态跳变/站位不明/角色离场无承接/位置漂移）。
         本校验在 M3 生成单镜时就发现问题，避免后续 M4 跨镜校验才发现。

    校验项（4 项 · 强制）:
      1. 站位明确度：每角色必须有画面位置关键词（左/中/右/前/后）
      2. 跨镜延续标注：画面描述必须含"延续镜00X"或"承接镜00X"或"位置重建"
      3. 道具状态跨镜延续：关键道具（墨镜/眼镜/名片/皮鞋）跨镜必须有延续说明
      4. 离场/入画承接：画面外角色必须有"承接镜00X离场"或"接镜00X入画"
    """
    issues = []

    # === 1. 站位明确度 ===
    # 提取资产引用段和画面描述段中的角色定位
    # 必须包含位置关键词（在资产引用段或画面描述段任一段出现即可）
    position_keywords = ["居中", "左侧", "右侧", "前景", "背景", "中景", "左三分之一", "右三分之一", "中心", "偏左", "偏右"]
    # 角色列表（v3.7 EP01）
    character_names = ["刘一鸣", "小仇", "骆骆"]

    # 提取画面描述段（站位的最终落点）
    desc_match = re.search(r'画面描述\s*\n(.+?)(?=\n\s*(?:光影氛围|音效|台词|技术参数|$))', text, re.DOTALL)
    desc_section = desc_match.group(1) if desc_match else ""

    # 查找资产人物_XXX 段
    asset_persons = re.findall(r'【人物_(\w+)：([^】]+)】', text)
    for name, desc in asset_persons:
        if name not in character_names:
            continue
        # 排除"画面外"（无需位置关键词）
        if "画面外" in desc:
            # 离场状态必须有承接说明
            if not re.search(r'承接镜\d+|接镜\d+|延续镜\d+', desc):
                issues.append({
                    "type": "v37_position_off_screen_no_inherit",
                    "severity": "中等",
                    "description": f"v3.7 治本·【人物_{name}】画面外离场，但缺承接标注（应为'承接镜00X离场'或'接镜00X入画'）"
                })
            continue

        # 在场角色必须有位置关键词（在资产引用段或画面描述段任一出现即可）
        has_position_in_asset = any(kw in desc for kw in position_keywords)
        has_position_in_desc = any(kw in desc_section for kw in position_keywords) if desc_section else False

        if not (has_position_in_asset or has_position_in_desc):
            issues.append({
                "type": "v37_position_unspecified",
                "severity": "中等",
                "description": f"v3.7 治本·【人物_{name}】在资产引用和画面描述段都未明确画面位置（应含：居中/左侧/右侧/前景/背景/中景 等关键词）"
            })

    # === 2. 跨镜延续标注 ===
    # 检查画面描述段是否有延续/承接/重建标注
    # 查找"延续镜""承接镜""位置重建""接镜"等
    desc_match = re.search(r'画面描述\s*\n(.+?)(?=\n\s*(?:光影氛围|音效|台词|技术参数|$))', text, re.DOTALL)
    if desc_match:
        desc_section = desc_match.group(1)
        has_inherit = bool(re.search(r'延续镜\d+|承接镜\d+|接镜\d+|位置重建', desc_section))
        if not has_inherit:
            # 例外：首镜（001）无上镜可承接
            is_first = re.search(r'镜001', text[:100]) is not None
            if not is_first:
                issues.append({
                    "type": "v37_no_cross_mirror_inherit",
                    "severity": "一般",
                    "description": "v3.7 治本·画面描述段缺跨镜延续标注（建议加'延续镜00X'或'承接镜00X'或'位置重建'）"
                })

    # === 3. 道具状态跨镜延续 ===
    # 检查关键道具是否有"延续""承接""→"等跨镜标记
    key_props = ["墨镜", "眼镜", "名片", "皮鞋"]
    for prop in key_props:
        prop_match = re.search(rf'【道具_{prop}：([^】]+)】', text)
        if prop_match:
            desc = prop_match.group(1)
            # 道具描述中应有跨镜延续说明
            has_prop_inherit = bool(re.search(r'延续|承接|→|镜\d+', desc))
            if not has_prop_inherit:
                # 例外：首镜道具是初始状态
                is_first = re.search(r'镜001', text[:100]) is not None
                if not is_first:
                    issues.append({
                        "type": "v37_prop_no_cross_mirror_state",
                        "severity": "一般",
                        "description": f"v3.7 治本·【道具_{prop}】缺跨镜状态延续标注（建议加'延续镜00X→'状态链）"
                    })

    # === 4. 离场/入画承接（在 #1 已检测画面外角色）===
    # 这一项合并到 #1 中

    return {
        "passed": len(issues) == 0,
        "issue_count": len(issues),
        "issues": issues,
    }


def validate_prompt(text):
    """执行所有校验（v1.0 + v2.0 M13 + v2.1 M14 + v3.0 M15）

    关键设计：M13 6 项校验（约束 19-21）只对"实际提示词内容"生效，
    文件末尾的"本镜自检·M9+M12+M13"段是元注释，剥离后再校验，
    避免 "无'延续镜00X'文字锚点（已删除）" 这类反讽声明被误判。

    v3.0 M15 新增：约束 24-26（元注释零容忍/自检段外置/合规单点化）
    """
    all_issues = []

    # 剥离本镜自检段（v3.3 txt 文件末尾元注释）
    prompt_body = strip_self_check_section(text)

    # v1.0 基础校验（对全文生效，self-check 段不影响）
    word_count, word_issues = check_word_count(text)
    all_issues.extend(word_issues)

    sections, section_issues = check_sections(text)
    all_issues.extend(section_issues)

    params, param_issues = check_core_parameters(text)
    all_issues.extend(param_issues)

    time_segs, time_issues = check_time_sequence(text)
    all_issues.extend(time_issues)

    lighting, lighting_issues = check_three_point_lighting(text)
    all_issues.extend(lighting_issues)

    constraints, constraint_issues = check_negative_constraints(text)
    all_issues.extend(constraint_issues)

    assets, asset_issues = check_asset_references(text)
    all_issues.extend(asset_issues)

    has_original, original_issues = check_original_text(text)
    all_issues.extend(original_issues)

    # v2.0 M13 新增校验（仅对 prompt_body 生效，跳过本镜自检段）
    physical, physical_issues = check_physical_details(prompt_body)
    all_issues.extend(physical_issues)

    supplementary, supplementary_issues = check_no_supplementary_section(prompt_body)
    all_issues.extend(supplementary_issues)

    anchors, anchor_issues = check_no_text_anchors(prompt_body)
    all_issues.extend(anchor_issues)

    scene_space, scene_issues = check_scene_space_coordinates(prompt_body)
    all_issues.extend(scene_issues)

    camera, camera_issues = check_camera_direction(prompt_body)
    all_issues.extend(camera_issues)

    blacklist, blacklist_issues = check_blacklist_words(prompt_body)
    all_issues.extend(blacklist_issues)

    # v2.1 M14 新增：人物资产档案去重检查
    asset_archive, asset_archive_issues = check_asset_archive_no_redundancy(prompt_body)
    all_issues.extend(asset_archive_issues)

    # v3.0 M15 新增：元注释剥离校验（约束 24-26）
    m15_meta, m15_meta_issues = check_no_meta_comments(prompt_body)
    all_issues.extend(m15_meta_issues)

    m15_self, m15_self_issues = check_no_self_check_section(prompt_body)
    all_issues.extend(m15_self_issues)

    m15_compliance, m15_compliance_issues = check_compliance_single_point(prompt_body)
    all_issues.extend(m15_compliance_issues)

    # v3.7 治本：跨镜站位继承校验（KB04 第十三章强制约束）
    v37_position = check_position_continuity(text)
    all_issues.extend(v37_position.get("issues", []))

    return {
        "word_count": word_count,
        "sections": sections,
        "core_parameters": params,
        "time_segments": len(time_segs),
        "lighting": lighting,
        "constraints": constraints,
        "asset_references": assets,
        "has_original_text": has_original,
        "m13_physical_details": physical,
        "m13_supplementary_section": supplementary,
        "m13_text_anchors": anchors,
        "m13_scene_space": scene_space,
        "m13_camera_direction": camera,
        "m13_blacklist": blacklist,
        "m14_asset_archive": asset_archive,
        "m15_no_meta": m15_meta,
        "m15_no_self_check": m15_self,
        "m15_compliance_single": m15_compliance,
        "v37_position_continuity": v37_position,
        "issues": all_issues,
        "issue_count": {
            "total": len(all_issues),
            "critical": sum(1 for i in all_issues if i["severity"] == "严重"),
            "warning": sum(1 for i in all_issues if i["severity"] == "一般"),
        }
    }


def print_report(report):
    """打印校验报告"""
    print("=" * 70)
    print("单镜提示词校验报告 v3.0（M13 v3.3 + M14 v3.4 + M15 v3.5 治本）")
    print("=" * 70)

    # 基本信息
    print(f"\n字数：{report['word_count']}")
    print(f"  - 状态：", end="")
    if report['word_count'] <= 1800:
        print("✓ 通过（v3.7 治本 · ≤1800 标准）")
    elif report['word_count'] <= 2200:
        print("⚠ 偏多（建议压缩到 ≤1800）")
    else:
        print("❌ 过多（v3.7 强约束 ≤1800）")

    # 5段式
    print(f"\n5段式结构：")
    for section, found in report['sections'].items():
        status = "✓" if found else "✗"
        print(f"  {status} {section}")

    # 12核心参数
    print(f"\n12核心参数：")
    for param, found in report['core_parameters'].items():
        status = "✓" if found else "✗"
        print(f"  {status} {param}")

    # 三点布光
    print(f"\n三点布光：")
    for light, found in report['lighting'].items():
        status = "✓" if found else "✗"
        print(f"  {status} {light}")

    # 资产引用
    print(f"\n资产引用（新格式：人物_/道具_/场景_）：")
    if isinstance(report['asset_references'], dict):
        stats = report['asset_references'].get('asset_stats', {})
        print(f"  人物：{stats.get('人物', 0)}")
        print(f"  道具：{stats.get('道具', 0)}")
        print(f"  场景：{stats.get('场景', 0)}")

    # M13 v2.0 新增项
    print(f"\n" + "=" * 70)
    print("M13 v3.3 重构自检（v2.0 新增）")
    print("=" * 70)

    m13_pd = report['m13_physical_details']
    if m13_pd['duration']:
        status = "✓" if m13_pd['passed'] else "✗"
        print(f"\n[约束19] 物理细节数（按时长分级）：{status}")
        print(f"  时长={m13_pd['duration']}s → 上限={m13_pd['limit']}")
        print(f"  实际={m13_pd['detail_count']}")

    m13_ss = report['m13_supplementary_section']
    status = "✓" if m13_ss['passed'] else "✗"
    print(f"\n[约束20] 无'补充物理细节'段：{status}")

    m13_ta = report['m13_text_anchors']
    status = "✓" if m13_ta['passed'] else "✗"
    print(f"\n[约束20] 无'延续镜00X'文字锚点：{status}")
    if m13_ta['matches']:
        print(f"  发现: {m13_ta['matches']}")

    m13_ssc = report['m13_scene_space']
    status = "✓" if m13_ssc['passed'] else "✗"
    print(f"\n[约束14] 场景空间坐标段（6 字段）：{status}")
    if m13_ssc['missing']:
        print(f"  缺少: {m13_ssc['missing']}")

    m13_cd = report['m13_camera_direction']
    status = "✓" if m13_cd['passed'] else "✗"
    print(f"\n[约束21] 机位方向行：{status}")

    m13_bl = report['m13_blacklist']
    status = "✓" if m13_bl['passed'] else "✗"
    print(f"\n[约束21] 黑名单词（反作用力/抛物线/帧率切换/微距离）：{status}")
    if m13_bl['found']:
        for k, v in m13_bl['found'].items():
            print(f"  {k}: {v}")

    # v2.1 M14 v3.4 治本
    m14_aa = report['m14_asset_archive']
    status = "✓" if m14_aa['passed'] else "✗"
    if m14_aa['section_exists']:
        print(f"\n[约束23] 资产档案去重（v3.4 治本·M14）：{status}")
        if m14_aa['redundant_items']:
            print(f"  冗余描述: {m14_aa['redundant_items']}")
    else:
        print(f"\n[约束23] 资产档案去重（v3.4 治本·M14）：✓（已删除·无需检查）")

    # v3.0 M15 v3.5 治本
    print(f"\n" + "=" * 70)
    print("M15 v3.5 元注释剥离（v3.0 新增）")
    print("=" * 70)

    m15_meta = report['m15_no_meta']
    status = "✓" if m15_meta['passed'] else "✗"
    print(f"\n[约束24] 元注释零容忍（v3.5 治本·M15）：{status}")
    if not m15_meta['passed']:
        print(f"  残留: {m15_meta['found_items'][:5]}")

    m15_self = report['m15_no_self_check']
    status = "✓" if m15_self['passed'] else "✗"
    print(f"\n[约束25] 自检段外置（v3.5 治本·M15）：{status}")
    if not m15_self['passed']:
        print(f"  残留: {m15_self['found']}")

    m15_compliance = report['m15_compliance_single']
    status = "✓" if m15_compliance['passed'] else "✗"
    print(f"\n[约束26] 合规信息单点化（v3.5 治本·M15）：{status}")
    print(f"  合规段出现次数: {m15_compliance['count']}")

    # v3.7 治本：跨镜站位继承校验
    print(f"\n" + "=" * 70)
    print("v3.7 治本·跨镜站位继承校验（KB04 第十三章强制约束）")
    print("=" * 70)

    v37 = report['v37_position_continuity']
    status = "✓" if v37['passed'] else "✗"
    print(f"\n[约束27] 跨镜站位继承：{status}")
    print(f"  问题数：{v37['issue_count']}")
    if v37['issues']:
        for issue in v37['issues'][:5]:
            print(f"  - [{issue['severity']}] {issue['description']}")
        if len(v37['issues']) > 5:
            print(f"  ... 还有 {len(v37['issues']) - 5} 个问题")

    # 剧本原词
    status = "✓" if report['has_original_text'] else "✗"
    print(f"\n剧本原词标注：{status}")

    # 问题总结
    print(f"\n" + "=" * 70)
    print(f"问题统计：")
    print(f"  严重：{report['issue_count']['critical']}")
    print(f"  一般：{report['issue_count']['warning']}")
    print(f"  总计：{report['issue_count']['total']}")
    print("=" * 70)

    if report['issues']:
        print(f"\n详细问题：")
        for i, issue in enumerate(report['issues'], 1):
            print(f"  {i}. [{issue['severity']}] {issue['description']}")


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python validate_prompt.py <提示词文件>")
        print("  python validate_prompt.py <提示词文件> --json")
        print("  python validate_prompt.py <目录> --batch")
        sys.exit(1)

    target = Path(sys.argv[1])

    if not target.exists():
        print(f"错误: 路径不存在: {target}")
        sys.exit(1)

    if target.is_dir() and "--batch" in sys.argv:
        # 批量校验
        txt_files = sorted(target.glob("*.txt"))
        if not txt_files:
            print(f"错误: 目录下无 .txt 文件: {target}")
            sys.exit(1)

        all_reports = []
        for f in txt_files:
            text = f.read_text(encoding="utf-8")
            report = validate_prompt(text)
            report['file'] = str(f)
            all_reports.append(report)

        # 汇总
        print("=" * 70)
        print(f"批量校验：{len(txt_files)} 个文件")
        print("=" * 70)
        for r in all_reports:
            fname = Path(r['file']).name
            critical = r['issue_count']['critical']
            warning = r['issue_count']['warning']
            total = r['issue_count']['total']
            print(f"\n{fname}: 严重={critical} 一般={warning} 总={total}")
            if critical > 0:
                for issue in r['issues']:
                    if issue['severity'] == '严重':
                        print(f"  🔴 [{issue['type']}] {issue['description']}")

        if "--json" in sys.argv:
            print(json.dumps(all_reports, ensure_ascii=False, indent=2))

    else:
        # 单文件校验
        text = target.read_text(encoding="utf-8")
        report = validate_prompt(text)

        if "--json" in sys.argv:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print_report(report)


if __name__ == "__main__":
    main()

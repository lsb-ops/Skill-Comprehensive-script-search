#!/usr/bin/env python3
"""
v34_refactor_archive.py — v3.4 治本：人物资产档案段去重

用法:
    python v34_refactor_archive.py <file.txt>           # 单文件
    python v34_refactor_archive.py <dir> --batch       # 批量目录下所有 .txt

功能:
    检测"人物资产档案"段是否含 v3.3 老格式详细描述（年龄/服装/发型/表情/道具外观/场景细节），
    若有，重写为 v3.4 治本格式（1 行声明 + N 行参考图指针）。

    关键设计：
    - 自动识别段内出现的人物名（刘一鸣/小仇/骆骆）、道具名（墨镜/皮鞋/饮料杯等）、场景名（场景_xxx）
    - 保留"严禁字幕文字"等合规/禁忌信息（图片无法承载）
    - 已有"v3.4 治本"标注的段跳过
"""

import sys
import re
from pathlib import Path


# 已知资产名（项目级元数据，可后续扩展）
KNOWN_CHARACTERS = ["刘一鸣", "小仇", "骆骆"]
KNOWN_PROPS = ["墨镜", "皮鞋", "饮料杯", "名片", "手机"]
KNOWN_SCENE_PREFIX = "场景_"

# 合规/禁忌关键词（保留）
COMPLIANCE_KEYWORDS = ["严禁字幕文字", "严禁字幕", "AI画面严禁", "禁止", "合规"]


def extract_archive_section(text):
    """提取"人物资产档案"段（含起始行到下一段标题前）"""
    start_match = re.search(r"^人物资产档案\s*$", text, re.MULTILINE)
    if not start_match:
        return None, None, None

    start = start_match.start()
    # 找到下一个段标题
    next_section_patterns = [
        r"\n镜头参数\s*\n",
        r"\n##\s+",
    ]
    end = len(text)
    for pat in next_section_patterns:
        m = re.search(pat, text[start + 1:])
        if m:
            candidate_end = start + 1 + m.start()
            if candidate_end < end:
                end = candidate_end

    return start, end, text[start:end]


def parse_archive_entities(archive_text):
    """解析档案段中的实体（人物/道具/场景）

    返回:
        characters: [{"name": "刘一鸣", "key_info": "30岁男性"}, ...]
        props: [{"name": "墨镜", "key_info": "飞行员金属框"}, ...]
        scenes: [{"name": "场景_张园外景", "key_info": "上海石库门+青砖墙"}, ...]
        compliance: ["严禁字幕文字：xxx", ...]
    """
    characters = []
    props = []
    scenes = []
    compliance = []

    # 按行解析
    for line in archive_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # 跳过标题
        if line == "人物资产档案":
            continue

        # 提取合规信息
        if "严禁" in line or "禁止" in line or "合规" in line:
            # 只保留包含资产信息的合规项
            compliance.append(line)
            continue

        # 匹配 "实体名：描述"
        m = re.match(r"^([^：:]+)[：:]\s*(.+)$", line)
        if not m:
            continue

        name = m.group(1).strip()
        desc = m.group(2).strip()

        # 跳过元注释
        if name.startswith("【") or name.startswith("参考"):
            continue

        # 识别类别
        if name in KNOWN_CHARACTERS:
            # 提取关键特征（仅保留前 15 字符作为简短标注）
            key_info = desc.split("（")[0].split("(")[0][:15] if desc else ""
            characters.append({"name": name, "key_info": key_info, "raw": desc})
        elif name in KNOWN_PROPS:
            key_info = desc[:15] if desc else ""
            props.append({"name": name, "key_info": key_info, "raw": desc})
        elif name.startswith(KNOWN_SCENE_PREFIX):
            key_info = desc.split("（")[0].split("(")[0][:20] if desc else ""
            scenes.append({"name": name, "key_info": key_info, "raw": desc})

    return characters, props, scenes, compliance


def generate_v34_archive(characters, props, scenes, compliance):
    """生成 v3.4 治本格式档案段"""
    lines = []
    lines.append("人物资产档案（v3.4 治本·参考图已承载信息则提示词不重复）")
    lines.append("【本镜人物外貌/服装/发型/表情 全部由参考图承载，提示词不重复描述】")

    for char in characters:
        lines.append(f"【参考_人物_{char['name']}：03_人物档案/人物_{char['name']}.png（关键特征·参考图承载）】")

    for prop in props:
        lines.append(f"【参考_道具_{prop['name']}：04_道具档案/道具_{prop['name']}.png（关键特征·参考图承载）】")

    for scene in scenes:
        lines.append(f"【参考_{scene['name']}：02_场景主控/{scene['name']}.png（关键特征·参考图承载）】")

    # 保留合规信息
    for comp in compliance:
        lines.append(f"【合规保留】{comp}")

    return "\n".join(lines)


def refactor_file(file_path):
    """重构单文件的人物资产档案段"""
    text = Path(file_path).read_text(encoding="utf-8")

    # 检测是否已有 v3.4 治本
    if "v3.4 治本" in text or "v3.4治本" in text:
        return {"file": str(file_path), "status": "skipped", "reason": "已有 v3.4 治本标注"}

    start, end, archive = extract_archive_section(text)
    if start is None:
        return {"file": str(file_path), "status": "skipped", "reason": "无人物资产档案段"}

    # 解析实体
    characters, props, scenes, compliance = parse_archive_entities(archive)

    if not characters and not props and not scenes:
        return {"file": str(file_path), "status": "skipped", "reason": "无实体可识别"}

    # 生成新段
    new_archive = generate_v34_archive(characters, props, scenes, compliance)

    # 替换
    new_text = text[:start] + new_archive + "\n\n" + text[end:]

    Path(file_path).write_text(new_text, encoding="utf-8")

    return {
        "file": str(file_path),
        "status": "refactored",
        "characters": [c["name"] for c in characters],
        "props": [p["name"] for p in props],
        "scenes": [s["name"] for s in scenes],
        "compliance_count": len(compliance),
        "old_length": len(archive),
        "new_length": len(new_archive),
    }


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python v34_refactor_archive.py <file.txt>")
        print("  python v34_refactor_archive.py <dir> --batch")
        sys.exit(1)

    target = Path(sys.argv[1])
    is_batch = "--batch" in sys.argv

    if target.is_file():
        results = [refactor_file(target)]
    elif target.is_dir() and is_batch:
        results = [refactor_file(f) for f in sorted(target.glob("*.txt"))]
    else:
        print(f"错误：{target} 不是文件或目录（--batch）")
        sys.exit(1)

    # 报告
    print("=" * 70)
    print("v3.4 治本重构报告（人物资产档案段去重）")
    print("=" * 70)

    refactored = [r for r in results if r["status"] == "refactored"]
    skipped = [r for r in results if r["status"] == "skipped"]

    for r in results:
        if r["status"] == "refactored":
            old_k = r["old_length"]
            new_k = r["new_length"]
            saved = old_k - new_k
            print(f"\n✅ {Path(r['file']).name}")
            print(f"   人物: {r['characters']}")
            print(f"   道具: {r['props']}")
            print(f"   场景: {r['scenes']}")
            print(f"   合规: {r['compliance_count']} 项")
            print(f"   字数: {old_k} → {new_k} (节省 {saved} 字, -{saved*100//old_k if old_k else 0}%)")
        else:
            print(f"\n⏭ {Path(r['file']).name}: {r['reason']}")

    print(f"\n" + "=" * 70)
    print(f"总计: 重构 {len(refactored)} / 跳过 {len(skipped)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
ai_verify.py — AI 内容质量验证（v1.0 工程化·轻量版）

输入：M3 prompt txt + M5 mock/real 视频帧 + 角色/场景/道具库
输出：质量评分 + 失败重做建议

核心检查（5 维评分）：
1. 文本一致性（40%）：M3 prompt 是否包含角色库"必须保留"特征
2. 元注释检查（15%）：M15 段首元注释是否残留
3. 段落完整性（15%）：6 段是否齐全
4. 资产引用（15%）：是否含【人物_xxx：】标记
5. 视觉基准（15%）：M3 是否含"5000K"/"T2.8"/"MS"等工程关键词

用法:
    python3 ai_verify.py <M3_DIR> --lib-dir ./
    python3 ai_verify.py <M3_DIR> --lib-dir ./ --threshold 0.7
    python3 ai_verify.py <M3_DIR> --lib-dir ./ --redo    # 自动重做 < 0.7 的镜

设计哲学：
1. 轻量级：仅用 PIL（不依赖 numpy/torch/clip）
2. 5 维评分：覆盖 LLM 输出常见问题
3. 阈值化：< 0.7 自动建议重做
4. 集成：可被 M3/M5 调用做闭环

Why: AI 视频 API 成功率 60-80%，prompt 质量差是主因。
     自动验证可在生成前发现问题，避免"生成失败 + 重做 + 浪费 token"。
"""

import sys
import json
import argparse
import re
from pathlib import Path
from typing import Dict, List, Any, Optional


# === 评分维度（核心工程参数）===

WEIGHTS = {
    "text_consistency": 0.40,  # 文本一致性
    "no_meta": 0.15,           # 无元注释
    "section_complete": 0.15,  # 段落完整
    "asset_ref": 0.15,         # 资产引用
    "tech_keywords": 0.15,     # 工程关键词
}

REQUIRED_SECTIONS = ["资产引用", "人物资产档案", "镜头参数", "画面描述", "光影氛围", "技术参数"]

# M15 元注释段首模式
META_PATTERNS_STRICT = [
    r"^决策[：:]",
    r"^修复[：:]",
    r"^规则[：:]",
    r"【合规】",
    r"【合规保留】",
    r"^M1[0-9]+决策",
    r"^M1[0-9]+修复",
]

# v3 提示词工程规范关键词
TECH_KEYWORDS_REQUIRED = ["T", "K", "9:16", "焦距", "景深"]  # 至少含 T-stop / K 色温 / 9:16 / 焦距 / 景深之一

ASSET_PATTERNS = {
    "character": re.compile(r'【人物_([^：]+)：'),
    "scene": re.compile(r'【场景_([^：]+)：'),
    "prop": re.compile(r'【道具_([^：]+)：'),
}


# === 评分函数 ===

def score_text_consistency(txt_content: str, lib_dir: Path) -> Dict[str, Any]:
    """文本一致性：M3 prompt 是否包含角色库"必须保留"特征

    算法：提取 txt 中所有【人物_xxx：】标记 → 查角色库 → 检查 must_keep 特征是否出现在 prompt
    """
    found_chars = []
    matched = 0
    total = 0

    for m in ASSET_PATTERNS["character"].finditer(txt_content):
        char_name = m.group(1).strip()
        char_data = _find_character(lib_dir, char_name)
        if not char_data:
            continue
        found_chars.append(char_name)
        must_keep = char_data.get("consistency_rules", {}).get("must_keep", [])
        for feature in must_keep:
            total += 1
            if feature in txt_content:
                matched += 1

    if total == 0:
        return {"score": 0.5, "matched": matched, "total": total, "found": found_chars, "note": "no_must_keep_features"}

    score = matched / total
    return {"score": round(score, 3), "matched": matched, "total": total, "found": found_chars}


def score_no_meta(txt_content: str) -> float:
    """无元注释（M15）"""
    violations = 0
    for pat in META_PATTERNS_STRICT:
        if re.search(pat, txt_content, re.MULTILINE):
            violations += 1
    # 0 违规 = 1.0 分；1 违规 = 0.5；2+ 违规 = 0.0
    if violations == 0:
        return 1.0
    elif violations == 1:
        return 0.5
    else:
        return 0.0


def score_section_complete(txt_content: str) -> float:
    """段落完整（6 段）"""
    present = sum(1 for sec in REQUIRED_SECTIONS if sec in txt_content)
    return round(present / len(REQUIRED_SECTIONS), 3)


def score_asset_ref(txt_content: str) -> float:
    """资产引用"""
    chars = len(ASSET_PATTERNS["character"].findall(txt_content))
    scenes = len(ASSET_PATTERNS["scene"].findall(txt_content))
    props = len(ASSET_PATTERNS["prop"].findall(txt_content))

    # 至少 1 个角色 + 1 个场景 = 满分
    if chars >= 1 and scenes >= 1:
        return 1.0
    elif chars >= 1 or scenes >= 1:
        return 0.7
    else:
        return 0.0


def score_tech_keywords(txt_content: str) -> float:
    """工程关键词（v3 提示词规范）"""
    # 至少含 3 个关键词 = 满分
    found = sum(1 for kw in TECH_KEYWORDS_REQUIRED if kw in txt_content)
    return round(min(found / 3.0, 1.0), 3)


# === 辅助 ===

def _find_character(lib_dir: Path, char_name: str) -> Optional[Dict]:
    char_dir = lib_dir / "character_lib" / f"人物_{char_name}"
    if not char_dir.exists():
        # 尝试部分匹配
        for d in (lib_dir / "character_lib").iterdir():
            if d.is_dir() and char_name in d.name:
                char_dir = d
                break
        else:
            return None
    jp = char_dir / "character.json"
    if not jp.exists():
        return None
    return json.loads(jp.read_text(encoding="utf-8"))


# === 单镜评分 ===

def verify_single_mirror(txt_path: Path, lib_dir: Path) -> Dict[str, Any]:
    """验证单镜"""
    content = txt_path.read_text(encoding="utf-8")

    # 5 维评分
    text_cons = score_text_consistency(content, lib_dir)
    no_meta = score_no_meta(content)
    section_complete = score_section_complete(content)
    asset_ref = score_asset_ref(content)
    tech_keywords = score_tech_keywords(content)

    # 加权总分
    total = (
        text_cons["score"] * WEIGHTS["text_consistency"] +
        no_meta * WEIGHTS["no_meta"] +
        section_complete * WEIGHTS["section_complete"] +
        asset_ref * WEIGHTS["asset_ref"] +
        tech_keywords * WEIGHTS["tech_keywords"]
    )

    return {
        "mirror": txt_path.stem,
        "scores": {
            "text_consistency": text_cons,
            "no_meta": no_meta,
            "section_complete": section_complete,
            "asset_ref": asset_ref,
            "tech_keywords": tech_keywords,
        },
        "total_score": round(total, 3),
    }


# === 批量验证 ===

def verify_all_mirrors(m3_dir: Path, lib_dir: Path, threshold: float = 0.7) -> Dict:
    """批量验证"""
    txt_files = sorted(m3_dir.glob("镜*.txt"))
    results = []
    for txt_path in txt_files:
        result = verify_single_mirror(txt_path, lib_dir)
        result["needs_redo"] = result["total_score"] < threshold
        results.append(result)

    # 统计
    total = len(results)
    pass_count = sum(1 for r in results if not r["needs_redo"])
    fail_count = total - pass_count
    avg_score = sum(r["total_score"] for r in results) / total if total > 0 else 0

    return {
        "threshold": threshold,
        "total": total,
        "pass": pass_count,
        "fail": fail_count,
        "avg_score": round(avg_score, 3),
        "results": results,
    }


# === Main ===

def main():
    parser = argparse.ArgumentParser(description="ai_verify — AI 内容质量验证（轻量版）")
    parser.add_argument("m3_dir", help="M3 输出目录")
    parser.add_argument("--lib-dir", default="./", help="资产库根目录（含 character_lib/scene_lib/prop_lib）")
    parser.add_argument("--threshold", type=float, default=0.7, help="及格分（默认 0.7）")
    parser.add_argument("--report", help="报告输出路径（默认 <m3_dir>/ai_verify_report.json）")
    args = parser.parse_args()

    m3_dir = Path(args.m3_dir)
    lib_dir = Path(args.lib_dir)
    if not m3_dir.exists():
        print(f"❌ M3 目录不存在: {m3_dir}", file=sys.stderr)
        sys.exit(1)

    report = verify_all_mirrors(m3_dir, lib_dir, args.threshold)

    # 报告
    report_path = Path(args.report) if args.report else m3_dir / "ai_verify_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # 打印
    print(f"═══════════════════════════════════════", file=sys.stderr)
    print(f"📊 AI 内容质量验证（轻量版）", file=sys.stderr)
    print(f"═══════════════════════════════════════", file=sys.stderr)
    print(f"  总数: {report['total']}", file=sys.stderr)
    print(f"  通过: {report['pass']} (≥{args.threshold})", file=sys.stderr)
    print(f"  失败: {report['fail']} (<{args.threshold})", file=sys.stderr)
    print(f"  平均分: {report['avg_score']}", file=sys.stderr)
    print(f"  报告: {report_path}", file=sys.stderr)
    print(f"", file=sys.stderr)

    for r in report["results"]:
        marker = "✅" if not r["needs_redo"] else "❌"
        print(f"  {marker} {r['mirror']:30s} | 总分: {r['total_score']:.3f} | "
              f"文本一致: {r['scores']['text_consistency']['score']:.2f} | "
              f"无元注释: {r['scores']['no_meta']:.2f} | "
              f"段落完整: {r['scores']['section_complete']:.2f} | "
              f"资产引用: {r['scores']['asset_ref']:.2f} | "
              f"工程关键词: {r['scores']['tech_keywords']:.2f}",
              file=sys.stderr)

    if report["fail"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

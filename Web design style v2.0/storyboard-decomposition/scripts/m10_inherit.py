#!/usr/bin/env python3
"""
m10_inherit.py — 跨集资产继承模块（v1.0 工程化）

输入：M3 输出的 镜*.txt + 角色/场景/道具库
输出：注入"延续资产"标记的增强 prompt txt

用法:
    python3 m10_inherit.py <M3_DIR> <output_dir> --ep EP02 [--characters-dir ./character_lib]
    python3 m10_inherit.py <M3_DIR> <output_dir> --ep EP02 --dry-run  # 预览不写

设计哲学：
1. 跨集复用 = 单一资产库 → 多集 prompt
2. 自动注入：M3 txt 解析【人物_xxx：】标记 → 查角色库 → 注入"延续资产"块
3. 道具状态继承：EP01 墨镜摘下 → EP02 默认"in_hand"
4. 场景库匹配：M3 中的【场景_xxx：】→ 查场景库 → 注入视觉基准

Why: 解决"用户做完 EP01 就放弃"的最大痛点 — 跨集一致性。
     EP02 自动继承 EP01 资产，无需用户手动复制。
"""

import sys
import json
import argparse
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


# === 资产标记解析 ===

ASSET_PATTERNS = {
    "character": re.compile(r'【人物_([^：]+)：([^】]*)】'),
    "scene": re.compile(r'【场景_([^：]+)：([^】]*)】'),
    "prop": re.compile(r'【道具_([^：]+)：([^】]*)】'),
}


def parse_assets_from_txt(txt_path: Path) -> Dict[str, List[Dict]]:
    """从 M3 txt 解析资产引用

    返回：{"characters": [{"name": "刘一鸣", "context": "前景MCU"}], "scenes": [...], "props": [...]}
    """
    content = txt_path.read_text(encoding="utf-8")
    result = {"characters": [], "scenes": [], "props": []}

    for m in ASSET_PATTERNS["character"].finditer(content):
        result["characters"].append({
            "name": m.group(1).strip(),
            "context": m.group(2).strip(),
        })

    for m in ASSET_PATTERNS["scene"].finditer(content):
        result["scenes"].append({
            "name": m.group(1).strip(),
            "context": m.group(2).strip(),
        })

    for m in ASSET_PATTERNS["prop"].finditer(content):
        result["props"].append({
            "name": m.group(1).strip(),
            "context": m.group(2).strip(),
        })

    return result


# === 库查找（兼容 m7/m8/m9 输出） ===

def find_character(char_lib_dir: Path, char_name: str) -> Optional[Dict]:
    """查角色库"""
    char_dir = char_lib_dir / f"人物_{char_name}"
    if not char_dir.exists():
        # 尝试直接匹配
        for d in char_lib_dir.iterdir():
            if d.is_dir() and char_name in d.name:
                char_dir = d
                break
        else:
            return None
    jp = char_dir / "character.json"
    if not jp.exists():
        return None
    return json.loads(jp.read_text(encoding="utf-8"))


def find_scene(scene_lib_dir: Path, scene_name: str) -> Optional[Dict]:
    """查场景库"""
    scene_dir = scene_lib_dir / f"场景_{scene_name}"
    if not scene_dir.exists():
        for d in scene_lib_dir.iterdir():
            if d.is_dir() and scene_name in d.name:
                scene_dir = d
                break
        else:
            return None
    jp = scene_dir / "scene.json"
    if not jp.exists():
        return None
    return json.loads(jp.read_text(encoding="utf-8"))


def find_prop(prop_lib_dir: Path, prop_name: str) -> Optional[Dict]:
    """查道具库"""
    prop_dir = prop_lib_dir / f"道具_{prop_name}"
    if not prop_dir.exists():
        for d in prop_lib_dir.iterdir():
            if d.is_dir() and prop_name in d.name:
                prop_dir = d
                break
        else:
            return None
    jp = prop_dir / "prop.json"
    if not jp.exists():
        return None
    return json.loads(jp.read_text(encoding="utf-8"))


# === 注入"延续资产"块 ===

def build_inheritance_block(assets: Dict, target_ep: str,
                             char_lib: Path, scene_lib: Path, prop_lib: Path) -> str:
    """构建跨集资产继承块

    输出格式：
    【跨集资产继承·EP02】
      • 人物: 刘一鸣 (延续 EP01 霸总经典三件套)
        必须保留: 身高 188cm, 全黑西装配色, 金属框墨镜
      • 场景: 张园外景 (延续 EP01 视觉基准)
        必须保留: 石库门建筑风格, 5000K 自然日光
      • 道具: 墨镜 (延续 EP01 镜004 状态)
        状态: 拿在手里左手
    """
    lines = [f"【跨集资产继承·{target_ep}】"]

    found_anything = False

    # 人物
    for char_ref in assets["characters"]:
        data = find_character(char_lib, char_ref["name"])
        if not data:
            continue
        found_anything = True
        lines.append(f"  • 人物: {data['name']} (延续 {data.get('ep_first_appearance', '?')} {data.get('ep_appearances', {}).get(data.get('ep_first_appearance', 'EP01'), {}).get('outfit', '主造型')})")
        consistency = data.get("consistency_rules", {})
        if consistency.get("must_keep"):
            lines.append(f"    必须保留: {', '.join(consistency['must_keep'])}")
        if data.get("prompt_template"):
            lines.append(f"    Prompt 模板: {data['prompt_template']}")

    # 场景
    for scene_ref in assets["scenes"]:
        data = find_scene(scene_lib, scene_ref["name"])
        if not data:
            continue
        found_anything = True
        lines.append(f"  • 场景: {data['name']} (延续 {data.get('ep_appearances', {}).get('EP01', {}).get('key_scenes', ['?'])[0] if 'EP01' in data.get('ep_appearances', {}) else '?'})")
        consistency = data.get("consistency_rules", {})
        if consistency.get("must_keep"):
            lines.append(f"    必须保留: {', '.join(consistency['must_keep'])}")
        vb = data.get("visual_baseline", {}).get("lighting", {})
        if vb.get("primary"):
            lines.append(f"    光照基准: {vb['primary']}")
        if data.get("prompt_template"):
            lines.append(f"    Prompt 模板: {data['prompt_template']}")

    # 道具
    for prop_ref in assets["props"]:
        data = find_prop(prop_lib, prop_ref["name"])
        if not data:
            continue
        found_anything = True
        # 取 EP 最后一个 state 引用
        state_evo = data.get("state_evolution", {})
        ep_states = {k: v for k, v in state_evo.items() if k.startswith(target_ep)}
        last_state = list(ep_states.values())[-1] if ep_states else (
            list(state_evo.values())[-1] if state_evo else {}
        )
        lines.append(f"  • 道具: {data['name']} (延续 {data.get('ep_appearances', {}).get('EP01', {}).get('first_mirror', '?')} 状态)")
        if last_state:
            lines.append(f"    状态: {last_state.get('state', '?')}")
            lines.append(f"    位置: {last_state.get('position', '?')}")
        templates = data.get("prompt_templates", {})
        if templates:
            default_template = templates.get("default") or templates.get("worn") or list(templates.values())[0]
            lines.append(f"    Prompt 模板: {default_template}")

    if not found_anything:
        return ""  # 没找到任何资产就不注入
    return "\n".join(lines)


# === 单镜处理 ===

def inherit_single_mirror(txt_path: Path, output_dir: Path, target_ep: str,
                           char_lib: Path, scene_lib: Path, prop_lib: Path) -> Dict:
    """处理单镜：解析资产 → 注入延续块 → 写新文件"""
    content = txt_path.read_text(encoding="utf-8")
    assets = parse_assets_from_txt(txt_path)

    inheritance_block = build_inheritance_block(assets, target_ep, char_lib, scene_lib, prop_lib)

    if not inheritance_block:
        return {"status": "no_assets", "mirror": txt_path.stem}

    # 在"资产引用"段后插入延续块
    new_content = content.replace(
        "资产引用",
        f"资产引用\n{inheritance_block}",
        1
    )

    output_path = output_dir / txt_path.name
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(new_content, encoding="utf-8")

    return {
        "status": "injected",
        "mirror": txt_path.stem,
        "assets_found": {
            "characters": [c["name"] for c in assets["characters"]],
            "scenes": [s["name"] for s in assets["scenes"]],
            "props": [p["name"] for p in assets["props"]],
        },
        "output": str(output_path),
    }


# === Main ===

def main():
    parser = argparse.ArgumentParser(description="m10_inherit — 跨集资产继承")
    parser.add_argument("m3_dir", help="M3 输出目录（镜*.txt）")
    parser.add_argument("output_dir", help="增强后输出目录")
    parser.add_argument("--ep", required=True, help="目标集数（如 EP02）")
    parser.add_argument("--characters-dir", default="./character_lib", help="角色库")
    parser.add_argument("--scenes-dir", default="./scene_lib", help="场景库")
    parser.add_argument("--props-dir", default="./prop_lib", help="道具库")
    parser.add_argument("--dry-run", action="store_true", help="预览，不写文件")
    args = parser.parse_args()

    m3_dir = Path(args.m3_dir)
    output_dir = Path(args.output_dir)
    char_lib = Path(args.characters_dir)
    scene_lib = Path(args.scenes_dir)
    prop_lib = Path(args.props_dir)

    if not m3_dir.exists():
        print(f"❌ M3 目录不存在: {m3_dir}", file=sys.stderr)
        sys.exit(1)

    txt_files = sorted(m3_dir.glob("镜*.txt"))
    print(f"📦 找到 {len(txt_files)} 个镜 txt", file=sys.stderr)

    results = []
    for txt_path in txt_files:
        if args.dry_run:
            assets = parse_assets_from_txt(txt_path)
            print(f"  {txt_path.stem}: chars={len(assets['characters'])}, scenes={len(assets['scenes'])}, props={len(assets['props'])}")
        else:
            result = inherit_single_mirror(txt_path, output_dir, args.ep, char_lib, scene_lib, prop_lib)
            results.append(result)
            status = result["status"]
            if status == "injected":
                print(f"  ✅ {result['mirror']}: 注入资产 {result['assets_found']}")
            else:
                print(f"  ⊙ {result['mirror']}: {status}")

    if not args.dry_run:
        injected = sum(1 for r in results if r["status"] == "injected")
        print(f"\n═══════════════════════════════════════", file=sys.stderr)
        print(f"📊 跨集资产继承总结", file=sys.stderr)
        print(f"═══════════════════════════════════════", file=sys.stderr)
        print(f"  总数: {len(results)}", file=sys.stderr)
        print(f"  注入: {injected}", file=sys.stderr)
        print(f"  无资产: {len(results) - injected}", file=sys.stderr)
        print(f"  目标: {args.ep}", file=sys.stderr)
        print(f"  输出: {output_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()

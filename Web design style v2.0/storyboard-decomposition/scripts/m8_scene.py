#!/usr/bin/env python3
"""
m8_scene.py — 场景库 CRUD 模块（v1.0 工程化）

输入：scene_lib/ 目录（多个场景子目录，每个含 scene.json）
输出：CLI 工具，list/show/create/update/delete/reference

设计哲学同 m7_character.py（统一资产库模式）
Why: 跨集场景一致性。EP01 张园外景 → EP02/EP03 复用同一视觉基准。
"""

import sys
import json
import argparse
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


SCENE_SCHEMA = {
    "id": "场景_xxx",
    "name": "场景名",
    "version": "1.0.0",
    "type": "scene",
    "created_at": "YYYY-MM-DD",

    "location": {
        "city": "城市",
        "district": "区",
        "specific": "具体地点",
        "era": "年代"
    },

    "time": {
        "default": "日/夜/黄昏/黎明",
        "valid_times": ["日"],
        "weather": "天气",
        "season": "季节"
    },

    "visual_baseline": {
        "architecture": [],
        "props": [],
        "lighting": {
            "primary": "光源描述",
            "intensity": "0-100%",
            "color_temperature": "K",
            "atmosphere": "氛围描述"
        },
        "color_palette": {
            "primary": ["#000000"],
            "accent": ["#ffffff"]
        },
        "aspect_ratio": "9:16",
        "lens_recommendation": "焦距+景深"
    },

    "mood": {
        "atmosphere": "氛围",
        "tension": "高/中/低",
        "emotional_arc": "情绪弧"
    },

    "sound": {
        "ambient": "环境音",
        "bgm_start": "BGM 起始",
        "foley": ["音效1"]
    },

    "assets": {
        "reference_images": [],
        "stable_diffusion_prompt": "SD prompt",
        "lora_path": None
    },

    "consistency_rules": {
        "must_keep": [],
        "must_change": []
    },

    "ep_appearances": {},

    "prompt_template": "（M3 prompt 模板片段）",
    "notes": "备注"
}


def find_scene_dir(lib_dir: Path, scene_id: str) -> Optional[Path]:
    return lib_dir / scene_id if (lib_dir / scene_id).is_dir() else None


def list_scenes(lib_dir: Path) -> List[Dict]:
    scenes = []
    for d in sorted(lib_dir.iterdir()):
        if not d.is_dir():
            continue
        jp = d / "scene.json"
        if not jp.exists():
            continue
        try:
            data = json.loads(jp.read_text(encoding="utf-8"))
            scenes.append({
                "id": data.get("id", d.name),
                "name": data.get("name", "?"),
                "location": data.get("location", {}).get("specific", "?"),
                "time": data.get("time", {}).get("default", "?"),
                "appearance_eps": list(data.get("ep_appearances", {}).keys()),
            })
        except json.JSONDecodeError as e:
            print(f"⚠ {jp}: JSON 错误: {e}", file=sys.stderr)
    return scenes


def show_scene(lib_dir: Path, scene_id: str) -> Optional[Dict]:
    d = find_scene_dir(lib_dir, scene_id)
    if not d:
        return None
    return json.loads((d / "scene.json").read_text(encoding="utf-8"))


def create_scene(lib_dir: Path, scene_id: str, template: Optional[Dict] = None) -> Dict:
    d = lib_dir / scene_id
    if d.exists():
        raise FileExistsError(f"场景已存在: {d}")
    d.mkdir(parents=True)
    data = template or SCENE_SCHEMA.copy()
    data["id"] = scene_id
    data["name"] = scene_id.replace("场景_", "")
    data["created_at"] = datetime.now().strftime("%Y-%m-%d")
    (d / "scene.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def delete_scene(lib_dir: Path, scene_id: str) -> bool:
    d = find_scene_dir(lib_dir, scene_id)
    if not d:
        return False
    shutil.rmtree(d)
    return True


def generate_reference(scene_data: Dict, target_ep: str) -> str:
    lines = [f"【延续资产·{scene_data['id']}】"]
    lines.append(f"  • 地点: {scene_data.get('location', {}).get('specific', '?')}")
    lines.append(f"  • 时间: {scene_data.get('time', {}).get('default', '?')}")
    lines.append(f"  • 目标集数: {target_ep}")
    consistency = scene_data.get("consistency_rules", {})
    if consistency.get("must_keep"):
        lines.append(f"  • 必须保留: {', '.join(consistency['must_keep'])}")
    vb = scene_data.get("visual_baseline", {})
    if vb.get("lighting"):
        lines.append(f"  • 光照基准: {vb['lighting'].get('primary', '?')}")
    if scene_data.get("prompt_template"):
        lines.append(f"  • Prompt 模板: {scene_data['prompt_template']}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="m8_scene — 场景库 CRUD")
    parser.add_argument("action", choices=["list", "show", "create", "delete", "reference"])
    parser.add_argument("scene_id", nargs="?")
    parser.add_argument("--lib-dir", default="./scene_lib")
    parser.add_argument("--ep", help="目标集数（reference）")
    args = parser.parse_args()

    lib_dir = Path(args.lib_dir)
    if not lib_dir.exists():
        print(f"❌ 场景库目录不存在: {lib_dir}", file=sys.stderr)
        sys.exit(1)

    if args.action == "list":
        scenes = list_scenes(lib_dir)
        if not scenes:
            print("（空）")
            return
        print(f"📚 场景库 ({len(scenes)} 个场景):\n")
        for s in scenes:
            eps = ", ".join(s["appearance_eps"])
            print(f"  {s['id']:30s} | {s['name']:10s} | {s['location']:20s} | {s['time']:4s} | 出场: {eps}")

    elif args.action == "show":
        if not args.scene_id:
            print("❌ show 需要 scene_id", file=sys.stderr)
            sys.exit(1)
        data = show_scene(lib_dir, args.scene_id)
        if not data:
            print(f"❌ 场景不存在: {args.scene_id}", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(data, ensure_ascii=False, indent=2))

    elif args.action == "create":
        if not args.scene_id:
            print("❌ create 需要 scene_id", file=sys.stderr)
            sys.exit(1)
        try:
            data = create_scene(lib_dir, args.scene_id)
            print(f"✅ 场景创建: {args.scene_id}")
        except FileExistsError as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "delete":
        if not args.scene_id:
            print("❌ delete 需要 scene_id", file=sys.stderr)
            sys.exit(1)
        if delete_scene(lib_dir, args.scene_id):
            print(f"✅ 场景已删除: {args.scene_id}")
        else:
            print(f"❌ 场景不存在: {args.scene_id}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "reference":
        if not args.scene_id or not args.ep:
            print("❌ reference 需要 scene_id 和 --ep", file=sys.stderr)
            sys.exit(1)
        data = show_scene(lib_dir, args.scene_id)
        if not data:
            print(f"❌ 场景不存在: {args.scene_id}", file=sys.stderr)
            sys.exit(1)
        print(generate_reference(data, args.ep))


if __name__ == "__main__":
    main()

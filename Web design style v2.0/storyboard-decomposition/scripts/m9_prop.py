#!/usr/bin/env python3
"""
m9_prop.py — 道具库 CRUD 模块（v1.0 工程化）

输入：prop_lib/ 目录
输出：CLI 工具，list/show/create/delete/reference

设计哲学同 m7/m8（统一资产库模式）
Why: 跨集道具状态演化（墨镜在 EP01 摘下后，EP02 不能戴回去）
"""

import sys
import json
import argparse
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


PROP_SCHEMA = {
    "id": "道具_xxx",
    "name": "道具名",
    "version": "1.0.0",
    "type": "prop",
    "created_at": "YYYY-MM-DD",

    "owner": "人物_xxx",
    "category": "配饰/服装/工具/食品",
    "subcategory": "墨镜/戒指/杯子",

    "appearance": {
        "type": "具体类型",
        "frame": "材质+颜色",
        "size": "尺寸",
        "brand_impression": "品牌感",
        "distinctive_features": []
    },

    "state_evolution": {
        "EP01_镜001_镜003": {
            "state": "戴在脸上",
            "position": "面部",
            "function": "遮挡"
        }
    },

    "consistency_rules": {
        "must_keep": [],
        "must_change": []
    },

    "assets": {
        "reference_images": []
    },

    "prompt_templates": {
        "worn": "（戴在身上的 prompt）",
        "in_hand": "（拿在手里的 prompt）",
        "default": "（默认 prompt）"
    },

    "notes": "备注"
}


def find_prop_dir(lib_dir: Path, prop_id: str) -> Optional[Path]:
    return lib_dir / prop_id if (lib_dir / prop_id).is_dir() else None


def list_props(lib_dir: Path) -> List[Dict]:
    props = []
    for d in sorted(lib_dir.iterdir()):
        if not d.is_dir():
            continue
        jp = d / "prop.json"
        if not jp.exists():
            continue
        try:
            data = json.loads(jp.read_text(encoding="utf-8"))
            props.append({
                "id": data.get("id", d.name),
                "name": data.get("name", "?"),
                "owner": data.get("owner", "?"),
                "category": data.get("category", "?"),
                "state_keys": list(data.get("state_evolution", {}).keys()),
            })
        except json.JSONDecodeError as e:
            print(f"⚠ {jp}: JSON 错误: {e}", file=sys.stderr)
    return props


def show_prop(lib_dir: Path, prop_id: str) -> Optional[Dict]:
    d = find_prop_dir(lib_dir, prop_id)
    if not d:
        return None
    return json.loads((d / "prop.json").read_text(encoding="utf-8"))


def create_prop(lib_dir: Path, prop_id: str, template: Optional[Dict] = None) -> Dict:
    d = lib_dir / prop_id
    if d.exists():
        raise FileExistsError(f"道具已存在: {d}")
    d.mkdir(parents=True)
    data = template or PROP_SCHEMA.copy()
    data["id"] = prop_id
    data["name"] = prop_id.replace("道具_", "")
    data["created_at"] = datetime.now().strftime("%Y-%m-%d")
    (d / "prop.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def delete_prop(lib_dir: Path, prop_id: str) -> bool:
    d = find_prop_dir(lib_dir, prop_id)
    if not d:
        return False
    shutil.rmtree(d)
    return True


def generate_state_reference(prop_data: Dict, ep: str, mirror_range: Optional[str] = None) -> str:
    """生成指定 EP+镜范围的道具状态引用"""
    lines = [f"【道具状态·{prop_data['id']}】"]
    lines.append(f"  • 拥有者: {prop_data.get('owner', '?')}")

    state_evo = prop_data.get("state_evolution", {})

    # 找匹配的 state key
    matched = []
    if mirror_range:
        # 解析 mirror_range 如 "EP01_镜004_镜011"
        for state_key, state_data in state_evo.items():
            if state_key.startswith(ep) and mirror_range in state_key:
                matched.append((state_key, state_data))
    else:
        # 默认取 EP 的第一个 state
        for state_key, state_data in state_evo.items():
            if state_key.startswith(ep):
                matched.append((state_key, state_data))

    for state_key, state_data in matched:
        lines.append(f"  • [{state_key}]")
        lines.append(f"    - 状态: {state_data.get('state', '?')}")
        lines.append(f"    - 位置: {state_data.get('position', '?')}")
        lines.append(f"    - 功能: {state_data.get('function', '?')}")
        if "transition" in state_data:
            lines.append(f"    - 转变: {state_data['transition']}")

    # Prompt 模板
    templates = prop_data.get("prompt_templates", {})
    if templates:
        for state_name, template in templates.items():
            lines.append(f"  • Prompt ({state_name}): {template}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="m9_prop — 道具库 CRUD")
    parser.add_argument("action", choices=["list", "show", "create", "delete", "state"])
    parser.add_argument("prop_id", nargs="?")
    parser.add_argument("--lib-dir", default="./prop_lib")
    parser.add_argument("--ep", help="目标集数（state 操作）")
    parser.add_argument("--mirror-range", help="镜范围，如 镜004_镜011（state 操作）")
    args = parser.parse_args()

    lib_dir = Path(args.lib_dir)
    if not lib_dir.exists():
        print(f"❌ 道具库目录不存在: {lib_dir}", file=sys.stderr)
        sys.exit(1)

    if args.action == "list":
        props = list_props(lib_dir)
        if not props:
            print("（空）")
            return
        print(f"📚 道具库 ({len(props)} 个道具):\n")
        for p in props:
            print(f"  {p['id']:20s} | {p['name']:15s} | 拥有: {p['owner']:15s} | 类别: {p['category']} | 状态点: {len(p['state_keys'])}")

    elif args.action == "show":
        if not args.prop_id:
            print("❌ show 需要 prop_id", file=sys.stderr)
            sys.exit(1)
        data = show_prop(lib_dir, args.prop_id)
        if not data:
            print(f"❌ 道具不存在: {args.prop_id}", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(data, ensure_ascii=False, indent=2))

    elif args.action == "create":
        if not args.prop_id:
            print("❌ create 需要 prop_id", file=sys.stderr)
            sys.exit(1)
        try:
            data = create_prop(lib_dir, args.prop_id)
            print(f"✅ 道具创建: {args.prop_id}")
        except FileExistsError as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "delete":
        if not args.prop_id:
            print("❌ delete 需要 prop_id", file=sys.stderr)
            sys.exit(1)
        if delete_prop(lib_dir, args.prop_id):
            print(f"✅ 道具已删除: {args.prop_id}")
        else:
            print(f"❌ 道具不存在: {args.prop_id}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "state":
        if not args.prop_id or not args.ep:
            print("❌ state 需要 prop_id 和 --ep", file=sys.stderr)
            sys.exit(1)
        data = show_prop(lib_dir, args.prop_id)
        if not data:
            print(f"❌ 道具不存在: {args.prop_id}", file=sys.stderr)
            sys.exit(1)
        print(generate_state_reference(data, args.ep, args.mirror_range))


if __name__ == "__main__":
    main()

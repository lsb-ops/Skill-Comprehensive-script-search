#!/usr/bin/env python3
"""
m7_character.py — 角色卡 CRUD 模块（v1.0 工程化）

输入：character_lib/ 目录（多个角色子目录，每个含 character.json）
输出：CLI 工具，支持 list/show/create/update/delete + 跨集资产引用

用法:
    python3 m7_character.py list                    # 列出所有角色
    python3 m7_character.py show 人物_刘一鸣         # 显示角色详情
    python3 m7_character.py create 人物_xxx         # 创建新角色（交互式）
    python3 m7_character.py update 人物_刘一鸣      # 更新角色（交互式）
    python3 m7_character.py delete 人物_xxx         # 删除角色
    python3 m7_character.py reference 人物_刘一鸣 EP02  # 生成 EP02 引用片段

设计哲学：
1. 角色卡 = 单一信息源（single source of truth）
2. 跨集复用：EP01 创建 → EP02/EP03 引用（state_evolution 累积）
3. schema 严格：JSON 字段名固定，工具链强依赖
4. CRUD 全：list/show/create/update/delete + reference
5. 与 M3/M5 集成：m3_generate.py 读角色库生成 prompt 模板

Why: 解决"用户做完 EP01 就放弃"的最大痛点 — 跨集角色一致性。
     角色库让 EP01 角色资产在 EP02 自动复用，无需重新设计。
"""

import sys
import json
import argparse
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


# === 角色卡 Schema（核心数据契约） ===

CHARACTER_SCHEMA = {
    "id": "人物_xxx",
    "name": "角色名",
    "version": "1.0.0",
    "type": "character",
    "role": "主角/配角/对手/群演",
    "ep_first_appearance": "EP01",
    "created_at": "YYYY-MM-DD",
    "updated_at": "YYYY-MM-DD",

    "basic_info": {
        "gender": "男/女",
        "age": 0,
        "height": "180cm",
        "ethnicity": "汉族",
        "voice": "描述",
    },

    "appearance": {
        "hair": "发型描述",
        "face": "脸型描述",
        "build": "体型描述",
        "skin": "肤色描述",
        "distinctive_features": ["特征1", "特征2"],
    },

    "wardrobe": {
        "primary_outfit": {
            "name": "主造型名",
            "items": ["衣服1", "衣服2"],
            "color_palette": ["#000000", "#1a1a2e"],
            "fit": "修身/宽松",
        },
    },

    "personality": {
        "core_traits": ["特征1", "特征2"],
        "speech_pattern": "语言风格",
        "tics": ["小动作1", "小动作2"],
    },

    "assets": {
        "reference_images": ["路径1", "路径2"],
        "lora_path": None,
        "ip_adapter_embeds": None,
    },

    "consistency_rules": {
        "must_keep": ["必须保留的特征"],
        "must_change": ["可以变化的特征"],
    },

    "ep_appearances": {
        "EP01": {
            "first_mirror": "镜001",
            "total_mirrors": 0,
            "key_scenes": ["场景1"],
            "outfit": "主造型名",
        },
    },

    "prompt_template": "（M3 prompt 模板片段）",
    "notes": "（备注）",
}


# === CRUD 操作 ===

def find_character_dir(lib_dir: Path, char_id: str) -> Optional[Path]:
    """查找角色目录"""
    char_dir = lib_dir / char_id
    if char_dir.exists() and char_dir.is_dir():
        return char_dir
    return None


def list_characters(lib_dir: Path) -> List[Dict]:
    """列出所有角色"""
    characters = []
    for char_dir in sorted(lib_dir.iterdir()):
        if not char_dir.is_dir():
            continue
        json_path = char_dir / "character.json"
        if not json_path.exists():
            continue
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            characters.append({
                "id": data.get("id", char_dir.name),
                "name": data.get("name", "?"),
                "role": data.get("role", "?"),
                "ep_first_appearance": data.get("ep_first_appearance", "?"),
                "appearance_eps": list(data.get("ep_appearances", {}).keys()),
                "version": data.get("version", "?"),
            })
        except json.JSONDecodeError as e:
            print(f"⚠ {json_path}: JSON 解析失败: {e}", file=sys.stderr)
    return characters


def show_character(lib_dir: Path, char_id: str) -> Optional[Dict]:
    """显示角色详情"""
    char_dir = find_character_dir(lib_dir, char_id)
    if not char_dir:
        return None
    json_path = char_dir / "character.json"
    return json.loads(json_path.read_text(encoding="utf-8"))


def create_character(lib_dir: Path, char_id: str, template: Optional[Dict] = None) -> Dict:
    """创建新角色（基于 schema 默认值）"""
    char_dir = lib_dir / char_id
    if char_dir.exists():
        raise FileExistsError(f"角色目录已存在: {char_dir}")

    char_dir.mkdir(parents=True)

    # 用模板填充
    data = template or CHARACTER_SCHEMA.copy()
    data["id"] = char_id
    data["name"] = char_id.replace("人物_", "")
    data["created_at"] = datetime.now().strftime("%Y-%m-%d")
    data["updated_at"] = datetime.now().strftime("%Y-%m-%d")

    json_path = char_dir / "character.json"
    json_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    return data


def update_character(lib_dir: Path, char_id: str, updates: Dict) -> Optional[Dict]:
    """更新角色字段"""
    char_dir = find_character_dir(lib_dir, char_id)
    if not char_dir:
        return None

    json_path = char_dir / "character.json"
    data = json.loads(json_path.read_text(encoding="utf-8"))

    # 深合并
    def deep_merge(target, source):
        for k, v in source.items():
            if isinstance(v, dict) and isinstance(target.get(k), dict):
                deep_merge(target[k], v)
            else:
                target[k] = v

    deep_merge(data, updates)
    data["updated_at"] = datetime.now().strftime("%Y-%m-%d")

    json_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    return data


def delete_character(lib_dir: Path, char_id: str) -> bool:
    """删除角色目录"""
    char_dir = find_character_dir(lib_dir, char_id)
    if not char_dir:
        return False
    shutil.rmtree(char_dir)
    return True


def generate_reference(char_data: Dict, target_ep: str) -> str:
    """生成跨集 prompt 引用片段

    用于 M3 提示词模板：自动注入"延续 EP01 角色资产"标记
    """
    appearances = char_data.get("ep_appearances", {})
    first_ep = char_data.get("ep_first_appearance", "?")
    last_ep_appearance = max(appearances.keys(), default=first_ep)

    lines = []
    lines.append(f"【延续资产·{char_data['id']}】")
    lines.append(f"  • 首次出场: {first_ep}")
    lines.append(f"  • 最近出场: {last_ep_appearance}")
    lines.append(f"  • 目标集数: {target_ep}")

    # 提取关键特征
    consistency = char_data.get("consistency_rules", {})
    must_keep = consistency.get("must_keep", [])
    if must_keep:
        lines.append(f"  • 必须保留: {', '.join(must_keep)}")

    # 上集外观延续
    if target_ep in appearances:
        ep_data = appearances[target_ep]
    elif last_ep_appearance in appearances:
        ep_data = appearances[last_ep_appearance]
    else:
        ep_data = {}

    if "outfit" in ep_data:
        lines.append(f"  • 延续造型: {ep_data['outfit']}")
    if "continuity_notes" in ep_data:
        lines.append(f"  • 延续说明: {ep_data['continuity_notes']}")

    # prompt 模板
    if "prompt_template" in char_data:
        lines.append(f"  • Prompt 模板: {char_data['prompt_template']}")

    return "\n".join(lines)


# === Main ===

def main():
    parser = argparse.ArgumentParser(description="m7_character — 角色卡 CRUD（v1.0 工程化）")
    parser.add_argument("action", choices=["list", "show", "create", "update", "delete", "reference"],
                        help="操作类型")
    parser.add_argument("char_id", nargs="?", help="角色 ID（如 人物_刘一鸣）")
    parser.add_argument("--lib-dir", default="./character_lib", help="角色库目录")
    parser.add_argument("--ep", help="目标集数（仅 reference 操作）")
    parser.add_argument("--template", help="创建时用的模板 JSON 路径")
    args = parser.parse_args()

    lib_dir = Path(args.lib_dir)
    if not lib_dir.exists():
        print(f"❌ 角色库目录不存在: {lib_dir}", file=sys.stderr)
        sys.exit(1)

    if args.action == "list":
        characters = list_characters(lib_dir)
        if not characters:
            print("（空）")
            return
        print(f"📚 角色库 ({len(characters)} 个角色):\n")
        for c in characters:
            eps = ", ".join(c["appearance_eps"])
            print(f"  {c['id']:20s} | {c['name']:8s} | {c['role']:10s} | 出场: {eps} | v{c['version']}")

    elif args.action == "show":
        if not args.char_id:
            print("❌ show 需要 char_id", file=sys.stderr)
            sys.exit(1)
        data = show_character(lib_dir, args.char_id)
        if not data:
            print(f"❌ 角色不存在: {args.char_id}", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(data, ensure_ascii=False, indent=2))

    elif args.action == "create":
        if not args.char_id:
            print("❌ create 需要 char_id", file=sys.stderr)
            sys.exit(1)
        template = None
        if args.template:
            template = json.loads(Path(args.template).read_text(encoding="utf-8"))
        try:
            data = create_character(lib_dir, args.char_id, template)
            print(f"✅ 角色创建: {args.char_id}")
            print(f"   路径: {lib_dir / args.char_id / 'character.json'}")
        except FileExistsError as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "update":
        if not args.char_id:
            print("❌ update 需要 char_id", file=sys.stderr)
            sys.exit(1)
        # 简单 update：stdin 读 JSON
        updates = json.loads(sys.stdin.read())
        data = update_character(lib_dir, args.char_id, updates)
        if not data:
            print(f"❌ 角色不存在: {args.char_id}", file=sys.stderr)
            sys.exit(1)
        print(f"✅ 角色已更新: {args.char_id}")

    elif args.action == "delete":
        if not args.char_id:
            print("❌ delete 需要 char_id", file=sys.stderr)
            sys.exit(1)
        if delete_character(lib_dir, args.char_id):
            print(f"✅ 角色已删除: {args.char_id}")
        else:
            print(f"❌ 角色不存在: {args.char_id}", file=sys.stderr)
            sys.exit(1)

    elif args.action == "reference":
        if not args.char_id or not args.ep:
            print("❌ reference 需要 char_id 和 --ep", file=sys.stderr)
            sys.exit(1)
        data = show_character(lib_dir, args.char_id)
        if not data:
            print(f"❌ 角色不存在: {args.char_id}", file=sys.stderr)
            sys.exit(1)
        ref = generate_reference(data, args.ep)
        print(ref)


if __name__ == "__main__":
    main()

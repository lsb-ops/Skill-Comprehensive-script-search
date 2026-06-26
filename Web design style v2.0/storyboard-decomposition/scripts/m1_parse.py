#!/usr/bin/env python3
"""
m1_parse.py — M1 剧本解析模块（v1.0 工程化）

输入：任意剧本（小说/大纲/分场/完整剧本）
输出：JSON 格式结构化数据
  - scenes: 场景列表
  - characters: 人物清单
  - actions: 戏剧动作清单
  - dialogue: 剧本原词（对白+舞台指示）
  - structure: 5 幕结构
  - style: 风格（自动检测）

用法:
    python3 m1_parse.py <剧本文件> [输出JSON]
    python3 m1_parse.py <剧本文件> --style 古早霸总
    echo "剧本内容..." | python3 m1_parse.py -

设计哲学：M1 是"语义理解"任务，最佳执行者是 LLM Agent。
本脚本提供：
1. JSON schema 定义（保证下游模块接口一致）
2. 启发式解析（场景/人物/对白识别，无 LLM 也能跑）
3. LLM 增强模式（--llm 启用，调用 LLM API 提高准确度）

Why：M1 是 M2/M3 的输入源，schema 一致性 = 工程可重现性
"""

import sys
import json
import re
import argparse
import os
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Any, Optional


# === JSON Schema 定义 ===

M1_OUTPUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "script_meta": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "ep": {"type": "string"},
                "style": {"type": "string"},
                "total_duration_target": {"type": "number"},
                "source_file": {"type": "string"},
            }
        },
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "pattern": r"^S\d{2}$"},
                    "time": {"type": "string", "enum": ["日", "夜", "黄昏", "黎明", "未知"]},
                    "location": {"type": "string"},
                    "characters": {"type": "array", "items": {"type": "string"}},
                    "props": {"type": "array", "items": {"type": "string"}},
                    "mood": {"type": "string"},
                    "structure_position": {"type": "string"},
                }
            }
        },
        "characters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "pattern": r"^P\d{2}$"},
                    "name": {"type": "string"},
                    "role": {"type": "string", "enum": ["主角", "对手", "配角", "群演"]},
                    "gender": {"type": "string"},
                    "age": {"type": "number"},
                    "height": {"type": "string"},
                    "traits": {"type": "array", "items": {"type": "string"}},
                }
            }
        },
        "actions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "pattern": r"^A\d{3}$"},
                    "scene_id": {"type": "string"},
                    "character_id": {"type": "string"},
                    "description": {"type": "string"},
                    "physical_details": {"type": "array", "items": {"type": "string"}},
                    "dialogue": {"type": "string"},
                }
            }
        },
        "dialogue": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "character_id": {"type": "string"},
                    "text": {"type": "string"},
                    "context": {"type": "string"},
                }
            }
        },
        "structure": {
            "type": "object",
            "properties": {
                "setup": {"type": "string"},
                "trigger": {"type": "string"},
                "twist1": {"type": "string"},
                "twist2": {"type": "string"},
                "resolution": {"type": "string"},
            }
        },
        "style": {
            "type": "string",
            "enum": ["古早霸总", "都市情感", "古装江湖", "科幻未来", "校园青春", "悬疑推理", "战争军事", "家庭伦理", "未知"]
        }
    }
}


# === 启发式解析（无 LLM）===

# 场景识别模式
SCENE_PATTERNS = [
    r'^第[一二三四五六七八九十\d]+[场幕]',
    r'^\d+[\.、]\s*场',
    r'^【场景[：:]',
    r'^\(场景',
    r'^Scene\s*\d+',
    r'^\d+[\.\s]+',  # 数字开头
]

# 对白识别模式
DIALOGUE_PATTERNS = [
    r'^(.+?)[：:]\s*[\"「](.+)[\"」]\s*$',  # 角色：内容
    r'^(.+?)\s*[：:]\s*[\"「](.+)[\"」]?\s*$',
    r'^(.+?)（(.+?)）\s*[：:]\s*(.+)$',  # 角色（情绪）：内容
]

# 人物识别模式（基于对白）
CHARACTER_HINTS = [
    r'^(.+?)[：:]',  # 对白中的角色
    r'^(.+?)（',  # 角色（情绪）
]


def detect_scenes(text: str) -> List[Dict[str, Any]]:
    """启发式场景识别"""
    scenes = []
    lines = text.split('\n')
    scene_idx = 1

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        for pattern in SCENE_PATTERNS:
            if re.match(pattern, line):
                # 提取场景描述
                location = re.sub(pattern, '', line).strip()
                location = re.sub(r'[【】\[\]（）()]', '', location)
                if len(location) > 50:
                    location = location[:50] + '...'

                scenes.append({
                    "id": f"S{scene_idx:02d}",
                    "time": "未知",
                    "location": location or f"场景{scene_idx}",
                    "characters": [],
                    "props": [],
                    "mood": "中性",
                    "structure_position": "建制" if scene_idx == 1 else "发展中"
                })
                scene_idx += 1
                break

    # 如果没有识别到场景，整个剧本作为单一场景
    if not scenes:
        scenes.append({
            "id": "S01",
            "time": "未知",
            "location": "（自动识别：单一场景）",
            "characters": [],
            "props": [],
            "mood": "中性",
            "structure_position": "建制"
        })

    return scenes


def detect_dialogue(text: str) -> List[Dict[str, Any]]:
    """启发式对白识别"""
    dialogue = []
    lines = text.split('\n')

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        for pattern in DIALOGUE_PATTERNS:
            m = re.match(pattern, line)
            if m:
                groups = m.groups()
                if len(groups) == 2:
                    char_name, content = groups
                    dialogue.append({
                        "id": f"D{len(dialogue)+1:03d}",
                        "character_id": char_name.strip(),
                        "text": content.strip(),
                        "context": lines[max(0, i-1)].strip() if i > 0 else ""
                    })
                elif len(groups) == 3:
                    char_name, emotion, content = groups
                    dialogue.append({
                        "id": f"D{len(dialogue)+1:03d}",
                        "character_id": char_name.strip(),
                        "text": content.strip(),
                        "context": f"[{emotion.strip()}]"
                    })
                break

    return dialogue


def extract_characters(text: str, dialogue: List[Dict]) -> List[Dict[str, Any]]:
    """从对白中提取人物清单"""
    char_names = set()
    for d in dialogue:
        if d.get("character_id"):
            char_names.add(d["character_id"])

    characters = []
    for i, name in enumerate(sorted(char_names), 1):
        characters.append({
            "id": f"P{i:02d}",
            "name": name,
            "role": "主角" if i == 1 else ("对手" if i == 2 else "配角"),
            "gender": "未知",
            "age": 0,
            "height": "未知",
            "traits": []
        })

    # 如果没有对白，从剧本描述中提取
    if not characters:
        # 启发式：提取大写/特殊格式的姓名
        potential_names = re.findall(r'([\u4e00-\u9fff]{2,3})(?:说|道|问|喊|笑|哭|走|来|去)', text)
        for i, name in enumerate(sorted(set(potential_names))[:5], 1):
            characters.append({
                "id": f"P{i:02d}",
                "name": name,
                "role": "主角" if i == 1 else "配角",
                "gender": "未知",
                "age": 0,
                "height": "未知",
                "traits": []
            })

    return characters


def detect_style(text: str) -> str:
    """启发式风格检测（无 LLM 版本）"""
    style_keywords = {
        "古早霸总": ["霸总", "总裁", "霸道", "邪魅", "冷酷", "壁咚", "豪车", "私人飞机", "白月光", "替身", "契约", "豪门"],
        "都市情感": ["职场", "恋爱", "相亲", "闺蜜", "前任", "咖啡店", "写字楼", "加班"],
        "古装江湖": ["江湖", "侠客", "武林", "门派", "武功", "皇宫", "朝廷", "江湖儿女"],
        "科幻未来": ["机器人", "AI", "太空", "星际", "飞船", "赛博", "未来", "克隆", "虚拟"],
        "校园青春": ["校园", "高中", "大学", "教室", "同桌", "毕业", "青春", "初恋"],
        "悬疑推理": ["案件", "凶手", "线索", "侦探", "真相", "密室", "推理", "嫌疑"],
        "战争军事": ["战场", "部队", "将军", "士兵", "战役", "军火", "军营", "前线"],
        "家庭伦理": ["家庭", "父母", "子女", "婆媳", "亲情", "家产", "遗产", "家族"],
    }

    scores = {}
    for style, keywords in style_keywords.items():
        score = sum(1 for kw in keywords if kw in text)
        scores[style] = score

    if not scores or max(scores.values()) == 0:
        return "未知"

    return max(scores, key=scores.get)


def parse_script(text: str, source_file: str = "", style_override: Optional[str] = None) -> Dict[str, Any]:
    """主解析入口"""
    # 1. 提取标题（第一行非空文本）
    title = ""
    for line in text.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            title = line[:50]
            break

    # 2. 场景
    scenes = detect_scenes(text)

    # 3. 对白
    dialogue = detect_dialogue(text)

    # 4. 人物（从对白提取）
    characters = extract_characters(text, dialogue)

    # 5. 动作（启发式：从动词密度高的句子提取）
    actions = []
    action_idx = 1
    sentences = re.split(r'[。！？\n]', text)
    for sent in sentences:
        sent = sent.strip()
        if not sent or len(sent) < 5 or len(sent) > 200:
            continue
        # 检测动作动词
        if re.search(r'(走|跑|推|拉|看|笑|哭|喊|打|抱|接|递|拿|放|坐|站|转身|回头)', sent):
            actions.append({
                "id": f"A{action_idx:03d}",
                "scene_id": scenes[0]["id"] if scenes else "S01",
                "character_id": characters[0]["id"] if characters else "P01",
                "description": sent,
                "physical_details": [],
                "dialogue": ""
            })
            action_idx += 1

    # 6. 5 幕结构（启发式：基于场景位置分配）
    structure = {}
    if scenes:
        n = len(scenes)
        structure["setup"] = scenes[0]["location"] if n > 0 else ""
        structure["trigger"] = scenes[1]["location"] if n > 1 else ""
        structure["twist1"] = scenes[n//2]["location"] if n > 2 else ""
        structure["twist2"] = scenes[3*n//4]["location"] if n > 3 else ""
        structure["resolution"] = scenes[-1]["location"] if n > 0 else ""

    # 7. 风格检测
    style = style_override if style_override and style_override != "auto" else detect_style(text)

    # 8. 元数据
    return {
        "script_meta": {
            "title": title,
            "ep": "EP01",
            "style": style,
            "total_duration_target": 80.0,
            "source_file": source_file
        },
        "scenes": scenes,
        "characters": characters,
        "actions": actions[:50],  # 限制数量
        "dialogue": dialogue[:30],  # 限制数量
        "structure": structure,
        "style": style
    }


def validate_output(data: Dict) -> List[str]:
    """验证输出是否符合 schema（轻量版）"""
    issues = []
    if not data.get("script_meta", {}).get("title"):
        issues.append("缺少 script_meta.title")
    if not data.get("scenes"):
        issues.append("缺少 scenes（至少应有 1 个场景）")
    if not data.get("characters"):
        issues.append("缺少 characters（至少应有 1 个人物）")
    if not data.get("style"):
        issues.append("缺少 style")
    return issues


# === LLM 增强模式（v1.0 工程化）===

# Anthropic Claude API 配置（支持 ANTHROPIC_BASE_URL 环境变量切换代理）
_DEFAULT_BASE = "https://api.anthropic.com"
_BASE = os.environ.get("ANTHROPIC_BASE_URL", _DEFAULT_BASE).rstrip("/")
LLM_CONFIG = {
    "endpoint": f"{_BASE}/v1/messages",
    "auth_env": "ANTHROPIC_API_KEY",
    "auth_token_env": "ANTHROPIC_AUTH_TOKEN",  # 兼容 proxy
    "model": os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
    "max_tokens": 4096,
    "api_version": "2023-06-01",
}


# 提示词：让 LLM 严格输出 JSON
LLM_PARSE_PROMPT = """你是专业的短剧分镜头脚本解析专家。请将以下剧本解析为严格 JSON 格式。

【输入剧本】
{script_text}

【输出要求】
1. 必须输出**纯 JSON**（不要 markdown 代码块、不要任何解释）
2. 字段必须严格遵循以下 schema（缺字段用空值/null/[]，不要添加新字段）：
{{
  "script_meta": {{
    "title": "剧本标题（首行）",
    "ep": "EP01（默认）",
    "style": "古早霸总/都市情感/古装江湖/科幻未来/校园青春/悬疑推理/战争军事/家庭伦理/未知",
    "total_duration_target": 80,
    "source_file": "源文件名"
  }},
  "scenes": [
    {{"id": "S01", "time": "日/夜/黄昏/黎明/未知", "location": "具体地点", "characters": ["角色名"], "props": ["道具名"], "mood": "氛围", "structure_position": "建制/触发/反转一/反转二/收束"}}
  ],
  "characters": [
    {{"id": "P01", "name": "姓名", "role": "主角/对手/配角/群演", "gender": "男/女/未知", "age": 数字或0, "height": "身高或未知", "traits": ["特征1"]}}
  ],
  "actions": [
    {{"id": "A001", "scene_id": "S01", "character_id": "P01", "description": "动作描述", "physical_details": ["细节1"], "dialogue": "对白原文"}}
  ],
  "dialogue": [
    {{"id": "D001", "character_id": "P01", "text": "对白内容", "context": "情绪/场景注"}}
  ],
  "structure": {{
    "setup": "第一幕地点/情境",
    "trigger": "第二幕触发事件",
    "twist1": "第三幕反转一",
    "twist2": "第四幕反转二",
    "resolution": "第五幕收束"
  }},
  "narrator": ["旁白原文（内心OS/画外音）"],
  "ambient_sound": {{"A": "环境音A段", "B": "环境音B段"}},
  "global_constraints": ["全局约束1", "全局约束2"],
  "style_cues": [{{"mirror": "镜007", "trigger": "风格切换Cue"}}],
  "timecode_map": {{"第一幕": "00:00-00:05"}}
}}

【重要】
- 5 幕结构：从剧本"第一幕/第二幕/..."中提取
- 旁白（narrator）：提取所有"内心OS/画外音"原文
- 环境音：从剧本"环境音"表格提取
- 全局约束：剧本开头【】括起的所有全局规则
- 风格切换Cue：标记风格切换的硬性 cue
- 角色 traits：从【人物外观】/【全局约束】提取关键外貌特征

现在请输出 JSON："""


def call_llm_parse(text: str, source_file: str = "") -> Optional[Dict[str, Any]]:
    """调用 Claude API 解析剧本

    Returns:
        解析后的 dict，失败返回 None
    """
    api_key = os.environ.get(LLM_CONFIG["auth_env"]) or os.environ.get(LLM_CONFIG.get("auth_token_env", ""), "")
    if not api_key:
        return None

    headers = {
        "x-api-key": api_key,
        "anthropic-version": LLM_CONFIG["api_version"],
        "content-type": "application/json",
    }

    body = json.dumps({
        "model": LLM_CONFIG["model"],
        "max_tokens": LLM_CONFIG["max_tokens"],
        "messages": [{
            "role": "user",
            "content": LLM_PARSE_PROMPT.format(script_text=text[:8000])  # 截断避免超长
        }]
    }).encode("utf-8")

    req = urllib.request.Request(
        LLM_CONFIG["endpoint"],
        data=body,
        headers=headers,
        method="POST"
    )

    # 指数退避重试 3 次
    for attempt in range(3):
        try:
            # 自签名证书场景下允许跳过验证（可通过 ANTHROPIC_INSECURE=1 启用）
            ctx = None
            if os.environ.get("ANTHROPIC_INSECURE") == "1":
                import ssl
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                content = result.get("content", [{}])[0].get("text", "")
                content = content.strip()
                if content.startswith("```"):
                    content = re.sub(r'^```(?:json)?\s*\n', '', content)
                    content = re.sub(r'\n```\s*$', '', content)
                return json.loads(content)
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, KeyError) as e:
            if attempt < 2:
                wait = 2 ** attempt
                print(f"⚠ LLM API 失败 (attempt {attempt+1}/3): {e}, {wait}s 后重试", file=sys.stderr)
                time.sleep(wait)
            else:
                print(f"❌ LLM API 最终失败: {e}", file=sys.stderr)
                return None
    return None


def mock_llm_parse(text: str, source_file: str = "") -> Dict[str, Any]:
    """Mock LLM 解析（无 API 凭证时演示用）

    演示 LLM 应输出的完整结构（含 5 幕/旁白/环境音/全局约束等启发式遗漏字段）
    """
    title = ""
    for line in text.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            title = line[:50]
            break

    narrator = re.findall(r'[「""\'\']{1,2}([^」""\'\']{5,80})[」""\'\']{1,2}', text)
    constraints = re.findall(r'【(.+?)】', text)
    cues = re.findall(r'(镜\d+).*?(?:刹车|划痕|风格切换)', text)

    return {
        "script_meta": {
            "title": title or "未命名剧本",
            "ep": "EP01",
            "style": "未知",
            "total_duration_target": 80.0,
            "source_file": source_file,
        },
        "scenes": [],
        "characters": [],
        "actions": [],
        "dialogue": [],
        "structure": {
            "setup": "（mock LLM 模式：请配置 ANTHROPIC_API_KEY 启用真实 LLM 解析）",
            "trigger": "",
            "twist1": "",
            "twist2": "",
            "resolution": "",
        },
        "narrator": narrator[:5],
        "ambient_sound": {"note": "（mock 模式：需 API key 启用完整解析）"},
        "global_constraints": constraints[:5],
        "style_cues": [{"mirror": c, "trigger": "mock"} for c in cues[:3]],
        "timecode_map": {},
        "_mock": True,
    }


def llm_parse_script(text: str, source_file: str = "", force_mock: bool = False) -> Dict[str, Any]:
    """LLM 解析入口（含 mock 降级）

    Args:
        text: 剧本文本
        source_file: 源文件名
        force_mock: 强制 mock（用于测试）

    Returns:
        解析后的 dict
    """
    if force_mock or not os.environ.get(LLM_CONFIG["auth_env"]):
        if not force_mock:
            print("⚠ 未配置 ANTHROPIC_API_KEY，使用 mock LLM 模式", file=sys.stderr)
        result = mock_llm_parse(text, source_file)
    else:
        result = call_llm_parse(text, source_file)
        if result is None:
            print("⚠ LLM 解析失败，降级到 mock 模式", file=sys.stderr)
            result = mock_llm_parse(text, source_file)

    # 合并：scenes/characters/dialogue/actions 仍走启发式（LLM 也常漏）
    heuristic = parse_script(text, source_file=source_file)
    for key in ("scenes", "characters", "dialogue", "actions"):
        if not result.get(key):
            result[key] = heuristic.get(key, [])
        elif key == "scenes" and len(result[key]) < len(heuristic.get(key, [])):
            existing = {s.get("id") for s in result[key]}
            for s in heuristic[key]:
                if s.get("id") not in existing:
                    result[key].append(s)

    # 保留 script_meta 风格
    if not result.get("style") or result.get("style") == "未知":
        result["style"] = heuristic.get("style", "未知")
    if result.get("script_meta"):
        result["script_meta"]["style"] = result.get("style", "未知")
        result["script_meta"]["source_file"] = source_file

    return result


def main():
    parser = argparse.ArgumentParser(description="M1 剧本解析（v1.0 工程化）")
    parser.add_argument("input", help="剧本文件路径（- 表示 stdin）")
    parser.add_argument("output", nargs="?", help="输出 JSON 路径（默认 stdout）")
    parser.add_argument("--style", default="auto", help="强制指定风格（默认自动检测）")
    parser.add_argument("--source-file", default="", help="源文件名（用于 metadata）")
    parser.add_argument("--validate", action="store_true", help="验证输出 schema")
    parser.add_argument("--llm", action="store_true", help="启用 LLM 增强模式（需 ANTHROPIC_API_KEY，否则降级 mock）")
    parser.add_argument("--mock-llm", action="store_true", help="强制 mock LLM 模式（跳过真实 API 调用）")
    args = parser.parse_args()

    # 读取输入
    if args.input == "-":
        text = sys.stdin.read()
        source = args.source_file or "<stdin>"
    else:
        text = Path(args.input).read_text(encoding="utf-8")
        source = args.input

    # 解析（启发式 或 LLM 增强）
    if args.llm or args.mock_llm:
        data = llm_parse_script(text, source_file=source, force_mock=args.mock_llm)
    else:
        data = parse_script(text, source_file=source, style_override=args.style)

    # 验证
    if args.validate:
        issues = validate_output(data)
        if issues:
            print("⚠ 输出验证发现问题:", file=sys.stderr)
            for issue in issues:
                print(f"  - {issue}", file=sys.stderr)
            if "--strict" in sys.argv:
                sys.exit(1)

    # 输出
    output_json = json.dumps(data, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output_json, encoding="utf-8")
        print(f"✅ M1 解析完成: {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()

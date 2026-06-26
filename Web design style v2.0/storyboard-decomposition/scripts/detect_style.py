#!/usr/bin/env python3
"""
detect_style.py — 剧本风格自动检测

用法:
    python detect_style.py <script_file>
    python detect_style.py <script_file> --json

支持的风格:
    古早霸总 / 都市情感 / 古装江湖 / 科幻未来
    校园青春 / 悬疑推理 / 战争军事 / 家庭伦理
"""

import sys
import json
import re
from pathlib import Path


# 风格关键词库
STYLE_KEYWORDS = {
    "古早霸总": {
        "high": ["霸总", "总裁", "霸道", "契约婚姻", "闪婚", "灰姑娘", "虐恋",
                "黑帮", "墨镜", "西装", "皮鞋", "普法", "教化", "升华", "剪影"],
        "medium": ["助理", "名片", "公司", "豪华", "豪车", "律师", "金额"],
        "patterns": [r"180cm", r"Prada", r"全黑西装"],
    },
    "都市情感": {
        "high": ["都市", "职场", "离婚", "婚姻", "复婚", "出轨", "求婚",
                "老公", "老婆", "婚礼", "离婚协议"],
        "medium": ["咖啡厅", "办公室", "加班", "前男友", "前女友"],
        "patterns": [r"\d+年\d+月", r"婚姻法"],
    },
    "古装江湖": {
        "high": ["古装", "江湖", "侠客", "剑", "武侠", "朝堂", "宫斗",
                "皇上", "娘娘", "太子", "武林", "门派", "江湖儿女"],
        "medium": ["长衫", "宫殿", "王爷", "大臣", "宫女"],
        "patterns": [r"少侠", r"大侠", r"皇宫"],
    },
    "科幻未来": {
        "high": ["科幻", "未来", "太空", "机器人", "AI", "星际", "赛博",
                "黑客", "程序", "算法", "飞船", "宇航员", "外星人"],
        "medium": ["全息", "数字", "代码", "虚拟", "穿越"],
        "patterns": [r"\d{4}年", r"宇宙"],
    },
    "校园青春": {
        "high": ["校园", "同学", "高考", "毕业", "校服", "青春",
                "教室", "操场", "初恋", "暗恋", "同桌", "学长", "学姐"],
        "medium": ["学生", "考试", "作业", "老师", "家长会"],
        "patterns": [r"高三", r"高一", r"高二"],
    },
    "悬疑推理": {
        "high": ["悬疑", "推理", "案件", "侦探", "凶手", "嫌疑", "警察",
                "证据", "案发现场", "死亡", "凶杀", "密室"],
        "medium": ["线索", "调查", "审讯", "嫌疑人", "证人"],
        "patterns": [r"死者", r"凶手"],
    },
    "战争军事": {
        "high": ["战争", "军事", "抗战", "解放战争", "抗美援朝", "士兵",
                "战场", "战壕", "冲锋", "牺牲", "战旗", "军装"],
        "medium": ["部队", "连长", "营长", "团长", "将军"],
        "patterns": [r"八路军", r"解放军", r"志愿军"],
    },
    "家庭伦理": {
        "high": ["家庭", "父亲", "母亲", "儿子", "女儿", "爷爷", "奶奶",
                "养老", "遗产", "传承", "代沟", "婆媳"],
        "medium": ["老公", "老婆", "结婚", "孩子", "家庭聚会"],
        "patterns": [r"全家", r"家人"],
    },
}


def count_keyword_matches(text, keywords):
    """计算关键词匹配数"""
    count = 0
    for kw in keywords:
        if kw in text:
            count += 1
    return count


def count_pattern_matches(text, patterns):
    """计算正则模式匹配数"""
    count = 0
    for p in patterns:
        if re.search(p, text):
            count += 1
    return count


def detect_style(text):
    """
    检测剧本风格

    Args:
        text: 剧本文本

    Returns:
        (style, score_dict)
    """
    scores = {}
    for style, config in STYLE_KEYWORDS.items():
        high_count = count_keyword_matches(text, config["high"])
        medium_count = count_keyword_matches(text, config["medium"])
        pattern_count = count_pattern_matches(text, config.get("patterns", []))

        # 高权重词 * 3 + 中权重词 * 1 + 模式 * 2
        score = high_count * 3 + medium_count * 1 + pattern_count * 2
        scores[style] = score

    # 排序
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # 如果最高分太低，返回默认风格
    if sorted_scores[0][1] < 3:
        return "古早霸总", scores  # 默认风格

    return sorted_scores[0][0], scores


def read_script(path):
    """读取剧本文件"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def main():
    if len(sys.argv) < 2:
        print("用法: python detect_style.py <剧本文件>")
        print("      python detect_style.py <剧本文件> --json")
        sys.exit(1)

    script_path = Path(sys.argv[1])
    if not script_path.exists():
        print(f"错误: 文件不存在: {script_path}")
        sys.exit(1)

    text = read_script(script_path)
    style, scores = detect_style(text)

    # 输出格式
    if "--json" in sys.argv:
        result = {
            "detected_style": style,
            "scores": scores,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"检测到的风格: {style}")
        print(f"\n各风格得分:")
        for s, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            bar = "█" * min(score, 50)
            print(f"  {s:8s} | {score:3d} | {bar}")


if __name__ == "__main__":
    main()

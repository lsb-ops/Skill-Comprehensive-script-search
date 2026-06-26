#!/usr/bin/env python3
"""
WebPPT Maker · 主题-布局选择器 (v3.4)

设计目的:
  v3.3 之前: apply_variance 用 9 种 layout 硬循环,不分类
  v3.4: 根据 topic 关键词 + content points 分类到 5 种内容主题,
        每种主题有 preferred_layouts 序列,变体由 variance 决定

5 种内容主题:
  - tutorial:  教程/AI/技术/方法 → qa, timeline, compare, numbers, card
  - listicle:  列表/真相/排行      → numbers, icon, card, poster, card
  - story:     故事/情感/经历      → storyline, poster, card, icon, waterfall
  - product:   产品/工具/平台      → poster, compare, numbers, card, qa
  - general:   兜底                → card, icon, numbers, timeline, qa

Why: 不同主题用同一套 layout 序列是"工具感"而非"作品感",
     主题适配是 reveal.js 模板走向专业级的关键。
"""

import re
from typing import List, Dict, Any


# ============================================================
# 5 种内容主题 + 关键词 + 推荐布局
# 注意: preferred_layouts 必须用中文名,匹配 LAYOUT_RENDERERS 的 key
# ============================================================
TOPIC_LAYOUT_THEMES: Dict[str, Dict[str, Any]] = {
    "tutorial": {
        "name_zh": "教程型",
        "name_en": "Tutorial / How-to",
        "keywords": [
            "教程", "教学", "学习", "方法", "步骤", "如何", "怎么", "怎样",
            "指南", "入门", "上手", "攻略", "tutorial", "how to", "guide",
            "ai", "代码", "编程", "工具", "软件", "python", "javascript",
            "react", "vue", "docker", "git", "api",
        ],
        "preferred_layouts": ["问答", "时间轴", "F模式", "对比", "数字", "卡片"],
        "motion": "fragment-fade-up",
        "rationale": "解释/步骤型内容需要时间线+对比+问答+F模式阅读流",
    },
    "listicle": {
        "name_zh": "列表型",
        "name_en": "Listicle / Ranking",
        "keywords": [
            "真相", "秘密", "盘点", "排行", "排名", "top", "必看",
            "个", "种", "招", "大", "层", "件", "条",
        ],
        "preferred_layouts": ["数字", "图标", "黄金", "大字报", "卡片", "焦点"],
        "motion": "fragment-zoom-in",
        "rationale": "数字+图标+卡片是列表黄金组合,zoom-in 强化节奏",
    },
    "story": {
        "name_zh": "故事型",
        "name_en": "Story / Narrative",
        "keywords": [
            "故事", "经历", "我", "我们", "人生", "感受", "情感", "回忆",
            "那年", "曾经", "后来", "那天", "小时候", "大学", "工作",
        ],
        "preferred_layouts": ["故事线", "大字报", "焦点", "Z模式", "卡片", "瀑布"],
        "motion": "fragment-slide-left",
        "rationale": "故事需要叙事节奏+情感大字+焦点锚+Z模式 hero",
    },
    "product": {
        "name_zh": "产品型",
        "name_en": "Product / Tool",
        "keywords": [
            "产品", "工具", "app", "软件", "平台", "推荐", "评测", "对比",
            "功能", "特性", "优势", "亮点", "新发布", "更新",
        ],
        "preferred_layouts": ["大字报", "对比", "焦点", "数字", "黄金", "卡片", "问答"],
        "motion": "fragment-bounce",
        "rationale": "产品需要大字+对比+量化价值,bounce 强化冲击力",
    },
    "general": {
        "name_zh": "通用型",
        "name_en": "General",
        "keywords": [],
        "preferred_layouts": ["卡片", "图标", "数字", "F模式", "时间轴", "黄金", "问答", "Z模式", "封面流"],
        "motion": "fragment-fade-up",
        "rationale": "兜底,中庸搭配 + 4 个新 attention layout + 封面流 (v3.8)",
    },
}


def _get_title(p: Any) -> str:
    """从 point 提取标题文本"""
    if isinstance(p, dict):
        return p.get("title", "")
    return str(p) if p else ""


def classify_topic(topic: str, points: List[Any]) -> str:
    """根据 topic + points 关键词分类到 5 种主题之一

    Args:
        topic: 视频主题字符串
        points: 内容要点 list (str 或 dict)

    Returns:
        str: 主题 ID ("tutorial" / "listicle" / "story" / "product" / "general")
    """
    text = (topic or "") + " " + " ".join(_get_title(p) for p in (points or []))
    text_lower = text.lower()

    # 计算每个非 general 主题的命中分
    scores = {}
    for theme, cfg in TOPIC_LAYOUT_THEMES.items():
        if theme == "general":
            continue
        score = 0
        for kw in cfg["keywords"]:
            kw_lower = kw.lower()
            if not kw_lower:
                continue
            count = text_lower.count(kw_lower)
            if count > 0:
                # 长关键词权重高(>3 字)
                weight = 2 if len(kw) >= 3 else 1
                score += count * weight
        scores[theme] = score

    if not scores or max(scores.values()) == 0:
        return "general"

    # v3.4.1: 处理平局 — product 专用 tie-breaker
    # 现象: "Notion 5 大新功能" 中 "ai" + "功能" 命中 tutorial/product 各 2 分平局
    # 解法: product 的"评测/新功能/亮点/推荐"等明确产品词命中时 +1 tie-breaker
    product_strong_keywords = ["评测", "新功能", "亮点", "推荐", "对比", "app"]
    for kw in product_strong_keywords:
        if kw in text_lower:
            scores["product"] = scores.get("product", 0) + 1
            break

    return max(scores, key=scores.get)


def select_layouts(topic: str, points: List[Any], variance: int,
                    mode: str = "portrait") -> List[str]:
    """根据 topic 主题 + variance 选 layout 序列

    Args:
        topic: 视频主题
        points: 内容要点
        variance: 1-10 (1=单 layout 重复, 5=主题前 5, 9+=完整 9)
        mode: portrait/landscape (目前不影响选择,保留扩展位)

    Returns:
        list of layout 名: ["qa", "timeline", "compare", ...]
    """
    if variance < 1 or variance > 10:
        raise ValueError(f"variance={variance} 必须在 1-10 之间")

    theme = classify_topic(topic, points)
    preferred = list(TOPIC_LAYOUT_THEMES[theme]["preferred_layouts"])

    # variance=1: 只用主题首选 layout
    if variance == 1:
        return [preferred[0]]

    # variance=2-8: 主题前 N 个 (N=min(variance, len(preferred)))
    n_preferred = min(variance, len(preferred))
    layouts = list(preferred[:n_preferred])

    # variance >= 9: 补齐 9 种 (从其他主题借,但保 preferred 在前)
    if variance >= 9:
        all_others = []
        for t, cfg in TOPIC_LAYOUT_THEMES.items():
            if t != "general":
                for l in cfg["preferred_layouts"]:
                    if l not in layouts and l not in all_others:
                        all_others.append(l)
        # 补足 9 种 (期望 9 layouts, 因 preferred 可能不足 9)
        layouts = layouts + all_others[: max(0, 9 - len(layouts))]

    return layouts


def get_theme_motion(theme: str) -> str:
    """返回主题推荐的 fragment_class"""
    return TOPIC_LAYOUT_THEMES.get(theme, TOPIC_LAYOUT_THEMES["general"])["motion"]


def get_theme_info(theme: str) -> Dict[str, Any]:
    """返回主题完整配置 (供调试/UI 用)"""
    return TOPIC_LAYOUT_THEMES.get(theme, TOPIC_LAYOUT_THEMES["general"])


# ============================================================
# Self-test
# ============================================================
if __name__ == "__main__":
    test_cases = [
        ("AI 写作 5 步教程", ["选择模型", "写 prompt", "迭代"], "tutorial"),
        ("咖啡的 3 个真相", ["脱水", "酸性", "烘焙"], "listicle"),
        ("那年我去西藏的故事", ["出发", "路上", "到达"], "story"),
        ("Notion 5 大新功能", ["AI", "协作", "数据库"], "product"),
        ("通用主题", ["a", "b", "c"], "general"),
    ]
    for topic, points, expected in test_cases:
        got = classify_topic(topic, points)
        status = "✅" if got == expected else "❌"
        print(f"  {status} classify({topic!r}) = {got} (expected {expected})")

    print()
    print("--- select_layouts (variance=5) ---")
    for topic, points, _ in test_cases:
        layouts = select_layouts(topic, points, 5)
        print(f"  {topic:20s} → {layouts}")

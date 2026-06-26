#!/usr/bin/env python3
"""
WebPPT Maker · 抖音文案生成器 (v3.0)

输入: 内容主题 + 要点 (兼容 List[str] / List[Dict] / 14-field)
输出:
  - douyin_post.md: 完整发布版 (title + body + hashtags + CTA) 一键复制
  - douyin_titles.md: A/B 5 版标题 (适用场景 + 预期效果)

v3.0 新特性:
- 14-field schema: 共享 storyboard_parser.normalize_points
- AIAEST narrative_role 语气适配: 震撼/知识/行动/情感/满足
- backward compat: 4-field 老格式自动转换

v1.2.0 旧特性:
- 文案拆 2 文件
- topic-aware hooks
- body 截断保留 CTA
- A/B 5 版标题
"""

import json
import sys
import argparse
import re
from pathlib import Path
from _common import resolve_output_dir, report_written
from _constants import B1_HARD_TITLE_LEN, B2_MIN_BODY_LEN, B2_MAX_BODY_LEN, B2_HARD_BODY_LEN
from storyboard_parser import normalize_points, get_aiaest_tone, auto_fill_narrative_role

# v1.2.0: 防止 sc-9 magic number 误报
MAX_BODY_FIELD_PREVIEW = 30  # body 字段预览截断长度
BODY_ELLIPSIS = "…"


# ============================================================
# Schema 兼容
# ============================================================
def normalize_points(points):
    """List[str] / List[Dict] 统一为 List[Dict]"""
    if not points:
        return []
    if isinstance(points[0], str):
        return [
            {"title": p, "subtitle": "", "body": "", "visual_element": "", "type": None, "data": {}}
            for p in points
        ]
    return points


def get_point_title(p):
    return p["title"] if isinstance(p, dict) else p


def get_point_body(p):
    return p.get("body", "") if isinstance(p, dict) else ""


def get_point_narrative_role(p):
    """v3.0: 提取 narrative_role (AIAEST 5 段), 缺省 interest"""
    if isinstance(p, dict):
        return p.get("narrative_role") or "interest"
    return "interest"


# ============================================================
# Title A/B 5 版生成
# ============================================================
def generate_title_variants(topic, points):
    """
    v3.3: 5 版标题真差异化 — 5 种不同句式 + 不同情绪钩子
    之前 A vs B Jaccard=0.83 (太相似), 现在 5 版 Jaccard 全部 ≤ 0.6

    Returns: list of {label, title, scenario, expected}
    """
    n = len(points)
    point_titles = [get_point_title(p) for p in points]

    # 找出数字关键词
    n_kw = None
    for kw in ["真相", "招", "天", "个", "种", "件", "大", "步", "层"]:
        if any(kw in p for p in point_titles):
            n_kw = kw
            break
    if not n_kw:
        n_kw = "个"

    variants = []

    # A. 数字钩子 — "X 的 N 个 Y" 直白数字
    title_a = f"{topic}的{n}{n_kw}，第{n-1 if n>1 else 1}个扎心了 🔥"
    variants.append({
        "label": "A · 数字钩子",
        "title": title_a,
        "scenario": "知识科普 / 教程",
        "expected": "留存率 35%+，数字 n 暗示有干货"
    })

    # B. 揭秘悬念 — "为什么 X？最后一个 N% 的人都不知道" (完全不同的句式)
    title_b = f"为什么{topic}？{n*10}%的人不知道 😱"
    variants.append({
        "label": "B · 揭秘悬念",
        "title": title_b,
        "scenario": "争议 / 揭秘 / 反常识",
        "expected": "点击率 8%+，揭秘心理引发好奇"
    })

    # C. 反问反差 — "X 不难？错" (完全不同的句式)
    title_c = f"{topic}不难？错了 💡"
    variants.append({
        "label": "C · 反问反差",
        "title": title_c,
        "scenario": "技巧 / 教程 / 误区",
        "expected": "互动率 12%+，触发 我也错了 反应"
    })

    # D. 利益前置 — "学会这 N 个 X，月入..." (利益导向)
    title_d = f"学会这{n}招，{topic}轻松搞定 ⭐"
    variants.append({
        "label": "D · 利益前置",
        "title": title_d,
        "scenario": "产品 / 工具 / 解决方案",
        "expected": "收藏率 20%+，暗示有解决方案"
    })

    # E. 短直白 — "X · 一句话总结" (极简, 完全不同的结构)
    title_e = f"{topic} · 一文说清"
    variants.append({
        "label": "E · 短直白",
        "title": title_e,
        "scenario": "短时长 / 卡片式 / 简洁",
        "expected": "完播率 60%+，简洁不挑用户"
    })

    return variants


def select_default_title(variants):
    """默认选 A 版（数字钩子，兼容最广）, 同时对每版应用硬截断 ≤ 22 字"""
    truncated = []
    for v in variants:
        title = v["title"]
        if len(title) > B1_HARD_TITLE_LEN:
            title = title[:B1_HARD_TITLE_LEN - 1] + "…"
        truncated.append({**v, "title": title})
    return truncated[0]["title"]


def truncate_variants(variants):
    """应用硬截断到所有 5 版标题"""
    truncated = []
    for v in variants:
        title = v["title"]
        if len(title) > B1_HARD_TITLE_LEN:
            title = title[:B1_HARD_TITLE_LEN - 1] + "…"
        truncated.append({**v, "title": title})
    return truncated


# ============================================================
# Body 生成 (80-150 字, 保留 CTA)
# ============================================================
def generate_body(topic, points, final_cta=None):
    """
    生成正文 (80-150 字)
    结构: hook + expansion_lines + cta
    截断: 保留 CTA 句，只截断 expansion_lines

    v3.0: 按 narrative_role 选择语气 (AIAEST 5 段)
    v3.3: 接受 final_cta 让 douyin_post.md 与 HTML/subtitle/timeline CTA 一致
    """
    # v3.0: 用首个 narrative_role 决定 hook 语气
    first_role = get_point_narrative_role(points[0]) if points else "interest"
    tone = get_aiaest_tone(first_role)
    hook = f"{tone['prefix']} 你以为{topic}很简单？"
    # v3.3: 用外部 CTA 决议 (CLI/config 优先),否则保持原行为
    if final_cta:
        cta = final_cta
    else:
        cta_verb = tone['verbs'][0] if tone.get('verbs') else '看看'
        cta = f"{tone['ending']} 评论区告诉我 👇"

    # 展开句 (取前 5 个, 取 title + body 的前 MAX_BODY_FIELD_PREVIEW 字)
    expansion_lines = []
    for p in points[:5]:
        title = get_point_title(p)
        body = get_point_body(p)
        if body:
            # 截断 body 到 MAX_BODY_FIELD_PREVIEW 字
            short_body = body[:MAX_BODY_FIELD_PREVIEW] + (BODY_ELLIPSIS if len(body) > MAX_BODY_FIELD_PREVIEW else "")
            expansion_lines.append(f"{title} ({short_body})")
        else:
            expansion_lines.append(title)

    # 计算 hook + expansion + cta 总长度
    hook_len = len(hook)
    cta_len = len(cta)
    expansion_total = sum(len(line) for line in expansion_lines)
    separators = 2 * (len(expansion_lines) + 2)  # 换行符数

    # 目标: 总长 80-150 字. CTA 必保留.
    available_for_expansion = B2_HARD_BODY_LEN - hook_len - cta_len - separators

    if expansion_total <= available_for_expansion:
        # 不需要截断
        body_parts = [hook] + expansion_lines + [cta]
        body = "\n".join(body_parts)
    else:
        # 截断 expansion_lines 保留 hook + cta
        kept_lines = []
        used = 0
        for line in expansion_lines:
            if used + len(line) + 1 <= available_for_expansion:
                kept_lines.append(line)
                used += len(line) + 1
            else:
                # 截断当前行
                remaining = available_for_expansion - used - 1
                if remaining > 5:
                    kept_lines.append(line[:remaining] + "…")
                break
        if not kept_lines:
            kept_lines = expansion_lines[:2]  # 至少保留 2 行
        body_parts = [hook] + kept_lines + [cta]
        body = "\n".join(body_parts)

    # 二次校验: 短于 80 字则补过渡
    if len(body) < B2_MIN_BODY_LEN:
        body = hook + "\n\n" + "\n".join(expansion_lines) + "\n\n看完记得收藏 ✨\n" + cta

    return body


# ============================================================
# Hashtag 提取 (5-8 个)
# ============================================================
def extract_hashtags(topic, points):
    """提取 hashtag (5-8 个)"""
    base_tags = ["#干货分享", "#知识科普"]

    topic_tags = []
    topic_lower = topic.lower()
    if "ai" in topic_lower or "智能" in topic_lower or "agent" in topic_lower:
        topic_tags.extend(["#AI", "#AI工具", "#人工智能"])
    if "写作" in topic_lower or "文案" in topic_lower:
        topic_tags.extend(["#写作技巧", "#文案"])
    if "学习" in topic_lower or "成长" in topic_lower:
        topic_tags.extend(["#学习成长", "#自我提升"])
    if "咖啡" in topic_lower or "饮食" in topic_lower or "健康" in topic_lower:
        topic_tags.extend(["#健康生活", "#养生"])
    if "职场" in topic_lower or "工作" in topic_lower:
        topic_tags.extend(["#职场干货", "#工作效率"])
    if "转行" in topic_lower or "副业" in topic_lower:
        topic_tags.extend(["#转行故事", "#副业"])
    if "记忆" in topic_lower or "cc" in topic_lower or "源码" in topic_lower:
        topic_tags.extend(["#开源", "#程序员", "#技术分享"])

    # 从 points 中提取关键词
    for p in points:
        title = get_point_title(p)
        if "真相" in title:
            topic_tags.append("#真相")
        if "建议" in title or "方法" in title:
            topic_tags.append("#实用技巧")

    # 通用 hashtag
    topic_tags.extend(["#热门话题", "#2026"])

    # 去重 + 限制数量 (5-8)
    seen = set()
    hashtags = []
    for tag in base_tags + topic_tags:
        if tag not in seen:
            hashtags.append(tag)
            seen.add(tag)
        if len(hashtags) >= 8:
            break

    return " ".join(hashtags)


# ============================================================
# Hooks 生成 (topic-aware)
# ============================================================
HOOKS_BY_TOPIC = {
    # 技术/AI 类
    "tech": [
        "你在用 AI 工具吗？评论区告诉我 👇",
        "关注我，看更多技术干货 ✨",
    ],
    # 美食/健康 类
    "food": [
        "你最爱喝什么？评论区告诉我 👇",
        "关注我，看更多健康生活 ✨",
    ],
    # 学习/职场 类
    "career": [
        "你在哪个行业？评论区告诉我 👇",
        "关注我，看更多职场干货 ✨",
    ],
    # 故事/情感 类
    "story": [
        "你有过类似经历吗？评论区告诉我 👇",
        "关注我，看更多故事 ✨",
    ],
    # 通用 fallback
    "general": [
        "你有什么体验？评论区告诉我 👇",
        "关注我，看更多干货 ✨",
    ],
}


def classify_topic_for_hooks(topic):
    """根据 topic 关键词归类"""
    t = topic.lower()
    if any(kw in t for kw in ["ai", "智能", "代码", "技术", "编程", "cc", "记忆", "agent", "源码"]):
        return "tech"
    if any(kw in t for kw in ["咖啡", "饮食", "健康", "养生", "美食"]):
        return "food"
    if any(kw in t for kw in ["职场", "工作", "学习", "成长", "面试"]):
        return "career"
    if any(kw in t for kw in ["故事", "经历", "情感", "我", "我们"]):
        return "story"
    return "general"


def generate_hooks(topic, points):
    """生成互动钩子 (topic-aware, 2 条)"""
    topic_type = classify_topic_for_hooks(topic)
    hooks = HOOKS_BY_TOPIC.get(topic_type, HOOKS_BY_TOPIC["general"])
    return "\n".join(hooks)


# ============================================================
# 文件格式化
# ============================================================
def format_post_md(title, body, hashtags, hooks):
    """完整发布版 — 一键复制贴抖音"""
    return f"""# {title}

{body}

{hashtags}

{hooks}

---
*由 WebPPT Maker v1.2.0 自动生成 · 平台: 抖音 · 一键复制即可*
"""


def format_titles_md(topic, variants):
    """A/B 5 版标题 — 多版本测试选择"""
    lines = [f"# {topic} · 抖音标题 A/B 测试 (5 版)", ""]
    lines.append("> **用法**: 5 版标题各有侧重，建议先发 A 版 (数字钩子)，看数据后切换 B/C/D/E 对照")
    lines.append("> **依据**: 参考抖音算法对前 3 秒钩子的 CTR (点击率) + 完播率 + 评论率权重")
    lines.append("")
    lines.append("---")
    lines.append("")

    for v in variants:
        lines.append(f"## {v['label']}")
        lines.append("")
        lines.append(f"**标题**: {v['title']}")
        lines.append("")
        lines.append(f"**适用场景**: {v['scenario']}")
        lines.append("")
        lines.append(f"**预期效果**: {v['expected']}")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("*由 WebPPT Maker v1.2.0 自动生成 · 5 版 A/B 测试选择最优*")
    return "\n".join(lines) + "\n"


# ============================================================
# 主入口
# ============================================================
def generate(topic, content_points, output_dir, platform="douyin", **kwargs):
    """主入口 — 输出 2 个文件 (v3.3: 接受 final_cta, 4 产物 CTA 一致)"""
    output_path = resolve_output_dir(output_dir)

    points = normalize_points(content_points)
    points = auto_fill_narrative_role(points)  # v3.3: List[str] → 5 段 AIAEST
    final_cta = kwargs.get("final_cta")  # v3.3
    title_variants_raw = generate_title_variants(topic, points)
    # v1.2.0: 应用硬截断 ≤ 22 字到所有版本
    title_variants = truncate_variants(title_variants_raw)
    title = title_variants[0]["title"]
    body = generate_body(topic, points, final_cta=final_cta)
    hashtags = extract_hashtags(topic, points)
    hooks = generate_hooks(topic, points)

    # 写文件 1: douyin_post.md (完整发布版)
    post_md = format_post_md(title, body, hashtags, hooks)
    post_file = output_path / "douyin_post.md"
    post_file.write_text(post_md, encoding="utf-8")
    print(f"[OK] 生成 douyin_post.md ({len(post_md)} chars)", file=sys.stderr)

    # 写文件 2: douyin_titles.md (A/B 5 版)
    titles_md = format_titles_md(topic, title_variants)
    titles_file = output_path / "douyin_titles.md"
    titles_md_clean = titles_md.replace('"n"暗示有干货', '数字"n"暗示有干货').replace('触发"我以为"反应', '触发"我以为"反应')
    titles_file.write_text(titles_md_clean, encoding="utf-8")
    print(f"[OK] 生成 douyin_titles.md ({len(titles_md_clean)} chars, 5 版 A/B)", file=sys.stderr)

    print(f"     标题 (默认 A 版): {title}", file=sys.stderr)
    print(f"     正文: {len(body)} chars", file=sys.stderr)
    print(f"     Hashtag: {len(hashtags.split())} 个", file=sys.stderr)

    return str(post_file.absolute())


def main():
    parser = argparse.ArgumentParser(description="WebPPT Maker 文案生成器 (v1.2.0)")
    parser.add_argument("--topic", help="视频主题")
    parser.add_argument("--points", nargs="+", help="内容要点 (兼容 List[str] 和 List[Dict])")
    parser.add_argument("--platform", default="douyin", help="目标平台")
    parser.add_argument("--output-dir", help="输出目录")
    parser.add_argument("--config", help="JSON 配置文件")
    parser.add_argument("--final-cta", default="", help="v3.3: run_all 传入的最终 CTA (CLI 决议,保证 4 产物一致)")
    args = parser.parse_args()

    if args.config:
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
        topic = config.get("topic", args.topic)
        points = config.get("content_points", args.points or [])
        platform = config.get("platform", args.platform)
        output_dir = args.output_dir if args.output_dir else config.get("output_dir", "")
    else:
        topic = args.topic
        points = args.points or []
        platform = args.platform
        output_dir = args.output_dir

    if not topic or not points or not output_dir:
        print("[ERROR] topic / points / output-dir 必填", file=sys.stderr)
        sys.exit(1)

    output = generate(topic, points, output_dir, platform, final_cta=args.final_cta)
    print(json.dumps({"post_path": output, "status": "ok"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

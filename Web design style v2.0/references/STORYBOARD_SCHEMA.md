# Storyboard Schema (14-field content_point) · v3.0

> **v3.0 新增**: 借鉴 storyboard-decomposition M2 分镜设计 + storyboard-completion-analysis 8/5/7/6/8 元数据
>
> **向后兼容**: 4-field 老 schema 自动升级到 14-field

## 为什么 14 字段

v1.x 4-field schema (title / subtitle / body / visual_element) 只能描述「内容」，
无法驱动「镜头语言」「叙事节奏」「动画强度」。

v3.0 14-field schema 把 4 个 generator 串成一条 pipeline:

```
content.json (14-field)
  ├→ generate_html.py:    type / fragment_class / visual_element → 渲染
  ├→ generate_copy.py:    narrative_role → AIAEST 语气
  ├→ generate_script.py:  shot_type / angle / movement → 镜头描述
  └→ generate_subtitle.py: atmosphere → 字幕标点
```

## 14 字段完整定义

| # | 字段 | 类型 | 必填 | 缺省 | 说明 |
|---|------|------|------|------|------|
| 1 | `id` | str | 自动 | `p01`/`p02`/... | 要点编号 |
| 2 | `title` | str | ✅ | — | 要点标题 |
| 3 | `subtitle` | str | ❌ | `""` | 副标题 |
| 4 | `body` | str | ❌ | `""` | 详细说明 |
| 5 | `visual_element` | str | ❌ | `""` | emoji 或 `xxx.svg` |
| 6 | `type` | enum | ❌ | auto | 9 种 layout: 卡片/大字报/时间轴/数字/对比/图标/故事线/问答/瀑布 |
| 7 | `shot_type` | enum | ❌ | `null` | 8 选 1: 特写/中景/全景/远景/俯拍/航拍/微距/鱼眼 |
| 8 | `angle` | enum | ❌ | `null` | 5 选 1: 正面/侧面/背面/俯视/仰视 |
| 9 | `movement` | enum | ❌ | `null` | 7 选 1: 静止/推近/拉远/横移/跟随/环绕/升降 |
| 10 | `lighting` | enum | ❌ | `null` | 6 选 1: 高调/低调/侧光/逆光/柔光/硬光 |
| 11 | `atmosphere` | enum | ❌ | `null` | 8 选 1: 紧迫/温暖/悬疑/活泼/庄严/忧郁/振奋/平静 |
| 12 | `narrative_role` | enum | ❌ | auto | AIAEST 5 段: attention/interest/action/emotion/satisfaction |
| 13 | `data` | dict | ❌ | `{}` | 数字 metric/unit, 对比 before/after |
| 14 | `fragment_class` | enum | ❌ | `fragment-fade-up` | reveal.js: fade-up/slide-left/slide-right/zoom-in/bounce |

## AIAEST 5 段叙事流

借鉴 `corporate-film-generator` 的 Attention→Interest→Action→Emotion→Satisfaction:

| 段 | 含义 | 配色温度 | layout | tone prefix | ending |
|----|------|----------|--------|-------------|--------|
| **A**ttention | 抓眼球 | 暖色高饱和 | 大字报 | 🔥 震撼型 | 你准备好了吗？ |
| **I**nterest | 引起兴趣 | 暖色 → 中性 | 卡片 | 💡 知识型 | 原来如此！ |
| **A**ction | 推动行为 | 中性 | 数字 | ⭐ 行动型 | 现在就去做！ |
| **E**motion | 触发情绪 | 冷色 → 暖色 | 故事线 | 💖 情感型 | 你有没有同感？ |
| **S**atisfaction | 满足感 | 暖色低饱和 | 问答 | ✨ 满足型 | 评论区告诉我吧！ |

**auto mode**: 缺省按索引自动分配 (`p01`→attention, `p02`→interest, `p03`→action, `p04`→emotion, `p05`→satisfaction, 5 段循环)

## 镜头语言 (8/5/7/6/8)

### shot_type (8 选 1)

| 值 | 英文 | 用途 |
|----|------|------|
| 特写 | CU (Close-Up) | 强调情绪、细节、表情 |
| 中景 | MS (Medium Shot) | 人物互动、产品演示 |
| 全景 | WS (Wide Shot) | 场景全貌、空间关系 |
| 远景 | ELS (Extreme Long Shot) | 环境氛围、宏大叙事 |
| 俯拍 | Top-Down | 流程、布局、操作步骤 |
| 航拍 | Aerial | 城市、地形、大场景 |
| 微距 | Macro | 食物、材质、纹理 |
| 鱼眼 | Fisheye | 创意效果、夸张情绪 |

### angle (5 选 1)

| 值 | 英文 | 用途 |
|----|------|------|
| 正面 | Front | 庄重、直接、客观 |
| 侧面 | Side | 运动感、轮廓、对比 |
| 背面 | Back | 神秘、跟随、视角代入 |
| 俯视 | High-Angle | 弱势、渺小、客观观察 |
| 仰视 | Low-Angle | 强势、英雄、敬畏 |

### movement (7 选 1)

| 值 | 英文 | 用途 |
|----|------|------|
| 静止 | Static | 对话、强调、停顿 |
| 推近 | Push-In | 聚焦、强调、情绪递进 |
| 拉远 | Pull-Out | 揭示环境、关系变化 |
| 横移 | Pan | 跟随、平行运动 |
| 跟随 | Follow | 追踪、动感 |
| 环绕 | Orbit | 360°展示、戏剧性 |
| 升降 | Crane | 大场景、仪式感 |

### lighting (6 选 1)

| 值 | 含义 | 情绪 |
|----|------|------|
| 高调 | 明亮、均匀 | 轻松、积极、科普 |
| 低调 | 暗调、高对比 | 戏剧、悬疑、严肃 |
| 侧光 | 一侧光照 | 立体感、轮廓 |
| 逆光 | 背景光 | 剪影、艺术、神秘 |
| 柔光 | 漫射、无影 | 唯美、温柔、亲切 |
| 硬光 | 强光、清晰影 | 力量、紧迫、警示 |

### atmosphere (8 选 1) → 字幕标点

| 值 | 标点 | 语气词 |
|----|------|--------|
| 紧迫 | ！ | 赶紧/立即/马上 |
| 温暖 | ~ | 慢慢/温暖/温柔 |
| 悬疑 | ？ | 为什么/怎么/什么 |
| 活泼 | ！ | 哈哈/耶/太棒了 |
| 庄严 | 。 | 确实/本质上/事实上 |
| 忧郁 | … | 可惜/遗憾/唉 |
| 振奋 | ！ | 冲/加油/必胜 |
| 平静 | 。 | 缓缓/静静/平和 |

## fragment_class (reveal.js 动画)

| 类 | 效果 |
|----|------|
| `fragment-fade-up` | 淡入 + 上移 30px (default) |
| `fragment-slide-left` | 从左滑入 |
| `fragment-slide-right` | 从右滑入 |
| `fragment-zoom-in` | 缩放 0.5→1 |
| `fragment-bounce` | 弹性进入 (cubic-bezier) |

## v1.x → v3.0 迁移示例

### v1.x 4-field (老)

```json
{
  "content_points": [
    {"title": "咖啡不脱水", "body": "2021 研究显示", "type": "大字报"}
  ]
}
```

### v3.0 14-field (新)

```json
{
  "content_points": [
    {
      "id": "p01",
      "title": "咖啡不脱水",
      "subtitle": "新研究颠覆 50 年认知",
      "body": "2021 年《营养学杂志》meta 分析显示...",
      "visual_element": "💡",
      "type": "大字报",
      "shot_type": "特写",
      "angle": "正面",
      "movement": "推近",
      "lighting": "高调",
      "atmosphere": "紧迫",
      "narrative_role": "attention",
      "data": {},
      "fragment_class": "fragment-bounce"
    }
  ]
}
```

**自动升级规则** (storyboard_parser.normalize_points):
- `id` 缺省 → 按索引 `p01`/`p02`/...
- `fragment_class` 缺省 → `fragment-fade-up`
- `narrative_role` 缺省 → 按 AIAEST 5 段循环自动分配
- `shot_type` / `angle` / `movement` / `lighting` / `atmosphere` 缺省 → `null` (脚本里显示 `—`)

## 校验

```bash
# 校验 14-field schema
python3 scripts/storyboard_parser.py --validate tests/dual_v3_test.json
# → [OK] schema 校验通过 (3 个要点)

# auto-fill narrative_role
python3 scripts/storyboard_parser.py --auto-aiaest --validate tests/dual_v3_test.json
# → 输出补全后的 JSON 到 stdout
```

`validate_point(point, strict=False)`:
- `False` (default): 只校验已填字段是否在合法集合
- `True`: 强制 `narrative_role` 必填 (AIAEST 严格模式)

## 借鉴出处

| 概念 | 来源 |
|------|------|
| 14-field schema 框架 | `storyboard-decomposition/M2_分镜设计.md:55-84` |
| 8 shot types + 5 angles + 7 movements | `storyboard-completion-analysis/SKILL.md:55-186` |
| AIAEST 5 段叙事 | `corporate-film-generator/SKILL.md:131-140` |
| reveal.js fragment 动画 | `reveal.js 5.1.0 官方文档` |
| backward compat 设计 | `taste-skill anti-slop L97-126` (向后兼容优先) |

# AIAEST 5 段叙事流 (v3.0)

> **借鉴**: corporate-film-generator/SKILL.md:131-140
> **目的**: 强制每页有 narrative_role, 让生成内容有节奏感

## 5 段叙事

```
  Attention           Interest             Action              Emotion             Satisfaction
  抓眼球 0-3s         引起兴趣 3-15s       推动行为 15-25s     触发情绪 25-35s     满足感 35-45s
  ┌──────────┐        ┌──────────┐         ┌──────────┐       ┌──────────┐        ┌──────────┐
  │  暖色高饱和        │  暖色 → 中性        │  中性     │       │  冷色 → 暖色       │  暖色低饱和  │
  │  大字报/封面       │  卡片/图标           │  数字/对比  │       │  故事线/问答       │  CTA       │
  └──────────┘        └──────────┘         └──────────┘       └──────────┘        └──────────┘
       ▲                   ▲                    ▲                   ▲                    ▲
   hook          知识扩展                数据支撑               共鸣                转化
```

## 5 段详解

### A · Attention (抓眼球)

| 维度 | 值 |
|------|-----|
| 时长 | 0-3 秒 (hook) |
| 配色 | 暖色高饱和 (#FF3B30 红 / #FF9500 橙) |
| layout | 大字报 |
| 文案 tone | 🔥 震撼型 |
| verbs | 揭秘 / 曝光 / 颠覆 / 真相 |
| ending | "你准备好了吗？" |
| 镜头 | 特写 + 推近 + 高调光 |
| atmosphere | 紧迫 |
| 字幕标点 | ！ |

**示例**: "🔥 你以为每天喝咖啡的 3 个真相很简单？"

### I · Interest (引起兴趣)

| 维度 | 值 |
|------|-----|
| 时长 | 3-15 秒 (3-4 个要点) |
| 配色 | 暖色 → 中性 (过渡) |
| layout | 卡片 / 图标 |
| 文案 tone | 💡 知识型 |
| verbs | 解析 / 拆解 / 解读 / 分析 |
| ending | "原来如此！" |
| 镜头 | 中景 + 侧面 / 横移 |
| atmosphere | 温暖 / 活泼 |
| 字幕标点 | ~ / ！ |

**示例**: "💡 真相 2：早上 9-11 点喝效果最好~"

### A · Action (推动行为)

| 维度 | 值 |
|------|-----|
| 时长 | 15-25 秒 (2-3 个要点) |
| 配色 | 中性 (蓝/灰) |
| layout | 数字 / 对比 |
| 文案 tone | ⭐ 行动型 |
| verbs | 试试 / 立即 / 马上 / 现在 |
| ending | "现在就去做！" |
| 镜头 | 全景 + 俯视 + 拉远 |
| atmosphere | 悬疑 / 庄严 |
| 字幕标点 | ？ / 。 |

**示例**: "⭐ 真相 3：超过 4 杯就会反向脱水？"

### E · Emotion (触发情绪)

| 维度 | 值 |
|------|-----|
| 时长 | 25-35 秒 (1-2 个故事) |
| 配色 | 冷色 → 暖色 (过渡) |
| layout | 故事线 / 问答 |
| 文案 tone | 💖 情感型 |
| verbs | 感受 / 体验 / 回忆 / 共鸣 |
| ending | "你有没有同感？" |
| 镜头 | 中景 + 正面 + 推近 |
| atmosphere | 温暖 / 平静 |
| 字幕标点 | ~ / 。 |

**示例**: "💖 我有次周末头疼到怀疑人生..."

### S · Satisfaction (满足感)

| 维度 | 值 |
|------|-----|
| 时长 | 35-45 秒 (CTA) |
| 配色 | 暖色低饱和 (#FFB800 暖黄) |
| layout | 问答 / 卡片 |
| 文案 tone | ✨ 满足型 |
| verbs | 总结 / 回顾 / 收获 / 升华 |
| ending | "评论区告诉我吧！" |
| 镜头 | 中景 + 正面 + 静止 |
| atmosphere | 平静 |
| 字幕标点 | 。 / ！ |

**示例**: "✨ 评论区告诉我你的体验 👇"

## 配色温度映射 (CSS Variable)

```css
:root {
  /* AIAEST 配色温度 */
  --aiaest-attention:     #FF3B30;  /* 红 (暖色高饱和) */
  --aiaest-interest:      #FF9500;  /* 橙 (暖色中饱和) */
  --aiaest-action:        #1a1a1a;  /* 黑 (中性) */
  --aiaest-emotion:       #5856D6;  /* 紫 (冷色 → 暖色过渡) */
  --aiaest-satisfaction:  #FFB800;  /* 黄 (暖色低饱和) */
}

[data-narrative="attention"]    { --accent: var(--aiaest-attention); }
[data-narrative="interest"]     { --accent: var(--aiaest-interest); }
[data-narrative="action"]       { --accent: var(--aiaest-action); }
[data-narrative="emotion"]      { --accent: var(--aiaest-emotion); }
[data-narrative="satisfaction"] { --accent: var(--aiaest-satisfaction); }
```

## 实施方式

### 方式 A: 显式指定 (推荐)

用户在 `content.json` 给每个点显式 `narrative_role`:

```json
{
  "content_points": [
    {"title": "...", "narrative_role": "attention"},
    {"title": "...", "narrative_role": "interest"},
    {"title": "...", "narrative_role": "action"},
    {"title": "...", "narrative_role": "emotion"},
    {"title": "...", "narrative_role": "satisfaction"}
  ]
}
```

### 方式 B: 自动分配 (auto mode)

`storyboard_parser.auto_fill_narrative_role(points)` 按 5 段循环自动分配:

```python
from storyboard_parser import normalize_points, auto_fill_narrative_role

points = normalize_points([...])  # 14-field
points = auto_fill_narrative_role(points)  # 缺省补全
# p01 → attention, p02 → interest, p03 → action, p04 → emotion, p05 → satisfaction
# p06 → attention (循环), ...
```

## 生成器如何消费 narrative_role

| 生成器 | 消费方式 |
|--------|----------|
| `generate_html.py` | `AIAEST_LAYOUT[role]` → 9 layout 之一 (大字报/卡片/数字/故事线/问答) |
| `generate_copy.py` | `get_aiaest_tone(role)` → prefix/verbs/ending 5 套 |
| `generate_script.py` | 时间线表新增 "叙事" 列 (attention/interest/...) |
| `generate_subtitle.py` | 通过 `atmosphere` 字段间接影响 (不是直接) |

## 借鉴出处

| 概念 | 来源 |
|------|------|
| AIAEST 5 段命名 | `corporate-film-generator/SKILL.md:131-140` |
| narrative_role 字段 | `storyboard-decomposition/M2_分镜设计.md:55-84` |
| 配色温度映射 | `taste-skill/skills/taste-skill-v1/SKILL.md:97-126` (Anti-Slop 推论) |
| 5 段循环算法 | 自创 (避免 6+ 点 5 段覆盖不全) |

# 示例 3 · 故事叙述类 · 30 岁转行 AI 的 90 天

## 这个示例在做什么

> **场景**: 个人叙事 — "我从大厂裸辞的 90 天"，情感共鸣类内容
>
> **关键卖点**: 第 30 天的反转（demo 跑通 + 我哭了）

## 内容参数

| 参数 | 值 | 原因 |
|------|------|------|
| `style` | 故事叙述 | 暗调 + 渐变 = 电影感 |
| `color_scheme` | 暖阳橙 | 温暖 + 励志 |
| `layout` | 时间轴 | 天然适合"X 天 / X 周"叙事 |
| `target_duration_sec` | 60 | 4 个时间点需要展开 |

## 一键运行

```bash
bash scripts/run_all.sh \
  --config examples/example_3_storytelling/content.json \
  --output-dir examples/example_3_storytelling/output
```

跑完后看 `examples/example_3_storytelling/output/`。

## 预期产物

- **6 页 PPT**: 封面 + 4 时间点 + CTA
- **配色**: 暖阳橙（温暖 + 励志）
- **排版**: 时间轴（左时间点 + 右描述）

## 学到的

- 故事叙述类必须有 **"反转/高潮"**，第 30 天的"我哭了"是情绪锚点
- 时间轴排版天然适合"X 天 / X 周"的内容
- 暖阳橙让故事类内容更有"温度"
- 60 秒比 30 秒更合适 — 故事需要呼吸

---
name: webppt-maker
description: "动态网页 PPT 一站式生成器 · 双模式 (9:16 竖屏 + 16:9 横屏) + reveal.js 动画 + taste-skill 3-dial 美学系统. 输入内容主题+要点 → 输出完整可发布视频素材包: HTML 网页 + 抖音文案 + 时间线剧本 + 剪映字幕 + 截图. Use when: 做网页PPT、抖音视频素材、9:16 短视频 PPT、16:9 演示文稿、动态网页 PPT、剪映字幕、抖音文案、视频分镜. 触发词：做网页PPT、做动态PPT、双模式PPT、生成PPT素材、剪映字幕、抖音视频、网页式PPT、动态网页."
version: 3.0.0
license: MIT
metadata:
  execution: full
  skill_type: workflow
  category: content-creation
  subcategory: video-material
  requires_dependencies: false
  optional_dependencies: [browser-use, python3]
  icon: 🎬
---

# WebPPT Maker · 动态网页 PPT (v3.0)

> 一句话: 主题 + 要点 → 9:16 + 16:9 双模式 HTML + 抖音文案 + 剧本 + 字幕 + 截图

## 5 行能力摘要

- **双模式**: 同一份 content.json → 9:16 (抖音/小红书) + 16:9 (桌面/分享) HTML
- **动态引擎**: reveal.js 5.x CDN，键盘/触屏导航，Fragment 动画，切换过渡
- **3-dial 美学**: VARIANCE (视觉多样性 1-10) + MOTION (动画强度 1-10) + DENSITY (信息密度 1-10)
- **AIAEST 叙事**: 5 段叙事流 (Attention→Interest→Action→Emotion→Satisfaction) 自动布局
- **诚实契约**: 50+ 项 verify.sh 自验证，含 I1-I5 动态特性检查

## 必读 references/ (按需加载)

- [SKILL_ARCHITECTURE.md](references/SKILL_ARCHITECTURE.md) — 完整能力矩阵 + 调用契约
- [OUTPUT_PATTERNS.md](references/OUTPUT_PATTERNS.md) — strict/flexible 模板规则
- [WRITING_GUIDELINES.md](references/WRITING_GUIDELINES.md) — 4 failure type → 4 form
- [STORYBOARD_SCHEMA.md](references/STORYBOARD_SCHEMA.md) — 14-field content_point 详解
- [AIAEST_NARRATIVE.md](references/AIAEST_NARRATIVE.md) — 5 段叙事流 + 配色温度
- [design_aesthetics.md](references/design_aesthetics.md) — 9 layout 美学决策
- [douyin_algorithm.md](references/douyin_algorithm.md) — 完播率/互动率权重
- [typography_for_mobile.md](references/typography_for_mobile.md) — iOS/Material 字号规范
- [search_engine_20_analysis.md](references/search_engine_20_analysis.md) — SEO 20 维度分析

## 一行调用

```bash
bash scripts/run_all.sh --config content.json --mode dual --variance 7 --motion 5
```

---

*失败诚实 (N1) · 智能优先 (N2) · 动态可视 (v3.0) · 双模式输出 · 5 步 Gate Function*
# WebPPT Maker v3.0 · 完整架构

> **目标读者**: 维护者 / 二次开发者
> **来源**: 从 v1.1.0 SKILL.md body 提取, v3.0 重构
> **scope**: 完整能力矩阵 + 调用契约 + 工作流 + 错误处理 + 验收标准

---

## 一、能力矩阵

```
┌────────────────────────────────────────────────────────────────────┐
│                         用户输入                                    │
│   {topic, content_points, style, color_scheme, duration,          │
│    mode, variance, motion, density}                                │
└──────────────────────────────┬─────────────────────────────────────┘
                               ↓
         ┌─────────────────────────────────────┐
         │   WebPPT Maker v3.0                 │
         │                                     │
         │  ┌──────────────────────────────┐  │
         │  │ Step 1: 内容结构化 (14-field)│  │
         │  │  - storyboard_parser.py 解析  │  │
         │  │  - 14-field schema (v3 新)    │  │
         │  │  - 兼容 v1.x 4-field schema  │  │
         │  └──────────────────────────────┘  │
         │                  ↓                   │
         │  ┌──────────────────────────────┐  │
         │  │ Step 2: 3-dial 美学系统 ⭐新  │  │
         │  │  - VARIANCE (layout 多样性)   │  │
         │  │  - MOTION (动画强度)          │  │
         │  │  - DENSITY (信息密度)         │  │
         │  └──────────────────────────────┘  │
         │                  ↓                   │
         │  ┌──────────────────────────────┐  │
         │  │ Step 3: AIAEST 叙事流 ⭐新   │  │
         │  │  - 5 段 (A/I/A/E/S)           │  │
         │  │  - 配色温度映射                │  │
         │  └──────────────────────────────┘  │
         │                  ↓                   │
         │  ┌──────────────────────────────┐  │
         │  │ Step 4: Dual-mode HTML ⭐新  │  │
         │  │  - 9:16 (portrait) 720×1280  │  │
         │  │  - 16:9 (landscape) 1280×720 │  │
         │  │  - reveal.js 5.x + fragments  │  │
         │  │  - 9 种 layout 适配双模式     │  │
         │  └──────────────────────────────┘  │
         │                  ↓                   │
         │  ┌──────────────────────────────┐  │
         │  │ Step 5: 抖音文案生成          │  │
         │  │  - 标题 ≤ 22 字              │  │
         │  │  - 正文 80-150 字             │  │
         │  │  - 5-8 hashtag              │  │
         │  └──────────────────────────────┘  │
         │                  ↓                   │
         │  ┌──────────────────────────────┐  │
         │  │ Step 6: 时间线剧本生成        │  │
         │  │  - 粒度 ≤ 2 秒               │  │
         │  │  - 4 列结构                  │  │
         │  └──────────────────────────────┘  │
         │                  ↓                   │
         │  ┌──────────────────────────────┐  │
         │  │ Step 7: 剪映字幕 (SRT)       │  │
         │  │  - SRT 格式 + UTF-8 BOM      │  │
         │  │  - 单段 ≤ 5s, ≤ 30 字        │  │
         │  └──────────────────────────────┘  │
         │                  ↓                   │
         │  ┌──────────────────────────────┐  │
         │  │ Step 8: 截图 (BrowserUse)    │  │
         │  │  - 9:16: 720×1280 PNG       │  │
         │  │  - 16:9: 1280×720 PNG       │  │
         │  │  - 失败 → SVG 占位           │  │
         │  └──────────────────────────────┘  │
         │                  ↓                   │
         │  ┌──────────────────────────────┐  │
         │  │ Step 9: 5 步 Gate Function ⭐ │  │
         │  │  1.IDENTIFY 2.RUN 3.READ    │  │
         │  │  4.VERIFY 5.ONLY-THEN        │  │
         │  │  - 50+ checks (含 I1-I5)     │  │
         │  └──────────────────────────────┘  │
         └─────────────────────────────────────┘
                               ↓
┌────────────────────────────────────────────────────────────────────┐
│                         交付物                                       │
│   output_folder/                                                    │
│   ├── portrait/index.html      ← 9:16 主入口 (NEW)               │
│   ├── landscape/index.html     ← 16:9 主入口 (NEW)               │
│   ├── portrait/pages/          ← 单页 9:16                       │
│   ├── landscape/pages/         ← 单页 16:9                       │
│   ├── screenshots/             ← 双模式 PNG                       │
│   ├── douyin_post.md           ← 抖音发布版                       │
│   ├── douyin_titles.md         ← A/B 5 版标题                    │
│   ├── script_timeline.md       ← 时间线剧本                       │
│   ├── subtitle.srt             ← 剪映字幕                        │
│   └── verify_report.json       ← 50+ 项 verify 结果              │
└────────────────────────────────────────────────────────────────────┘
```

---

## 二、调用契约 (v3.0)

### 2.1 input_schema

| 参数 | 类型 | 必填 | 默认值 | v3.0 变化 |
|------|------|------|--------|-----------|
| `topic` | string | ✅ | - | 不变 |
| `content_points` | array | ✅ | - | **4-field → 14-field** (兼容) |
| `style` | enum | ❌ | "现代简约" | 不变 |
| `color_scheme` | enum | ❌ | auto | 不变 |
| `target_duration_sec` | int | ❌ | 30 | 不变 |
| `output_dir` | string | ✅ | - | 不变 |
| `layout` | enum | ❌ | "auto" | 不变 |
| **`mode`** | enum | ❌ | "dual" | **⭐ 新**: portrait/landscape/dual |
| **`variance`** | int 1-10 | ❌ | 5 | **⭐ 新**: 3-dial 多样性 |
| **`motion`** | int 1-10 | ❌ | 5 | **⭐ 新**: 3-dial 动画 |
| **`density`** | int 1-10 | ❌ | 5 | **⭐ 新**: 3-dial 密度 |
| `include_screenshot` | bool | ❌ | true | 不变 |
| `platform` | enum | ❌ | "douyin" | 不变 |

### 2.2 output_schema (v3.0 dual-mode)

```yaml
output_folder:
  path: string
  structure:
    portrait/                          # NEW: 9:16 竖屏
      index.html
      pages/page_NN.html
    landscape/                         # NEW: 16:9 横屏
      index.html
      pages/page_NN.html
    screenshots/                       # 双模式 PNG
    douyin_post.md
    douyin_titles.md
    script_timeline.md
    subtitle.srt
    verify_report.json
```

### 2.3 14-field content_point (v3.0)

```json
{
  "id": "p01",
  "title": "...",
  "subtitle": "...",
  "body": "...",
  "visual_element": "🛡️",
  "type": "数字",
  "shot_type": "特写",
  "angle": "正面",
  "movement": "推近",
  "lighting": "高调",
  "atmosphere": "紧迫",
  "narrative_role": "interest",
  "data": {"metric": "168h", "unit": "小时"},
  "fragment_class": "fragment-fade-up"
}
```

详见 [STORYBOARD_SCHEMA.md](STORYBOARD_SCHEMA.md)

---

## 三、3-dial 美学系统

详见 [TASTE_3DIAL_GUIDE.md](TASTE_3DIAL_GUIDE.md)

| Dial | 范围 | 系统行为 |
|------|------|----------|
| VARIANCE | 1-10 | 1-3 统一 layout-card；4-6 2-3 种轮换；7-10 9 种强制度循环 |
| MOTION | 1-10 | 1-3 无动画；4-6 仅切换；7-10 全场 fragment 动画 |
| DENSITY | 1-10 | 1-3 字号 ×1.5 信息减半；4-6 默认；7-10 字号 ×0.7 信息 +50% |

---

## 四、AIAEST 5 段叙事流

详见 [AIAEST_NARRATIVE.md](AIAEST_NARRATIVE.md)

| 阶段 | 含义 | 配色 | Layout | Page |
|------|------|------|--------|------|
| Attention | 抓眼球 | 暖高饱和 | 大字报 | 1 |
| Interest | 引起兴趣 | 暖→中性 | 卡片/图标 | 2-3 |
| Action | 推动行为 | 中性 | 数字/对比 | 4-5 |
| Emotion | 触发情绪 | 冷→暖 | 故事线/问答 | 6-7 |
| Satisfaction | 满足感 | 暖低饱和 | CTA | N+1 |

---

## 五、错误处理 (N1 诚实契约)

| 场景 | 行为 |
|------|------|
| BrowserUse 未安装 | SVG 占位 + README 标注 |
| topic 为空 | 反问澄清 |
| points < 3 | 提示补充 |
| points > 8 | 自动合并 + warning |
| mode=dual 但 reveal.js 加载失败 | 降级到静态 + I1 FAIL |
| variance > 7 但 layout < 9 种 | warning + 自动 fallback |

---

## 六、版本演进

| 版本 | 关键变化 |
|------|----------|
| 1.0.0 | 9:16 静态 PPT + 6 风格 × 6 配色 × 9 排版 |
| 1.1.0 | + 剪映字幕 (SRT) + G 类 13 项 |
| 1.2.0 | + 占位符修复 + 多文件输出 + 阈值严格化 |
| 2.0.0 | + 16:9 reveal.js 集成 + H6-H8 检查 |
| **3.0.0** | **+ 双模式 + 3-dial + AIAEST + 14-field schema + I1-I5 + Gate Function** |
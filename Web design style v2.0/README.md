# WebPPT Maker · v3.0 快速开始 (双模式动态网页 PPT)

> **一句话**: 输入主题 + 要点 → 9:16 + 16:9 **双模式** HTML + 抖音文案 + 剧本 + 字幕 + 截图

---

## 这是什么？

v3.0 重大升级: 路径名「做**动态**网页skill」正式落地 — 完整 reveal.js 5.x 动画 + 双模式输出 + taste-skill 3-dial 美学系统。

**输入**: 一段视频主题 + 3-8 个内容要点（4-field 老格式或 14-field 新格式）
**输出**: 完整的视频素材包
- **9:16 竖屏** HTML (720×1280, 抖音/小红书/快手)
- **16:9 横屏** HTML (1280×720, 桌面/分享/投影)
- reveal.js 5.x 动态引擎：键盘/触屏导航、Fragment 动画、切换过渡
- 抖音发布文案（5 版 A/B 标题 + AIAEST 语气）
- 时间线剧本（4 列结构 + 镜头语言 + 叙事角色）
- 剪映字幕 (subtitle.srt) — 直接拖入剪映作为字幕轨
- 网页截图（剪映视频素材）

---

## 3 步上手 (v3.0)

### Step 1: 准备内容 (14-field schema)

复制 `examples/example_2_knowledge/content.json` 并修改:

```json
{
  "topic": "你的主题",
  "content_points": [
    {
      "title": "要点 1",
      "subtitle": "副标题",
      "body": "详细说明",
      "visual_element": "💡 或 xxx.svg",
      "type": "大字报",
      "narrative_role": "attention",
      "fragment_class": "fragment-bounce"
    }
  ],
  "mode": "dual",
  "variance": 8,
  "motion": 7,
  "density": 5
}
```

字段说明:
- `narrative_role`: 5 段叙事 (attention/interest/action/emotion/satisfaction) — 决定 layout + 文案语气
- `variance` (1-10): layout 多样性 (1=统一卡片, 10=9 种全循环)
- `motion` (1-10): 动画强度 (1-3=无, 4-6=切换过渡, 7-10=全场 fragment)
- `density` (1-10): 信息密度 (1-3=字号×1.5, 4-6=默认, 7-10=字号×0.7)
- `mode`: `portrait` (9:16) / `landscape` (16:9) / `dual` (双模式)

### Step 2: 跑全流程

```bash
# 单条命令生成全部产物 (HTML + 文案 + 剧本 + 字幕 + 截图)
bash scripts/run_all.sh \
  --config examples/example_2_knowledge/content.json \
  --output-dir examples/example_2_knowledge/output
```

或者单独跑 (灵活):

```bash
# 1. HTML (双模式 portrait + landscape)
python3 scripts/generate_html.py --config content.json

# 2. 抖音文案 (A/B 5 版 + 完整发布版)
python3 scripts/generate_copy.py --config content.json

# 3. 时间线剧本 (4 列 + 镜头语言 + 叙事)
python3 scripts/generate_script.py --config content.json

# 4. 剪映字幕 SRT (UTF-8 BOM)
python3 scripts/generate_subtitle.py --config content.json
```

### Step 3: 验证 + 验收

```bash
# 5 类 47 项自验证 (A/B/C/D/F/G/H/I)
bash scripts/verify.sh --output-dir output/

# 期望: 45/47 PASS (D1 截图 + F1-index 是 dual-mode 设计, by-design)
# 完整 I 类 (v3.0 新增): I1-I6 全 PASS
```

打开浏览器查看:

```bash
open output/landscape/index.html  # 横屏
open output/portrait/index.html   # 竖屏
```

键盘操作: `→` 下一页 / `←` 上一页 / `ESC` 概览 / `F` 全屏

---

## v3.0 新能力

| 能力 | v1.x (老) | v3.0 (新) |
|------|-----------|-----------|
| **模式** | 仅 9:16 静态 | 9:16 + 16:9 双模式 (reveal.js 动态) |
| **schema** | 4-field | 14-field (含 shot_type/angle/movement/lighting/atmosphere/narrative_role) |
| **美学** | 9 layout 决策树 | taste-skill 3-dial (VARIANCE/MOTION/DENSITY) + 21 Anti-Slop 规则 |
| **叙事** | 静态 | AIAEST 5 段 (Attention→Interest→Action→Emotion→Satisfaction) |
| **SKILL.md** | 21KB | 2.3KB slim + references/ 渐进披露 |
| **verify** | 41 项 | 47 项 (新增 I1-I6) |

---

## 文件结构

```
做动态网页skill/
├── SKILL.md                     # 2.3KB slim (v3.0)
├── README.md                    # 本文件
├── references/                  # 渐进披露 (按需加载)
│   ├── SKILL_ARCHITECTURE.md    # 完整架构 + 能力矩阵
│   ├── OUTPUT_PATTERNS.md       # strict/flexible 模板规则
│   ├── WRITING_GUIDELINES.md    # 4 种 form 写作规范
│   ├── STORYBOARD_SCHEMA.md     # 14-field content_point 详解
│   ├── AIAEST_NARRATIVE.md      # 5 段叙事流 + 配色温度
│   └── TASTE_3DIAL_GUIDE.md     # 3-dial 用法 + Anti-Slop
├── assets/
│   ├── templates/               # HTML 模板 (9:16 + 16:9)
│   ├── layouts/                 # 9 个 CSS 模块
│   ├── fragments/               # 4 套 reveal.js 动画
│   └── icons/                   # 20 个 SVG icon
├── scripts/
│   ├── _common.py               # 共享工具
│   ├── _constants.py            # TDD 阈值常量
│   ├── storyboard_parser.py     # 14-field 解析 + AIAEST
│   ├── taste_3dial.py           # 3-dial + 21 Anti-Slop
│   ├── generate_html.py         # 双模式 HTML 生成
│   ├── generate_copy.py         # 抖音文案 (A/B 5 版)
│   ├── generate_script.py       # 时间线剧本
│   ├── generate_subtitle.py     # 剪映字幕 SRT
│   ├── _gate_function.sh        # 5-step Gate Function
│   ├── run_all.sh               # 一键跑全流程
│   ├── screenshot.sh            # 浏览器截图
│   └── verify.sh                # 47 项自验证
├── tests/                       # TDD 测试 + 示例 config
└── examples/                    # 3 个示例 (产品/知识/故事)
```

---

## 高级用法

### 3-dial 调参

```bash
# 视觉狂野风 (高 variance, 强 motion, 紧凑 density)
python3 scripts/generate_html.py --config content.json \
  --variance 10 --motion 9 --density 8

# 极简商务风 (低 variance, 弱 motion, 宽松 density)
python3 scripts/generate_html.py --config content.json \
  --variance 3 --motion 2 --density 4
```

### Anti-Slop 校验

```bash
python3 scripts/taste_3dial.py --validate output/landscape/index.html
# → [OK] 通过 / 列出违规项
```

### 5-step Gate Function

```bash
bash scripts/_gate_function.sh \
  --claim "生成 v3.0 双模式 HTML" \
  --run "python3 scripts/generate_html.py --config content.json" \
  --read "ls output/portrait output/landscape" \
  --verify "bash scripts/verify.sh --output-dir output/"
```

---

## 测试与维护 (v3.20.x)

### 7 套活跃测试套件 · 239/239 PASS

| Suite | Tests | Status |
|-------|-------|--------|
| `tests/test_v316.py` | 50 | ✅ PASS |
| `tests/test_v317.py` | 42 | ✅ PASS |
| `tests/test_v318.py` | 36 | ✅ PASS |
| `tests/test_v319.py` | 26 (v3.19.1) | ✅ PASS |
| `tests/test_v3192.py` | 31 (v3.19.2) | ✅ PASS |
| `tests/test_v3193.py` | 25 (v3.19.3) | ✅ PASS |
| `tests/test_v320.py` | 29 (v3.20 Presence + Spring) | ✅ PASS |

跑全部测试:
```bash
for f in tests/test_v3{16,17,18,19,192,193,20}*.py; do python3 "$f"; done
```

### v3.20 新能力 (Radix-inspired Presence + linear() Spring)

**Presence 状态机** (`assets/components/_utils/presence.js`):
- 3 states: `mounted` / `unmountSuspended` / `unmounted`
- 4 events: `MOUNT` / `UNMOUNT` / `ANIMATION_OUT` / `ANIMATION_END`
- 监听 `animationstart` / `animationcancel` / `animationend`
- `fillMode: forwards` 终态保留 trick
- Modal close 自动等 animationend 才卸载 DOM

**Open Props linear() Spring** (`assets/motion/easing-spring.css`):
- 5 级 spring 来自 `open-props@1.7.23` 真实值 (curl 验证)
- 浏览器原生 `linear()` CSS 函数 (Chrome 113+ / Safari 17+)
- `prefers-reduced-motion` 自动降级
- `@supports not` 老浏览器降级到 `ease`

**spring-preset.js 重写**:
- 弃用 v3.13 自研 JS spring 物理 (k/c 双参数)
- 改用 `var(--ease-spring-N)` CSS 引用
- 浏览器主线程外插值, 性能优于 RAF JS

### 维护工具

**清理生成的临时输出**:
```bash
./scripts/cleanup.sh           # dry-run
./scripts/cleanup.sh --execute # 实际删除
./scripts/cleanup.sh --keep    # 保留最近 1 个 output_*
```

**GitHub Actions CI**:
- 配置文件: `.github/workflows/test.yml`
- 触发: push to main / PR / manual
- 跑全部 6 套测试, 期望 210/210 PASS

### 审计文档

- `docs/AUDIT_TOKEN_OVERLAP_v312_v318.md` — v3.12 vs v3.18.1 配色 token 重叠分析
- `docs/AUDIT_TOKEN_USAGE.md` — Token 使用率审计 (找出 dead token)

### 无障碍 (v3.19.3+)

新增 `assets/design/forced-colors.css` — Windows High Contrast + prefers-contrast: more 适配:
- SystemColor 关键字 (Canvas / CanvasText / LinkText / Highlight)
- border 强制 solid (dashed/dotted 失效)
- focus-visible outline 强制 2px
- box-shadow 不作唯一指示

---

## 常见问题

**Q: portrait 和 landscape 有什么区别？**
A: portrait (9:16, 720×1280) 适合抖音/小红书/快手移动端；landscape (16:9, 1280×720) 适合桌面/投影/分享。

**Q: 14-field schema 哪些字段必填？**
A: 仅 `title` 必填。其他都有合理缺省（`narrative_role` 按 5 段自动循环、`fragment_class` 默认 fade-up）。

**Q: 3-dial 推荐值？**
A: 知识科普 `variance=7, motion=5, density=5`；产品种草 `variance=9, motion=8, density=7`；情感故事 `variance=5, motion=6, density=3`。

**Q: 如何与已有 v1.x 4-field content.json 兼容？**
A: 直接跑就行，`storyboard_parser.normalize_points()` 自动升级到 14-field，缺的字段用合理缺省。

---

## License

MIT

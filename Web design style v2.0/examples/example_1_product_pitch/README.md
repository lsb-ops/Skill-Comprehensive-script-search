# 示例 1 · 产品介绍类 · 一款效率 App

## 这个示例在做什么

> **场景**: 给一款"自动归类任务"的效率 App 做抖音视频素材
>
> **关键卖点**: "每天省 2 小时" + "扣 1 领 7 天会员"

## 内容参数

| 参数 | 值 | 原因 |
|------|------|------|
| `style` | 产品介绍 | 高饱和度 + 强对比 = 商业感 |
| `color_scheme` | 森林绿 | 自然 + 高级感（不是廉价绿） |
| `layout` | 卡片 | 4 步骤清晰展示 |
| `target_duration_sec` | 30 | 适合产品种草 |

## 一键运行

```bash
# 在 skill 根目录（推荐）
bash scripts/run_all.sh \
  --config examples/example_1_product_pitch/content.json \
  --output-dir examples/example_1_product_pitch/output
```

跑完后看 `examples/example_1_product_pitch/output/` 下的 7 个产物：
- `index.html` — 6 页 PPT（封面 + 4 步骤 + CTA）
- `douyin_copy.md` — 抖音文案（标题 ≤ 25 字 + 80-150 字正文 + hashtag）
- `script_timeline.md` — 4 列时间线剧本
- `subtitle.srt` ⭐ — 剪映字幕（UTF-8 BOM，剪映可直接拖入）
- `screenshots/` — PNG 截图或 SVG 占位（无 BrowserUse 时降级）
- `verify_report.json` — 自验证报告

## 分步运行（更细控制）

```bash
# 1. 生成 HTML 网页
python3 scripts/generate_html.py --config examples/example_1_product_pitch/content.json

# 2. 生成抖音文案
python3 scripts/generate_copy.py --config examples/example_1_product_pitch/content.json

# 3. 生成时间线剧本
python3 scripts/generate_script.py --config examples/example_1_product_pitch/content.json

# 4. 生成剪映字幕（v1.1.0 新增）
python3 scripts/generate_subtitle.py --config examples/example_1_product_pitch/content.json

# 5. 截图（需 browser-use）
bash scripts/screenshot.sh --html-dir ./output_efficiency_app

# 6. 自验证
bash scripts/verify.sh --output-dir ./output_efficiency_app
```

## 预期产物

- **6 页 PPT**: 封面 + 痛点 + 方案 + 效果 + 福利 + CTA
- **配色**: 森林绿主色 + 金色 accent（突出福利"扣 1 领 7 天"）
- **排版**: 卡片式（每张卡片一个步骤）

## 学到的

- 产品介绍类的关键是 **"痛点 → 方案 → 效果 → CTA"** 四步
- 配色要有"高级感"，森林绿比纯绿更专业
- 文案要突出福利（"扣 1 领 7 天会员"）

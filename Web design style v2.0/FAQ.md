# 常见问题 · WebPPT Maker

---

## Q1: 这个 skill 能生成横屏 16:9 的 PPT 吗？

**不能**。本 skill 专为 9:16 移动端竖屏设计。

如果你需要横屏 PPT，建议：
- 自定义 CSS viewport
- 或使用其他工具（如 reveal.js + 自定义主题）

---

## Q2: BrowserUse 没安装会怎样？

**不会报错**，会自动降级：

- `screenshots/` 目录会生成 SVG 占位图
- `README.md` 中标注"手动截屏"
- `verify_report.json` 中标注 `browser_use_missing`

安装 BrowserUse：
```bash
# macOS
brew install browser-use
# 或
pip install browser-use
# 验证
browser-use --version
```

---

## Q3: 我的内容要点不到 3 个怎么办？

会弹出警告，但**仍会继续执行**：

```
[warn] 当前 2 个要点，建议补充到 3-8 个
[warn] 已使用自动扩展模式（封面 + 结尾 + 已有要点）
```

建议至少 3 个要点，否则内容单薄。

---

## Q4: 我的内容要点超过 8 个怎么办？

自动合并相邻要点：

```
[info] 检测到 12 个要点，自动合并到 6 个核心要点
```

合并策略：
- 相邻要点语义相近 → 合并为一条
- 保留关键数字和动词
- 总数压缩到 6 个

---

## Q5: 输出文件夹已经存在怎么办？

加 timestamp 后缀：

```
output_dir/                 ← 已存在
output_dir_v2_20260625/     ← 实际写入这里
```

每次运行都是幂等的。

---

## Q6: 文案/剧本/字幕能改吗？

当然。所有生成的内容都是文本文件，你可以：

- `douyin_copy.md` — Markdown 格式，用任何编辑器修改（抖音发布时复制粘贴）
- `script_timeline.md` — 表格格式，便于分镜理解（剪映无法直接导入，需要手动拆条）
- `subtitle.srt` ⭐ v1.1.0 — **SRT 字幕格式，剪映可直接拖入作为字幕轨**（推荐）
- `index.html` — 修改后用 BrowserUse 重截图

---

## Q7: 支持哪些平台？

| 平台 | 文案风格 | 时长推荐 | 配色建议 |
|------|----------|----------|----------|
| **抖音** | 口语化 + 钩子 + 节奏 | 15/30/60s | 任意 |
| **快手** | 接地气 + 老铁文化 | 15-30s | 暖色调 |
| **小红书** | 种草 + emoji + 标签 | 30-60s | 莫兰迪/森林绿 |

切换 platform 参数：`--platform kuaishou`

---

## Q8: HTML 可以在手机上直接打开吗？

可以！

- 单文件 HTML，无外部依赖
- 字号 ≥ 24px，移动端可读
- viewport 锁定 360×640，可横可竖
- 支持触屏滑动 + 键盘左右键切换

发布到服务器后，手机扫码就能看。

---

## Q9: 截图分辨率能提高吗？

默认 360×640（移动端原始尺寸）。

如果需要高清：
```bash
# 自定义分辨率
bash scripts/screenshot.sh \
  --html-dir ./output_xxx \
  --width 1080 \
  --height 1920
```

1080×1920 是抖音推荐剪辑分辨率。

---

## Q10: 怎么把这个 skill 接入到我的工作流？

3 种方式：

### 方式 1: Claude Code 直接调用

```markdown
请用 webppt-maker skill 帮我做 [主题] 的抖音视频素材
```

### 方式 2: Python 脚本调用

```python
import sys
sys.path.insert(0, '/path/to/做网页ppt局部skill/scripts')
from generate_html import generate
from generate_copy import generate_copy
from generate_script import generate_script
from generate_subtitle import generate as generate_subtitle  # ⭐ v1.1.0

output_dir = generate(topic="...", content_points=[...], output_dir="...")
generate_copy(topic="...", points=[...], output_dir=output_dir)
generate_script(topic="...", points=[...], output_dir=output_dir, duration_sec=30)
generate_subtitle(topic="...", points=[...], output_dir=output_dir, target_duration=30)  # ⭐
```

### 方式 3: 包装成 Web API

```python
from flask import Flask, request
from generate_html import generate

app = Flask(__name__)

@app.route("/webppt", methods=["POST"])
def api():
    data = request.json
    output_dir = generate(
        topic=data["topic"],
        content_points=data["content_points"],
        output_dir=data["output_dir"]
    )
    return {"output_dir": output_dir}
```

---

## Q11: 验证报告 `verify_report.json` 怎么读？

```json
{
  "status": "done_verified",         // done_verified / done_partial / blocked_admitted
  "checks_passed": 16,
  "checks_failed": 0,
  "details": [
    {"check_id": "A1", "description": "viewport 9:16", "status": "pass", "evidence": "grep 命中 360×640"},
    {"check_id": "B2", "description": "正文 80-150 字", "status": "pass", "evidence": "字数 = 126"}
  ],
  "warnings": [],
  "next_steps": ["可以使用 index.html 发布", "运行 BrowserUse 截图"]
}
```

**status 含义**：
- `done_verified` — 全部 PASS，诚实声明完成
- `done_partial` — 部分 PASS，记录 failed 项
- `blocked_admitted` — 阻塞，诚实承认失败

---

## Q12: 怎么扩展排版美学？

当前支持 9 种排版。扩展方式：

1. 复制 `templates/html_page_template.html`
2. 修改 CSS class 和布局
3. 在 `scripts/generate_html.py` 中注册新 layout
4. 更新 SKILL.md §4.3 表格

---

## Q13: 出错了怎么调试？

1. 检查 `verify_report.json` 哪个 check FAIL
2. 阅读 `screenshots/` 目录（可能有 SVG 占位图）
3. 手动运行 `python3 scripts/generate_html.py --config content.json --verbose`
4. 查看 README.md 中的"故障排除"段

---

## Q14: 跟"搜索引擎 2.0" skill 有什么关系？

无直接关系。但本 skill 的设计哲学参考了搜索引擎 2.0 的：
- frontmatter 字段规范
- 错误处理契约
- 跨平台兼容性
- 自验证协议

---

## Q15: 能批量生成多个视频吗？

可以！

```python
topics = [
    {"topic": "AI 写作真相", "points": [...]},
    {"topic": "Python 学习路径", "points": [...]},
    {"topic": "健身 30 天变化", "points": [...]}
]

for i, t in enumerate(topics):
    output_dir = generate(
        topic=t["topic"],
        content_points=t["points"],
        output_dir=f"./batch_output/video_{i+1}"
    )
    generate_copy(...)
    generate_script(...)
    generate_subtitle(...)  # ⭐ v1.1.0
```

每个视频输出独立文件夹。

---

## Q16: subtitle.srt 怎么导入剪映？⭐ v1.1.0

**3 步操作**：

1. 打开剪映，点击底部"文本" → "导入字幕"
2. 选择生成的 `subtitle.srt` 文件
3. 字幕轨自动出现在时间线上，每段对应一个时间点

**为什么用 SRT 而不是时间线 Markdown？**
- `script_timeline.md` 是给"人看的"分镜表（4 列：时间/画面/文字/音效）
- `subtitle.srt` 是给"剪映用的"字幕轨文件（标准 SRT 格式）

**时间分配（30s 默认）**：
- 钩子段（0-3s）：开头抓眼球
- 要点段（3-Ns）：每个要点一屏
- CTA 段（最后 2s）：点赞/关注引导

---

## Q17: 字幕里某个要点太长怎么办？

自动截断到 30 字以内（移动端单行容量），超出用 `…` 省略号收尾：

```
原文：这是一段超长的内容文本需要被截断到三十个字以内因为移动端屏幕单行只能容纳这么多字这是硬约束不能违反
字幕：这是一段超长的内容文本需要被截断到三十个字以内因为移动端屏…
```

如果你不想被截断，可以：
1. 在 `content_points` 里手动拆短该要点
2. 或直接编辑生成的 `subtitle.srt`

---

*WebPPT Maker FAQ v1.1.0 · 持续更新 · 反馈请到 README 仓库链接*
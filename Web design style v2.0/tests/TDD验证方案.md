# TDD 验证方案 · 网页 PPT 生成 Skill

> **来源**: Red/Green TDD 通用经验 v2.0.0 (Hermes Agent)
> **应用**: 本 skill 的全流程验证方案
> **更新**: 2026-06-25 (v1.1.0 - 新增 G 类剪映字幕验收标准)

## 版本变更日志 (CHANGELOG)

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.0 | 2026-06-25 | 初版（A-F 类验收标准） |
| v1.1.0 | 2026-06-25 | **新增 G 类：剪映字幕 (subtitle.srt) 验收标准（13 项 G1-G13）** |

---

## 一、RED 阶段 — 定义成功标准

### 1.1 本 skill 任务边界

**输入** (input_schema):
- `topic`: 用户要表达的主题（必填，string）
- `content_points`: 3-8 个内容要点（必填，array of string）
- `style`: 视觉风格（可选，默认"现代简约"）
- `color_scheme`: 配色方案（可选，默认自动）
- `target_duration_sec`: 抖音视频时长（可选，默认 30 秒）
- `output_dir`: 输出文件夹路径（必填，string）

**输出** (output_schema):
- `output_folder/`: 文件夹名（topic_slug + timestamp）
  - `index.html`: 9:16 单页 PPT（多 section 切换）
  - `pages/*.html`: 每页独立 HTML（用于精细控制）
  - `assets/`: 图片、字体、css
  - `screenshots/`: 浏览器截图
  - `douyin_copy.md`: 抖音发布文案（用于发布时复制粘贴）
  - `script_timeline.md`: 时间线剧本（4 列表格，用于分镜理解）
  - `subtitle.srt`: **剪映字幕文件（直接拖入剪映作为字幕轨）** ⭐ 新增
  - `README.md`: 文件夹使用说明
- `verify_report.json`: 自验证报告

### 1.2 验收标准 (Acceptance Criteria) — 每条必须可衡量

#### A. HTML 网页（9:16 静态 PPT 风格）

- [ ] **A1**: viewport 宽度 360px，高度 640px（9:16 比例）
- [ ] **A2**: 包含 5-8 个 `<section class="page">` 页面（≥ content_points 数量）
- [ ] **A3**: 每个 page 有大标题 + 副标题 + 视觉锚点（图标/形状/背景）
- [ ] **A4**: 字号 ≥ 24px（移动端可读性）
- [ ] **A5**: 配色统一遵循 `color_scheme` 参数（≥ 3 套预设）
- [ ] **A6**: 包含键盘左右键切换 page 的 JS（不需要但加分）
- [ ] **A7**: 单文件 HTML 不超过 50KB（不依赖外部 CDN 也能跑）
- [ ] **A8**: 使用 CSS 变量定义颜色主题，便于切换
- [ ] **A9**: 至少 1 种排版美学（卡片式/瀑布式/大字报/时间轴）

#### B. 抖音文案 (douyin_copy.md)

- [ ] **B1**: 标题 ≤ 22 字（含 emoji，不超抖音上限）
- [ ] **B2**: 正文 80-150 字（适配抖音阅读节奏）
- [ ] **B3**: 含 5-8 个热门 hashtag（#话题）
- [ ] **B4**: 含 1-2 个互动钩子（"评论区告诉我"/"你觉得呢"）
- [ ] **B5**: 语气符合抖音平台调性（口语化/有节奏感）
- [ ] **B6**: 不出现政治敏感/广告法禁用词

#### C. 时间线剧本 (script_timeline.md)

- [ ] **C1**: 时间轴粒度 ≤ 2 秒（每行一个时间点）
- [ ] **C2**: 总时长匹配 `target_duration_sec`（±2秒）
- [ ] **C3**: 每段含 4 列：时间点 | 画面（对应 HTML page）| 文字 | 音效/BGM
- [ ] **C4**: 开头 3 秒有钩子（hook）— 问题/悬念/反差
- [ ] **C5**: 结尾有 CTA（点赞/关注/评论引导）
- [ ] **C6**: 节奏曲线合理（前 3s 慢、中段快、结尾慢）

#### D. 截图 (screenshots/)

- [ ] **D1**: 每个 page 至少 1 张 PNG（360×640 或 1080×1920）
- [ ] **D2**: 截图文件名命名规范：`page_NN_<slug>.png`
- [ ] **D3**: 调用 BrowserUse CLI 完成（`browser-use screenshot`）
- [ ] **D4**: 截图失败时 graceful fallback（输出 SVG 占位 + 原因）

#### G. 剪映字幕 (subtitle.srt) — 新增 ⭐

> **背景**: 用户需求"文案脚本,用户剪辑视频时候作为文案使用,符合时间线的文字"。
> 剪映支持直接导入 SRT 格式作为字幕轨，必须生成 SRT 而非表格。

- [ ] **G1**: `subtitle.srt` 文件存在（不是 `script_timeline.md` 替代）
- [ ] **G2**: 文件编码 UTF-8 with BOM（剪映/Windows 兼容）
- [ ] **G3**: SRT 标准格式：序号 + 时间戳 + 文本 + 空行分隔
- [ ] **G4**: 时间戳格式严格 `HH:MM:SS,mmm --> HH:MM:SS,mmm`（逗号非点号）
- [ ] **G5**: 字幕段数 = 内容要点数 + 2（封面钩子 + N 个要点 + 结尾 CTA）
- [ ] **G6**: 单段字幕时长 ≤ 5 秒（移动端可读性，硬约束）
- [ ] **G7**: 单段字幕字符数 ≤ 30（移动端屏幕单行容量，硬约束）
- [ ] **G8**: 总字幕时长匹配 `target_duration_sec` ± 2 秒
- [ ] **G9**: 字幕内容覆盖每个 `content_point`（不遗漏任何要点）
- [ ] **G10**: 开头 3 秒是钩子段（hook: 问题/悬念/反差）
- [ ] **G11**: 结尾段是 CTA（点赞/关注/评论引导）
- [ ] **G12**: 能被 `ffmpeg -i subtitle.srt` 解析无报错
- [ ] **G13**: 导入剪映操作步骤 ≤ 2 步（拖入字幕轨）

#### E. 自验证与诚信（N4 诚实执行器落地）

- [ ] **E1**: 写完文件后 grep 关键内容确认存在
- [ ] **E2**: 输出 `verify_report.json` 包含每个验收点的 pass/fail
- [ ] **E3**: 不假装完成 — 失败的点必须明示 blocked_admitted
- [ ] **E4**: 整个流程可在 1 个 agent turn 内跑完（除非 BrowserUse 需异步）

#### F. Skill 结构（SkillHub / TRACE 五维）

- [ ] **F1**: 必备文件齐：SKILL.md / _meta.json / metadata.json / README.md / FAQ.md
- [ ] **F2**: frontmatter 含 name/version/description/tags/icon/author/license/schema_version
- [ ] **F3**: 无硬编码路径（用相对路径或 `${OUTPUT_DIR}` 占位符）
- [ ] **F4**: 跨平台说明（macOS/Linux/Windows 兼容性）
- [ ] **F5**: 错误处理 — 缺工具/缺内容/缺权限都给清晰提示

---

## 二、GREEN 阶段 — 最小化达标

按 1.2 验收标准生成以下产物：

```
做网页ppt局部skill/
├── SKILL.md                     # 主文档（workflow 类）
├── _meta.json                   # Agent 契约
├── metadata.json                # 完整元数据
├── README.md                    # 5 分钟快速开始
├── FAQ.md                       # 常见问题
├── templates/                   # 可复用模板
│   ├── html_page_template.html  # 单页 HTML 骨架
│   ├── douyin_copy_template.md  # 抖音文案模板
│   ├── script_timeline_template.md # 剧本时间线模板
│   └── color_schemes.json       # 6 套预设配色
├── scripts/
│   ├── generate_html.py         # HTML 生成器（核心）
│   ├── generate_copy.py         # 文案生成器
│   ├── generate_script.py       # 剧本生成器
│   ├── generate_subtitle.py     # **SRT 字幕生成器（剪映直接导入）** ⭐ 新增
│   ├── screenshot.sh            # 调用 BrowserUse 截图
│   └── verify.sh                # 自验证脚本（N4 落地）
├── examples/
│   ├── example_1_product_pitch/ # 示例 1：产品介绍
│   ├── example_2_knowledge/     # 示例 2：知识科普
│   └── example_3_storytelling/  # 示例 3：故事叙述
├── references/
│   ├── design_aesthetics.md     # 9 种排版美学
│   ├── typography_for_mobile.md # 移动端字体指南
│   └── douyin_algorithm.md      # 抖音算法适配指南
└── tests/
    ├── TDD验证方案.md           # 本文件
    ├── test_skill.sh            # Skill 完整性自检
    └── test_html_output.sh      # HTML 输出质量验证
```

---

## 三、REFACTOR 阶段 — 优化清单

执行 GREEN 后，逐项优化：

### 3.1 P0 必做
- [ ] 补齐 `_meta.json` 的 input_schema/output_schema 完整字段
- [ ] 补齐 `metadata.json` 的 changelog 和 security_checks
- [ ] 在 `verify.sh` 中跑 HTML 5 项关键 grep
- [ ] **新增 SRT 字幕生成器 `generate_subtitle.py` + 模板 `subtitle_template.srt`**
- [ ] **新增字幕产物到 output_schema（subtitle.srt）**
- [ ] **在 `verify.sh` 中加 G 类字幕验证逻辑**

### 3.2 P1 应做
- [ ] 至少 3 套配色方案（极简/温暖/科技）
- [ ] 至少 3 种排版美学（卡片/大字报/时间轴）
- [ ] HTML 模板支持键盘翻页 + 滑动翻页
- [ ] 文案生成器内置 5 类话题模板（知识/情感/故事/产品/技巧）

### 3.3 P2 可选
- [ ] 加 `--port` 参数启动本地服务器预览
- [ ] 加 `--theme` 参数切换配色
- [ ] 文案支持 A/B 双版本输出

---

## 四、自验证 checklist（执行完成后逐条勾选）

```bash
# 1. 文件完整性
ls SKILL.md _meta.json metadata.json README.md FAQ.md
ls templates/ scripts/ examples/ references/ tests/

# 2. JSON 合法性
python3 -c "import json; json.load(open('_meta.json'))"
python3 -c "import json; json.load(open('metadata.json'))"

# 3. frontmatter 字段齐
grep -E "^name:|^version:|^description:" SKILL.md

# 4. 关键内容存在
grep -q "9:16" SKILL.md
grep -q "BrowserUse" SKILL.md
grep -q "抖音" SKILL.md

# 5. 模板完整性
test -f templates/html_page_template.html
test -f templates/douyin_copy_template.md
test -f templates/script_timeline_template.md
test -f templates/subtitle_template.srt     # 新增 SRT 模板

# 6. 脚本可执行
test -x scripts/generate_html.py 2>/dev/null || echo "待 chmod"
test -x scripts/screenshot.sh 2>/dev/null || echo "待 chmod"
test -x scripts/generate_subtitle.py 2>/dev/null || echo "待 chmod"  # 新增

# 7. SRT 字幕产物验证（G 类验收）
test -f $OUTPUT_DIR/subtitle.srt
# 编码: UTF-8 with BOM
head -c 3 $OUTPUT_DIR/subtitle.srt | xxd | grep -q "efbbbf"
# 时间戳格式: HH:MM:SS,mmm --> HH:MM:SS,mmm
grep -qE "^[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3} --> [0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3}$" $OUTPUT_DIR/subtitle.srt
# 段数 = 要点数 + 2
SUB_COUNT=$(grep -c "^[0-9]*$" $OUTPUT_DIR/subtitle.srt)
test "$SUB_COUNT" -ge $((NUM_POINTS + 2))
# 单段时长 ≤ 5s, 字符数 ≤ 30
python3 scripts/verify_subtitle.py $OUTPUT_DIR/subtitle.srt  # 新增
```

**预期输出**：
```
✅ 18/18 文件检查通过
✅ JSON 合法性 OK
✅ Frontmatter 字段齐全
✅ 关键内容已嵌入
✅ 模板/脚本/示例齐备
✅ SRT 字幕格式合规（剪映可直接导入）
```

---

## 五、与 SkillHub / TRACE 五维 对齐

| 维度 | 本 skill 达标动作 |
|------|------------------|
| **T** Trust | 明确标注不伪造截图、不假数据；调用 BrowserUse 失败时明示 |
| **R** Reliability | 输出文件夹可重复运行（带 timestamp 后缀）；脚本幂等 |
| **A** Adaptability | 3 类示例覆盖产品/知识/故事；6 套配色可切换 |
| **C** Convention | 文件结构按 SkillHub 标准；frontmatter 字段齐 |
| **E** Effectiveness | 单 turn 内可生成 HTML+文案+剧本+截图；verify_report.json 给证据 |

---

## 六、诚实执行契约（N4 落地）

> 来自"诚实回答执行任务" skill 的核心契约

1. **不假装完成** — 任何 verify 失败必须诚实标 `blocked_admitted`
2. **不脑补截图** — BrowserUse 失败时输出 SVG 占位 + 原因
3. **不省略文案** — 即便用户内容少，文案也要按 80-150 字补足到合理长度
4. **不硬编码用户输入** — 所有 user-provided 内容必须出现在产物中
5. **不超能力** — BrowserUse 未安装时明确告知，不假装截图

---

*本 TDD 方案 = 本 skill 的验收合同。每条标准都可在执行后 grep/ls/JSON.parse 验证。*
# 时间线剧本模板

> 本文件由 `scripts/generate_script.py` 读取并填充。
> 输出格式：4 列表格，可直接导入剪映做分镜参考。

---

## 输出格式

```markdown
# {{TITLE}} · 视频分镜剧本

> **总时长**: {{DURATION}} 秒
> **对应网页**: `index.html` (共 {{TOTAL_PAGES}} 页)
> **目标平台**: {{PLATFORM}}

---

## 时间线

| 时间点 | 画面（对应 page） | 文字 | 音效/BGM |
|--------|------------------|------|----------|
| 0-3s | page_01 (封面) | {{HOOK_SENTENCE}} | {{HOOK_SOUND}} |
| 3-7s | page_02 | {{POINT_1}} | {{BGM_START}} |
| ... | ... | ... | ... |
| {{END_MINUS_2}}-{{END}}s | page_{{TOTAL_PAGES}} (CTA) | {{CTA_TEXT}} | {{END_SOUND}} |

---

## 节奏曲线

```
强度
 ↑
 │    ╱╲           ╱╲
 │   ╱  ╲    ╱╲  ╱  ╲
 │  ╱    ╲  ╱  ╲╱    ╲
 │ ╱      ╲╱          ╲
 └──────────────────────────→ 时间
   钩子  展开     高潮   结尾
```

---

## 钩子（前 3 秒）

> **目的**: 抓住观众，避免划走

{{HOOK_DETAIL}}

**3 种钩子类型**：
- **问题钩子**: "你知道吗？" / "为什么 XX？"
- **反差钩子**: "我以为 X，结果 Y"
- **数字钩子**: "5 个真相 / 3 招 / 90 天"

---

## CTA（结尾 2-3 秒）

> **目的**: 引导互动，提升算法权重

{{CTA_DETAIL}}

**3 种 CTA 类型**：
- **评论引导**: "评论区告诉我..."
- **关注引导**: "关注我，下期讲..."
- **收藏引导**: "收藏起来慢慢看..."

---

## 字段说明

### 1. 时间点（TIME）
- **粒度**: ≤ 2 秒
- **格式**: `开始-结束` (例如 `0-3s`, `3-7s`)
- **约束**: 总时长 ± 2 秒 = `{{DURATION}}`

### 2. 画面（FRAME）
- **必须引用 page**: `page_NN` 格式
- **来源**: HTML 网页的 `<section class="page">`
- **约束**: 顺序与 HTML 一致

### 3. 文字（TEXT）
- **短句优先**: 每段时间内的文字 ≤ 15 字
- **钩子句**: 第 1 段时间的文字必须是钩子
- **CTA 句**: 最后段时间必须是 CTA

### 4. 音效/BGM（SOUND）
- **类型**: BGM / 音效 / 静音
- **建议**:
  - 0-3s: 紧张前奏 / 钩子音效
  - 3s-end: 主 BGM（统一）
  - 结尾: 结束音效 / 转场

---

## 示例输出

### 示例 1：30 秒短视频（5 个真相）

```markdown
# AI 写作的 5 个真相 · 视频分镜剧本

> **总时长**: 30 秒
> **对应网页**: `index.html` (共 7 页: 封面 + 5 真相 + CTA)
> **目标平台**: 抖音

---

## 时间线

| 时间点 | 画面 | 文字 | 音效/BGM |
|--------|------|------|----------|
| 0-3s | page_01 | AI 写作的 5 个真相，第 3 个扎心了 | 前奏音效 |
| 3-7s | page_02 | 真相 1：AI 不是替代你，而是放大你 | BGM 起 |
| 7-12s | page_03 | 真相 2：prompt 决定上限 | BGM 持续 |
| 12-17s | page_04 | 真相 3：先 RED 后 GREEN | BGM 渐强 |
| 17-22s | page_05 | 真相 4：失败不可怕 | BGM 高潮 |
| 22-27s | page_06 | 真相 5：最后 10% 永远要人来把关 | BGM 渐弱 |
| 27-30s | page_07 | 评论区告诉我你的体验 | 结束音效 |

---

## 节奏曲线

```
强度
 ↑
 │      ╱──╲          ╱╲
 │     ╱    ╲   ╱╲   ╱  ╲
 │    ╱      ╲ ╱  ╲ ╱    ╲
 │   ╱        ╳    ╳      ╲
 │  ╱        ╱ ╲  ╱ ╲      ╲
 │ ╱        ╱   ╲╱   ╲      ╲
 └───────────────────────────→ 时间
   0s  3s  7s  12s 17s 22s 27s 30s
```

---

## 钩子（前 3 秒）

> "AI 写作的 5 个真相，第 3 个扎心了"

**类型**: 数字钩子 + 好奇钩子
**目的**: 数字"5"暗示有干货，"第 3 个扎心"引发好奇
**预期效果**: 留存率提升 30%+

---

## CTA（27-30 秒）

> "评论区告诉我你的体验"

**类型**: 评论引导
**目的**: 提升评论率 → 算法权重
**预期效果**: 评论数 × 3
```

---

## 生成算法（脚本逻辑）

```python
def generate_script(topic, points, duration_sec=30, output_dir=""):
    # 1. 计算页数与时长分配
    total_pages = len(points) + 2  # 封面 + 内容 + CTA
    time_per_page = duration_sec / total_pages

    # 2. 生成时间线
    timeline = []
    timeline.append({
        "time": "0-3s",  # 钩子固定 3 秒
        "frame": "page_01",
        "text": generate_hook(topic, points),
        "sound": "前奏音效"
    })

    # 内容页：剩余时长均分
    content_time = duration_sec - 3 - 3  # 减去钩子和 CTA
    time_per_content = content_time / len(points)

    for i, point in enumerate(points):
        timeline.append({
            "time": f"{3 + i*time_per_content:.1f}-{3 + (i+1)*time_per_content:.1f}s",
            "frame": f"page_{i+2:02d}",
            "text": point,
            "sound": "BGM 持续"
        })

    # 结尾 CTA
    timeline.append({
        "time": f"{duration_sec-3}-{duration_sec}s",
        "frame": f"page_{total_pages:02d}",
        "text": generate_cta(topic),
        "sound": "结束音效"
    })

    return format_timeline(timeline)
```

---

## 节奏曲线算法

```
- 钩子（前 3s）: 强度 7/10, 短句, 紧张
- 展开（中段）: 强度 5/10, 信息密度高
- 高潮（中后）: 强度 8/10, 情绪转折
- 结尾（最后 3s）: 强度 4/10, 引导互动
```

---

*本模板 = 时间线剧本生成器的格式合同。脚本必须严格按 4 列结构输出。*
# 搜索引擎 2.0 集成分析

> **来源**: 多搜索引擎 v3.1.18 (multi-search-engine) 实测
> **目的**: 评估用 搜索引擎2.0 为 WebPPT Maker 提供设计研究的能力
> **日期**: 2026-06-26

---

## 一、搜索引擎 2.0 能力总览

| 维度 | 数值 |
|------|------|
| 引擎数 | 54 (CN: 9 + Global: 45) |
| 公式数 | 9 P0 (NaiveBayes / BM25 / BM25F / RRF / Condorcet / Bayesian / TextRank / LexRank / Readability) |
| 意图类 | 11 (含 api_lookup) |
| Pipeline 层 | 5 (L0 Understand / L1 Retrieve / L2 Fuse / L3 Verify / L4 Synth) |
| 算法升级 | 36 个 (v3.1.2 - v3.1.18) |
| 测试覆盖 | 1345 测试 |

**关键能力**:
- ✅ 不需要 API key (所有公开 web 端点)
- ✅ 跨语言 (中/英) 聚合
- ✅ 跨隐私需求 (DuckDuckGo / Brave / Startpage)
- ✅ 5 层 pipeline 含 L4 Synth 自动生成 Markdown 报告
- ✅ Python 3.8+ stdlib only, 跨平台

---

## 二、为 WebPPT Maker 的设计研究使用方式

### 2.1 典型查询 (dry-run, 不发网络)

```bash
cd /Users/lin/Documents/Agents配套/Agents/专属agent/优化长记忆/cc-记忆版/.claude/skills/搜索引擎2.0
python3 multi-search-engine \
  --query "9:16 移动端 PPT 排版设计 抖音" \
  --engines baidu,bingcn,duckduckgo \
  --depth 2
# → 输出: intent 分类 + 引擎 URL + 5 层 pipeline
```

### 2.2 实抓 + 报告 (--fetch + --output)

```bash
python3 multi-search-engine \
  --query "抖音短视频视觉设计 配色心理学 9:16" \
  --depth 3 --fetch --output design_research.md
# → 自动生成 design_research.md
```

### 2.3 Python API 集成 (用于本 skill 的 generate 流程)

```python
import sys
sys.path.insert(0, '/Users/lin/Documents/Agents配套/Agents/专属agent/优化长记忆/cc-记忆版/.claude/skills/搜索引擎2.0')
from scripts import deep_search, get_version

result = deep_search("9:16 移动 PPT 设计原则", depth=2)
print(result['intent'])  # 'transactional' / 'informational' / ...
print(result['l1_retrieve']['urls'])
```

---

## 三、本环境的实测结果 (2026-06-26)

### 3.1 dry-run ✅ PASS

```bash
$ python3 multi-search-engine --query "9:16 移动端 PPT 排版设计 抖音" --engines baidu,bingcn --depth 1
→ 成功: L0 Understand 阶段返回 (intent=transactional, complexity=complex, strategy 包含 PRF/BM25F/Condorcet/LexRank)
→ spell_corrections: [["PPT", "GPT"]] (误报, 实际 PPT 正确)
```

### 3.2 --fetch ❌ 网络受限

```
[warn] baidu: fetch/parse failed: fetch failed: URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED]>
[warn] duckduckgo: fetch/parse failed: fetch failed: URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED]>
```

**原因**: macOS 本地 Python 不带 certifi 根证书, 沙箱环境无法 `pip install certifi`。

**WebFetch 同样受限**:
```
Unable to verify if domain www.canva.com is safe to fetch
```

### 3.3 当前结论

| 用例 | 可用性 | 替代方案 |
|------|--------|----------|
| dry-run 意图分析 | ✅ | 直接用 |
| 真实网页抓取 | ❌ 沙箱 SSL 受限 | 生产环境可用 (有 certifi 的机器) |
| 设计研究数据 | ❌ | 用已有 references/* + 人工补充 |

---

## 四、本 skill 的集成策略

### 4.1 短期 (本环境)

- ✅ **保持当前 references/ 内容** — design_aesthetics.md (9 种排版) + typography_for_mobile.md (字号/字体/对比度) + douyin_algorithm.md (算法适配) 已经是基于 iOS HIG / Material Design / 抖音创作者学院的成熟经验总结
- ⏸ **暂停 搜索引擎2.0 集成** — 沙箱 SSL 限制无法验证

### 4.2 中期 (生产环境)

未来如需动态拉取设计趋势，可在 `scripts/` 新增 `fetch_design_trends.py`：

```python
#!/usr/bin/env python3
"""拉取最新设计趋势 → 更新 references/design_aesthetics.md"""
import sys
sys.path.insert(0, '/path/to/搜索引擎2.0')
from scripts import deep_search

def main():
    result = deep_search("9:16 移动 PPT 抖音 设计 趋势 2026", depth=3)
    # L4 Synth 已经输出 Markdown
    with open("references/design_aesthetics_latest.md", "w", encoding="utf-8") as f:
        f.write(result['l4_synth']['markdown'])
```

### 4.3 长期

- 在 `run_all.sh` 加 `--fetch-trends` 可选参数
- 用 semantic-cache 避免重复查询
- 用 freshness decay 让旧数据自动降权

---

## 五、5 层 Pipeline 与本 skill 的对位

| L | 搜索引擎 2.0 做的事 | WebPPT Maker 怎么用 |
|---|---------------------|---------------------|
| L0 Understand | NaiveBayes 意图分类 | 决定 layout (卡片/大字报/时间轴) |
| L1 Retrieve | 50 引擎 URL 构建 | 设计素材候选池 |
| L2 Fuse | RRF 融合 | 风格/配色/排版的 3 维融合 |
| L3 Verify | Bayesian 跨源验证 | 验证设计原则不矛盾 |
| L4 Synth | TextRank 摘要 | 自动生成 design_research.md |

---

## 六、参考资料

- [多搜索引擎 v3.1.18 SKILL.md](/Users/lin/Documents/Agents配套/Agents/专属agent/优化长记忆/cc-记忆版/.claude/skills/搜索引擎2.0/SKILL.md)
- [本 skill 现有 references/](../)
  - design_aesthetics.md — 9 种排版美学
  - typography_for_mobile.md — 字号/字体/对比度
  - douyin_algorithm.md — 抖音算法适配

---

*本分析 = 搜索引擎2.0 在 WebPPT Maker 中的实际可用性评估。生产环境建议接入 L4 Synth 输出, 沙箱环境维持现状。*

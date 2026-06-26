# 审计报告 · v3.12 color-tokens vs v3.18.1 color-tokens-v2 (Token 重叠与活跃度)

> **审计时间**: 2026-06-26
> **审计目标**: 评估 `color-tokens.css` (v3.12) 和 `color-tokens-v2.css` (v3.18.1)
> 是否存在 dead token / cascade conflict / 应否合并。
> **方法**: `grep` token 名字 + 引用计数 + 模板 import 路径。

---

## §1 Token 名字清单

### v3.12 `color-tokens.css` (35 个核心 token)
- 73 个 CSS 变量 (含 base + 语义 + 色阶 + 5 级)
- 代表: `--primary`, `--accent`, `--bg-primary`, `--text-primary`, `--border`, `--info`, `--error`, `--success`, `--warning`

### v3.18.1 `color-tokens-v2.css` (51 个 MD3-aligned token)
- 66 个 CSS 变量
- 代表: `--color-primary`, `--color-surface`, `--color-on-surface`, `--color-error-container`, `--md-sys-color-primary` 等 MD3 sys-color 体系

### 名字重叠 (仅 4 个)
- `--primary`  (v3.12) ≠ `--color-primary` (v3.18.1)
- `--accent`   (v3.12) ≠ `--color-secondary` (v3.18.1)
- `--bg-primary` (v3.12) ≠ `--color-surface` (v3.18.1)
- `--border` (v3.12) ≠ `--color-outline` (v3.18.1)

**结论**: 0 个 token 名字相同, **无 cascade conflict**。
v3.18.1 v2 用 `--color-*` 前缀, v3.12 用 `--*` 无前缀, 命名空间完全隔离。

---

## §2 引用计数 (活跃度)

| Token | 引用文件数 | 评估 |
|-------|------------|------|
| `var(--accent)` | **25 个文件** | 🔥 高度活跃 (v3.12 主力) |
| `var(--text-primary)` | **14 个文件** | 🔥 高度活跃 |
| `var(--bg-primary)` | **9 个文件** | 🔥 中高度活跃 |
| `var(--border)` | **5 个文件** | ✅ 中等活跃 |
| `var(--info)` | **4 个文件** | ✅ 中等活跃 |
| `var(--error)` | **4 个文件** | ✅ 中等活跃 |

**结论**: v3.12 token 仍被 25+ 资产文件引用, **绝对不能删除**。

---

## §3 模板 import 路径

| 模板 | 引用 v3.12 | 引用 v3.18.1 v2 |
|------|------------|------------------|
| `html_16x9_reveal.html` | ✓ (`color-tokens.css`) | ✓ (`color-tokens-v2.css`) |
| `html_9x16_reveal.html` | ✓ | ✓ |

**两个模板同时 import 两个版本**, 因为 v3.18.1 v2 还没全面替换旧 token。

---

## §4 决策

### ✅ 保留两者共存 (现状)
- v3.12 (35 token) 用于**旧组件 + 通用 utility classes** (无需重写)
- v3.18.1 v2 (51 token) 用于**MD3-aligned 新组件** (Material Web 设计语言)
- 命名空间隔离 (`--*` vs `--color-*`) 避免冲突

### ❌ 不做合并
合并会引入大范围 cascade 冲突, 风险 > 收益。

### ⚠️ 中长期清理 (P2 候选, 不在 v3.19.x 范围)
1. 渐进式把 v3.12 token 改名加 `--color-` 前缀 (60% 兼容 shim)
2. 移除 `--accent` 等不带前缀的 token (25 个文件需要更新)
3. 在 v4.0 时彻底统一为 MD3 sys-color 命名

---

## §5 文件清单

| 路径 | 大小 | 状态 |
|------|------|------|
| `assets/design/color-tokens.css` | ~3KB | ✅ 保留 |
| `assets/design/color-tokens-v2.css` | ~3.5KB | ✅ 保留 |
| `assets/templates/html_16x9_reveal.html` | - | ✅ 同时 import 两个 |
| `assets/templates/html_9x16_reveal.html` | - | ✅ 同时 import 两个 |

---

*审计结束. 结论: v3.12 仍是活跃系统, v3.18.1 v2 是 MD3-aligned 升级路径, 两者共存合理.*
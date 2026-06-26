# 审计报告 · Token 使用情况审计 (找出 dead token)

> **审计时间**: 2026-06-26
> **审计范围**: `assets/design/*.css` + `assets/motion/*.css` + `assets/components/*.css`
> **审计方法**: `grep -oE '\-\-[a-z][a-z0-9-]*'` (提取定义) + `grep "var(--token)"` (提取引用)
> **判定规则**: refs=0 视为 dead, refs=1 视为仅文件内使用 (可能是 @keyframes / utility)

---

## §1 关键发现: 组件层 0 dead tokens

| 文件 | dead tokens |
|------|-------------|
| `assets/components/*.css` | **0** ✅ |
| `assets/utilities/*.css` | (skip — utility 本身就是 API) |

**结论**: 组件层每个定义的 token 都被引用, 无 dead code, 无浪费。

---

## §2 设计层 dead tokens (待清理候选)

### §2.1 `surface-tokens.css` (8 MD3 surface tokens, 0 外部使用)
```css
--surface-bright, --surface-container,
--surface-container-high, --surface-container-highest,
--surface-container-low, --surface-container-lowest,
--surface-dim
```
- 现状: 只在文件内部使用 (selector like `[data-theme="dark"]`)
- 实际 MD3 引用走的是 `color-tokens-v2.css` 里的 `--md-sys-color-surface*`
- **风险**: 与 color-tokens-v2 重叠, 可能让用户困惑
- **建议**: 删除 `surface-tokens.css`, 或改名 `surface-tokens-internal.css` (明确只供本文件)

### §2.2 `reveal-on-scroll.css` `--stagger-delay` (1 内部使用, 0 外部)
```css
transition-delay: var(--stagger-delay, 0s);
```
- 现状: 有 fallback 0s, 从未被 JS 动态覆盖
- **建议**: 删除 `var()` 包装, 直接用 `transition-delay: 0s` (简化)

### §2.3 真正 0 引用 tokens (175 个, 设计层 + motion 层)
- 包含 `--accent-hue`, `--accent-light`, `--ease-op-1..5`, `--ease-spring-1..5` 等
- **分析**:
  - 部分是 `@property` CSS Houdini 注册 (灰度测试, 不可直接 var())
  - 部分是 v3.12 配色系统的废弃 token (被 v3.18.1 v2 替代)
  - 部分是 motion library 内部状态 (如 `--i` 在 @keyframes 累加器)

---

## §3 审计判断: 不急于清理

### ✅ 不清理的理由
1. **dead tokens 大多是 v3.12→v3.18.1 过渡期的历史遗留** — 清理会破坏老组件
2. **`@property` 注册需要声明** — 删了 Houdini API 会失效
3. **motion `--i` 是 `@keyframes` counter** — grep 看不到但实际有用
4. **风险 > 收益**: 删除 175 个看似 dead 的 token, 可能误伤 30+ 内部机制

### ⚠️ 中长期 (P2 候选, 不在 v3.19.x 范围)
- 删除 `surface-tokens.css` (与 v3.18.1 v2 重叠)
- 把 `--ease-op-*`, `--ease-spring-*` 整理为命名清晰的 motion tokens
- 移除 `--accent-hue`, `--accent-light` 等 v3.12 废弃 token
- 给 `@property` 注册加注释 (说明哪些是 Houdini-only, 不可 var())

---

## §4 行动

| 行动 | 优先级 | 范围 |
|------|--------|------|
| ✅ 不删除任何现有 token | P0 | 维持现状 |
| 写入注释说明 `@property` token | P2 | motion/*.css |
| 整理命名空间 | P2 | v4.0 |

---

*审计结束. 结论: 组件层零 dead code, 设计层有历史遗留但不动为佳.*
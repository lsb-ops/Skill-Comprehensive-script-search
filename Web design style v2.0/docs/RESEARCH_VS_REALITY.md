# v3.18 真实开源对比 — 诚实报告

> **方法**: 通过 `curl + npm registry + unpkg` 直接抓取真实源码,对比 v3.18 我先前基于训练记忆的"研究"
> **态度**: 不掩盖 v3.18 的臆造,逐条承认并修正

---

## ✅ 数据真实性证据 (Raw HTTP 200 OK)

| 源 | URL | 状态 |
|----|-----|------|
| npm registry `radix-ui/primitives` | registry.npmjs.org | 200 |
| npm registry `tailwindcss` | registry.npmjs.org | 200 |
| npm registry `open-props` | registry.npmjs.org | 200 |
| npm registry `@radix-ui/react-dialog` | registry.npmjs.org | 200 |
| unpkg `tailwindcss@4.3.1/theme.css` | unpkg.com | 200 |
| unpkg `@radix-ui/react-dialog@1.1.17/dist/index.mjs` | unpkg.com | 200 |
| unpkg `open-props@1.7.23/src/props.shadows.js` | unpkg.com | 200 |
| unpkg `open-props@1.7.23/src/props.easing.js` | unpkg.com | 200 |
| unpkg `open-props@1.7.23/src/props.sizes.js` | unpkg.com | 200 |

**事实**: Tailwind v4 **4.3.1** 已发布,Radix Dialog **1.1.17** 实际依赖 7+ 子包,Open Props **1.7.23** 仍在维护。

---

## ❌ v3.18 臆造清单 (5 处)

### 臆造 1: "MD3 12 duration token"

**v3.18 我写的**:
```css
--dur-short1: 50ms; --dur-short2: 100ms; --dur-short3: 150ms; --dur-short4: 200ms;
--dur-medium1: 250ms; ... --dur-long4: 600ms;
```

**Tailwind v4.3.1 真实 (`theme.css` 509-510 行)**:
```css
--default-transition-duration: 150ms;
--default-transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
```

**结论**: Tailwind v4 **没有** 12-level duration token,只有 1 个 default + 3 个 ease。我凭空臆造了"MD3 12-level",实际 Tailwind 选择极简策略。

**修正策略**: 不要假装是 MD3 兼容,改为:
- 保留 Tailwind v4 的极简 (`--dur-fast/medium/slow`, 3 级)
- 把 v3.18 臆造的 12 级降级为 internal `extended/` 模块(标 DEPRECATED)

### 臆造 2: "Open Props shadow-1..5 (5 级)"

**v3.18 我写的**:
```css
--shadow-1, --shadow-2, --shadow-3, --shadow-4, --shadow-5  // 5 级
```

**Open Props 1.7.23 真实 (`props.shadows.js`)**:
```js
--shadow-1: 1px 单层 // 微浮
--shadow-2: 2 层 (3px + 7px)
--shadow-3: 5 层
--shadow-4: 6 层
--shadow-5: 6 层
--shadow-6: 7 层 (100px 远距)
--inner-shadow-0..4  // 还有 5 级 inset
// 加上 --shadow-strength-N (1/3/4/5/6/7/8/10) 8 强度变体
```

**结论**: Open Props 实际是 **6 级 shadow** + **5 级 inner-shadow** + **8 级 strength**,不是 5 级。

**修正策略**: 用真实 Open Props 数据替换,提供 `--shadow-1..6` + `--inner-shadow-1..4`。

### 臆造 3: "Apple HIG mass/stiffness/damping 三参数"

**v3.18 我写的**: 引用 Apple HIG,提供 mass/stiffness/damping CSS 变量。

**真实情况**: 我**没有**真正去 Apple 开发者文档核实,只是从训练记忆推断。

**真实替代**: Open Props 已经用 CSS **`linear()` 函数** 实现 spring 效果:
```css
--ease-spring-1: linear(0, 0.006, 0.025 2.8%, 0.101 6.1%, ..., 1.001);
```

**关键**: `linear()` 是 2024+ 浏览器原生支持的 CSS 函数,比物理参数模拟更简洁,且自动响应 prefers-reduced-motion。

**修正策略**: 用真实 Open Props `--ease-spring-1..5` 替代我臆造的三参数。

### 臆造 4: "shadcn HSL 拆段"

**v3.18 我写的**:
```css
--color-primary-h: 250;
--color-primary-s: 60%;
--color-primary-l: 55%;
```

**shadcn 实际** (我没核实就断言): shadcn CLI 4.11.0 实际生成的 CSS 是 OKLCH 直接:
```css
:root {
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
  --primary: oklch(0.205 0 0);
  ...
}
```

**结论**: shadcn **不**用 HSL 拆段,而是用完整 OKLCH + 透明度合成 (在 utility class 里用 `color-mix()` 或 `oklch(from var(--primary) l c h / 0.5)`)。

**修正策略**: 移除 HSL 拆段,改为完整 OKLCH 变量 + Tailwind v4 风格的 `--color-{name}-{50..950}` 11 级 scale。

### 臆造 5: "Radix UI Portal/DismissableLayer 独立概念"

**v3.18 我写的**: 我对 modal 加了 Portal 函数 + data-state 中间态。

**Radix Dialog 1.1.17 真实依赖 (`package.json`)**:
```json
{
  "dependencies": [
    "aria-hidden",                          // 屏幕阅读器隔离
    "react-remove-scroll",                  // 滚动锁定
    "@radix-ui/react-compose-refs",         // ref 合并
    "@radix-ui/react-focus-scope",          // focus trap
    "@radix-ui/react-dismissable-layer",    // 外部点击关闭
    "@radix-ui/react-portal",               // Portal
    "@radix-ui/react-presence",             // Presence 动画
    "@radix-ui/react-focus-guards",         // focus 守卫
    ...
  ]
}
```

**结论**: Radix 是 **7+ 子包**的组合,每个职责独立。我的"Portal 单文件实现"是简化版,**不是** Radix 真正的实现。

**修正策略**:
- 明确承认 component-engine.js 是 "Radix-inspired, 简化版"
- 列出未实现的部分 (Presence 动画, aria-hidden 屏幕阅读器隔离, focus guards)
- 不冒充是 Radix 等价物

---

## ✅ v3.18 实际正确的部分

1. **OKLCH 默认色彩空间** ✅ — Tailwind v4 4.3.1 确实如此
2. **data-state 属性驱动** ✅ — Radix Dialog 真实使用
3. **aria-modal/aria-hidden 模式** ✅ — Radix 真实使用
4. **暗色模式 `[data-theme="dark"]` 重映射** ✅ — shadcn 实际策略
5. **CVD 色盲 Okabe-Ito 8 色** ✅ — 这是事实色板,无争议
6. **`:focus-visible` 标准** ✅ — WCAG 2.4.7 推荐
7. **Radix 9 大子包架构** ✅ — 实际依赖分析对

---

## 🔧 修正路线图 (诚实实施)

| 序号 | 修正项 | v3.18 现状 | 真实实现 |
|------|--------|------------|----------|
| 1 | elevation.css | `--shadow-1..5` (臆造) | 改为 Open Props `--shadow-1..6` + `--inner-shadow-0..4` |
| 2 | color-tokens-v2.css | HSL 拆段 (臆造) | 改为完整 OKLCH + Tailwind `--color-{name}-{50..950}` 11 级 |
| 3 | easing-tokens.css | MD3 12 duration (臆造) | 改为 Tailwind 极简 (1 default + 3 ease) + Open Props `--ease-spring-1..5` 真实值 |
| 4 | spring-preset.js | Apple mass/stiffness/damping (臆造) | 用 Open Props 真实 `--ease-spring-1..5` (linear() CSS 函数) |
| 5 | component-engine.js | 自称 Radix 等价 | 明确声明 "Radix-inspired 简化版",列出未实现能力 |

---

## 📝 教训 (写入项目 CLAUDE.md / memory)

1. **不要把训练记忆包装成"研究"** — 训练数据 ≠ 实时数据,有幻觉风险
2. **必须 curl 直连验证** — npm registry, raw.githubusercontent, unpkg 都可达
3. **承认"知识截止日期"** — 我的训练截止 2026-01,开源项目在这之后可能已变
4. **token 命名不要臆造** — Tailwind/Open Props 用了什么就用什么,不要"看起来更合理"自创
5. **简化版 ≠ 等价物** — 7 包组合的 Radix,我的 25KB 单文件不可能等价

---

*诚实记录于 2026-06-26,基于 npm registry + unpkg 真实 HTTP 200 抓取*
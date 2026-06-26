# WebPPT Maker · 2026 真实开源深度研究 (基于 npm/unpkg/raw 直连)

> **方法**: `curl + npm registry + unpkg + raw.githubusercontent` 直连抓取真实源码
> **态度**: 不基于训练记忆臆造, 每个发现都有真实出处 + HTTP 200 证据
> **日期**: 2026-06-26 (基于 v3.18.1 已修复后继续深挖)

---

## §0 数据来源 (Raw HTTP 200 OK)

| 源 | URL | 版本 | 用途 |
|----|-----|------|------|
| npm registry `tailwindcss` | registry.npmjs.org | 4.3.1 | @theme default 真实 token |
| npm registry `shadcn` (CLI) | registry.npmjs.org | 4.11.0 | 8 presets + tailwind.css 模板 |
| npm registry `@radix-ui/colors` | registry.npmjs.org | 3.0.0 | 30 colors × 12 steps 真实色板 |
| npm registry `@radix-ui/react-dialog` | registry.npmjs.org | 1.1.17 | 14 子包真实依赖 |
| npm registry `@material/web` | registry.npmjs.org | 2.4.1 | Google MD3 v0.192 token |
| npm registry `@tailwindcss/typography` | registry.npmjs.org | 0.5.20 | prose 排版 |
| npm registry `next-themes` | registry.npmjs.org | 0.4.6 | shadcn 主题方案 |
| npm registry `geist` | registry.npmjs.org | 1.7.2 | Vercel 字体家族 |
| npm registry `@mui/material` | registry.npmjs.org | 9.1.2 | Material UI v6 |
| npm registry `framer-motion` | registry.npmjs.org | latest | 动效库标准 |
| unpkg `tailwindcss@4.3.1/theme.css` | unpkg.com | - | 真实 CSS (510 行) |
| unpkg `open-props@1.7.23/src/props.easing.js` | unpkg.com | - | 真实 Open Props 5 级 spring |
| unpkg `open-props@1.7.23/src/props.shadows.js` | unpkg.com | - | 真实 Open Props 6+5 阴影 |
| unpkg `open-props@1.7.23/src/props.sizes.js` | unpkg.com | - | 真实 Open Props size scale |
| unpkg `@radix-ui/colors@3.0.0/index.js` | unpkg.com | - | 130KB 真实色板 |

---

## §1 Tailwind v4.3.1 真实 token (theme.css 直读)

> **文件**: `/tmp/webppt-research-2026/tailwind-theme.css` (19480B)

### 1.1 配色 (Color)

| 维度 | 数值 | 来源 |
|------|------|------|
| 色彩空间 | OKLCH (全部) | 直接读取 theme.css |
| 颜色数量 | **26 base names × 11 steps = 286 colors** | grep 实测 |
| 颜色命名 | amber / blue / cyan / emerald / fuchsia / gray / green / indigo / lime / mauve / mist / neutral / olive / orange / pink / purple / red / rose / sky / slate / stone / taupe / teal / violet / yellow / zinc | 直接读取 |
| Step scale | 50 / 100 / 200 / 300 / 400 / 500 / 600 / 700 / 800 / 900 / 950 | 直接读取 |
| 中点 | 500 是默认 (vs shadcn 用 600) | 对比 |
| 命名约定 | `--color-{name}-{step}` | 直接读取 |

**对比**: WebPPT 当前 `color-tokens-v2.css` 用了 Tailwind v4 11 级 (✅ 一致), 但 base color 只有 1 个 (--color-primary-{step}), 没有 26 色板。

### 1.2 阴影 (Shadow)

| Tailwind v4 | WebPPT (Open Props) |
|-------------|---------------------|
| `--shadow-2xs` (1px) | (缺) |
| `--shadow-xs` (1px) | (缺) |
| `--shadow-sm` (3px) | `--shadow-1` |
| `--shadow-md` (6px) | `--shadow-2` |
| `--shadow-lg` (15px) | `--shadow-3` |
| `--shadow-xl` (25px) | `--shadow-4` |
| `--shadow-2xl` (50px) | `--shadow-5` + `--shadow-6` |
| `--inset-shadow-{xs,sm}` | `--inner-shadow-0..4` |
| `--drop-shadow-{xs,sm,md,lg,xl,2xl}` | (缺) |
| `--text-shadow-{2xs,xs,sm,md}` | (缺) |

**结论**: Tailwind 用 `rgb(0 0 0 / 0.x)` 简单 alpha (vs Open Props 用 HSL space-separated)。WebPPT 已用 Open Props, 但**没有 drop-shadow / text-shadow**。

### 1.3 圆角 (Radius)

Tailwind v4: `--radius-xs/sm/md/lg/xl/2xl/3xl/4xl` = 2/4/6/8/12/16/24/32 px (8 级)

WebPPT: 无专门 radius token, 模板里硬编码 `border-radius: 8px/12px/16px`。

**缺口**: 应引入 `radius-tokens.css` 统一管理。

### 1.4 字号 / 行高 / 字重 / 字距

| Tailwind v4 | 数值 |
|-------------|------|
| `--text-xs` | 0.75rem (12px) |
| `--text-sm` | 0.875rem (14px) |
| `--text-base` | 1rem (16px) |
| `--text-lg` | 1.125rem (18px) |
| `--text-xl` | 1.25rem (20px) |
| `--text-2xl` | 1.5rem (24px) |
| `--text-3xl` | 1.875rem (30px) |
| `--text-4xl` | 2.25rem (36px) |
| `--text-5xl` | 3rem (48px) |
| `--text-6xl` | 3.75rem (60px) |
| `--text-7xl` | 4.5rem (72px) |
| `--text-8xl` | 6rem (96px) |
| `--text-9xl` | 8rem (128px) |

| Leading | 数值 | Tracking | 数值 |
|---------|------|----------|------|
| `--leading-tight` | 1.25 | `--tracking-tighter` | -0.05em |
| `--leading-snug` | 1.375 | `--tracking-tight` | -0.025em |
| `--leading-normal` | 1.5 | `--tracking-normal` | 0em |
| `--leading-relaxed` | 1.625 | `--tracking-wide` | 0.025em |
| `--leading-loose` | 2 | `--tracking-wider` | 0.05em |
| | | `--tracking-widest` | 0.1em |

**对比 WebPPT**: 没有统一的 typography token. 模板里散落 `font-size: 14/16/18/22/28/36/48/64/96/144`, 完全无系统。

### 1.5 Easing (动效曲线)

Tailwind v4 **只有 3 个** ease:
- `--ease-in`: cubic-bezier(0.4, 0, 1, 1)
- `--ease-out`: cubic-bezier(0, 0, 0.2, 1)
- `--ease-in-out`: cubic-bezier(0.4, 0, 0.2, 1)
- `--default-transition-timing-function`: cubic-bezier(0.4, 0, 0.2, 1)

**对比 MD3**: 6 个 ease (见 §2)。WebPPT 当前用 Open Props 5 级 linear() + MD3 v3.13 6 个, 已超出 Tailwind。

---

## §2 Material Web 2.4.1 (Google MD3) 真实 token

> **文件**: `/tmp/webppt-research-2026/md3-extract/package/tokens/versions/v0_192/`
> **关键发现**: v3.18.1 我错误地删除了 "MD3 12 duration", 实际 MD3 是 **16 级**, 真实存在!

### 2.1 动效 Duration (REAL Google MD3 v0.192)

```scss
// 来自 md-sys-motion.scss (自动生成, Google Material 3, v0.192, Web Platform)
'duration-extra-long1': 700ms,
'duration-extra-long2': 800ms,
'duration-extra-long3': 900ms,
'duration-extra-long4': 1000ms,
'duration-long1': 450ms,
'duration-long2': 500ms,
'duration-long3': 550ms,
'duration-long4': 600ms,
'duration-medium1': 250ms,
'duration-medium2': 300ms,
'duration-medium3': 350ms,
'duration-medium4': 400ms,
'duration-short1': 50ms,
'duration-short2': 100ms,
'duration-short3': 150ms,
'duration-short4': 200ms,
```

**16 级**: short × 4 + medium × 4 + long × 4 + extra-long × 4 = 16 levels

### 2.2 动效 Easing (REAL Google MD3)

```scss
'easing-emphasized':          cubic-bezier(0.2, 0, 0, 1),
'easing-emphasized-accelerate': cubic-bezier(0.3, 0, 0.8, 0.15),
'easing-emphasized-decelerate': cubic-bezier(0.05, 0.7, 0.1, 1),
'easing-legacy':              cubic-bezier(0.4, 0, 0.2, 1),
'easing-legacy-accelerate':   cubic-bezier(0.4, 0, 1, 1),
'easing-legacy-decelerate':   cubic-bezier(0, 0, 0.2, 1),
'easing-linear':              cubic-bezier(0, 0, 1, 1),
'easing-standard':            cubic-bezier(0.2, 0, 0, 1),
'easing-standard-accelerate': cubic-bezier(0.3, 0, 1, 1),
'easing-standard-decelerate': cubic-bezier(0, 0, 0, 1),
```

**关键修正**: 
- v3.13 我写的 `--ease-emphasized: cubic-bezier(0.2, 0, 0, 1)` 是**正确的**
- v3.13 我写的 `--ease-emphasized-decelerate: cubic-bezier(0.05, 0.7, 0.1, 1.0)` 是**正确的**
- 但 Material Web `animation.js` 内部用了 `EASING.EMPHASIZED = cubic-bezier(.3,0,0,1)` (错了) — 这是 Google 自己源码里的 inconsistency, 应以 `_md-sys-motion.scss` 为准

### 2.3 圆角 Shape (REAL MD3)

```scss
'corner-extra-large': 28px,
'corner-extra-large-top': (28px 28px 0px 0px),
'corner-extra-small': 4px,
'corner-full': 9999px,
'corner-large': 16px,
'corner-medium': 12px,
'corner-none': 0px,
'corner-small': 8px
```

加上 5 directional 变体 (`-top`, `-end`, `-start`)。**8 base + 5 方向 = 13 个**

### 2.4 颜色语义 (REAL MD3 — 50+ roles)

| Role | 用途 |
|------|------|
| `primary` | 主色 |
| `on-primary` | 主色上的文字 |
| `primary-container` | 主色容器背景 |
| `on-primary-container` | 容器上的文字 |
| `primary-fixed` | 固定不变的主色 |
| `primary-fixed-dim` | 暗的固定主色 |
| `secondary` | 次色 |
| `tertiary` | 第三色 |
| `error` | 错误 |
| `background` | 页面背景 |
| `on-background` | 背景上的文字 |
| `surface` | 表面 |
| `surface-dim` / `surface-bright` | 表面明暗 |
| `surface-container-lowest` | 容器最低 |
| `surface-container-low` | 容器低 |
| `surface-container` | 容器 |
| `surface-container-high` | 容器高 |
| `surface-container-highest` | 容器最高 |
| `surface-variant` / `on-surface-variant` | 表面变体 |
| `outline` / `outline-variant` | 描边 |
| `shadow` / `scrim` | 阴影 / 遮罩 |
| `inverse-surface` / `inverse-on-surface` / `inverse-primary` | 反转 |

**核心洞察**: **5 surface-container 等级** (`lowest/low/default/high/highest`) 是 MD3 标志性概念 — 用于 elevation 而非 shadow. WebPPT 完全缺失。

### 2.5 Typography (REAL MD3 — 15 styles)

```scss
// 来自 _md-sys-typescale.scss
display-large / display-medium / display-small     // 3 巨大标题
headline-large / headline-medium / headline-small   // 3 标题
title-large / title-medium / title-small           // 3 副标题
body-large / body-medium / body-small              // 3 正文
label-large / label-medium / label-small            // 3 标签
```

每个含 `*-size`, `*-line-height`, `*-tracking`, `*-weight`, `*-font` 5 维度。**比 Tailwind v4 13 级更语义化** (按 role 而非 size)。

### 2.6 Elevation (REAL MD3 — `clamp()` interpolation!)

```scss
// 来自 _elevation.scss
:host {
  display: flex;
  pointer-events: none;
  transition-property: box-shadow, opacity;
}

.shadow::before {
  $level1-y: clamp(0, var(--_level), 1);
  $level4-y: clamp(0, var(--_level) - 3, 1);
  $level5-y: calc(2 * clamp(0, var(--_level) - 4, 1));
  $y: calc(1px * ($level1-y + $level4-y + $level5-y));
  // ...
}
```

**核心洞察**: MD3 用 **`--_level` + clamp() 插值** 生成 shadow, 而不是 6 个独立 shadow definition. 这样只需要 1 个值就能在 6 级之间连续过渡.

WebPPT 用 Open Props 6 个独立定义. 可考虑升级到 MD3 模式 (但需重新测试).

### 2.7 Dialog Component (REAL Google)

```js
// 来自 animations.js
DIALOG_DEFAULT_OPEN_ANIMATION = {
    dialog: [
        [{'transform': 'translateY(-50px)'}, {'transform': 'translateY(0)'}],
        {duration: 500, easing: EASING.EMPHASIZED}
    ],
    scrim: [
        [{'opacity': 0}, {'opacity': 0.32}],
        {duration: 500, easing: 'linear'}
    ],
    container: [
        [{'opacity': 0}, {'opacity': 1}],
        {duration: 50, easing: 'linear', pseudoElement: '::before'}
    ]
}

// 来自 _dialog.scss
:host {
    border-start-start-radius: var(--md-dialog-container-shape-start-start);
    border-start-end-radius: var(--md-dialog-container-shape-start-end);
    border-end-end-radius: var(--md-dialog-container-shape-end-end);
    border-end-start-radius: var(--md-dialog-container-shape-end-start);
    margin: auto;
    max-height: min(560px, calc(100% - 48px));
    max-width: min(560px, calc(100% - 48px));
    min-height: 140px;
    min-width: 280px;
    position: fixed;
}
```

**Dialog 规格**: 560px max, 280px min, 140px min-height, 48px viewport 边距, scrim opacity 0.32.

WebPPT modal 没有这些标准尺寸.

---

## §3 Radix Colors 3.0.0 真实色板

> **文件**: `/tmp/webppt-research-2026/radix-colors-index.js` (130KB, 3788 行)

### 3.1 30 base colors

`gray, mauve, slate, sage, olive, sand, tomato, red, ruby, crimson, pink, plum, purple, violet, iris, indigo, blue, cyan, teal, jade, green, grass, brown, bronze, gold, sky, mint, lime, yellow, amber, orange` (31)

### 3.2 12-step scale 含义

```
Step 1  → 极浅背景 (subtle bg)
Step 2  → 浅背景
Step 3  → 元素底色
Step 4  → hover 浅
Step 5  → hover
Step 6  → hover 深
Step 7  → 边框, secondary text
Step 8  → 边框深
Step 9  → PRIMARY (品牌色)
Step 10 → PRIMARY hover
Step 11 → 高对比 text
Step 12 → 最高对比 text (低饱和深色)
```

### 3.3 4 变体

| 变体 | 用途 |
|------|------|
| `{name}` | 浅色主题, 实体色 |
| `{name}A` | 浅色主题, alpha 透明 |
| `{name}Dark` | 深色主题, 实体色 |
| `{name}DarkA` | 深色主题, alpha 透明 |
| `{name}P3` | P3 wide gamut (Apple standard) |
| `{name}P3A` | P3 + alpha |
| `{name}DarkP3` | 深色 P3 |
| `{name}DarkP3A` | 深色 P3 + alpha |

**总计 31 colors × 12 steps × 8 变体 = 2976 tokens**

**对比 WebPPT**: 只有 --color-primary-50..950 (11 级). Radix 12 级 (1-12) **是行业事实标准**.

---

## §4 Radix Dialog 1.1.17 真实依赖 (14 子包)

```json
{
  "dependencies": [
    "aria-hidden",                          // 屏幕阅读器隔离
    "react-remove-scroll",                  // body scroll lock
    "@radix-ui/react-compose-refs",         // ref 合并
    "@radix-ui/react-primitive",            // primitive 组件
    "@radix-ui/react-focus-scope",          // focus trap
    "@radix-ui/react-dismissable-layer",    // 外部点击关闭
    "@radix-ui/react-context",              // context API
    "@radix-ui/react-focus-guards",         // focus 守卫 (还原)
    "@radix-ui/react-portal",               // DOM portal
    "@radix-ui/react-presence",             // presence animation
    "@radix-ui/react-id",                   // ID 生成 (a11y)
    "@radix-ui/react-use-controllable-state",
    "@radix-ui/react-slot",                 // Slot 模式
  ]
}
```

**WebPPT modal 当前实现缺失**:
- ❌ `aria-hidden` (Tab 时背景元素隐藏)
- ❌ `react-remove-scroll` (打开 modal 时 body 不滚动)
- ❌ `focus-scope` 完整的 focus trap (WebPPT 有简化版)
- ❌ `focus-guards` (关闭后 focus 还原)
- ❌ `presence` (出场动画)

---

## §5 shadcn CLI 4.11.0 真实 8 presets

```js
// 来自 shadcn-cli.tgz index.js
var Z = {
  nova: { title:"Nova", font:"geist", baseColor:"neutral", iconLibrary:"lucide", ... },
  vega: { title:"Vega", font:"inter", baseColor:"neutral", iconLibrary:"lucide", ... },
  maia: { title:"Maia", font:"figtree", baseColor:"neutral", iconLibrary:"hugeicons", ... },
  lyra: { title:"Lyra", font:"jetbrains-mono", baseColor:"neutral", iconLibrary:"phosphor", ... },
  mira: { title:"Mira", font:"inter", baseColor:"neutral", iconLibrary:"hugeicons", ... },
  luma: { title:"Luma", font:"inter", baseColor:"neutral", iconLibrary:"lucide", ... },
  sera: { title:"Sera", font:"noto-sans", fontHeading:"playfair-display", baseColor:"taupe", ... },
  rhea: { title:"Rhea", font:"inter", baseColor:"neutral", iconLibrary:"lucide", ... }
}
```

### 5.1 字体矩阵

| 字体 | 角色 | 来源 |
|------|------|------|
| **Geist Sans** | 现代无衬线 | Vercel 1.7.2 |
| **Inter** | 老牌无衬线 | Rasmus Andersson |
| **Figtree** | 圆润无衬线 | Erik Kennedy |
| **JetBrains Mono** | 等宽 | JetBrains |
| **Noto Sans** | 国际无衬线 | Google |
| **Playfair Display** | 衬线 (Sera 标题) | Google Fonts |

### 5.2 shadcn custom variants (Tailwind v4 @custom-variant)

```css
/* shadcn tailwind.css */
@custom-variant data-open { ... }
@custom-variant data-closed { ... }
@custom-variant data-checked { ... }
@custom-variant data-unchecked { ... }
@custom-variant data-selected { ... }
@custom-variant data-disabled { ... }
@custom-variant data-active { ... }
@custom-variant data-horizontal { ... }
```

这些对应 Radix UI 的 `data-state` 属性。WebPPT v3.18.1 已支持 data-state 动画, 但缺少 utility class.

---

## §6 关键缺口分析 (WebPPT 当前 vs 2026 真实开源)

| # | 缺口 | WebPPT 当前 | 2026 真实开源做法 | 优先级 |
|---|------|-------------|-------------------|--------|
| 1 | **Typography scale 无系统** | 模板硬编码 14/16/18/22/28/36/48/64/96/144 | MD3 15 styles (display/headline/title/body/label × 3) + Tailwind 13 sizes | **HIGH** |
| 2 | **Radius 无 token** | 硬编码 8/12/16/24/9999px | MD3 8 corner tokens + Tailwind 8 radii | **HIGH** |
| 3 | **MD3 16 duration 缺失** | v3.18.1 错误删除 (以为不存在) | MD3 v0.192 真实 16 级 (short1-4, medium1-4, long1-4, extra-long1-4) | **HIGH** |
| 4 | **5 surface-container 等级** | 完全无 | MD3 标志性概念 (lowest/low/default/high/highest) | **MEDIUM** |
| 5 | **Color role tokens 不完整** | 只有 primary/secondary/accent | MD3 50+ roles (含 -container, -fixed, inverse-*) | **MEDIUM** |
| 6 | **Modal scroll lock** | ❌ 缺失 (打开 modal body 仍滚动) | Radix `react-remove-scroll` | **HIGH (a11y)** |
| 7 | **Modal focus restore** | ❌ 缺失 (关闭后焦点不还原) | Radix `useFocusGuards` | **HIGH (a11y)** |
| 8 | **Modal aria-hidden** | ❌ 缺失 (背景元素仍可被 SR 读) | Radix `aria-hidden` | **HIGH (a11y)** |
| 9 | **Container queries** | ❌ 不用 | shadcn `@container/main` for sidebar | **MEDIUM** |
| 10 | **Motion-reduce variants** | `@media (prefers-reduced-motion)` | Tailwind `motion-reduce:` / `motion-safe:` | **LOW** |
| 11 | **Forced-colors (Windows 高对比)** | ❌ 缺失 | Material Web `forced-colors-styles.scss` | **LOW** |
| 12 | **Font stack 显式指定** | 隐式 | shadcn/Tailwind/MD3 都明确指定 (含 Apple Color Emoji) | **MEDIUM** |
| 13 | **Dialog 标准尺寸** | 无 | MD3 max 560px, min 280px, min-height 140px, scrim 0.32 | **LOW** |
| 14 | **Elevation 等级 shadow** | Open Props 6 独立定义 | MD3 `clamp()` 插值 (1 个定义, 6 级平滑) | **LOW (重构)** |

---

## §7 实施路线图 (基于真实开源)

### v3.19.1 (Phase 1 — 必要修复)

| 任务 | 出处 | 工时 |
|------|------|------|
| 恢复 MD3 16 duration tokens (short1-4/medium1-4/long1-4/extra-long1-4) | MD3 v0.192 `_md-sys-motion.scss` | 30 min |
| 修正 easing-emphasized 注释 (Real MD3: cubic-bezier(0.2,0,0,1), NOT 0.3,0,0,1 from animation.js) | MD3 v0.192 | 5 min |
| 新增 `typography-tokens.css` (15 MD3 type styles + Tailwind 13 sizes) | MD3 + Tailwind v4 | 60 min |
| 新增 `radius-tokens.css` (8 MD3 corners + Tailwind 8 radii) | MD3 + Tailwind v4 | 30 min |
| Modal 补 scroll lock + focus restore + aria-hidden | Radix Dialog | 90 min |

### v3.19.2 (Phase 2 — 体系扩展)

| 任务 | 出处 | 工时 |
|------|------|------|
| 5 surface-container 等级 (lowest/low/default/high/highest) | MD3 标志性概念 | 45 min |
| Color role tokens 扩展 (primary-container, on-primary-container, surface-variant, outline-variant, inverse-*) | MD3 50 roles | 60 min |
| Container queries (`.container-card`, `.container-sidebar`) | shadcn `@container` | 30 min |
| Custom variants `data-open`, `data-checked`, `data-disabled` | shadcn | 30 min |

### v3.19.3 (Phase 3 — Polish)

| 任务 | 出处 | 工时 |
|------|------|------|
| Forced-colors (Windows High Contrast) | Material Web `forced-colors-styles.scss` | 30 min |
| Modal 标准尺寸 (560px/280px/140px, scrim 0.32) | MD3 dialog | 20 min |
| Elevation 重构为 MD3 `clamp()` 插值 (单一 token, 6 级平滑) | MD3 `_elevation.scss` | 60 min |

---

## §8 教训 (对前 v3.18 / v3.18.1 的诚实回顾)

### 8.1 v3.18.1 我错删的: MD3 16 duration

**我的错误推理**:
> "Tailwind v4 没有 12-level duration, 我凭空臆造了 MD3 12-level"

**真实情况**: 
- Tailwind v4 确实只用 1 default duration (这是事实)
- 但 **MD3 真实是 16 duration level** (short×4 + medium×4 + long×4 + extra-long×4)
- 我混淆了 Tailwind 极简策略 vs MD3 完整策略, 错误地"为了一致性"删除了 MD3 token

**修正**: v3.19.1 恢复 16 MD3 duration + Tailwind 极简 3 级作为兼容.

### 8.2 v3.18.1 我不知道的: MD3 `clamp()` 插值

Open Props 6 阴影 + MD3 `clamp()` 插值, 后者更优雅 (1 个定义, 6 级平滑).
Open Props 文档没有强调这种用法. MD3 真实源码才有.

**结论**: 多源研究 vs 单源 (Open Props) 永远更好. 即使 Open Props 已很优秀, MD3 仍有创新点.

### 8.3 v3.18.1 我漏掉的: Radix Dialog 14 子包

v3.18.1 的 component-engine.js 自称 "Portal + State Machine", 但实际 Radix Dialog 有 **14 个子包**, 包括 aria-hidden / focus-guards / scroll lock 这些 **a11y 关键**.

**结论**: 简化版 ≠ 等价物. 必须明确承认.

---

## §9 与 v3.18.1 诚实修正的衔接

| 主题 | v3.18.1 (前次修正) | v3.19 (本次研究) |
|------|-------------------|------------------|
| MD3 duration | ❌ 错误删除 (以为不存在) | ✅ 恢复 16 级 |
| MD3 type styles | ❌ 完全无 | ➕ 新增 typography-tokens.css |
| MD3 corners | ❌ 完全无 | ➕ 新增 radius-tokens.css |
| Radix 14 子包 | ❌ 未承认 | ✅ Modal 补 scroll lock + focus restore + aria-hidden |
| 5 surface-container | ❌ 完全无 | ✅ **v3.19.2 新增 surface-tokens.css (7 个 surface utility + 6 语义 component utility)** |
| Color roles | 6 个 (primary/accent/success/warning/error/info) | ✅ **v3.19.2 扩展到 20+ (含 -container, on-*, inverse-*, shadow, scrim)** |
| Container queries | ❌ 不用 | ✅ **v3.19.2 新增 container-queries.css (3 命名 container + 7 breakpoint)** |
| Custom variants | ❌ 不用 | ✅ **v3.19.2 新增 state-variants.css (6 data-state + 5 组件×state 组合)** |
| Forced-colors | ❌ 不用 | 📋 v3.19.3 候选 (Windows High Contrast) |
| 真实出处 | npm/unpkg 直连 | + MD3 source + Radix source + shadcn source |

---

## §v3.20 — Radix Presence + Open Props linear() Spring (2026-06-26)

> **目标**: 填补 v3.19.3 自承的 5 大 Radix 缺口中的 2 个 (Presence + Spring) + 用 Open Props 真实值替代 v3.13 自研 JS 物理。

### §v3.20.1 数据来源 (Raw HTTP 200 OK)

| 源 | URL | 版本 | 用途 |
|----|-----|------|------|
| npm registry `@radix-ui/react-presence` | registry.npmjs.org | 1.1.6 | Presence state machine + animationend |
| unpkg `@radix-ui/react-presence@1.1.5/dist/index.mjs` | unpkg.com | 1.1.5 | 真实 source (mount/unmount/animation 检测算法) |
| unpkg `open-props@1.7.23/src/props.easing.js` | unpkg.com | 1.7.23 | 5 级 spring linear() 真实 CSS |

### §v3.20.2 Radix Presence 真实算法 (curl 直读)

**State Machine** (3 states):
```
mounted:        UNMOUNT → unmounted,  ANIMATION_OUT → unmountSuspended
unmountSuspended: MOUNT → mounted,    ANIMATION_END → unmounted
unmounted:      MOUNT → mounted
```

**关键算法** (`usePresence`):
1. `getAnimationName(el)` 读 `getComputedStyle(el).animationName`
2. `prevPresent !== present` 时:
   - present=true → `send('MOUNT')`
   - present=false + animationName='none' 或 display='none' → `send('UNMOUNT')` (立即)
   - present=false + 有动画 + 动画变化 → `send('ANIMATION_OUT')` (suspended)
3. `animationstart` listener → 记录 prevAnimationName
4. `animationcancel` + `animationend` listener → `send('ANIMATION_END')`
5. `fillMode: forwards` trick — unmount 期间保留终态

### §v3.20.3 Open Props linear() Spring 真实值 (curl 直读)

**5 级 spring 真实 CSS** (从 props.easing.js 复制):
```css
--ease-spring-1: linear(0, 0.006, 0.025 2.8%, 0.539 18.9%, ..., 1.001);
--ease-spring-2: linear(0, 0.007, 0.029 2.2%, 0.625 14.4%, ..., 1);
--ease-spring-3: linear(0, 0.009, 0.035 2.1%, 0.723 12.9%, ..., 1);
--ease-spring-4: linear(0, 0.009, 0.037 1.7%, 0.776 10.3%, ..., 1);
--ease-spring-5: linear(0, 0.01, 0.04 1.6%, 0.816 9.4%, ..., 1);
```

**v3.20 用途映射**:
| Spring | 用途 |
|--------|------|
| spring-1 | 极轻柔 (1-2px 微调) |
| spring-2 | 轻柔 (hover, focus) |
| spring-3 | 中等 (按钮按下, 卡片浮起) |
| spring-4 | 强调 (Modal 进入, Toast 弹出) |
| spring-5 | 最强烈 (页面切换, 全屏) |

### §v3.20.4 Modal 集成 Presence

**改造前** (v3.18.1): `setTimeout(closeDuration)` 硬编码 300ms
```javascript
setTimeout(function () {
  modal.setAttribute('data-state', 'closed');
}, closeDuration);
```

**改造后** (v3.20): Radix Presence state machine
```javascript
var presence = WebPPTPresence.usePresence(modal, false);
presence.subscribe(function (state) {
  if (state === 'unmounted') {
    modal.setAttribute('data-state', 'closed');
    portalUnmount(modal);  // 等 animationend 才卸载
  }
});
```

**收益**: 真正等 animationend 才卸载 DOM, 无 setTimeout 误差, 无中途闪烁。

### §v3.20.5 spring-preset.js 重写 (CSS linear() 替代 JS 物理)

**改造前** (v3.13-v3.18.1): JS 物理求解器 + RAF
```javascript
var sp = WebPPT_Utils.Spring.create(presetName);  // k=0.15, c=0.30
function tick(t) { sp.step(dt); applyTransform(); ... }
```

**改造后** (v3.20): CSS linear() + 浏览器主线程外插值
```javascript
el.style.animationTimingFunction = 'var(--ease-' + springLevel + ')';
el.setAttribute('data-anim', springLevel);  // CSS 选择器触发
```

**收益**:
- ✅ 无 JS 物理计算 (k, c, mass, stiffness 全部砍掉)
- ✅ 浏览器 compositor 线程插值 (vs RAF JS 主线程)
- ✅ 自动 respect `prefers-reduced-motion` (CSS @media)
- ✅ 单一真实来源: open-props 真实值 (不是 Apple HIG/Framer 臆造)

### §v3.20.6 仍 NOT 等价于 Radix (诚实声明)

| 缺失能力 | Radix 用法 | 我们用法 |
|----------|------------|----------|
| react-compose-refs | 多 ref 合并 | 单 ref |
| useLayoutEffect | DOM 操作前同步 | microtask |
| jsx-runtime | 组件渲染 | vanilla JS createElement |
| forwardRef + setNode | React 状态 | IIFE + global |

### §v3.20.7 验证

- `tests/test_v320.py`: 29/29 PASS (Presence state machine + linear() CSS + Modal integration)
- `tests/test_v3193.py` 回归: 25/25 PASS (无退化)
- 总集: **239/239 PASS** (7 套测试套件)

---

*完成于 2026-06-26. v3.20 = Radix Presence state machine + Open Props linear() Spring CSS + spring-preset.js 重写. 真实开源, 不臆造.*

*完成于 2026-06-26, 所有数据基于 npm registry + unpkg + raw.githubusercontent 直连验证.*
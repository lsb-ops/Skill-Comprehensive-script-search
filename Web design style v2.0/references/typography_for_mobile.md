# 移动端字体与排版指南

> **来源**: iOS HIG + Material Design + 移动端设计经验
> **适用**: WebPPT Maker 的 HTML 网页
> **版本**: 1.0.0 (2026-06-25)

---

## 一、字号体系

### 1.1 移动端基准字号

| 用途 | 字号 | 备注 |
|------|------|------|
| 封面标题 | 42-48px | 视频封面要"抢眼" |
| 页面标题 | 28-36px | 主标题 |
| 副标题 | 20-24px | 解释标题 |
| 正文 | 20-24px | 移动端最小可读 |
| 辅助文字 | 14-16px | 注释/来源 |

### 1.2 推荐字号映射

```css
:root {
  --font-size-base: 24px;   /* 正文 */
  --font-size-h1: 36px;     /* 主标题 */
  --font-size-h2: 28px;     /* 副标题 */
  --font-size-body: 20px;   /* 描述 */
  --font-size-caption: 16px; /* 注释 */
  --font-size-poster: 48px; /* 大字报 */
  --font-size-number: 96px; /* 数字风 */
}
```

---

## 二、字体选择

### 2.1 中文

| 字体 | 风格 | 适用 |
|------|------|------|
| **PingFang SC** | 默认，无衬线 | 通用 |
| **Hiragino Sans GB** | 备用 | macOS 旧版 |
| **Microsoft YaHei** | 备用 | Windows |
| **Source Han Sans** | 开源 | 跨平台 |
| **Noto Sans SC** | Google | 网页 |

### 2.2 英文

| 字体 | 风格 | 适用 |
|------|------|------|
| **SF Pro Display** | Apple 默认 | iOS |
| **Helvetica Neue** | 经典 | 通用 |
| **Inter** | 现代 | 网页 |
| **Roboto** | Google | Android |

### 2.3 数字 / 等宽

| 字体 | 用途 |
|------|------|
| **SF Mono** | 代码、编号 |
| **JetBrains Mono** | 代码 |
| **DIN** | 数据展示 |

### 2.4 推荐字体栈

```css
/* 中文优先 */
font-family: -apple-system, BlinkMacSystemFont, "PingFang SC",
             "Hiragino Sans GB", "Microsoft YaHei", "Source Han Sans SC",
             "Noto Sans SC", sans-serif;

/* 英文优先 */
font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display",
             "Helvetica Neue", "Inter", sans-serif;

/* 数字优先 */
font-family: "SF Mono", "JetBrains Mono", "DIN", monospace;
```

---

## 三、行距与字距

### 3.1 行距（line-height）

```css
/* 中文：1.5-1.7 倍行距 */
.body { line-height: 1.6; }

/* 英文：1.4-1.6 倍行距 */
.body-en { line-height: 1.5; }

/* 大字标题：1.1-1.3 倍 */
.title { line-height: 1.2; }
```

### 3.2 字距（letter-spacing）

```css
/* 中文默认 */
.title { letter-spacing: 0; }

/* 英文标题：负字距显得紧凑 */
.title-en { letter-spacing: -0.5px; }

/* 大字报：负字距 */
.poster { letter-spacing: -1px; }
```

### 3.3 段落间距

```css
/* 段落之间 */
p + p { margin-top: 16px; }

/* 标题与正文 */
h2 + p { margin-top: 12px; }

/* 卡片内边距 */
.card { padding: 32px 24px; }
```

---

## 四、颜色与对比度

### 4.1 WCAG 对比度标准

| 等级 | 对比度 | 适用 |
|------|--------|------|
| AAA | 7:1 | 正文（小字） |
| AA | 4.5:1 | 正文（标准） |
| AA Large | 3:1 | 大字（≥18px） |

### 4.2 推荐配色对比度

```
#000000 on #FFFFFF = 21:1   ✅ AAA
#666666 on #FFFFFF = 5.7:1 ✅ AA
#999999 on #FFFFFF = 2.85:1 ❌ 不达标
```

**反模式**:
- ❌ 浅灰文字 on 浅色背景（看不清）
- ❌ 高饱和度文字 on 同饱和度背景（刺眼）

---

## 五、响应式设计

### 5.1 Viewport 设置

```html
<meta name="viewport" content="width=360, initial-scale=1, maximum-scale=1, user-scalable=no">
```

**为什么 width=360**：
- 抖音视频拍摄标准 = 1080×1920 (3 倍 DPR)
- 渲染尺寸 = 360×640
- 锁定 viewport 避免被缩放

### 5.2 使用 rem + vw 混合

```css
/* 基于 360 视口 */
.title { font-size: 10vw; }  /* 360 视口下 = 36px */
.body { font-size: 5.5vw; }   /* 360 视口下 = 20px */

/* 或基于 16px 根字号 */
html { font-size: 16px; }
.title { font-size: 2.25rem; } /* = 36px */
```

### 5.3 移动端适配检查清单

- [ ] viewport 设置正确
- [ ] 字号 ≥ 16px（小字）
- [ ] 字号 ≥ 24px（正文）
- [ ] 行距 ≥ 1.4 倍
- [ ] 点击区域 ≥ 44×44pt（iOS）
- [ ] 颜色对比度 ≥ AA
- [ ] 横向滚动禁止（除非必要）

---

## 六、动画与交互

### 6.1 翻页动画（推荐）

```css
.page {
  transition: transform 0.3s ease, opacity 0.3s ease;
}
.page.active {
  transform: translateY(0);
  opacity: 1;
}
.page.hidden {
  transform: translateY(20px);
  opacity: 0;
}
```

### 6.2 微交互

```css
/* 按钮点击 */
button:active { transform: scale(0.96); }

/* 卡片悬浮 */
.card:hover { transform: translateY(-4px); }

/* 进度条 */
.progress { transition: width 0.3s ease; }
```

### 6.3 减少动画（a11y）

```css
@media (prefers-reduced-motion: reduce) {
  * { transition: none !important; animation: none !important; }
}
```

---

## 七、可访问性（A11y）

### 7.1 基础要求

- [ ] 所有文字使用真实文字（非图片）
- [ ] 颜色对比度 ≥ AA
- [ ] 焦点状态明显
- [ ] 触摸目标 ≥ 44×44pt

### 7.2 屏幕阅读器

```html
<h1 aria-level="1">主标题</h1>
<section aria-label="第 2 页: 真相 1">...</section>
<button aria-label="下一页">→</button>
```

---

## 八、字体性能优化

### 8.1 字体子集化

```bash
# 使用 fonttools 子集化
pyftsubset NotoSansSC-Regular.ttf \
  --text="你好的我是在不有这" \
  --output-file=NotoSansSC-subset.ttf
```

### 8.2 字体加载策略

```css
/* 优先系统字体 */
font-family: -apple-system, "PingFang SC", sans-serif;

/* 自托管字体 */
@font-face {
  font-family: 'MyFont';
  src: url('/fonts/myfont.woff2') format('woff2');
  font-display: swap;  /* 避免 FOIT */
}
```

---

## 九、常见错误

| 错误 | 后果 | 修正 |
|------|------|------|
| 字号太小 (<16px) | 看不清 | ≥24px 正文 |
| 行距太密 (<1.3) | 难阅读 | ≥1.5 倍行距 |
| 颜色对比度低 | 看不清 | ≥AA 4.5:1 |
| 字体太多 (>3 种) | 视觉杂乱 | ≤2 种字体 |
| 横向滚动 | 移动端灾难 | 锁定 viewport |
| 全大写英文 | 难阅读 | 仅标题用 |
| 中文英文之间无空格 | 不美观 | 加半角空格 |

---

## 十、参考资料

- [iOS Human Interface Guidelines - Typography](https://developer.apple.com/design/human-interface-guidelines/typography)
- [Material Design - Type Scale](https://m3.material.io/styles/typography/type-scale-tokens)
- [Google Fonts - 中文](https://fonts.google.com/noto/specimen/Noto+Sans+SC)
- [Web Content Accessibility Guidelines (WCAG) 2.1](https://www.w3.org/TR/WCAG21/)

---

*本指南 = WebPPT Maker HTML 模板的字体决策依据。所有字号、字体、行距均按此标准实现。*
# 设计美学参考 · 9 种排版美学

> **来源**: 移动端 PPT 设计经验 + 设计系统研究
> **适用**: WebPPT Maker 的 layout 参数选择
> **版本**: 1.0.0 (2026-06-25)

---

## 一、为什么排版美学重要？

抖音视频的**前 3 秒**决定留存率。但**前 3 秒之外**的视觉节奏，决定**完播率**。

好的排版美学 = 让观众"不知不觉看下去"，不退出。

---

## 二、9 种排版美学详解

### 1. 卡片式（Card）

**适用场景**: 知识科普、要点罗列、清单类内容

**视觉特征**:
- 每页一个大卡片（圆角 + 阴影）
- 卡片内有数字编号 + 标题
- 背景简洁，聚焦内容

**CSS 关键**:
```css
.card {
  background: var(--bg-secondary);
  border-radius: 24px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  padding: 32px;
}
.number {
  background: var(--accent);
  color: white;
  border-radius: 50%;
  width: 48px; height: 48px;
  line-height: 48px;
}
```

**抖音应用**:
- 视频号"每天一个知识点"
- 罗永浩的"清单体"
- 适合"5 个真相"、"3 招"等结构化内容

---

### 2. 大字报（Poster）

**适用场景**: 强观点、情绪化、反差内容

**视觉特征**:
- 整页 = 一句大文字（字号 48-64px）
- 加粗 + 高对比色背景
- 辅助小图标

**CSS 关键**:
```css
.big-text {
  font-size: 48px;
  font-weight: 900;
  line-height: 1.2;
  letter-spacing: -1px;
}
```

**抖音应用**:
- 刘润的"日签"风格
- 半佛仙人的"惊悚体"
- 适合金句、颠覆性观点

---

### 3. 时间轴（Timeline）

**适用场景**: 故事叙述、过程展示、成长记录

**视觉特征**:
- 左侧时间点（小圆点 + 文字）
- 右侧事件描述
- 视觉引导线（可选）

**CSS 关键**:
```css
.timeline-item {
  display: flex;
  gap: 16px;
}
.timeline-dot {
  width: 12px; height: 12px;
  border-radius: 50%;
  background: var(--accent);
}
```

**抖音应用**:
- "30 天挑战"
- "90 天转行"
- 个人成长 Vlog

---

### 4. 瀑布流（Waterfall）

**适用场景**: 多观点并列、信息密度高

**视觉特征**:
- 上中下三层
- 顶部 = 核心结论
- 中部 = 关键论据
- 底部 = 行动号召

**CSS 关键**:
```css
.waterfall { display: flex; flex-direction: column; gap: 16px; }
.waterfall-top { font-size: 32px; font-weight: 900; }
.waterfall-mid { font-size: 20px; color: var(--text-secondary); }
.waterfall-bottom { font-size: 24px; color: var(--accent); }
```

**抖音应用**:
- "深度分析"类
- "为什么 XX" 类
- 财经/商业分析

---

### 5. 数字风（Numbers）

**适用场景**: 数据展示、排行榜、对比分析

**视觉特征**:
- 大数字（80-120px）占主视觉
- 副标题小字说明
- 数据来源标注

**CSS 关键**:
```css
.big-number {
  font-size: 96px;
  font-weight: 900;
  color: var(--accent);
  line-height: 1;
}
```

**抖音应用**:
- "中国 XX 数据"
- "全球 XX 排行"
- 适合财经、科普类

---

### 6. 对比式（Compare）

**适用场景**: 前后对比、好坏对比、新旧对比

**视觉特征**:
- 左右分栏（或上下分栏）
- 左右/上下有明确分隔
- 中间可用箭头或 VS

**CSS 关键**:
```css
.compare {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 16px;
  align-items: center;
}
```

**抖音应用**:
- "减肥前后"
- "装修前后"
- "学习方法对比"

---

### 7. 图标式（Icon）

**适用场景**: 概念解释、品牌介绍

**视觉特征**:
- 中央大图标（80-120px）
- 周围文字围绕
- 图标 + 文字一体化

**CSS 关键**:
```css
.icon-large {
  width: 100px; height: 100px;
  margin-bottom: 24px;
}
```

**抖音应用**:
- App 推荐
- 工具介绍
- 适合视觉化内容

---

### 8. 故事线（Storyline）

**适用场景**: 连续剧情、叙事推进

**视觉特征**:
- 顶部剧情线（横向进度条）
- 中部当前剧情画面
- 底部文字说明

**CSS 关键**:
```css
.storyline-track {
  height: 4px;
  background: var(--accent);
  transition: width 0.3s;
}
```

**抖音应用**:
- 连续剧解说
- "故事会"风格
- 适合剧情号

---

### 9. 问答式（Q&A）

**适用场景**: 答疑、FAQ、知识解释

**视觉特征**:
- 顶部 = 问题（大字）
- 分隔线
- 底部 = 答案（小字 + 详细）

**CSS 关键**:
```css
.q { font-size: 32px; font-weight: 700; }
.divider { border-top: 2px dashed var(--border); margin: 24px 0; }
.a { font-size: 20px; line-height: 1.6; }
```

**抖音应用**:
- "你不知道的 XX"
- "为什么 XX"
- 知识科普

---

## 三、排版美学选择决策树

```
你的内容是？
├── 多个并列要点（3-8 个）
│   ├── 简单 → 卡片式
│   └── 复杂 → 时间轴 / 瀑布
├── 强观点 / 情绪化
│   └── 大字报
├── 数据展示
│   └── 数字风
├── 对比分析
│   └── 对比式
├── 故事叙述
│   └── 时间轴 / 故事线
├── 概念解释
│   └── 图标式 / 问答式
└── 不确定
    └── auto → 默认卡片式
```

---

## 四、排版美学 × 风格 × 配色 三维矩阵

| 排版 | 推荐风格 | 推荐配色 |
|------|----------|----------|
| 卡片 | 知识科普 | 深海蓝 |
| 大字报 | 故事叙述 | 暖阳橙 |
| 时间轴 | 故事叙述 | 暖阳橙 |
| 瀑布 | 现代简约 | 极简黑白 |
| 数字 | 知识科普 | 深海蓝 |
| 对比 | 故事叙述 | 暖阳橙 |
| 图标 | 科技未来 | 赛博朋克 |
| 故事线 | 故事叙述 | 莫兰迪 |
| 问答 | 知识科普 | 深海蓝 |

---

## 五、视觉节奏建议

**节奏曲线**:
```
前 3s    →  钩子 (大字报/对比)
3-7s    →  主体 (卡片/时间轴)
中段    →  展开 (瀑布/数字)
结尾    →  CTA (大字报)
```

**反模式**:
- ❌ 全程同一排版（视觉疲劳）
- ❌ 每页换排版（视觉混乱）
- ❌ 排版与内容不匹配（如数字风讲情感）

---

## 六、A/B 测试建议

为同一内容生成 2-3 种排版，看哪种完播率高：

```python
# generate_html.py 增加 --ab-test 参数
python3 generate_html.py --topic "..." --points [...] --ab-test card,poster,timeline
# → 输出 3 个文件夹，比较效果
```

---

## 七、未来扩展

- [ ] 3D 排版（CSS transform）
- [ ] 动态排版（CSS animation）
- [ ] 视频化排版（背景视频）
- [ ] AI 自动选择排版（基于内容语义）

---

*本设计美学参考 = WebPPT Maker 的视觉决策依据。所有排版均在 templates/html_page_template.html 中实现。*
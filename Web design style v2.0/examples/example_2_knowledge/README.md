# 示例 2 · 知识科普类 · 每天喝咖啡的真相

## 这个示例在做什么

> **场景**: 科普"每天喝咖啡的 3 个真相"，破除"咖啡脱水"的谣言
>
> **关键卖点**: 真相 1 反直觉 + 真相 3 提醒适量

## 内容参数

| 参数 | 值 | 原因 |
|------|------|------|
| `style` | 知识科普 | 浅蓝 + 信息图 = 专业 + 信任 |
| `color_scheme` | 深海蓝 | 医疗/科学感 |
| `layout` | 数字 | 强调"3 个真相"结构 |
| `target_duration_sec` | 30 | 3 个真相刚好 |

## 一键运行

```bash
bash scripts/run_all.sh \
  --config examples/example_2_knowledge/content.json \
  --output-dir examples/example_2_knowledge/output
```

跑完后看 `examples/example_2_knowledge/output/`。

## 预期产物

- **5 页 PPT**: 封面 + 3 真相 + CTA
- **配色**: 深海蓝主色 + 亮蓝 accent
- **排版**: 数字风（大数字 "1" "2" "3"）

## 学到的

- 知识科普类用"真相"作为钩子词
- 数字风排版适合"3 个 / 5 个"这种结构
- 深海蓝配色让科学类内容更可信

# SVG Icon 库目录

> v3.0 新增 · 替代 v1.x emoji (`visual_element` 字段)
> Anti-slop 规则: taste-skill 禁止 generic emoji, 改用具体领域 SVG

## 已实现 (20 个)

| 文件 | 含义 | 适用 |
|------|------|------|
| `lightbulb.svg` | 灯泡 · 想法/创意 | 知识科普, 教程 |
| `shield.svg` | 盾牌 · 保护/守护 | 安全, 防御 |
| `gear.svg` | 齿轮 · 配置/系统 | 工具, 设置 |
| `brain.svg` | 大脑 · 智能/思考 | AI, 记忆, 认知 |
| `lightning.svg` | 闪电 · 速度/能量 | 性能, 速度, 力量 |
| `checkmark.svg` | 勾 · 完成/确认 | 成功, 通过 |
| `rocket.svg` | 火箭 · 启动/增长 | 产品, 业务, 增长 |
| `diamond.svg` | 钻石 · 价值/品质 | 高级, 价值, 精华 |
| `book.svg` | 书 · 知识/学习 | 教育, 教程 |
| `clock.svg` | 时钟 · 时间/计时 | 时间, 等待 |
| `heart.svg` | 心 · 喜爱/情感 | 情感, 健康, 关怀 |
| `star.svg` | 星 · 评分/明星 | 推荐, 评价 |
| `flag.svg` | 旗 · 标记/里程碑 | 目标, 节点 |
| `chat.svg` | 对话 · 沟通/客服 | 评论, 互动, 客服 |
| `key.svg` | 钥匙 · 权限/关键 | 安全, 权限, 关键 |
| `wrench.svg` | 扳手 · 工具/修复 | 工具, 维护, 设置 |
| `fire.svg` | 火 · 火热/紧急 | 热点, 紧急, 流量 |
| `chart.svg` | 图表 · 数据/分析 | 数据, 增长, 报告 |
| `eye.svg` | 眼睛 · 观察/洞察 | 视觉, 监控, 分析 |
| `target.svg` | 靶 · 目标/精准 | 目标, KPI, 命中 |

## 使用方式

```python
# generate_html.py
if point.get("visual_element", "").endswith(".svg"):
    icon_path = f"assets/icons/{point['visual_element']}"
    # 在 HTML 中引用 <img src="...">
```

## 待补全 (P2 候选)

30+ 常用图标待补: camera, microphone, music, video, download, upload, share, lock, unlock, user, users, settings, search, filter, calendar, location, etc.

详见 taste-skill/skills/imagegen-frontend-web/skills/icons/catalog.md 借鉴.
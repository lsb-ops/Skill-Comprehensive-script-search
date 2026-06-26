# 分镜头脚本优化器 (Storyboard Shot Optimizer)

AI驱动的分镜头脚本优化工具，支持景别优化、人物表情优化、动作优化、镜头完善。

## 核心功能

- **景别优化**: 远景/中景/近景/特写智能选择与切换
- **表情优化**: 人物情绪细节丰富和层次优化
- **动作优化**: 动作描写从模糊到具体的优化
- **镜头完善**: 镜头运动、转场、角度的优化建议
- **调研支持**: 集成16个搜索引擎，可进行全球 cinematography 调研

## 安装

将整个 `storyboard-shot-optimizer` 目录添加到 Agent 的 Skills 路径即可。

## 使用方法

### 基础调用

```
请优化以下分镜头脚本:
镜头1: 主角走进房间，看到空荡荡的办公桌，震惊地停下脚步。
镜头2: 特写他的表情，眉头紧皱，嘴唇颤抖。
```

### 带参数调用

```markdown
/opt storyboard-shot-optimizer
--input 镜头1: ...
--optimize all
--style cinematic
--depth normal
```

## 文件结构

```
storyboard-shot-optimizer/
├── SKILL.md              # 主文档
├── _meta.json            # 元数据
├── metadata.json         # 详细配置
├── README.md             # 说明文档
├── tools/
│   └── 搜索引擎/
│       ├── search.py     # 搜索引擎脚本
│       └── 配置.json     # 引擎配置
└── references/           # 参考文档(可选)
```

## 搜索引擎工具

### 命令行调用

```bash
# 搜索景别相关资料
python3 tools/搜索引擎/search.py --query "cinematography shot composition" --engines Google,Baidu --count 5

# 搜索表情表演相关
python3 tools/搜索引擎/search.py --query "facial expression acting" --region global --count 10

# 中文搜索
python3 tools/搜索引擎/search.py --query "分镜头 景别 规则" --region cn --count 5
```

## 优化输出示例

输入:
```
镜头1: 主角走进房间，看到空荡荡的办公桌，震惊地停下脚步。
```

输出:
```json
{
  "shot_id": 1,
  "optimized": {
    "shot_type": "中景 → 远景",
    "shot_angle": "平视 → 低角度微仰",
    "camera_movement": "缓慢推近",
    "action": "走进房间 → 脚步放缓，目光由远及近扫视至办公桌",
    "expression": "震惊 → 震惊逐渐凝固为不安",
    "emotion_curve": "↑↑↑ 震惊"
  },
  "reason": "远景开场交代压抑氛围，低角度增强主角渺小感"
}
```

## 版本

v1.0.0 - 2026-06-01

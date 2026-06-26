# 企业宣传片生成器 - 经验教训记录

> 记录追问过程中的洞察、纠正和最佳实践

---

## 记录格式

```markdown
## [LRN-YYYYMMDD-XXX] category

**时间**: ISO-8601
**优先级**: low | medium | high | critical
**状态**: pending | resolved | promoted
**领域**: dimensions | narrative | questions | output | memory

### Summary
一句话描述

### Details
详细上下文

### Suggested Action
具体改进建议

---
```

## 记录分类

| 类型 | 说明 | 触发场景 |
|------|------|----------|
| `correction` | 用户纠正 | 回答被纠正时 |
| `insight` | 关键洞察 | 追问获得重要信息时 |
| `best_practice` | 最佳实践 | 问题特别有效时 |
| `error` | 错误 | 生成效果不理想时 |
| `knowledge_gap` | 知识缺口 | 发现信息不完整时 |

## 优先级说明

| 优先级 | 适用场景 |
|--------|----------|
| `low` | 轻微改进建议 |
| `medium` | 一般优化 |
| `high` | 重要改进，影响生成质量 |
| `critical` | 必须修复，影响功能 |

---

## 经验教训示例

### 示例1：追问技巧

```markdown
## [LRN-20260528-001] best_practice

**时间**: 2026-05-28T10:00:00Z
**优先级**: high
**状态**: pending
**领域**: questions

### Summary
"一句话介绍"是很好的开场问题

### Details
在Wave 1中使用"用一句话介绍公司"作为开场问题，
比直接问"公司名称、行业、业务"效果更好。
用户更愿意展开回答，信息量更丰富。

### Suggested Action
将"一句话介绍"作为企业介绍维度的首个问题

---
```

### 示例2：叙事洞察

```markdown
## [LRN-20260528-002] insight

**时间**: 2026-05-28T11:00:00Z
**优先级**: high
**状态**: pending
**领域**: narrative

### Summary
创始人故事比产品数据更能引发情感共鸣

### Details
当用户回答"为什么创业"时，用STAR法则深挖后，
生成的文案情感得分比直接罗列产品数据的版本高47%。

### Suggested Action
在Wave 2加入创始人动机深挖，作为必问项

---
```

### 示例3：纠正记录

```markdown
## [LRN-20260528-003] correction

**时间**: 2026-05-28T12:00:00Z
**优先级**: medium
**状态**: pending
**领域**: dimensions

### Summary
对"行业地位"的判断需要客观数据支撑

### Details
用户说"行业领先"，追问后发现实际上市场份额只有8%。
之前的生成基于用户主观判断，导致文案过于夸大。

### Suggested Action
在询问行业地位时，追问具体数字，并建议使用"行业主流供应商"等客观描述

---
```

---

## 待处理项

<!-- 待处理的经验教训 -->

---

## 已处理项

<!-- 已解决或已升级的经验教训 -->

---

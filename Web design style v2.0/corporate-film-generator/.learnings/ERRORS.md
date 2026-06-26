# 企业宣传片生成器 - 错误记录

> 记录生成过程中的错误和失败模式

---

## 记录格式

```markdown
## [ERR-YYYYMMDD-XXX] context

**时间**: ISO-8601
**优先级**: high | critical
**状态**: pending | resolved
**领域**: narrative | memory | generation | questions

### Summary
错误描述

### Error
```
错误信息或输出
```

### Context
- 操作/命令
- 输入或参数
- 环境详情

### Suggested Fix
可能的解决方案

---
```

## 常见错误类型

| 类型 | 说明 |
|------|------|
| `narrative` | 叙事结构问题 |
| `memory` | 记忆系统问题 |
| `generation` | 生成质量问题 |
| `questions` | 追问逻辑问题 |

---

## 错误日志

<!-- 错误记录 -->

---

# Writing Guidelines · 4 failure type → 4 form

> 借鉴自 superpowers/skills/writing-skills/SKILL.md:459-543
> 用于决定 SKILL.md / verify 提示用什么句式

---

## 4 种 failure type

| Failure | 含义 | 例子 |
|---------|------|------|
| **知识缺口** | 用户不知道该怎么做 | "如何选 portrait/landscape?" |
| **错误倾向** | 用户会自然做错 | "9:16 在桌面端会很丑" |
| **不一致** | 用户每次输出格式不同 | title 可能 18/22/30 字 |
| **遗漏步骤** | 用户会跳过 | "忘了加 reveal.js" |

---

## 4 种 form 模板

### 1. Prohibition (禁用规则)

**适用**: 错误倾向, 一旦违反产物损坏

```markdown
❌ 禁用 X
   Why: Y (具体损失)
   How: 用 Z 替代
```

**示例**:
```markdown
❌ 禁用纯黑 #000000
   Why: 没有层次感, 视觉扁平 (taste-skill Anti-Slop)
   How: 用 #1a1a1a (近黑) 替代
```

---

### 2. Recipe (操作步骤)

**适用**: 知识缺口, 多步骤流程

```markdown
To do X:
1. Step A
2. Step B
3. Verify: 检查 C
```

**示例**:
```markdown
To 生成 dual-mode PPT:
1. `bash scripts/run_all.sh --mode dual --config content.json`
2. 检查 `output/portrait/` 和 `output/landscape/` 都存在
3. `bash scripts/verify.sh --output-dir output/` 期望 50+/50+
```

---

### 3. REQUIRED slot (必填字段)

**适用**: 不一致, 必须有特定字段

```markdown
REQUIRED in content_point:
- `id` (e.g., "p01")
- `narrative_role` (attention/interest/action/emotion/satisfaction)
```

**示例**:
```markdown
REQUIRED in content.json:
- `topic` (string, ≤ 30 字)
- `content_points` (array, 3-8 个)
- `output_dir` (string, 绝对路径)
```

---

### 4. Conditional (条件分支)

**适用**: 上下文相关, 给出 if-then 决策

```markdown
If 用户要发抖音: 用 portrait 模式
If 用户要做分享: 用 landscape 模式
If 用户不确定: 用 dual 模式 (默认)
```

**示例**:
```markdown
If variance ≥ 7: 强制每页 layout 不同
If variance 4-6: 2-3 种 layout 轮换
If variance ≤ 3: 统一 layout-card
```

---

## Iron Law: NO SKILL WITHOUT FAILING TEST FIRST

> 借鉴自 superpowers/writing-skills/SKILL.md:30-44

任何 SKILL.md 新规则都必须:
1. 先写一个压力测试场景 (pressure scenario)
2. 看 agent 不带 skill 时失败
3. 写最小 skill 规则
4. 验证 agent 带 skill 时通过
5. **不满足以上 4 步 → 该规则不写进 skill**

---

## Bulletproofing (防绕过)

### Rationalization Table (反绕过表)

针对常见"我以为这样也行"：

| 借口 | 反驳 |
|------|------|
| "用户看不到 HTML 源码" | 截图会暴露 layout 问题 |
| "反正输出能用" | N1 失败=0 价值 |
| "加 reveal.js 太麻烦" | 不用 reveal.js 就不是动态 |
| "variance=10 太激进" | 用户明确选择要遵守 |

### Red Flags (红旗)

- 🚩 "差不多就行"
- 🚩 "用户大概不会用这个"
- 🚩 "先这样吧, 后面再说"
- 🚩 "我觉得 9:16 够了"

---

## Micro-testing (微测试)

任何规则加进 skill 前, 跑 ≥5 次微测试:
1. 不带 skill 跑 (control)
2. 带 skill 跑 (treatment)
3. 对比差异
4. 验证 skill 真的改进输出

---

## 5 步 Gate Function (verify 模板)

借鉴 superpowers/verification-before-completion:

```
1. IDENTIFY  — 声明完成什么
   e.g., "生成 9:16 + 16:9 双模式 HTML, 50+ verify PASS"

2. RUN       — 执行命令
   e.g., `bash scripts/run_all.sh --mode dual --config tests/v3.json`

3. READ      — 检查输出
   e.g., `ls output/portrait/ output/landscape/`

4. VERIFY    — 比对声明
   e.g., 50+ checks PASS, I1-I5 全绿

5. ONLY THEN — 标记 done_verified
   e.g., `status: done_verified`
```

---

## 持续迭代

任何 SKILL.md 规则, 3 次被绕过 → 升级到 prohibition (HR 类)
任何 prohibition 被成功绕过 → 立刻修复 (P0 优先级)
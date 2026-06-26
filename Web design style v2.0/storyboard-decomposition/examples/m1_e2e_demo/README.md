# m1_e2e_demo — 真实端到端示例

## 目的

演示完整流水线：M1 解析 → M2 分镜设计 → M3 提示词生成，
用真实 EP01 数据验证工程化版本可重现 11 镜 v3.5 结构。

## 文件

- `00_input_script.md` — EP01 源数据（分镜头脚本）
- `01_run_demo.sh` — 一键演示脚本
- `output/` — 运行后生成的产物

## 使用

```bash
./01_run_demo.sh
```

## 预期输出

- M1: 6 个场景 + 2 个核心人物
- M2: 8 镜 / 60s / 3 CUE（开篇风格切换 / 中段教化升级 / 升华）
- M3: 8 个 txt 骨架（待 LLM 填充画面描述段）

## 重要说明

**输入限制**：本示例以"分镜头脚本"作为输入，但 M1 解析器
是为"原始剧本"（小说/大纲/分场）设计的。

如果需要从"分镜头脚本"反向解析，需要 LLM 介入（M1 的 LLM 增强模式）。
当前 M1 启发式对分镜头表的解析准确度有限，预期 50-70%。

**最佳实践**：M1 输入应该是源剧本（不含镜头表），不是分镜头脚本。

## 真实使用流程

1. 用户提供源剧本（小说/大纲/分场）
2. `python3 scripts/m1_parse.py source.md m1.json` → M1 解析
3. `python3 scripts/m2_design.py m1.json m2.json --total-duration 60` → M2 分镜
4. `python3 scripts/m3_generate.py m2.json m1.json --out-dir ./prompts` → M3 骨架
5. 把 ./prompts/镜*.txt 发给 LLM，让它填充【画面描述】段
6. LLM 填充后，用 `python3 scripts/validate_prompt.py *.txt` 校验
7. 用 `python3 scripts/continuity_check.py ./prompts` 检查跨镜衔接

## 已知问题

- M1 启发式对"分镜头表"输入解析不准（识别为场景而非角色/动作）
- M3 骨架阶段字数偏少（~700 字），LLM 填充后应达 ≤1800 字（v3.7 治本）
- M4 衔接校验依赖 prompt 质量，骨架阶段会报告大量问题（预期）

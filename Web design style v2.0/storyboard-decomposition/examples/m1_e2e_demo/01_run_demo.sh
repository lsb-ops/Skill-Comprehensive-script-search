#!/usr/bin/env bash
# 01_run_demo.sh — m1_e2e_demo 演示
#
# 流程：
#   1. 跑 run_skill.sh（输入 EP01 源剧本）
#   2. 显示 M1/M2/M3 关键输出
#   3. 对比 11 镜 v3.5 真实数据（examples/example-古早霸总-EP01/）
#
# 用法:
#   ./01_run_demo.sh

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SCRIPTS="$(dirname "$SCRIPT_DIR")/../scripts"
EXAMPLE_DIR="$(dirname "$SCRIPT_DIR")/example-古早霸总-EP01"
OUTPUT_DIR="$SCRIPT_DIR/output"

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${BLUE}[DEMO]${NC} $1"; }
log_ok() { echo -e "${GREEN}✓${NC} $1"; }
log_warn() { echo -e "${YELLOW}⚠${NC} $1"; }

# === 1. 跑流水线 ===

log "═══════════════════════════════════════"
log "📚 m1_e2e_demo: 跑真实 EP01 源剧本"
log "═══════════════════════════════════════"

rm -rf "$OUTPUT_DIR"
"$SKILL_SCRIPTS/run_skill.sh" "$SCRIPT_DIR/00_input_script.md" \
    --output-dir "$OUTPUT_DIR" \
    --style 古早霸总 \
    --total-duration 60 \
    --skip-m4 2>&1 | grep -E "(✅|❌|⚠|完成|失败|→)" | sed 's/^/  /'

# === 2. 显示 M1 关键输出 ===

log ""
log "═══════════════════════════════════════"
log "📊 M1 输出概览"
log "═══════════════════════════════════════"

python3 -c "
import json
d = json.load(open('$OUTPUT_DIR/m1/m1_output.json'))
print(f'  标题: {d[\"script_meta\"][\"title\"]}')
print(f'  风格: {d[\"style\"]}')
print(f'  场景数: {len(d[\"scenes\"])}')
print(f'  人物数: {len(d[\"characters\"])}')
print(f'  对白数: {len(d[\"dialogue\"])}')
print()
print('  场景列表:')
for s in d['scenes']:
    chars = ', '.join(s.get('characters', []))
    print(f'    {s[\"id\"]} [{s.get(\"time\", \"?\")}] {s[\"location\"]} (人物: {chars})')
print()
print('  人物清单:')
for c in d['characters']:
    print(f'    {c[\"id\"]} {c[\"name\"]} ({c[\"role\"]}, {c[\"gender\"]}, {c[\"age\"]}岁)')
"

# === 3. 显示 M2 关键输出 ===

log ""
log "═══════════════════════════════════════"
log "📊 M2 分镜设计"
log "═══════════════════════════════════════"

python3 -c "
import json
d = json.load(open('$OUTPUT_DIR/m2/m2_output.json'))
meta = d['design_meta']
print(f'  目标镜数: {meta[\"target_mirror_count\"]} / 实际: {meta[\"actual_mirror_count\"]}')
print(f'  总时长: {meta[\"total_duration\"]}s')
print(f'  CUE 数量: {len(d[\"cue_timeline\"])}')
print()
print('  分镜列表:')
for m in d['mirrors']:
    cue = f'CUE{m[\"cue_index\"]}' if m.get('cue_index', 0) > 0 else '----'
    print(f'    {m[\"id\"]} {m[\"duration_sec\"]:>4.1f}s [{m[\"structure_position\"]:>3}] {m[\"shot_size\"]}·{m[\"camera_movement\"]} {cue}')
print()
print('  CUE 时间轴:')
for c in d['cue_timeline']:
    print(f'    CUE{c[\"cue_index\"]} {c[\"cue_type\"]} → {c[\"mirror_id\"]} @ {c[\"position_sec\"]}s')
print()
print('  色彩曲线:')
for c in d['color_curve']:
    print(f'    {c[\"act\"]} → {c[\"mirror_id\"]} | {c[\"tone\"]} | 饱和度 {c[\"saturation\"]}')
print()
print('  节拍分析:')
p = d['pacing']
print(f'    平均 {p[\"avg_duration\"]}s / 最短 {p[\"min_duration\"]}s / 最长 {p[\"max_duration\"]}s / 标准差 {p[\"std_dev\"]} ({p[\"rhythm_pattern\"]})')
"

# === 4. 显示 M3 关键输出 ===

log ""
log "═══════════════════════════════════════"
log "📊 M3 提示词生成"
log "═══════════════════════════════════════"

M3_FILES=$(ls "$OUTPUT_DIR/m3"/镜*.txt 2>/dev/null | wc -l | tr -d ' ')
log "  文件数: $M3_FILES"
log "  示例: 镜001 前 20 行"
log ""
head -20 "$OUTPUT_DIR/m3/镜001_"*.txt 2>/dev/null | sed 's/^/    /'

# === 5. 对比 v3.5 真实数据 ===

log ""
log "═══════════════════════════════════════"
log "📊 对比 v3.5 真实数据（examples/example-古早霸总-EP01/）"
log "═══════════════════════════════════════"

if [ -d "$EXAMPLE_DIR" ]; then
    V35_COUNT=$(ls "$EXAMPLE_DIR"/镜*.txt 2>/dev/null | wc -l | tr -d ' ')
    log "  v3.5 镜 txt 数: $V35_COUNT"
    log "  本次生成: $M3_FILES"
    log "  v3.5 vs 本次：$V35_COUNT / $M3_FILES"
    log ""
    log "  关键检查:"
    if [ "$M3_FILES" -ge 5 ] && [ "$M3_FILES" -le 20 ]; then
        log_ok "  镜数在 5-20 合理区间"
    else
        log_warn "  镜数异常: $M3_FILES"
    fi
    log ""
    log "  段落完整性检查（每个文件应有 6 段）:"
    SEC_OK=$(python3 -c "
import os
required = ['资产引用', '人物资产档案', '镜头参数', '画面描述', '光影氛围', '技术参数']
files = sorted([f for f in os.listdir('$OUTPUT_DIR/m3') if f.endswith('.txt')])
all_ok = 0
for f in files:
    content = open(os.path.join('$OUTPUT_DIR/m3', f), encoding='utf-8').read()
    if all(sec in content for sec in required):
        all_ok += 1
print(f'{all_ok}/{len(files)}')
")
    log "    $SEC_OK 文件通过 6 段完整性检查"
    if [ "$SEC_OK" = "$M3_FILES/$M3_FILES" ]; then
        log_ok "  全部文件 6 段完整"
    else
        log_warn "  部分文件段落缺失"
    fi
else
    log_warn "  v3.5 示例目录不存在，跳过对比"
fi

log ""
log "═══════════════════════════════════════"
log "🎉 m1_e2e_demo 完成"
log "═══════════════════════════════════════"
log ""
log "📂 输出目录: $OUTPUT_DIR"
log "   m1_output.json    - 剧本结构化解析"
log "   m2_output.json    - 分镜设计 + CUE + 色彩曲线"
log "   m3/镜*.txt        - 提示词骨架（待 LLM 填充画面描述段）"
log ""
log "💡 下一步：把 m3/镜*.txt 发给 LLM，让它填充【画面描述】段。"
log "   填充后用 validate_prompt.py 校验："
log "   python3 $SKILL_SCRIPTS/validate_prompt.py $OUTPUT_DIR/m3/镜001_*.txt"

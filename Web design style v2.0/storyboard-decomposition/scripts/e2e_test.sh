#!/usr/bin/env bash
# e2e_test.sh — 端到端测试脚本
#
# 测试场景：
# 1. 自动生成 4 种风格的测试剧本（古早霸总/都市情感/古装江湖/悬疑推理）
# 2. 跑 M1→M2→M3→M4 完整流水线
# 3. 验证 12 项硬约束
# 4. 输出 PASS/FAIL 总结
#
# 用法:
#   ./e2e_test.sh           # 跑全部 4 种风格
#   ./e2e_test.sh --quick   # 只跑 1 种风格（古早霸总）
#   ./e2e_test.sh --style 古早霸总  # 跑指定风格

# 不使用 set -e（让 assert 自由报告失败）
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
TEST_DIR="/tmp/skill_e2e_test_$$"
PASS_COUNT=0
FAIL_COUNT=0

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# === 测试剧本模板（4 种风格） ===

write_script_古早霸总() {
cat <<'SCRIPT_EOF'
测试剧本·古早霸总风格

第一场：总裁办公室
场景：高档办公室，落地窗外是城市天际线。下午 4 点，斜阳打在办公桌上。
陆景琛坐在办公桌前批阅文件，眉头紧蹙。
林念卿推门而入，手里拿着一份文件。
陆景琛：林念卿，你来做什么？
林念卿：陆总，这份合同有问题，我需要您重新考虑。
陆景琛：我的决定，不需要你来质疑。

第二场：顶楼套房
场景：夜晚的顶楼套房，灯光昏黄。
陆景琛：如果你愿意，我可以解释。
林念卿：解释？你能解释这三年吗？

第三场：雨中街道
场景：雨夜，街道上行人稀少。
陆景琛：如果...我愿意改变呢？
林念卿：太迟了。
SCRIPT_EOF
}

write_script_都市情感() {
cat <<'SCRIPT_EOF'
测试剧本·都市情感风格

第一场：咖啡店
场景：街角咖啡店，下午阳光透过玻璃窗。柔和爵士乐。
苏晴和顾晨相对而坐。
苏晴：顾晨，我们...是不是应该谈谈？
顾晨：（低头搅动咖啡）我知道你想说什么。
苏晴：那就别逃避了。

第二场：写字楼天台
场景：城市写字楼天台，傍晚，晚霞满天。
苏晴：你真的要走了吗？
顾晨：是的。但我会一直记得你。

第三场：机场
场景：机场出发大厅，人来人往。
顾晨：保重。
苏晴：你也是。
SCRIPT_EOF
}

write_script_古装江湖() {
cat <<'SCRIPT_EOF'
测试剧本·古装江湖风格

第一场：客栈大堂
场景：江南客栈大堂，灯笼高挂，人声鼎沸。
叶孤城手持长剑，缓步入内。
店小二：客官，您是打尖还是住店？
叶孤城：找一个人。

第二场：城外竹林
场景：城外竹林，月光如水。
西门吹雪：叶孤城，三年未见，你的剑更利了。
叶孤城：你的心却乱了。

第三场：山顶决战
场景：山顶悬崖，月光刺眼。
叶孤城：这一剑，我会让你死得明白。
SCRIPT_EOF
}

write_script_悬疑推理() {
cat <<'SCRIPT_EOF'
测试剧本·悬疑推理风格

第一场：案发现场
场景：密室书房，地上有血迹，窗户紧锁。
警探林涛勘查现场，神色凝重。
助手：队长，死者死于凌晨 2 点。
林涛：2 点...但监控显示他 1 点就回家了。

第二场：嫌疑人审讯室
场景：审讯室，灯光惨白。
嫌疑人陈默：我什么都没做。
林涛：你的指纹在凶器上。

第三场：真相揭露
场景：林涛办公室，夜深。
林涛：真相只有一个。
SCRIPT_EOF
}

# === 工具函数 ===

log() { echo -e "${BLUE}[E2E]${NC} $1"; }
log_pass() { echo -e "${GREEN}✓${NC} $1"; PASS_COUNT=$((PASS_COUNT+1)); }
log_fail() { echo -e "${RED}✗${NC} $1"; FAIL_COUNT=$((FAIL_COUNT+1)); }
log_warn() { echo -e "${YELLOW}⚠${NC} $1"; }

assert() {
    local condition="$1"
    local desc="$2"
    if [ "$condition" = "0" ]; then
        log_pass "$desc"
    else
        log_fail "$desc"
    fi
}

# === 单个 E2E 测试 ===

run_e2e_for_style() {
    local style="$1"
    local test_id="e2e_$$"

    log ""
    log "═══════════════════════════════════════"
    log "🧪 测试: $style"
    log "═══════════════════════════════════════"

    # 准备测试目录
    local work_dir="$TEST_DIR/$test_id"
    mkdir -p "$work_dir"
    local script_file="$work_dir/test_script.txt"

    # 调用对应 writer
    case "$style" in
        古早霸总) write_script_古早霸总 > "$script_file" ;;
        都市情感) write_script_都市情感 > "$script_file" ;;
        古装江湖) write_script_古装江湖 > "$script_file" ;;
        悬疑推理) write_script_悬疑推理 > "$script_file" ;;
        *) log_fail "未知风格: $style"; return 1 ;;
    esac

    # 跑流水线
    log "  → 跑 M1→M2→M3→M4..."
    "$SCRIPT_DIR/run_skill.sh" "$script_file" --output-dir "$work_dir/out" --style "$style" --total-duration 80 2>&1 | grep -E "(✅|❌|⚠|完成|失败)" | sed 's/^/    /' || true

    # === 12 项硬约束校验 ===

    # 1. M1 输出存在
    if [ -f "$work_dir/out/m1/m1_output.json" ]; then
        log_pass "M1 输出存在"
    else
        log_fail "M1 输出不存在"
        return 1
    fi

    # 2. M1 检测到 style
    local m1_style=$(python3 -c "import json; print(json.load(open('$work_dir/out/m1/m1_output.json'))['style'])" 2>/dev/null)
    if [ "$m1_style" = "$style" ]; then
        log_pass "M1 style 检测正确: $m1_style"
    else
        log_fail "M1 style 检测错误: 期望=$style, 实际=$m1_style"
    fi

    # 3. M2 输出存在
    if [ -f "$work_dir/out/m2/m2_output.json" ]; then
        log_pass "M2 输出存在"
    else
        log_fail "M2 输出不存在"
        return 1
    fi

    # 4. M2 镜数在 5-16 之间
    local mirror_count=$(python3 -c "import json; print(len(json.load(open('$work_dir/out/m2/m2_output.json'))['mirrors']))" 2>/dev/null)
    if [ "$mirror_count" -ge 5 ] && [ "$mirror_count" -le 16 ]; then
        log_pass "M2 镜数合理: $mirror_count (5-16)"
    else
        log_fail "M2 镜数异常: $mirror_count"
    fi

    # 5. M2 总时长在 75-85s
    local total_duration=$(python3 -c "import json; d=json.load(open('$work_dir/out/m2/m2_output.json')); print(sum(m['duration_sec'] for m in d['mirrors']))" 2>/dev/null)
    if python3 -c "exit(0 if 75 <= $total_duration <= 85 else 1)"; then
        log_pass "M2 总时长合理: ${total_duration}s (75-85)"
    else
        log_fail "M2 总时长异常: ${total_duration}s"
    fi

    # 6. M2 CUE 数量 = 3
    local cue_count=$(python3 -c "import json; d=json.load(open('$work_dir/out/m2/m2_output.json')); print(len(d['cue_timeline']))" 2>/dev/null)
    if [ "$cue_count" -eq 3 ]; then
        log_pass "M2 CUE 数量正确: 3"
    else
        log_fail "M2 CUE 数量错误: $cue_count (期望 3)"
    fi

    # 7. M2 CUE 唯一性
    local cue_unique=$(python3 -c "
import json
d = json.load(open('$work_dir/out/m2/m2_output.json'))
cues = [m['cue_index'] for m in d['mirrors'] if m.get('cue_index', 0) > 0]
print(len(set(cues)) == 3 and len(cues) == 3)
" 2>/dev/null)
    if [ "$cue_unique" = "True" ]; then
        log_pass "M2 CUE 唯一性正确"
    else
        log_fail "M2 CUE 唯一性错误"
    fi

    # 8. M2 5 幕结构覆盖
    local positions_covered=$(python3 -c "
import json
d = json.load(open('$work_dir/out/m2/m2_output.json'))
positions = set(m['structure_position'] for m in d['mirrors'])
print(len(positions) >= 3)
" 2>/dev/null)
    if [ "$positions_covered" = "True" ]; then
        log_pass "M2 结构位置覆盖 ≥3 幕"
    else
        log_fail "M2 结构位置覆盖 < 3 幕"
    fi

    # 9. M3 文件数 = M2 镜数
    local m3_file_count=$(ls "$work_dir/out/m3"/镜*.txt 2>/dev/null | wc -l | tr -d ' ')
    if [ "$m3_file_count" -eq "$mirror_count" ]; then
        log_pass "M3 文件数 = 镜数: $m3_file_count"
    else
        log_fail "M3 文件数 $m3_file_count ≠ 镜数 $mirror_count"
    fi

    # 10. M3 无元注释残留
    mkdir -p "$work_dir/out/m3_validate"
    python3 "$SCRIPT_DIR/m3_generate.py" "$work_dir/out/m2/m2_output.json" "$work_dir/out/m1/m1_output.json" --out-dir "$work_dir/out/m3_validate" --validate > "$work_dir/out/m3_validate.log" 2>&1
    local meta_count=$(grep -oE "'files_with_meta': [0-9]+" "$work_dir/out/m3_validate.log" | head -1)
    if echo "$meta_count" | grep -q ": 0"; then
        log_pass "M3 无元注释残留"
    else
        log_fail "M3 元注释校验异常: ${meta_count:-无输出}"
    fi

    # 11. M3 段落完整性
    local sections_ok=$(python3 -c "
import os
required = ['资产引用', '人物资产档案', '镜头参数', '画面描述', '光影氛围', '技术参数']
files = [f for f in os.listdir('$work_dir/out/m3') if f.endswith('.txt')]
all_ok = True
for f in files:
    content = open(os.path.join('$work_dir/out/m3', f), encoding='utf-8').read()
    for sec in required:
        if sec not in content:
            all_ok = False
            break
print(all_ok)
" 2>/dev/null)
    if [ "$sections_ok" = "True" ]; then
        log_pass "M3 6 段全部完整"
    else
        log_fail "M3 部分段落缺失"
    fi

    # 12. M4 校验报告存在
    if [ -f "$work_dir/out/m4/continuity_report.json" ]; then
        log_pass "M4 校验报告生成"
    else
        log_fail "M4 校验报告未生成"
    fi

    log "  → 完成: $style"
}

# === 主流程 ===

QUICK_MODE=false
TARGET_STYLE=""

while [ $# -gt 0 ]; do
    case "$1" in
        --quick) QUICK_MODE=true; shift ;;
        --style) TARGET_STYLE="$2"; shift 2 ;;
        *) echo "未知参数: $1"; exit 1 ;;
    esac
done

mkdir -p "$TEST_DIR"
trap "rm -rf $TEST_DIR" EXIT

log "🚀 Skill E2E 测试启动"
log "工作目录: $TEST_DIR"

if [ -n "$TARGET_STYLE" ]; then
    run_e2e_for_style "$TARGET_STYLE"
elif [ "$QUICK_MODE" = true ]; then
    run_e2e_for_style "古早霸总"
else
    for style in 古早霸总 都市情感 古装江湖 悬疑推理; do
        run_e2e_for_style "$style"
    done
fi

# === 总结 ===

log ""
log "═══════════════════════════════════════"
log "📊 E2E 测试总结"
log "═══════════════════════════════════════"
log "  通过: $PASS_COUNT"
log "  失败: $FAIL_COUNT"
log ""

if [ "$FAIL_COUNT" -eq 0 ]; then
    log "🎉 全部通过！"
    exit 0
else
    log "❌ 有 $FAIL_COUNT 项失败"
    exit 1
fi

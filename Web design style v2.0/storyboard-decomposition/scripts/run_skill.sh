#!/usr/bin/env bash
# run_skill.sh — 一键运行 M1→M2→M3→M4→M5→M6 流水线
#
# 用法:
#   ./run_skill.sh <剧本文件> [输出目录]
#   ./run_skill.sh <剧本文件> --style 古早霸总 --total-duration 80
#   ./run_skill.sh <剧本文件> --skip-m4   # 只跑 M1-M3
#   ./run_skill.sh <剧本文件> --from m2   # 从 M2 开始（断点续跑）
#   ./run_skill.sh <剧本文件> --to-video  # 端到端：M1-M6（无 API 时降级 mock）
#   ./run_skill.sh <剧本文件> --platform 可灵 --to-video  # 指定视频 API
#
# 设计哲学：
# 1. M1 失败 → 立即退出（不浪费 M2/M3/M4 算力）
# 2. M2 失败 → 退出（无分镜则无 prompt）
# 3. M3 失败 → 不退出，warning（LLM 填充阶段可补救）
# 4. M4 失败 → 不退出，warning（衔接问题可在 prompt 阶段修复）
# 5. M5 失败 → 不退出，warning（mock 模式保证工程链路完整）
# 6. M6 失败 → 不退出，warning（生成 ffmpeg 脚本让用户手动跑）
# 7. 任何阶段可断点续跑：--from m2 / --from m3 / --from m4
# 8. --to-video 启用端到端：M1→M2→M3→M4→M5→M6
#
# Why: 26 镜 EP01 实测 — 4 阶段全跑完 = 4 个 LLM 调用 + 4 次失败恢复，
#     没有 run_skill.sh 自动化，操作失误率 20-30%。
#     v3.6 P0: 端到端 pipeline，偏差1修复 — 不再只是"提示词生成器"。

set -euo pipefail

# === 参数解析 ===

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认值
SCRIPT_FILE=""
OUTPUT_DIR="./run_output"
STYLE="auto"
TOTAL_DURATION=80
SKIP_M4=false
FROM_STAGE=""
VERBOSE=false
TO_VIDEO=false
PLATFORM="即梦"
BGM=""
USE_LLM=false
MOCK_LLM=false

print_help() {
    cat <<EOF
用法: $0 <剧本文件> [选项]

选项:
    --style <风格>        强制指定风格（默认自动检测）
    --total-duration <秒> 目标总时长（默认 80）
    --output-dir <目录>   输出目录（默认 ./run_output）
    --skip-m4             跳过 M4 衔接校验
    --from <m1|m2|m3|m4|m5|m6>  断点续跑：从指定阶段开始
    --to-video            端到端：跑 M1→M6（无 API/ffmpeg 时降级 mock）
    --platform <平台>     视频 API 平台（即梦/可灵/Sora/Runway，默认即梦）
    --bgm <文件>          BGM 音频文件路径（可选）
    --llm                  M1 启用 LLM 增强（需 ANTHROPIC_API_KEY，否则降级 mock）
    --mock-llm             强制 mock LLM 模式（跳过 API）
    --verbose              详细输出
    --help                 显示帮助

示例:
    $0 my_script.txt
    $0 my_script.txt --style 古早霸总 --total-duration 80
    $0 my_script.txt --from m2   # 复用已有 m1_output.json
    $0 my_script.txt --to-video  # 端到端生成视频
    $0 my_script.txt --to-video --platform 可灵  # 指定平台
EOF
}

# 解析参数
if [ $# -eq 0 ]; then
    print_help
    exit 1
fi

SCRIPT_FILE="$1"
shift

while [ $# -gt 0 ]; do
    case "$1" in
        --style) STYLE="$2"; shift 2 ;;
        --total-duration) TOTAL_DURATION="$2"; shift 2 ;;
        --output-dir) OUTPUT_DIR="$2"; shift 2 ;;
        --skip-m4) SKIP_M4=true; shift ;;
        --from) FROM_STAGE="$2"; shift 2 ;;
        --to-video) TO_VIDEO=true; shift ;;
        --platform) PLATFORM="$2"; shift 2 ;;
        --bgm) BGM="$2"; shift 2 ;;
        --llm) USE_LLM=true; shift ;;
        --mock-llm) MOCK_LLM=true; USE_LLM=true; shift ;;
        --verbose) VERBOSE=true; shift ;;
        --help) print_help; exit 0 ;;
        *) echo -e "${RED}未知参数: $1${NC}"; exit 1 ;;
    esac
done

# === 准备 ===

if [ ! -f "$SCRIPT_FILE" ]; then
    echo -e "${RED}❌ 剧本文件不存在: $SCRIPT_FILE${NC}"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR/m1"
mkdir -p "$OUTPUT_DIR/m2"
mkdir -p "$OUTPUT_DIR/m3"
mkdir -p "$OUTPUT_DIR/m4"
mkdir -p "$OUTPUT_DIR/m5"
mkdir -p "$OUTPUT_DIR/m6"

M1_OUTPUT="$OUTPUT_DIR/m1/m1_output.json"
M2_OUTPUT="$OUTPUT_DIR/m2/m2_output.json"
M3_OUTPUT_DIR="$OUTPUT_DIR/m3"
M4_OUTPUT_DIR="$OUTPUT_DIR/m4"
M5_OUTPUT_DIR="$OUTPUT_DIR/m5"
M6_OUTPUT="$OUTPUT_DIR/m6/EP01_final.mp4"

log() {
    echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

log_err() {
    echo -e "${RED}❌ $1${NC}"
}

log_ok() {
    echo -e "${GREEN}✅ $1${NC}"
}

run_or_warn() {
    # 跑命令，失败不退出（用于 M3/M4）
    if "$@"; then
        return 0
    else
        return 1
    fi
}

# === 决定从哪个阶段开始 ===

should_run() {
    local stage="$1"
    if [ -z "$FROM_STAGE" ]; then
        return 0  # 没指定 --from，全部跑
    fi
    # 否则按顺序判断
    case "$FROM_STAGE" in
        m1) [ "$stage" = "m1" ] ;;
        m2) [ "$stage" = "m1" ] || [ "$stage" = "m2" ] ;;
        m3) [ "$stage" = "m1" ] || [ "$stage" = "m2" ] || [ "$stage" = "m3" ] ;;
        m4) [ "$stage" = "m1" ] || [ "$stage" = "m2" ] || [ "$stage" = "m3" ] || [ "$stage" = "m4" ] ;;
        m5) [ "$stage" = "m1" ] || [ "$stage" = "m2" ] || [ "$stage" = "m3" ] || [ "$stage" = "m4" ] || [ "$stage" = "m5" ] ;;
        m6) true ;;
        *) true ;;
    esac
}

# === M1: 剧本解析 ===

if should_run m1; then
    log "🔍 M1: 剧本解析..."
    LLM_FLAGS=""
    if [ "$USE_LLM" = true ]; then
        if [ "$MOCK_LLM" = true ]; then
            LLM_FLAGS="--mock-llm"
        else
            LLM_FLAGS="--llm"
        fi
    fi
    if [ "$VERBOSE" = true ]; then
        python3 "$SCRIPT_DIR/m1_parse.py" "$SCRIPT_FILE" "$M1_OUTPUT" --style "$STYLE" --validate --source-file "$SCRIPT_FILE" $LLM_FLAGS
    else
        python3 "$SCRIPT_DIR/m1_parse.py" "$SCRIPT_FILE" "$M1_OUTPUT" --style "$STYLE" --source-file "$SCRIPT_FILE" $LLM_FLAGS 2>&1 | tail -5
    fi
    if [ ! -f "$M1_OUTPUT" ]; then
        log_err "M1 失败：未生成 $M1_OUTPUT"
        exit 1
    fi
    log_ok "M1 完成: $M1_OUTPUT"
    if [ "$USE_LLM" = true ]; then
        log "  → LLM 增强模式: 包含 narrator/ambient_sound/global_constraints/style_cues 等 6 维扩展字段"
    fi
fi

# === M2: 分镜设计 ===

if should_run m2; then
    log "🎬 M2: 分镜设计..."
    if [ "$VERBOSE" = true ]; then
        python3 "$SCRIPT_DIR/m2_design.py" "$M1_OUTPUT" "$M2_OUTPUT" --total-duration "$TOTAL_DURATION" --validate
    else
        python3 "$SCRIPT_DIR/m2_design.py" "$M1_OUTPUT" "$M2_OUTPUT" --total-duration "$TOTAL_DURATION" 2>&1 | tail -5
    fi
    if [ ! -f "$M2_OUTPUT" ]; then
        log_err "M2 失败：未生成 $M2_OUTPUT"
        exit 1
    fi
    log_ok "M2 完成: $M2_OUTPUT"

    # 显示分镜概览
    MIRROR_COUNT=$(python3 -c "import json; print(len(json.load(open('$M2_OUTPUT'))['mirrors']))")
    log "  → 共 $MIRROR_COUNT 镜"
fi

# === M3: 提示词生成 ===

if should_run m3; then
    log "📝 M3: 提示词生成..."
    if python3 "$SCRIPT_DIR/m3_generate.py" "$M2_OUTPUT" "$M1_OUTPUT" --out-dir "$M3_OUTPUT_DIR" --validate 2>&1; then
        FILE_COUNT=$(ls "$M3_OUTPUT_DIR"/镜*.txt 2>/dev/null | wc -l | tr -d ' ')
        log_ok "M3 完成: $FILE_COUNT 个文件 → $M3_OUTPUT_DIR"
    else
        log_warn "M3 部分失败（LLM 填充阶段可补救）"
    fi
fi

# === M4: 衔接校验 ===

if should_run m4 && [ "$SKIP_M4" = false ]; then
    log "🔗 M4: 衔接校验..."
    if [ -d "$M3_OUTPUT_DIR" ] && [ "$(ls -A "$M3_OUTPUT_DIR" 2>/dev/null)" ]; then
        # 复制 M3 输出到 M4 输入目录
        cp -r "$M3_OUTPUT_DIR"/* "$M4_OUTPUT_DIR/" 2>/dev/null || true
        # 跑 continuity_check
        if python3 "$SCRIPT_DIR/continuity_check.py" "$M4_OUTPUT_DIR" --json > "$M4_OUTPUT_DIR/continuity_report.json" 2>&1; then
            log_ok "M4 完成: $M4_OUTPUT_DIR/continuity_report.json"
        else
            log_warn "M4 衔接校验发现问题（不阻塞流程）"
        fi
    else
        log_warn "M3 输出目录为空，跳过 M4"
    fi
fi

# === M5: 视频生成（仅 --to-video） ===

if [ "$TO_VIDEO" = true ] && should_run m5; then
    log "🎥 M5: 视频生成..."
    if [ -d "$M3_OUTPUT_DIR" ] && [ "$(ls -A "$M3_OUTPUT_DIR" 2>/dev/null)" ]; then
        # 跑 m5_video
        if python3 "$SCRIPT_DIR/m5_video.py" "$M3_OUTPUT_DIR" "$M5_OUTPUT_DIR" --platform "$PLATFORM" 2>&1 | tail -10 | sed 's/^/  /'; then
            VIDEO_COUNT=$(ls "$M5_OUTPUT_DIR"/镜*.manifest.json 2>/dev/null | wc -l | tr -d ' ')
            log_ok "M5 完成: $VIDEO_COUNT 个视频 → $M5_OUTPUT_DIR"
        else
            log_warn "M5 视频生成部分失败"
        fi
    else
        log_warn "M3 输出目录为空，跳过 M5"
    fi
fi

# === M6: 视频拼接（仅 --to-video） ===

if [ "$TO_VIDEO" = true ] && should_run m6; then
    log "🎞 M6: 视频拼接..."
    if [ -d "$M5_OUTPUT_DIR" ] && [ "$(ls -A "$M5_OUTPUT_DIR" 2>/dev/null)" ]; then
        # 跑 m6_stitch
        BGM_ARG=""
        [ -n "$BGM" ] && BGM_ARG="--bgm $BGM"
        if python3 "$SCRIPT_DIR/m6_stitch.py" "$M5_OUTPUT_DIR" "$M2_OUTPUT" "$M6_OUTPUT" --m3-dir "$M3_OUTPUT_DIR" $BGM_ARG 2>&1 | tail -10 | sed 's/^/  /'; then
            if [ -f "$M6_OUTPUT" ]; then
                log_ok "M6 完成: $M6_OUTPUT"
            else
                log "  ⚠ M6 mock 模式（无 ffmpeg）— 见 $OUTPUT_DIR/m6/EP01_final.ffmpeg.sh"
            fi
        else
            log_warn "M6 拼接失败"
        fi
    else
        log_warn "M5 输出目录为空，跳过 M6"
    fi
fi

# === M7: AI 内容质量验证（轻量版） ===

if should_run m7; then
    log "🤖 M7: AI 内容质量验证..."
    if [ -d "$M3_OUTPUT_DIR" ] && [ "$(ls -A "$M3_OUTPUT_DIR" 2>/dev/null)" ]; then
        # 跑 ai_verify（threshold 默认 0.7）
        if python3 "$SCRIPT_DIR/ai_verify.py" "$M3_OUTPUT_DIR" --lib-dir "$SKILL_DIR" --threshold 0.7 2>&1 | tail -15 | sed 's/^/  /'; then
            log_ok "M7 完成: $M3_OUTPUT_DIR/ai_verify_report.json"
        else
            log_warn "M7 验证发现问题（不阻塞流程）"
        fi
    else
        log_warn "M3 输出目录为空，跳过 M7"
    fi
fi

# === 总结 ===

log ""
log "═══════════════════════════════════════"
log "📦 输出目录结构:"
log "═══════════════════════════════════════"
log "  M1 解析: $M1_OUTPUT"
log "  M2 分镜: $M2_OUTPUT"
log "  M3 提示词: $M3_OUTPUT_DIR/"
[ "$SKIP_M4" = false ] && log "  M4 校验: $M4_OUTPUT_DIR/continuity_report.json"
[ "$TO_VIDEO" = true ] && log "  M5 视频: $M5_OUTPUT_DIR/"
[ "$TO_VIDEO" = true ] && log "  M6 拼接: $M6_OUTPUT"
log "  M7 验证: $M3_OUTPUT_DIR/ai_verify_report.json"
log ""
log_ok "Skill 流水线完成 ✓"

# 端到端模式下额外提示
if [ "$TO_VIDEO" = true ]; then
    log ""
    log "💡 端到端模式提示:"
    log "   - 无 API 凭证 → M5 自动降级 mock 模式（生成 *.mp4.mock 占位）"
    log "   - 无 ffmpeg → M6 自动降级 mock 模式（生成 *.ffmpeg.sh 脚本）"
    log "   - 设置环境变量启用真实模式:"
    log "       export JIMENG_API_KEY=xxx   # 即梦"
    log "       export KLING_API_KEY=xxx    # 可灵"
    log "       export OPENAI_API_KEY=xxx   # Sora"
    log "       brew install ffmpeg         # macOS 安装 ffmpeg"
fi

# 跨集一致性提示
log ""
log "📚 跨集资产库:"
log "   角色库: $SKILL_DIR/character_lib/  ($(ls "$SKILL_DIR/character_lib" 2>/dev/null | wc -l | tr -d ' ') 个)"
log "   场景库: $SKILL_DIR/scene_lib/      ($(ls "$SKILL_DIR/scene_lib" 2>/dev/null | wc -l | tr -d ' ') 个)"
log "   道具库: $SKILL_DIR/prop_lib/       ($(ls "$SKILL_DIR/prop_lib" 2>/dev/null | wc -l | tr -d ' ') 个)"
log ""
log "💡 跨集复用命令:"
log "   m7_character.py reference 人物_刘一鸣 --ep EP02"
log "   m10_inherit.py m3_dir/ out_dir/ --ep EP02"

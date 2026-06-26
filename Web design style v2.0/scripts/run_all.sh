#!/usr/bin/env bash
#
# WebPPT Maker · 一键编排脚本
#
# 一次跑完 5 个 generator + screenshot + verify，输出"诚实契约"风格的报告。
#
# 用法:
#   bash scripts/run_all.sh --config content.json
#   bash scripts/run_all.sh --topic "AI 写作" --points "真相1" "真相2" "真相3" \
#                            --output-dir ./output_ai
#
# 设计原则:
#   - 任一 generator 失败 → 立刻退出 (set -e) + 明确诊断 (N1 诚实契约)
#   - screenshot 失败 → 继续（graceful fallback 到 SVG），verify 报告体现
#   - verify 失败 → 退出码非零，方便 CI 集成
#   - 结束时输出用户能直接用的下一步操作
#

set -eo pipefail

# ============================================================
# 路径
# ============================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# ============================================================
# 参数
# ============================================================
CONFIG_FILE=""
TOPIC=""
POINTS=()
STYLE="现代简约"
COLOR_SCHEME="auto"
LAYOUT="auto"
DURATION=30
VARIANCE=5
MOTION=5
DENSITY=5
CTA_TEXT=""
CLI_CTA_TEXT=""
CLI_OUTPUT_DIR=""
OUTPUT_DIR=""
SKIP_SCREENSHOT=0
CLEAN_SCREENSHOT=0

while [[ $# -gt 0 ]]; do
  case $1 in
    --config)
      CONFIG_FILE="$2"
      shift 2
      ;;
    --topic)
      TOPIC="$2"
      shift 2
      ;;
    --points)
      shift
      while [[ $# -gt 0 && ! "$1" =~ ^-- ]]; do
        POINTS+=("$1")
        shift
      done
      ;;
    --style)
      STYLE="$2"
      shift 2
      ;;
    --color-scheme)
      COLOR_SCHEME="$2"
      shift 2
      ;;
    --layout)
      LAYOUT="$2"
      shift 2
      ;;
    --variance)
      VARIANCE="$2"
      shift 2
      ;;
    --motion)
      MOTION="$2"
      shift 2
      ;;
    --density)
      DENSITY="$2"
      shift 2
      ;;
    --cta)
      CLI_CTA_TEXT="$2"
      CTA_TEXT="$2"
      shift 2
      ;;
    --duration)
      DURATION="$2"
      shift 2
      ;;
    --output-dir)
      CLI_OUTPUT_DIR="$2"
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --skip-screenshot)
      SKIP_SCREENSHOT=1
      shift
      ;;
    --clean-screenshot)
      CLEAN_SCREENSHOT=1
      shift
      ;;
    -h|--help)
      echo "用法: bash scripts/run_all.sh --config content.json"
      echo "  或: bash scripts/run_all.sh --topic 'X' --points 'A' 'B' 'C' --output-dir ./out"
      echo ""
      echo "参数:"
      echo "  --config FILE          JSON 配置文件"
      echo "  --topic TOPIC          视频主题（直接命令行模式）"
      echo "  --points P1 P2 ...     内容要点（直接命令行模式）"
      echo "  --style STYLE          视觉风格（默认：现代简约）"
      echo "  --color-scheme SCHEME  配色方案（默认：auto）"
      echo "  --layout LAYOUT        排版美学（默认：auto）"
      echo "  --variance 1-10        VARIANCE 视觉多样性（默认：5）"
      echo "  --motion 1-10          MOTION 动画强度（默认：5）"
      echo "  --density 1-10         DENSITY 信息密度（默认：5）"
      echo "  --duration SECONDS     视频时长（默认：30）"
      echo "  --output-dir DIR       输出目录（默认：./output_<topic>_<timestamp>）"
      echo "  --skip-screenshot      跳过截图（快速测试用）"
      echo "  --clean-screenshot     截图前移除 dev overlay (page-number/nav-hint)"
      exit 0
      ;;
    *)
      echo "[ERROR] 未知参数: $1"
      echo "用法: bash $0 --help"
      exit 1
      ;;
  esac
done

# ============================================================
# 从 config 读取（如果指定）
# ============================================================
if [[ -n "$CONFIG_FILE" ]]; then
  if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "[ERROR] 配置文件不存在: $CONFIG_FILE"
    exit 1
  fi
  echo "[INFO] 从配置文件读取: $CONFIG_FILE"

  # v3.3: 安全的 config 解析 — 写到 tempfile 然后 source,避免 eval 注入
  CONFIG_ENV_FILE=$(mktemp -t webppt_config.XXXXXX)
  trap "rm -f '$CONFIG_ENV_FILE'" EXIT
  python3 -c "
import json, sys, shlex
with open('$CONFIG_FILE', encoding='utf-8') as f:
    d = json.load(f)
def shell_escape(s):
    # shlex.quote 包装为可直接 source 的赋值 (单引号包裹)
    return shlex.quote(str(s))
print('TOPIC=' + shell_escape(d.get('topic', '')))
print('STYLE=' + shell_escape(d.get('style', '现代简约')))
print('COLOR_SCHEME=' + shell_escape(d.get('color_scheme', 'auto')))
print('LAYOUT=' + shell_escape(d.get('layout', 'auto')))
print('VARIANCE=' + shell_escape(d.get('variance', 5)))
print('MOTION=' + shell_escape(d.get('motion', 5)))
print('DENSITY=' + shell_escape(d.get('density', 5)))
print('CTA_TEXT=' + shell_escape(d.get('cta_text', '')))
print('DURATION=' + shell_escape(d.get('target_duration_sec', 30)))
print('OUTPUT_DIR=' + shell_escape(d.get('output_dir', '')))
points = d.get('content_points', [])
titles = []
for p in points:
    if isinstance(p, dict):
        titles.append(p.get('title', ''))
    else:
        titles.append(str(p))
# shlex.quote 每个 title 后, 用数组形式赋值
quoted = ' '.join(shell_escape(t) for t in titles)
print(f'POINTS=({quoted})')
" > "$CONFIG_ENV_FILE"
  # shellcheck disable=SC1090
  source "$CONFIG_ENV_FILE"

  if [[ -z "$TOPIC" || ${#POINTS[@]} -eq 0 ]]; then
    echo "[ERROR] 配置文件缺少 topic 或 content_points"
    exit 1
  fi
  # v3.2: 若 config 没设 output_dir，保留 CLI --output-dir 值 (而不是被空串覆盖)
  if [[ -z "$OUTPUT_DIR" && -n "$CLI_OUTPUT_DIR" ]]; then
    OUTPUT_DIR="$CLI_OUTPUT_DIR"
  fi
  # v3.2: 同理保留 CLI --cta 值
  if [[ -z "$CTA_TEXT" && -n "$CLI_CTA_TEXT" ]]; then
    CTA_TEXT="$CLI_CTA_TEXT"
  fi
fi

# ============================================================
# 必填检查
# ============================================================
if [[ -z "$TOPIC" ]]; then
  echo "[ERROR] 必须提供 --topic 或 --config"
  exit 1
fi
if [[ ${#POINTS[@]} -lt 3 ]]; then
  echo "[ERROR] 至少需要 3 个 --points（当前 ${#POINTS[@]} 个）"
  exit 1
fi
if [[ -z "$OUTPUT_DIR" ]]; then
  SAFE_TOPIC=$(echo "$TOPIC" | tr ' ' '_' | tr -cd '[:alnum:]_')
  OUTPUT_DIR="./output_${SAFE_TOPIC}_$(date +%Y%m%d_%H%M%S)"
  echo "[INFO] 未指定 --output-dir，使用: $OUTPUT_DIR"
fi

# ============================================================
# 跑前检查
# ============================================================
echo "============================================================"
echo "WebPPT Maker · 一键编排"
echo "============================================================"
echo "主题: $TOPIC"
echo "要点数: ${#POINTS[@]}"
echo "风格/配色/排版: $STYLE / $COLOR_SCHEME / $LAYOUT"
echo "时长: ${DURATION}s"
echo "输出: $OUTPUT_DIR"
echo "============================================================"
echo ""

# ============================================================
# v3.3: 决议 FINAL_CTA (CLI > config > 主题默认),保证 4 产物 CTA 一致
# ============================================================
# 从 config 读 cta_text (如果用了 --config)
CONFIG_CTA_TEXT=""
if [[ -n "$CONFIG_FILE" ]]; then
  CONFIG_CTA_TEXT=$(python3 -c "
import json, sys
try:
    with open('$CONFIG_FILE', encoding='utf-8') as f:
        d = json.load(f)
    print(d.get('cta_text', ''))
except Exception:
    print('')
")
fi
# 调用 _cta_resolver 决议最终 CTA (CLI_CTA_TEXT > CONFIG_CTA_TEXT > 主题默认)
FINAL_CTA=$(python3 "$SKILL_DIR/scripts/_cta_resolver.py" "$CLI_CTA_TEXT" "$CONFIG_CTA_TEXT" "$STYLE")

# ============================================================
# Step 1: 生成 HTML
# ============================================================
echo "[1/5] 生成 HTML 网页..."
HTML_OUT=$(python3 "$SKILL_DIR/scripts/generate_html.py" \
  --topic "$TOPIC" \
  --points "${POINTS[@]}" \
  --style "$STYLE" \
  --color-scheme "$COLOR_SCHEME" \
  --layout "$LAYOUT" \
  --variance "$VARIANCE" \
  --motion "$MOTION" \
  --density "$DENSITY" \
  --cta "$CTA_TEXT" \
  --final-cta "$FINAL_CTA" \
  --output-dir "$OUTPUT_DIR" 2>&1) || {
    echo "[ERROR] HTML 生成失败"
    echo "$HTML_OUT" | tail -10
    exit 1
}
# 提取实际输出目录（JSON 的 output_folder 字段）
FINAL_DIR=$(echo "$HTML_OUT" | python3 "$SKILL_DIR/scripts/_extract_output_dir.py")
if [[ -z "$FINAL_DIR" ]]; then
  FINAL_DIR="$OUTPUT_DIR"
fi
echo "    ✅ HTML → $FINAL_DIR/index.html"
echo ""

# ============================================================
# Step 2-4: copy / script / subtitle (用同一个 FINAL_DIR)
# ============================================================
echo "[2/5] 生成抖音文案..."
python3 "$SKILL_DIR/scripts/generate_copy.py" \
  --topic "$TOPIC" \
  --points "${POINTS[@]}" \
  --output-dir "$OUTPUT_DIR" \
  --final-cta "$FINAL_CTA" 2>&1 | grep -E "^\[OK\]|^\[ERROR\]" | sed 's/^/    /'
echo ""

echo "[3/5] 生成时间线剧本..."
python3 "$SKILL_DIR/scripts/generate_script.py" \
  --topic "$TOPIC" \
  --points "${POINTS[@]}" \
  --duration "$DURATION" \
  --output-dir "$OUTPUT_DIR" \
  --final-cta "$FINAL_CTA" 2>&1 | grep -E "^\[OK\]|^\[ERROR\]" | sed 's/^/    /'
echo ""

echo "[4/5] 生成剪映字幕 ⭐ v1.1.0..."
python3 "$SKILL_DIR/scripts/generate_subtitle.py" \
  --topic "$TOPIC" \
  --points "${POINTS[@]}" \
  --duration "$DURATION" \
  --output-dir "$OUTPUT_DIR" \
  --final-cta "$FINAL_CTA" 2>&1 | grep -E "^\[OK\]|^\[ERROR\]" | sed 's/^/    /'
echo ""

# ============================================================
# Step 5: 截图（可选跳过）
# ============================================================
if [[ "$SKIP_SCREENSHOT" -eq 0 ]]; then
  echo "[5/5] 截图（BrowserUse，无则降级 SVG）..."
  if [[ "$CLEAN_SCREENSHOT" -eq 1 ]]; then
    SCREENSHOT_ARGS="--no-dev-overlay"
    echo "    --clean-screenshot: 启用 (移除 page-number/nav-hint)"
  else
    SCREENSHOT_ARGS=""
  fi
  bash "$SKILL_DIR/scripts/screenshot.sh" --html-dir "$FINAL_DIR" $SCREENSHOT_ARGS 2>&1 | tail -10 | sed 's/^/    /'
  echo ""
else
  echo "[5/5] 截图（已跳过 --skip-screenshot）"
  echo ""
fi

# ============================================================
# 自验证
# ============================================================
echo "============================================================"
echo "[verify] 跑自验证（verify.sh，含 G 类字幕验收）"
echo "============================================================"
if bash "$SKILL_DIR/scripts/verify.sh" --output-dir "$OUTPUT_DIR" 2>&1 | tail -25; then
  echo ""
  echo "============================================================"
  echo "✅ 全部完成"
  echo "============================================================"
  echo ""
  echo "📂 输出目录: $FINAL_DIR"
  echo ""
  echo "📋 产物清单:"
  for f in index.html douyin_post.md douyin_titles.md script_timeline.md subtitle.srt verify_report.json; do
    if [[ -f "$FINAL_DIR/$f" ]]; then
      SIZE=$(wc -c < "$FINAL_DIR/$f" | tr -d ' ')
      echo "   ✅ $f ($SIZE bytes)"
    else
      echo "   ❌ $f (缺失)"
    fi
  done
  echo ""
  echo "🚀 下一步:"
  echo "   1. 打开 $FINAL_DIR/index.html 预览网页 (9 种 layout 多样化)"
  echo "   2. 复制 $FINAL_DIR/douyin_post.md 到抖音发布 (一键)"
  echo "   3. 从 $FINAL_DIR/douyin_titles.md 选标题 (5 版 A/B)"
  echo "   4. 把 $FINAL_DIR/subtitle.srt 拖入剪映作为字幕轨"
  echo "   5. 使用 $FINAL_DIR/screenshots/*.png 作为视频素材"
  exit 0
else
  echo ""
  echo "============================================================"
  echo "⚠️  验证发现问题（产物可能仍可用）"
  echo "============================================================"
  echo "📂 输出目录: $FINAL_DIR"
  echo "📋 报告: $FINAL_DIR/verify_report.json"
  exit 1
fi

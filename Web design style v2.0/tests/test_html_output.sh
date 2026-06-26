#!/usr/bin/env bash
#
# WebPPT Maker · HTML 输出质量验证脚本
#
# 跑一个端到端测试:
#   1. 生成 HTML 网页
#   2. 验证 viewport / 页数 / 字号
#   3. 生成文案和剧本
#   4. 验证文案和剧本质量
#   5. 跑 verify.sh
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# 准备临时输出目录
TEST_OUTPUT="$SKILL_DIR/tests/_test_output"
rm -rf "$TEST_OUTPUT"
mkdir -p "$TEST_OUTPUT"

# 测试输入
TEST_TOPIC="AI 写作的 5 个真相"
TEST_POINTS=(
  "真相 1：AI 不是替代你，而是放大你"
  "真相 2：prompt 决定上限"
  "真相 3：先 RED 后 GREEN"
  "真相 4：失败不可怕，可怕的是不知道哪里失败"
  "真相 5：最后 10% 永远要人来把关"
)

echo "============================================================"
echo "端到端测试: 生成 HTML + 文案 + 剧本"
echo "============================================================"

# ============================================================
# Step 1: 生成 HTML
# ============================================================
echo ""
echo "[Step 1] 生成 HTML 网页"

# 捕获实际输出目录（脚本会在已存在时加 timestamp 后缀）
HTML_GEN_OUTPUT=$(python3 "$SKILL_DIR/scripts/generate_html.py" \
  --topic "$TEST_TOPIC" \
  --points "${TEST_POINTS[@]}" \
  --style "现代简约" \
  --color-scheme "极简黑白" \
  --layout "卡片" \
  --output-dir "$TEST_OUTPUT" 2>&1)

# 提取实际输出路径
ACTUAL_OUTPUT=$(echo "$HTML_GEN_OUTPUT" | python3 -c "
import json, sys
for line in sys.stdin:
    line = line.strip()
    if line.startswith('{'):
        try:
            d = json.loads(line)
            print(d.get('output_folder', ''))
            break
        except: pass
")

# 兼容：如果没找到 JSON 输出，回退到默认
if [[ -z "$ACTUAL_OUTPUT" ]]; then
  ACTUAL_OUTPUT=$(find "$SKILL_DIR/tests" -maxdepth 1 -name "_test_output*" -type d | sort | tail -1)
fi

TEST_OUTPUT="$ACTUAL_OUTPUT"
echo "[INFO] 实际输出目录: $TEST_OUTPUT"

# ============================================================
# Step 2: 验证 HTML
# ============================================================
echo ""
echo "[Step 2] 验证 HTML 网页"

INDEX_FILE="$TEST_OUTPUT/index.html"

if [[ ! -f "$INDEX_FILE" ]]; then
  echo "❌ index.html 未生成"
  exit 1
fi

PAGE_COUNT=$(grep -cE 'data-page="[0-9]+"' "$INDEX_FILE")
if [[ "$PAGE_COUNT" -ge 5 ]]; then
  echo "✅ 页数 = $PAGE_COUNT (≥ 5)"
else
  echo "❌ 页数 = $PAGE_COUNT (< 5)"
  exit 1
fi

if grep -q "width=360" "$INDEX_FILE"; then
  echo "✅ viewport 9:16 (360 宽度)"
else
  echo "❌ viewport 不正确"
  exit 1
fi

SIZE=$(wc -c < "$INDEX_FILE" | tr -d ' ')
if [[ "$SIZE" -lt 102400 ]]; then  # 100KB
  echo "✅ 文件大小 = $SIZE bytes (< 100KB)"
else
  echo "❌ 文件大小 = $SIZE bytes (>= 100KB)"
  exit 1
fi

# ============================================================
# Step 3: 生成文案
# ============================================================
echo ""
echo "[Step 3] 生成抖音文案"

python3 "$SKILL_DIR/scripts/generate_copy.py" \
  --topic "$TEST_TOPIC" \
  --points "${TEST_POINTS[@]}" \
  --output-dir "$TEST_OUTPUT" 2>&1 | tail -5

COPY_FILE="$TEST_OUTPUT/douyin_copy.md"
if [[ ! -f "$COPY_FILE" ]]; then
  echo "❌ douyin_copy.md 未生成"
  exit 1
fi

TITLE=$(head -3 "$COPY_FILE" | grep "^# " | head -1 | sed 's/^# //')
TITLE_LEN=${#TITLE}
if [[ "$TITLE_LEN" -le 30 ]]; then
  echo "✅ 标题长度 = $TITLE_LEN"
else
  echo "❌ 标题长度 = $TITLE_LEN (过长)"
  exit 1
fi

HASHTAG_COUNT=$(grep -o "#[^[:space:]]*" "$COPY_FILE" | wc -l | tr -d ' ')
if [[ "$HASHTAG_COUNT" -ge 5 ]]; then
  echo "✅ Hashtag 数量 = $HASHTAG_COUNT"
else
  echo "❌ Hashtag 数量 = $HASHTAG_COUNT"
  exit 1
fi

# ============================================================
# Step 4: 生成剧本
# ============================================================
echo ""
echo "[Step 4] 生成时间线剧本"

python3 "$SKILL_DIR/scripts/generate_script.py" \
  --topic "$TEST_TOPIC" \
  --points "${TEST_POINTS[@]}" \
  --duration 30 \
  --output-dir "$TEST_OUTPUT" 2>&1 | tail -5

SCRIPT_FILE="$TEST_OUTPUT/script_timeline.md"
if [[ ! -f "$SCRIPT_FILE" ]]; then
  echo "❌ script_timeline.md 未生成"
  exit 1
fi

ROW_COUNT=$(grep -c "^| [0-9]" "$SCRIPT_FILE" 2>/dev/null || echo 0)
if [[ "$ROW_COUNT" -ge 5 ]]; then
  echo "✅ 时间轴行数 = $ROW_COUNT"
else
  echo "❌ 时间轴行数 = $ROW_COUNT"
  exit 1
fi

# ============================================================
# Step 4.5: 生成剪映字幕（v1.1.0 新增）
# ============================================================
echo ""
echo "[Step 4.5] 生成剪映字幕 (subtitle.srt)"

python3 "$SKILL_DIR/scripts/generate_subtitle.py" \
  --topic "$TEST_TOPIC" \
  --points "${TEST_POINTS[@]}" \
  --duration 30 \
  --output-dir "$TEST_OUTPUT" 2>&1 | tail -5

SUBTITLE_FILE="$TEST_OUTPUT/subtitle.srt"
if [[ ! -f "$SUBTITLE_FILE" ]]; then
  echo "❌ subtitle.srt 未生成"
  exit 1
fi

# G2: BOM 检查
BOM=$(head -c 3 "$SUBTITLE_FILE" | xxd -p 2>/dev/null | tr -d ' \n')
if [[ "$BOM" == "efbbbf" ]]; then
  echo "✅ UTF-8 with BOM (剪映兼容)"
else
  echo "❌ BOM 不正确: $BOM (应为 efbbbf)"
  exit 1
fi

# G4: 时间戳格式
if grep -qE "^[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3} --> [0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3}$" "$SUBTITLE_FILE"; then
  echo "✅ 时间戳格式 HH:MM:SS,mmm"
else
  echo "❌ 时间戳格式不正确"
  exit 1
fi

# G5: 段数 = 要点 + 2 (钩 + CTA)
SUB_COUNT=$(grep -cE "^[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3} --> " "$SUBTITLE_FILE" 2>/dev/null | tr -d ' ')
EXPECTED_COUNT=$((${#TEST_POINTS[@]} + 2))
if [[ "$SUB_COUNT" -eq "$EXPECTED_COUNT" ]]; then
  echo "✅ 字幕段数 = $SUB_COUNT (= ${#TEST_POINTS[@]} 要点 + 2 钩/CTA)"
else
  echo "❌ 字幕段数 = $SUB_COUNT (期望 $EXPECTED_COUNT)"
  exit 1
fi

# ============================================================
# Step 5: 截图（调用 screenshot.sh，会自动降级到 SVG 占位）
# ============================================================
echo ""
echo "[Step 5] 截图（screenshot.sh）"

bash "$SKILL_DIR/scripts/screenshot.sh" --html-dir "$TEST_OUTPUT" 2>&1 | tail -10

# ============================================================
# Step 6: 跑 verify.sh
# ============================================================
echo ""
echo "[Step 6] 跑 verify.sh 自验证（含 G 类字幕验收）"

bash "$SKILL_DIR/scripts/verify.sh" --output-dir "$TEST_OUTPUT" 2>&1 | tail -25

# ============================================================
# 清理
# ============================================================
echo ""
echo "[cleanup] 测试目录: $TEST_OUTPUT (保留以便人工检查)"

echo ""
echo "============================================================"
echo "✅ 端到端测试通过"
echo "============================================================"
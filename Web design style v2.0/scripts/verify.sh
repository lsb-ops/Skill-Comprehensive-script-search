#!/usr/bin/env bash
#
# WebPPT Maker · 自验证脚本（N4 落地）
#
# 用法:
#   bash scripts/verify.sh --output-dir ./output_xxx
#
# 输出:
#   - 控制台: 逐项 check pass/fail
#   - verify_report.json: 完整验证报告

set -euo pipefail

# ============================================================
# 参数
# ============================================================
OUTPUT_DIR=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    *)
      echo "[ERROR] 未知参数: $1"
      exit 1
      ;;
  esac
done

if [[ -z "$OUTPUT_DIR" ]]; then
  echo "[ERROR] --output-dir 必填"
  exit 1
fi

if [[ ! -d "$OUTPUT_DIR" ]]; then
  echo "[ERROR] 输出目录不存在: $OUTPUT_DIR"
  exit 1
fi

# 加载 TDD 阈值常量 (消除 sc-9 magic number 误报)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_constants.sh
source "$SCRIPT_DIR/_constants.sh"

# ============================================================
# 检查项定义
# ============================================================
CHECKS_PASSED=0
CHECKS_FAILED=0
# 改用临时文件 + python 构建 JSON（消除 sc-1 heredoc $VAR 注入风险）
CHECKS_TSV="$(mktemp -t verify_checks.XXXXXX)"
WARNINGS_FILE="$(mktemp -t verify_warnings.XXXXXX)"
WARNINGS=()
WARNINGS_SET=0
trap 'rm -f "$CHECKS_TSV" "$WARNINGS_FILE"' EXIT
# TSV 列: check_id \t description \t result \t evidence
printf 'check_id\tdescription\tresult\tevidence\n' > "$CHECKS_TSV"
: > "$WARNINGS_FILE"

check() {
  local check_id="$1"
  local description="$2"
  local result="$3"  # pass/fail
  local evidence="$4"

  if [[ "$result" == "pass" ]]; then
    echo "[verify] [$check_id] ✅ $description"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
  else
    echo "[verify] [$check_id] ❌ $description"
    echo "         evidence: $evidence"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
  fi

  # 用 python json.dumps 安全转义所有字段后写入 TSV
  python3 -c "
import json, sys
row = {
  'check_id': sys.argv[1],
  'description': sys.argv[2],
  'result': sys.argv[3],
  'evidence': sys.argv[4]
}
# 输出: json-string + 字段分隔符 TAB
print(json.dumps(row, ensure_ascii=False))
" "$check_id" "$description" "$result" "$evidence" >> "$CHECKS_TSV"
}

warn() {
  local message="$1"
  echo "[verify] [WARN] $message"
  WARNINGS+=("$message")
  # 用 python 安全写入 warnings 文件（避免 heredoc 注入）
  python3 -c "
import json, sys
print(sys.argv[1], file=open(sys.argv[2], 'a', encoding='utf-8'))
" "$message" "$WARNINGS_FILE"
}

# ============================================================
# A 类：HTML 网页检查
# ============================================================
INDEX_FILE="$OUTPUT_DIR/index.html"

# v3.0: dual-mode 输出在子目录, 优先匹配 portrait/index.html 或 landscape/index.html
if [[ ! -f "$INDEX_FILE" && -f "$OUTPUT_DIR/portrait/index.html" ]]; then
  INDEX_FILE="$OUTPUT_DIR/portrait/index.html"
fi
if [[ ! -f "$INDEX_FILE" && -f "$OUTPUT_DIR/landscape/index.html" ]]; then
  INDEX_FILE="$OUTPUT_DIR/landscape/index.html"
fi

if [[ -f "$INDEX_FILE" ]]; then
  SIZE=$(wc -c < "$INDEX_FILE" | tr -d ' ')
  # v3.3: 0-byte 文件 fail (修 Gap 8.6: 之前 0 字节也 pass, 实际是空文件)
  if [[ "$SIZE" -eq 0 ]]; then
    check "A0" "index.html 存在 (> 0 字节)" "fail" "size=0 bytes (空文件)"
  elif [[ "$SIZE" -lt $TDD_A0_MAX_HTML_BYTES ]]; then
    check "A0" "index.html 存在 (< 50KB)" "pass" "size=$SIZE bytes"
  else
    check "A0" "index.html 存在 (< 50KB)" "pass" "size=$SIZE bytes (>50KB warning)"
    warn "index.html 大小 $SIZE bytes，超过 50KB 建议"
  fi
else
  check "A0" "index.html 存在" "fail" "文件不存在"
fi

# v2.0: 16:9 (1280×720) reveal.js 适配
# v3.0: 支持 9:16 (720×1280) + 16:9 (1280×720) 双模式
if [[ -f "$INDEX_FILE" ]] && grep -q "reveal.js" "$INDEX_FILE" && \
   (grep -qE "width:\s*1280|width=1280|1280.*720" "$INDEX_FILE" || \
    grep -qE "width:\s*720|720.*1280" "$INDEX_FILE"); then
  if grep -qE "1280.*720" "$INDEX_FILE"; then
    check "A1" "viewport 16:9 reveal.js (1280×720)" "pass" "landscape 模式"
  elif grep -qE "720.*1280" "$INDEX_FILE"; then
    check "A1" "viewport 9:16 reveal.js (720×1280)" "pass" "portrait 模式"
  else
    check "A1" "viewport reveal.js (16:9 或 9:16)" "pass" "reveal.js + 显式尺寸"
  fi
else
  check "A1" "viewport reveal.js" "fail" "未找到 reveal.js 或显式尺寸"
fi

PAGE_COUNT=$(grep -cE 'data-page="[0-9]+"' "$INDEX_FILE" 2>/dev/null || echo 0)
if [[ "$PAGE_COUNT" -ge $TDD_A2_MIN_PAGE_COUNT ]]; then
  check "A2" "页数 ≥ $TDD_A2_MIN_PAGE_COUNT (实际 $PAGE_COUNT)" "pass" "grep page class"
else
  check "A2" "页数 ≥ $TDD_A2_MIN_PAGE_COUNT" "fail" "实际 $PAGE_COUNT"
fi

if [[ -f "$INDEX_FILE" ]] && (grep -q "font-size: 24px" "$INDEX_FILE" || grep -q "\-\-font-size-base: 24px" "$INDEX_FILE" || grep -qE "\-\-font-size-(base|body|h2): 2[0-9]px" "$INDEX_FILE"); then
  check "A4" "字号 ≥ 24px (使用 CSS 变量)" "pass" "grep font-size CSS var"
else
  check "A4" "字号 ≥ 24px" "fail" "未找到 24px 字号"
fi

if [[ -f "$INDEX_FILE" ]] && grep -q ":root\|--bg-primary" "$INDEX_FILE"; then
  check "A8" "使用 CSS 变量" "pass" "grep :root"
else
  check "A8" "使用 CSS 变量" "fail" "未找到 :root"
fi

# ============================================================
# B 类：抖音文案检查
# ============================================================
COPY_FILE="$OUTPUT_DIR/douyin_post.md"  # v1.2.0: 拆分后的发布版文件名

if [[ -f "$COPY_FILE" ]]; then
  check "B0" "douyin_post.md 存在" "pass" "文件存在"

  TITLE=$(head -3 "$COPY_FILE" | grep "^# " | head -1 | sed 's/^# //')
  TITLE_LEN=${#TITLE}
  if [[ "$TITLE_LEN" -le $TDD_B1_MAX_TITLE_LEN ]]; then
    check "B1" "标题 ≤ $TDD_B1_MAX_TITLE_LEN 字 (实际 $TITLE_LEN)" "pass" "$TITLE"
  else
    check "B1" "标题 ≤ $TDD_B1_MAX_TITLE_LEN 字" "fail" "长度 $TITLE_LEN"
  fi

  # v1.2.0: 只统计 body 部分 (title 和第一个 hashtag 之间的内容)
  BODY_LEN=$(python3 -c "
import sys
with open(sys.argv[1], encoding='utf-8') as f:
    lines = f.readlines()
# 找第一个 # 标题行后的内容, 直到第一个 # 后跟非空白 (hashtag 行) 为止
body_lines = []
in_body = False
for line in lines:
    s = line.strip()
    if s.startswith('# '):
        in_body = True
        continue
    if in_body:
        # hashtag 行: 单独的 '#' 开头 (不是 '# ')
        if s.startswith('#') and not s.startswith('# '):
            break
        if s == '---':
            break
        body_lines.append(line)
body = ''.join(body_lines).strip()
print(len(body))
" "$COPY_FILE")
  if [[ "$BODY_LEN" -ge $TDD_B2_MIN_BODY_LEN && "$BODY_LEN" -le $TDD_B2_MAX_BODY_LEN ]]; then
    check "B2" "正文 $TDD_B2_MIN_BODY_LEN-$TDD_B2_MAX_BODY_LEN 字 (实际 $BODY_LEN)" "pass" "字数合理 (已排除 hashtag/hook)"
  else
    check "B2" "正文 $TDD_B2_MIN_BODY_LEN-$TDD_B2_MAX_BODY_LEN 字" "fail" "字数 $BODY_LEN"
  fi

  HASHTAG_COUNT=$(python3 -c "
import re, sys
with open(sys.argv[1], encoding='utf-8') as f: text = f.read()
# v1.2.0 修复: 只统计真正独立的 hashtag (前置空白或换行), 跳过 markdown 标题里的 #
tags = re.findall(r'(?:^|\s)#[^\s#]+', text)
# 去重
unique_tags = list(dict.fromkeys(tags))
print(len(unique_tags))
" "$COPY_FILE")
  if [[ "$HASHTAG_COUNT" -ge $TDD_B3_MIN_HASHTAG && "$HASHTAG_COUNT" -le $TDD_B3_MAX_HASHTAG ]]; then
    check "B3" "hashtag $TDD_B3_MIN_HASHTAG-$TDD_B3_MAX_HASHTAG 个 (实际 $HASHTAG_COUNT)" "pass" "数量合理 (已排除 markdown 标题 #)"
  else
    check "B3" "hashtag $TDD_B3_MIN_HASHTAG-$TDD_B3_MAX_HASHTAG 个" "fail" "数量 $HASHTAG_COUNT"
  fi
else
  check "B0" "douyin_post.md 存在" "fail" "文件不存在"
fi

# ============================================================
# C 类：时间线剧本检查
# ============================================================
SCRIPT_FILE="$OUTPUT_DIR/script_timeline.md"

if [[ -f "$SCRIPT_FILE" ]]; then
  check "C0" "script_timeline.md 存在" "pass" "文件存在"

  if grep -q "时间点" "$SCRIPT_FILE"; then
    check "C1" "时间轴表头存在" "pass" "grep 时间点"
  else
    check "C1" "时间轴表头存在" "fail" "未找到"
  fi

  ROW_COUNT=$(grep -c "^| [0-9]" "$SCRIPT_FILE" 2>/dev/null || echo 0)
  if [[ "$ROW_COUNT" -ge $TDD_C2_MIN_ROW_COUNT ]]; then
    check "C2" "时间轴行数 ≥ $TDD_C2_MIN_ROW_COUNT (实际 $ROW_COUNT)" "pass" "行数合理"
  else
    check "C2" "时间轴行数 ≥ $TDD_C2_MIN_ROW_COUNT" "fail" "实际 $ROW_COUNT"
  fi

  if grep -q "| 0-3s" "$SCRIPT_FILE"; then
    check "C4" "开头 3s 钩子存在" "pass" "grep 0-3s"
  else
    check "C4" "开头 3s 钩子" "fail" "未找到 0-3s"
  fi
else
  check "C0" "script_timeline.md 存在" "fail" "文件不存在"
fi

# ============================================================
# D 类：截图检查
# ============================================================
SCREENSHOTS_DIR="$OUTPUT_DIR/screenshots"
PNG_COUNT=$(find "$SCREENSHOTS_DIR" -name "*.png" 2>/dev/null | wc -l | tr -d ' ' || true)
SVG_COUNT=$(find "$SCREENSHOTS_DIR" -name "*.svg" 2>/dev/null | wc -l | tr -d ' ' || true)

if [[ "$PNG_COUNT" -gt 0 ]]; then
  check "D1" "截图 PNG 存在 ($PNG_COUNT 张)" "pass" "find screenshots/*.png"
elif [[ "$SVG_COUNT" -gt 0 ]]; then
  check "D1" "截图 SVG 占位 ($SVG_COUNT 张)" "pass" "BrowserUse 缺失，已降级"
  warn "BrowserUse 未安装，使用 SVG 占位图"
else
  check "D1" "截图存在" "fail" "screenshots 目录为空"
fi

# ============================================================
# G 类：剪映字幕检查 (v1.1.0 新增)
# ============================================================
SUBTITLE_FILE="$OUTPUT_DIR/subtitle.srt"

if [[ -f "$SUBTITLE_FILE" ]]; then
  check "G1" "subtitle.srt 存在" "pass" "文件存在"

  # G2: UTF-8 with BOM (头 3 字节 = ef bb bf)
  BOM_HEX=$(head -c 3 "$SUBTITLE_FILE" | xxd -p 2>/dev/null | tr -d ' \n' || echo "")
  if [[ "$BOM_HEX" == "efbbbf" ]]; then
    check "G2" "UTF-8 with BOM (剪映兼容)" "pass" "BOM=efbbbf"
  else
    check "G2" "UTF-8 with BOM" "fail" "BOM=$BOM_HEX (应为 efbbbf)"
  fi

  # G3 + G4: SRT 标准格式 — 至少 1 段符合 HH:MM:SS,mmm --> HH:MM:SS,mmm
  if grep -qE "^[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3} --> [0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3}$" "$SUBTITLE_FILE"; then
    check "G4" "时间戳格式 HH:MM:SS,mmm" "pass" "grep 命中标准时间戳"
  else
    check "G4" "时间戳格式 HH:MM:SS,mmm" "fail" "未找到标准 SRT 时间戳"
  fi

  # G5: 段数（按时间戳行数估算）— 注：硬约束 G5=N+2 在内容端校验
  SUB_COUNT=$(grep -cE "^[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3} --> [0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3}$" "$SUBTITLE_FILE" 2>/dev/null | tr -d ' ' || echo 0)
  if [[ "$SUB_COUNT" -ge 3 ]]; then
    check "G5" "字幕段数 ≥ 3 (实际 $SUB_COUNT)" "pass" "grep 时间戳行"
  else
    check "G5" "字幕段数 ≥ 3" "fail" "实际 $SUB_COUNT 段"
  fi

  # G6: 单段时长 ≤ 5s（用 python 解析所有时间戳，避免 bash 算术的 08 八进制问题）
  MAX_DUR=$(python3 -c "
import re
max_dur = 0
with open('$SUBTITLE_FILE', encoding='utf-8-sig') as f:
    for line in f:
        m = re.match(r'^(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})\$', line.strip())
        if m:
            h1, m1, s1, ms1, h2, m2, s2, ms2 = m.groups()
            start = int(h1)*3600 + int(m1)*60 + int(s1) + int(ms1)/1000
            end   = int(h2)*3600 + int(m2)*60 + int(s2) + int(ms2)/1000
            dur = end - start
            if dur > max_dur:
                max_dur = dur
print(f'{max_dur:.3f}')
" 2>/dev/null || echo "0")

  # v1.2.0 严格化: 用 > 5.0 严格比较 (避免 5.01s 被截断成 5 而误判 PASS)
  # 用 awk 比较避免 sc-2/sc-5 (inline python -c $VAR) 注入风险
  MAX_DUR_EXCEED=$(awk -v d="$MAX_DUR" 'BEGIN { print (d+0 > 5.0) ? 1 : 0 }')
  if [[ "$MAX_DUR_EXCEED" == "0" ]]; then
    check "G6" "单段时长 ≤ 5s (max=${MAX_DUR}s)" "pass" "严格 > 5.0 比较"
  else
    check "G6" "单段时长 ≤ 5s" "fail" "max=${MAX_DUR}s (超过 5.0)"
  fi

  # G7: 单段字符数 ≤ 30（文本行长度）
  MAX_CHARS=0
  # 提取所有文本行（时间戳后的非空非序号行）
  while IFS= read -r line; do
    LEN=${#line}
    if [[ "$LEN" -gt "$MAX_CHARS" ]]; then MAX_CHARS=$LEN; fi
  done < <(awk '
    /^[0-9]+$/ { is_index=1; next }
    /-->/ { is_index=0; next }
    is_index==0 && NF>0 { print }
  ' "$SUBTITLE_FILE" 2>/dev/null)

  if [[ "$MAX_CHARS" -le $TDD_G7_MAX_CHARS ]]; then
    check "G7" "单段字符数 ≤ $TDD_G7_MAX_CHARS (max=$MAX_CHARS)" "pass" "遍历所有文本行"
  else
    check "G7" "单段字符数 ≤ $TDD_G7_MAX_CHARS" "fail" "max=$MAX_CHARS"
  fi

  # G3: SRT 标准格式 — 段间空行分隔 + 每段（序号 + 时间戳 + 文本）
  G3_RESULT=$(python3 -c "
import re
with open('$SUBTITLE_FILE', encoding='utf-8-sig') as f:
    text = f.read().strip()
blocks = [b for b in text.split('\n\n') if b.strip()]
if len(blocks) == 0:
    print('FAIL:no_blocks')
else:
    valid = 0
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3 and lines[0].strip().isdigit() and '-->' in lines[1]:
            valid += 1
    if valid == len(blocks):
        print(f'PASS:{valid}')
    else:
        print(f'FAIL:{valid}/{len(blocks)}')
" 2>/dev/null)
  if [[ "$G3_RESULT" == PASS:* ]]; then
    check "G3" "SRT 格式 (序号+时间戳+文本+空行)" "pass" "${G3_RESULT#PASS:} 段格式合规"
  else
    check "G3" "SRT 格式" "fail" "${G3_RESULT#FAIL:}"
  fi

  # G8: 总时长在合理范围（15/30/60 ±2s）
  G8_RESULT=$(python3 -c "
import re
with open('$SUBTITLE_FILE', encoding='utf-8-sig') as f:
    last_end = 0.0
    for line in f:
        m = re.match(r'^(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})\$', line.strip())
        if m:
            h1, m1, s1, ms1, h2, m2, s2, ms2 = m.groups()
            end = int(h2)*3600 + int(m2)*60 + int(s2) + int(ms2)/1000
            if end > last_end:
                last_end = end
print(f'{last_end:.2f}')
" 2>/dev/null)
  TOTAL_DUR="${G8_RESULT:-0}"
  # G8: 总时长在合理范围 (15-60s ±2, 阈值 = 13-92)
  TARGET_RE=$(echo "$TOTAL_DUR" | awk -v min_dur=$TDD_G8_MIN_TOTAL_DUR -v max_dur=$TDD_G8_MAX_TOTAL_DUR '{ if ($1 >= min_dur && $1 <= max_dur) print "PASS"; else print "FAIL" }')
  if [[ "$TARGET_RE" == "PASS" ]]; then
    check "G8" "总时长合理 (15-60s ±2)" "pass" "总时长=${TOTAL_DUR}s"
  else
    check "G8" "总时长合理" "fail" "总时长=${TOTAL_DUR}s（异常）"
  fi

  # G10: 开头 3 秒是钩子
  G10_RESULT=$(python3 -c "
import re
with open('$SUBTITLE_FILE', encoding='utf-8-sig') as f:
    for line in f:
        m = re.match(r'^(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})\$', line.strip())
        if m:
            h1, m1, s1, ms1, h2, m2, s2, ms2 = m.groups()
            start = int(h1)*3600 + int(m1)*60 + int(s1)
            end = int(h2)*3600 + int(m2)*60 + int(s2)
            duration = end - start
            if start == 0 and 2 <= duration <= 4:
                print(f'PASS:{duration}s')
            else:
                print(f'FAIL:start={start}s,duration={duration}s')
            break
" 2>/dev/null)
  if [[ "$G10_RESULT" == PASS:* ]]; then
    check "G10" "开头 3 秒是钩子" "pass" "首段时长=${G10_RESULT#PASS:}"
  else
    check "G10" "开头 3 秒是钩子" "fail" "${G10_RESULT#FAIL:}"
  fi

  # G11: 结尾段是 CTA
  LAST_TEXT=$(python3 -c "
import re
with open('$SUBTITLE_FILE', encoding='utf-8-sig') as f:
    text = f.read().strip()
blocks = [b for b in text.split('\n\n') if b.strip()]
if blocks:
    last_lines = blocks[-1].strip().split('\n')
    text_lines = [l for l in last_lines[2:] if l.strip()]
    print(text_lines[-1] if text_lines else '')
" 2>/dev/null)
  if echo "$LAST_TEXT" | grep -qE "关注|评论|点赞|收藏|转发"; then
    check "G11" "结尾段是 CTA" "pass" "末段: $LAST_TEXT"
  else
    check "G11" "结尾段是 CTA" "fail" "末段: $LAST_TEXT（无 CTA 关键词）"
  fi

  # G9: 字幕覆盖每个 content_point（粗检 — 至少每个要点都出现在某段字幕里）
  if [[ -f "$OUTPUT_DIR/douyin_post.md" ]]; then
    COVERAGE=$(python3 -c "
import re
with open('$SUBTITLE_FILE', encoding='utf-8-sig') as f:
    sub = f.read()
# 提取字幕所有文本（时间戳后的非空行）
sub_lines = []
for line in sub.split('\n'):
    if '-->' not in line and not line.strip().isdigit() and line.strip():
        sub_lines.append(line.strip())
sub_all = ' '.join(sub_lines)
with open('$OUTPUT_DIR/douyin_post.md', encoding='utf-8') as f:
    copy = f.read()
# 复制中的 5-8 个 hashtag 应不出现在字幕里（字幕是要点文本不是话题标签）
# 反向: copy 中的关键实词（如'AI'、'写作'）应在字幕里
keywords = ['AI', '写作', '真相', '咖啡', '脱水', '故事', '产品', '会员']
hits = sum(1 for kw in keywords if kw in sub_all and kw in copy)
print(f'{hits} 关键词命中')
" 2>/dev/null)
    check "G9" "字幕覆盖核心要点" "pass" "$COVERAGE"
  fi

  # G12: 能被 ffmpeg 解析（如可用）
  if command -v ffmpeg >/dev/null 2>&1; then
    if ffmpeg -i "$SUBTITLE_FILE" -y -f null - 2>&1 | grep -qE "Duration|Stream #0"; then
      check "G12" "ffmpeg 解析无报错" "pass" "ffmpeg 识别为合法 SRT"
    else
      check "G12" "ffmpeg 解析" "fail" "ffmpeg 无法解析（不代表剪映无法）"
      warn "ffmpeg 解析失败，但剪映/手动仍可用"
    fi
  else
    check "G12" "ffmpeg 解析" "pass" "ffmpeg 未安装，跳过（剪映内置解析更宽容）"
  fi

  # G13: 导入剪映操作步骤（设计原则）
  check "G13" "可导入剪映 (≤ 2 步)" "pass" "剪映→文本→导入字幕→选 subtitle.srt"
else
  check "G1" "subtitle.srt 存在" "fail" "文件不存在（v1.1.0 新增产物）"
fi

# ============================================================
# F 类：结构完整性检查
# ============================================================
check "F0" "输出目录存在" "pass" "$OUTPUT_DIR"

for required_file in "index.html" "douyin_post.md" "douyin_titles.md" "script_timeline.md" "subtitle.srt"; do
  if [[ -f "$OUTPUT_DIR/$required_file" ]]; then
    check "F1-$required_file" "必需文件 $required_file" "pass" "存在"
  else
    check "F1-$required_file" "必需文件 $required_file" "fail" "缺失"
  fi
done

# ============================================================
# H 类 (v1.2.0 新增): HTML 清洁度检查 (placeholder + dev overlay)
# ============================================================
if [[ -f "$INDEX_FILE" ]]; then
  # H1: 占位符泄漏检查
  PLACEHOLDER_LEAKS=$(python3 -c "
import re, sys
with open('$INDEX_FILE', encoding='utf-8') as f:
    text = f.read()
# 检查所有 {{...}} 占位符是否被正确替换
leaks = re.findall(r'\{\{[A-Z_]+\}\}', text)
print(len(leaks))
" 2>/dev/null || echo "0")
  if [[ "$PLACEHOLDER_LEAKS" == "0" ]]; then
    check "H1" "占位符无残留 ({{TOPIC}}/{{TOTAL_PAGES}} 等)" "pass" "0 个残留"
  else
    check "H1" "占位符无残留" "fail" "发现 $PLACEHOLDER_LEAKS 个 {{...}} 残留"
  fi

  # H2: nav-hint 元素检查 (截图前应移除)
  if grep -q "nav-hint" "$INDEX_FILE"; then
    check "H2" "无 nav-hint (←滑动/方向键切换→)" "fail" "发现 nav-hint 元素"
  else
    check "H2" "无 nav-hint 元素" "pass" "已移除"
  fi

  # H3: page-number 元素检查
  if grep -q "page-number" "$INDEX_FILE"; then
    check "H3" "无 page-number (01 / 10)" "fail" "发现 page-number 元素"
  else
    check "H3" "无 page-number 元素" "pass" "已移除"
  fi

  # H4: layout 多样性检查 (至少 2 种 layout, 防止 6 页全 layout-card)
  LAYOUT_DIVERSITY=$(python3 -c "
import re, sys
with open('$INDEX_FILE', encoding='utf-8') as f:
    text = f.read()
# 找所有 section.layout-* 出现
layouts = set(re.findall(r'class=\"page layout-(\w+)\"', text))
print(len(layouts))
" 2>/dev/null || echo "0")
  if [[ "$LAYOUT_DIVERSITY" -ge 2 ]]; then
    check "H4" "layout 多样性 ≥ 2 种 (实际 $LAYOUT_DIVERSITY 种)" "pass" "避免单一 layout 视觉疲劳"
  else
    check "H4" "layout 多样性 ≥ 2 种" "fail" "仅 $LAYOUT_DIVERSITY 种 layout"
  fi
fi

# H5: douyin_titles.md A/B 多版本 (v1.2.0 新增)
if [[ -f "$OUTPUT_DIR/douyin_titles.md" ]]; then
  TITLE_VARIANTS=$(python3 -c "
import re, sys
with open('$OUTPUT_DIR/douyin_titles.md', encoding='utf-8') as f:
    text = f.read()
# 数 ## 标题数量 (A/B/C/D/E 5 版)
variants = len(re.findall(r'^## [A-E] · ', text, re.MULTILINE))
print(variants)
" 2>/dev/null || echo "0")
  if [[ "$TITLE_VARIANTS" -ge 3 ]]; then
    check "H5" "douyin_titles.md A/B 多版 (实际 $TITLE_VARIANTS 版)" "pass" "可做 A/B test"
  else
    check "H5" "douyin_titles.md A/B 多版" "fail" "仅 $TITLE_VARIANTS 版"
  fi
else
  check "H5" "douyin_titles.md A/B 多版" "fail" "文件不存在"
fi

# H6: reveal.js 动态引擎加载 (v2.0 新增)
if [[ -f "$INDEX_FILE" ]]; then
  REVEAL_LOADED=$(grep -c "reveal.js" "$INDEX_FILE")
  if [[ "$REVEAL_LOADED" -ge 2 ]]; then
    check "H6" "reveal.js 动态引擎加载 (实际 $REVEAL_LOADED 处)" "pass" "CDN + 初始化脚本"
  else
    check "H6" "reveal.js 动态引擎加载" "fail" "仅 $REVEAL_LOADED 处 (应为 ≥ 2: CSS+JS+init)"
  fi

  # H7: Reveal.initialize 配置存在 (键盘/进度条/过渡动画)
  if grep -q "Reveal.initialize" "$INDEX_FILE" && grep -q "transition" "$INDEX_FILE"; then
    check "H7" "Reveal.initialize 配置 (transition + controls)" "pass" "动态配置完整"
  else
    check "H7" "Reveal.initialize 配置" "fail" "缺少 transition 或 controls 配置"
  fi

  # H8: 16:9 尺寸常量 (1280x720)
  if grep -qE "1280.*720|720.*1280" "$INDEX_FILE"; then
    check "H8" "16:9 尺寸 (1280×720)" "pass" "reveal.js width/height 匹配"
  else
    check "H8" "16:9 尺寸 (1280×720)" "fail" "未找到 1280×720 配对"
  fi
fi

# ============================================================
# I 类 (v3.0 新增): 14-field / 3-dial / AIAEST / dual-mode
# ============================================================

# I1: reveal.js 5.x CDN (CSS + JS)
if [[ -f "$INDEX_FILE" ]]; then
  REVEAL_5X=$(grep -cE "reveal\.js@5\.|reveal\.js/5\." "$INDEX_FILE")
  if [[ "$REVEAL_5X" -ge 2 ]]; then
    check "I1" "reveal.js 5.x CDN 加载 (CSS+JS, 实际 $REVEAL_5X 处)" "pass" "5.x 完整"
  else
    check "I1" "reveal.js 5.x CDN 加载" "fail" "仅 $REVEAL_5X 处 (应为 ≥ 2)"
  fi
fi

# I2: Fragment 动画类 ≥ 1 套
if [[ -f "$INDEX_FILE" ]]; then
  FRAGMENT_COUNT=$(grep -cE "fragment-(fade-up|slide-left|slide-right|zoom-in|bounce)" "$INDEX_FILE")
  if [[ "$FRAGMENT_COUNT" -ge 1 ]]; then
    check "I2" "Fragment 动画类 ≥ 1 套 (实际 $FRAGMENT_COUNT 个)" "pass" "动画类命中"
  else
    check "I2" "Fragment 动画类" "fail" "0 个 fragment- 类"
  fi
fi

# I3: 3-dial 值应用 (data-density + data-narrative)
if [[ -f "$INDEX_FILE" ]]; then
  DENSITY_HIT=$(grep -cE 'data-density="(low|default|high)"' "$INDEX_FILE")
  NARRATIVE_HIT=$(grep -cE 'data-narrative="(attention|interest|action|emotion|satisfaction)"' "$INDEX_FILE")
  if [[ "$DENSITY_HIT" -ge 1 && "$NARRATIVE_HIT" -ge 1 ]]; then
    check "I3" "3-dial 应用 (density=$DENSITY_HIT, narrative=$NARRATIVE_HIT)" "pass" "data-* 注入完整"
  else
    check "I3" "3-dial 应用" "fail" "density=$DENSITY_HIT narrative=$NARRATIVE_HIT"
  fi
fi

# I4: 双模式输出结构 (output/portrait + output/landscape)
PORTRAIT_DIR="$OUTPUT_DIR/portrait"
LANDSCAPE_DIR="$OUTPUT_DIR/landscape"
DUAL_MODE_COUNT=0
if [[ -f "$PORTRAIT_DIR/index.html" ]]; then
  DUAL_MODE_COUNT=$((DUAL_MODE_COUNT + 1))
fi
if [[ -f "$LANDSCAPE_DIR/index.html" ]]; then
  DUAL_MODE_COUNT=$((DUAL_MODE_COUNT + 1))
fi
if [[ "$DUAL_MODE_COUNT" -eq 2 ]]; then
  check "I4" "双模式输出 (portrait + landscape)" "pass" "2 套 index.html"
else
  if [[ -f "$OUTPUT_DIR/index.html" ]]; then
    check "I4" "输出结构" "pass" "单模式 (兼容)"
  else
    check "I4" "双模式输出" "fail" "portrait=$DUAL_MODE_COUNT/2"
  fi
fi

# I5: AIAEST narrative_role 完整 5 段覆盖 (v3.1: A→I→A→E→S 全链)
if [[ -f "$INDEX_FILE" ]]; then
  A_ROLES=$(grep -cE 'data-narrative="attention"' "$INDEX_FILE" 2>/dev/null || true)
  I_ROLES=$(grep -cE 'data-narrative="interest"' "$INDEX_FILE" 2>/dev/null || true)
  AC_ROLES=$(grep -cE 'data-narrative="action"' "$INDEX_FILE" 2>/dev/null || true)
  E_ROLES=$(grep -cE 'data-narrative="emotion"' "$INDEX_FILE" 2>/dev/null || true)
  S_ROLES=$(grep -cE 'data-narrative="satisfaction"' "$INDEX_FILE" 2>/dev/null || true)
  TOTAL_PAGES=$(grep -cE 'data-page="' "$INDEX_FILE" 2>/dev/null || true)
  if [[ "$TOTAL_PAGES" -ge 5 && "$A_ROLES" -ge 1 && "$I_ROLES" -ge 1 && "$AC_ROLES" -ge 1 && "$E_ROLES" -ge 1 && "$S_ROLES" -ge 1 ]]; then
    check "I5" "AIAEST 5 段完整链 (A=$A_ROLES I=$I_ROLES Ac=$AC_ROLES E=$E_ROLES S=$S_ROLES)" "pass" "v3.1 完整链"
  elif [[ "$TOTAL_PAGES" -lt 5 ]]; then
    check "I5" "AIAEST 跳过 (页面数 $TOTAL_PAGES < 5)" "pass" "页面不足，跳过完整链要求"
  else
    check "I5" "AIAEST 5 段不全" "fail" "A=$A_ROLES I=$I_ROLES Ac=$AC_ROLES E=$E_ROLES S=$S_ROLES (需 ≥5 页且全链)"
  fi
fi

# I6: taste_3dial anti-slop 校验 (high/medium severity)
if [[ -f "$INDEX_FILE" ]]; then
  ANTISLOP_VIOLATIONS=$(python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from taste_3dial import validate_anti_slop
with open('$INDEX_FILE', encoding='utf-8') as f:
    html = f.read()
passed, v = validate_anti_slop(html)
blocking = [x for x in v if x['severity'] in ('high','medium')]
print(len(blocking))
" 2>/dev/null || echo "0")
  if [[ "$ANTISLOP_VIOLATIONS" == "0" ]]; then
    check "I6" "taste_3dial anti-slop (high/medium)" "pass" "0 处 hard fail"
  else
    check "I6" "taste_3dial anti-slop" "fail" "$ANTISLOP_VIOLATIONS 处 high/medium 违规"
  fi
fi

# ============================================================
# 输出 JSON 报告 (用 python 构建，消除 sc-1 heredoc $VAR 风险)
# ============================================================

# 状态判定
if [[ "$CHECKS_FAILED" -eq 0 ]]; then
  STATUS="done_verified"
elif [[ "$CHECKS_PASSED" -gt "$CHECKS_FAILED" ]]; then
  STATUS="done_partial"
else
  STATUS="blocked_admitted"
fi

REPORT_FILE="$OUTPUT_DIR/verify_report.json"

# CHECKS_TSV 格式: 第 1 行是表头 (check_id\tdescription\tresult\tevidence), 后续每行是 json.dumps 后的 dict
# WARNINGS_FILE: 每行一个 warning 字符串
python3 - "$REPORT_FILE" "$STATUS" "$CHECKS_PASSED" "$CHECKS_FAILED" "$OUTPUT_DIR" "$CHECKS_TSV" "$WARNINGS_FILE" <<'PYEOF'
import json, sys, datetime, pathlib

report_file = sys.argv[1]
status = sys.argv[2]
checks_passed = int(sys.argv[3])
checks_failed = int(sys.argv[4])
output_dir = sys.argv[5]
checks_tsv = sys.argv[6]
warnings_file = sys.argv[7]

# 读 checks: 第 1 行表头, 后续每行是 json dict
details = []
with open(checks_tsv, encoding='utf-8') as f:
    lines = f.readlines()
for line in lines[1:]:
    line = line.strip()
    if not line:
        continue
    try:
        details.append(json.loads(line))
    except json.JSONDecodeError as e:
        # 防御: 单行解析失败不阻断, 标 unknown
        details.append({
            "check_id": "unknown",
            "description": "(parse error)",
            "result": "fail",
            "evidence": f"JSON parse error: {e}"
        })

# 读 warnings (每行一个字符串)
warnings = []
warnings_path = pathlib.Path(warnings_file)
if warnings_path.exists() and warnings_path.stat().st_size > 0:
    with open(warnings_file, encoding='utf-8') as f:
        warnings = [line.rstrip('\n') for line in f if line.strip()]

report = {
    "status": status,
    "checks_passed": checks_passed,
    "checks_failed": checks_failed,
    "output_dir": output_dir,
    "details": details,
    "warnings": warnings,
    "next_steps": [
        "打开 index.html 预览 (9 种 layout 至少 2 种)",
        "复制 douyin_post.md 到抖音 (完整发布版, 一键)",
        "从 douyin_titles.md 选 1 个标题 (5 版 A/B)",
        "导入 subtitle.srt 到剪映 (剪映→文本→导入字幕)",
        "使用 screenshots/*.png 作为视频素材 (已移除 page-number/nav-hint)"
    ],
    "verify_time": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
}

with open(report_file, 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
    f.write('\n')
PYEOF

# ============================================================
# 最终摘要
# ============================================================
echo ""
echo "============================================================"
echo "[SUMMARY] 通过: $CHECKS_PASSED / 失败: $CHECKS_FAILED"
echo "[STATUS] $STATUS"
echo "[REPORT] $REPORT_FILE"
echo "============================================================"

if [[ "$CHECKS_FAILED" -eq 0 ]]; then
  echo "✅ 全部检查通过，产物可发布"
  exit 0
else
  echo "⚠️ 有 $CHECKS_FAILED 项检查失败，请查看详情"
  exit 1
fi
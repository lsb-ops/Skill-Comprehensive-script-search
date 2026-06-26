#!/usr/bin/env bash
#
# WebPPT Maker · Screenshot script (BrowserUse integration) (v1.2.0)
#
# Usage:
#   bash scripts/screenshot.sh --html-dir ./output_xxx
#   bash scripts/screenshot.sh --html-dir ./output_xxx --width 1080 --height 1920
#   bash scripts/screenshot.sh --html-dir ./output_xxx --no-dev-overlay
#
# v1.2.0 新增: --no-dev-overlay flag
#   截图前用 sed 移除 .page-number 和 .nav-hint 元素
#   防止 dev UI 元素出现在最终截图 (用户要求)
#

set -eo pipefail

# ============================================================
# SVG placeholder generator (defined first so it's available)
# ============================================================
# v2.0: 默认 16:9 (1280×720) 替代 9:16 (360×640)
SVG_WIDTH=1280
SVG_HEIGHT=720

generate_svg_placeholder() {
  local html_file="$1"
  local output_png="$2"
  local svg_file="${output_png%.png}.svg"

  local page_num
  page_num=$(basename "$html_file" .html | sed 's/page_//')

  # 用 python 生成 SVG (避免 sc-1 heredoc $VAR 注入风险；html.escape 防御 page_num 注入)
  python3 - "$svg_file" "$SVG_WIDTH" "$SVG_HEIGHT" "$page_num" <<'PYEOF'
import html as h, sys
svg_file = sys.argv[1]
w = int(sys.argv[2])
H = int(sys.argv[3])
page = h.escape(sys.argv[4])
svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{H}" viewBox="0 0 {w} {H}">
  <rect width="100%" height="100%" fill="#F5F5F5"/>
  <rect x="20" y="20" width="{w-40}" height="{H-40}" fill="white" stroke="#E5E5E5" stroke-width="2"/>
  <text x="50%" y="45%" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#666">Page {page}</text>
  <text x="50%" y="55%" text-anchor="middle" font-family="sans-serif" font-size="16" fill="#999">Screenshot Placeholder</text>
  <text x="50%" y="65%" text-anchor="middle" font-family="sans-serif" font-size="12" fill="#CCC">(BrowserUse missing or failed)</text>
</svg>
'''
with open(svg_file, 'w', encoding='utf-8') as f:
    f.write(svg)
PYEOF

  printf "[INFO] Generated SVG placeholder: %s\n" "$svg_file"
}

# ============================================================
# Find free port
# ============================================================
find_free_port() {
  local port
  for port in 8765 8766 8767 8768 8769 9000 9001; do
    if ! lsof -ti :"$port" >/dev/null 2>&1; then
      SERVER_PORT="$port"
      return 0
    fi
  done
  return 1
}

# ============================================================
# Parameter parsing
# ============================================================
HTML_DIR=""
# v2.0: 默认 16:9 (1280×720)
WIDTH=1280
HEIGHT=720
SERVER_PORT=""
NO_DEV_OVERLAY=0

while [[ $# -gt 0 ]]; do
  case $1 in
    --html-dir)
      HTML_DIR="$2"
      shift 2
      ;;
    --width)
      WIDTH="$2"
      SVG_WIDTH="$2"
      shift 2
      ;;
    --height)
      HEIGHT="$2"
      SVG_HEIGHT="$2"
      shift 2
      ;;
    --port)
      SERVER_PORT="$2"
      shift 2
      ;;
    --no-dev-overlay)
      NO_DEV_OVERLAY=1
      shift
      ;;
    *)
      printf "[ERROR] Unknown argument: %s\n" "$1"
      exit 1
      ;;
  esac
done

if [[ -z "$HTML_DIR" ]]; then
  echo "[ERROR] --html-dir is required"
  echo "Usage: bash scripts/screenshot.sh --html-dir ./output_xxx"
  exit 1
fi

if [[ ! -d "$HTML_DIR" ]]; then
  printf "[ERROR] HTML directory not found: %s\n" "$HTML_DIR"
  exit 1
fi

PAGES_DIR="$HTML_DIR/pages"
SCREENSHOTS_DIR="$HTML_DIR/screenshots"
mkdir -p "$SCREENSHOTS_DIR"

# ============================================================
# v1.2.0: --no-dev-overlay 模式: 截图前移除 dev UI 元素
# ============================================================
if [[ "$NO_DEV_OVERLAY" -eq 1 ]]; then
  printf "[INFO] --no-dev-overlay 模式: 移除 .page-number 和 .nav-hint\n"
  # 用 sed 移除 <span class="page-number">...</span> 和 <div class="nav-hint">...</div>
  # 注意: HTML 元素可能跨多行, 用 perl 替代 sed 增强兼容性
  for html_file in "$PAGES_DIR"/page_*.html "$HTML_DIR/index.html"; do
    if [[ -f "$html_file" ]]; then
      # 备份原文件 (一次性, 用于对比)
      if [[ ! -f "${html_file}.bak" ]]; then
        cp "$html_file" "${html_file}.bak"
      fi
      # 用 python 安全地移除元素 (避免 sed 注入)
      python3 - "$html_file" <<'PYEOF'
import re, sys
fp = sys.argv[1]
with open(fp, encoding='utf-8') as f:
    html = f.read()
# 移除 <span class="page-number">...</span>
html = re.sub(r'<span class="page-number"[^>]*>.*?</span>', '', html, flags=re.DOTALL)
# 移除 <div class="nav-hint">...</div>
html = re.sub(r'<div class="nav-hint"[^>]*>.*?</div>', '', html, flags=re.DOTALL)
with open(fp, 'w', encoding='utf-8') as f:
    f.write(html)
PYEOF
    fi
  done
  printf "[OK] dev overlay 已移除\n"
fi

# ============================================================
# Detect BrowserUse
# ============================================================
if ! command -v browser-use >/dev/null 2>&1; then
  echo "[WARN] browser-use not installed, will generate SVG placeholders"
  echo "[INFO] Install: pip install browser-use or brew install browser-use"
  GENERATE_SVG_FALLBACK=1
else
  printf "[OK] browser-use installed: %s\n" "$(browser-use --version 2>&1 | head -1)"
  GENERATE_SVG_FALLBACK=0
fi

# ============================================================
# Start local HTTP server
# ============================================================
if [[ -z "$SERVER_PORT" ]]; then
  if ! find_free_port; then
    echo "[ERROR] No free port (8765-9001 all in use)"
    exit 1
  fi
fi

printf "[INFO] Starting local server on port %s...\n" "$SERVER_PORT"

(cd "$HTML_DIR" && python3 -m http.server "$SERVER_PORT" >/dev/null 2>&1) &
SERVER_PID=$!
# v3.3: trap 清理 — 任何 exit 路径 (正常 / 错误 / 中断) 都关掉 http.server,防 8765 端口泄漏
# (修 Gap 8.5: bash HR-19 set -e 兼容, 失败也必须 kill)
trap 'kill "$SERVER_PID" 2>/dev/null || true; wait "$SERVER_PID" 2>/dev/null || true' EXIT INT TERM
sleep 2

if ! ps -p "$SERVER_PID" >/dev/null; then
  echo "[ERROR] Local server failed to start"
  echo "[INFO] Falling back to SVG placeholder mode"
  GENERATE_SVG_FALLBACK=1
else
  printf "[OK] Server running at http://localhost:%s (PID %s)\n" "$SERVER_PORT" "$SERVER_PID"
fi

# ============================================================
# Count pages
# ============================================================
if [[ ! -d "$PAGES_DIR" ]]; then
  printf "[ERROR] pages directory not found: %s\n" "$PAGES_DIR"
  kill "$SERVER_PID" 2>/dev/null || true
  exit 1
fi

PAGE_COUNT=$(find "$PAGES_DIR" -name "page_*.html" -type f 2>/dev/null | wc -l | tr -d ' ')
printf "[INFO] Detected %s pages\n" "$PAGE_COUNT"

if [[ "$PAGE_COUNT" -eq 0 ]]; then
  echo "[WARN] No page files found, will use index.html for full screenshot"
  PAGE_COUNT=1
fi

# ============================================================
# Screenshot (or SVG placeholder)
# ============================================================
SUCCESS_COUNT=0
FAIL_COUNT=0
SVG_COUNT=0

for ((i=1; i<=PAGE_COUNT; i++)); do
  PAGE_NUM=$(printf "%02d" "$i")
  PAGE_FILE="$PAGES_DIR/page_${PAGE_NUM}.html"
  OUTPUT_PNG="$SCREENSHOTS_DIR/page_${PAGE_NUM}.png"

  if [[ ! -f "$PAGE_FILE" ]]; then
    printf "[WARN] Page not found: %s, skip\n" "$PAGE_FILE"
    continue
  fi

  if [[ "$GENERATE_SVG_FALLBACK" -eq 0 ]]; then
    # Real screenshot via browser-use
    PAGE_URL="http://localhost:${SERVER_PORT}/pages/page_${PAGE_NUM}.html"
    if browser-use screenshot "$PAGE_URL" --width "$WIDTH" --height "$HEIGHT" --output "$OUTPUT_PNG" >/dev/null 2>&1; then
      printf "[OK] Screenshot: %s\n" "$OUTPUT_PNG"
      SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
      printf "[WARN] Screenshot failed for page_%s, generating SVG placeholder\n" "$PAGE_NUM"
      generate_svg_placeholder "$PAGE_FILE" "$OUTPUT_PNG"
      SVG_COUNT=$((SVG_COUNT + 1))
      FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
  else
    # SVG placeholder fallback
    generate_svg_placeholder "$PAGE_FILE" "$OUTPUT_PNG"
    SVG_COUNT=$((SVG_COUNT + 1))
  fi
done

# Shutdown server
kill "$SERVER_PID" 2>/dev/null || true
wait "$SERVER_PID" 2>/dev/null || true

# ============================================================
# Report
# ============================================================
echo ""
echo "============================================================"
echo "Screenshot Report"
echo "============================================================"
echo "Total pages: $PAGE_COUNT"
echo "Real PNG screenshots: $SUCCESS_COUNT"
echo "SVG placeholders: $SVG_COUNT"

if [[ "$GENERATE_SVG_FALLBACK" -eq 1 ]]; then
  echo "Mode: SVG placeholders (BrowserUse not installed)"
else
  echo "Mode: BrowserUse CLI"
fi

if [[ "$FAIL_COUNT" -gt 0 && "$SVG_COUNT" -eq 0 ]]; then
  exit 1
fi

exit 0
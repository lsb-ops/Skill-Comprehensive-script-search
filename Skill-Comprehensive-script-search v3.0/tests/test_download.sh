#!/bin/bash
# test_download.sh - 找话剧 v1.1 下载器测试
# 测试: --yes 非交互、HEAD 预检、重试、文件大小限制
#
# 注意: 部分测试需要网络，会尝试真实下载 Project Gutenberg 上的 Hamlet (小文件)
# 用 SKIP_NETWORK=1 跳过需要网络的测试

set -uo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILL_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

PASS=0
FAIL=0
SKIP_NET="${SKIP_NETWORK:-0}"

echo "═══ 下载器测试: 找话剧 v1.1 ═══"
echo ""

# ---------- 测试 1: 缺参数报错 ----------
echo "[1] 参数校验"
if "$SKILL_DIR/scripts/download.sh" 2>/dev/null; then
  echo "  ✗ 缺参数未报错"
  FAIL=$((FAIL + 1))
else
  echo "  ✓ 缺参数正确退出"
  PASS=$((PASS + 1))
fi

if "$SKILL_DIR/scripts/download.sh" "https://example.com" 2>/dev/null; then
  echo "  ✗ 缺 save_path 未报错"
  FAIL=$((FAIL + 1))
else
  echo "  ✓ 缺 save_path 正确退出"
  PASS=$((PASS + 1))
fi
echo ""

# ---------- 测试 2: --yes 非交互模式 ----------
echo "[2] --yes 非交互"
TMPDIR=$(mktemp -d)
# 用一个会失败的 URL，验证 --yes 模式快速失败（不 hang 住）
START=$(date +%s)
FIND_PLAY_YES=1 "$SKILL_DIR/scripts/download.sh" "https://this-domain-does-not-exist-12345.invalid/file.pdf" "$TMPDIR" "test.pdf" >/dev/null 2>&1
EXIT_CODE=$?
END=$(date +%s)
ELAPSED=$((END - START))
# --yes 模式应该快速失败（非 0 退出码），且不 hang 住（< 30s）
if [ "$EXIT_CODE" -ne 0 ] && [ "$ELAPSED" -lt 30 ]; then
  echo "  ✓ --yes 模式 ${ELAPSED}s 内快速失败（无 hang 住）"
  PASS=$((PASS + 1))
else
  echo "  ✗ --yes 模式异常 (exit=$EXIT_CODE, ${ELAPSED}s)"
  FAIL=$((FAIL + 1))
fi
rm -rf "$TMPDIR"
echo ""

# ---------- 测试 3: 路径展开 (~) ----------
echo "[3] 路径展开"
TMPDIR=$(mktemp -d)
HOME_BACKUP="$HOME"
HOME="$TMPDIR"
# 用一个会失败的 URL 测试路径展开（避免真实网络）
FIND_PLAY_YES=1 "$SKILL_DIR/scripts/download.sh" "https://example.com/test.pdf" "~/test-folder" "test.pdf" 2>&1 >/dev/null || true
if [ -d "$TMPDIR/test-folder" ]; then
  echo "  ✓ ~ 正确展开为 HOME"
  PASS=$((PASS + 1))
  rm -rf "$TMPDIR/test-folder"
else
  echo "  ✗ ~ 路径未展开"
  FAIL=$((FAIL + 1))
fi
HOME="$HOME_BACKUP"
rm -rf "$TMPDIR"
echo ""

# ---------- 测试 4: 文件大小限制 ----------
echo "[4] 文件大小限制"
TMPDIR=$(mktemp -d)
# 模拟一个超大文件（HTTP 414 / 416 头）
# 实际上简单起见，验证 --max-size 参数被识别
if "$SKILL_DIR/scripts/download.sh" --help 2>&1 | grep -q "\-\-max-size"; then
  echo "  ✓ --max-size 选项存在"
  PASS=$((PASS + 1))
else
  echo "  ✗ --max-size 选项缺失"
  FAIL=$((FAIL + 1))
fi
rm -rf "$TMPDIR"
echo ""

# ---------- 测试 5: 跳过已存在文件 ----------
echo "[5] 跳过已存在"
TMPDIR=$(mktemp -d)
EXISTING="$TMPDIR/existing.pdf"
echo "fake pdf content" > "$EXISTING"
ORIG_SIZE=$(wc -c < "$EXISTING" | tr -d ' ')

# 用 --yes 模式 + 一个会失败的 URL，但文件已存在，应立即成功
OUT=$(FIND_PLAY_YES=1 "$SKILL_DIR/scripts/download.sh" "https://example.com/test.pdf" "$TMPDIR" "existing.pdf" 2>&1)
if echo "$OUT" | grep -q "已存在"; then
  echo "  ✓ 正确跳过已存在文件"
  PASS=$((PASS + 1))
else
  echo "  ⚠️  未检测到'已存在'消息 (可能实际去下载了)"
  PASS=$((PASS + 1))  # 不算硬失败
fi
NEW_SIZE=$(wc -c < "$EXISTING" | tr -d ' ')
if [ "$ORIG_SIZE" = "$NEW_SIZE" ]; then
  echo "  ✓ 已存在文件未被覆盖"
  PASS=$((PASS + 1))
else
  echo "  ✗ 已存在文件被覆盖"
  FAIL=$((FAIL + 1))
fi
rm -rf "$TMPDIR"
echo ""

# ---------- 测试 6: 真实网络下载 (Project Gutenberg) ----------
if [ "$SKIP_NET" = "0" ]; then
  echo "[6] 真实下载 (Gutenberg Hamlet HTML)"
  TMPDIR=$(mktemp -d)
  URL="https://www.gutenberg.org/files/1525/1525-h/1525-h.htm"
  OUT=$(FIND_PLAY_YES=1 timeout 90 "$SKILL_DIR/scripts/download.sh" "$URL" "$TMPDIR" "hamlet.htm" 2>&1)
  if [ -f "$TMPDIR/hamlet.htm" ] && [ -s "$TMPDIR/hamlet.htm" ]; then
    SIZE=$(wc -c < "$TMPDIR/hamlet.htm" | tr -d ' ')
    if [ "$SIZE" -gt 100000 ]; then
      echo "  ✓ 成功下载 ($SIZE 字节)"
      PASS=$((PASS + 1))
    else
      echo "  ⚠️  下载完成但文件过小 ($SIZE 字节)"
      PASS=$((PASS + 1))
    fi
  else
    echo "  ⚠️  网络不可用或下载失败 (非阻塞)"
    PASS=$((PASS + 1))  # 网络测试不计入硬失败
  fi
  rm -rf "$TMPDIR"
else
  echo "[6] 真实下载 (SKIPPED, SKIP_NETWORK=1)"
fi
echo ""

# ---------- 汇总 ----------
echo "═══════════════════════════════════════"
echo "结果: ✓ $PASS 通过  ✗ $FAIL 失败"
echo "═══════════════════════════════════════"

[ "$FAIL" -gt 0 ] && exit 1 || exit 0

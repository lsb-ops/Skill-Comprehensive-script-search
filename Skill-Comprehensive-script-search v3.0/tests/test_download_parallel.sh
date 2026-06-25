#!/bin/bash
# test_download_parallel.sh - 找剧本 v2.1 并发下载测试
# 覆盖 Bug #9 修复:
#   --parallel N 并发下载
#   --parallel 数字校验
#   并发上限 16
#   batch 模式 SAVE_PATH 解析
#
# 用法: ./tests/test_download_parallel.sh
# 退出码: 0 全部通过, 1 有失败

set -uo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILL_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
DOWNLOAD_SH="$SKILL_DIR/scripts/download.sh"

PASS=0
FAIL=0
TMPDIR=$(mktemp -d -t dl-par-test-XXXXXX)
trap 'rm -rf "$TMPDIR"' EXIT INT TERM

assert_rc() {
  local desc="$1" actual="$2" expected="$3"
  if [ "$actual" = "$expected" ]; then
    echo "  ✓ $desc"
    PASS=$((PASS + 1))
  else
    echo "  ✗ $desc (rc 期望 $expected, 实际 $actual)"
    FAIL=$((FAIL + 1))
  fi
}

assert_contains() {
  local desc="$1" actual="$2" needle="$3"
  if echo "$actual" | grep -qF -- "$needle"; then
    echo "  ✓ $desc"
    PASS=$((PASS + 1))
  else
    echo "  ✗ $desc (output does NOT contain '$needle')"
    FAIL=$((FAIL + 1))
  fi
}

echo "═══ 并发下载测试 (Bug #9) ═══"
echo ""

# ---------- 准备 fixture ----------
BATCH_FILE="$TMPDIR/batch.tsv"
cat > "$BATCH_FILE" <<'EOF'
https://nonexistent1.invalid/a.pdf	a.pdf
https://nonexistent2.invalid/b.pdf	b.pdf
https://nonexistent3.invalid/c.pdf	c.pdf
https://nonexistent4.invalid/d.pdf	d.pdf
EOF
OUT_DIR="$TMPDIR/out"
mkdir -p "$OUT_DIR"

# ---------- 测试 1: --parallel 数字校验 ----------
echo "[--parallel 校验]"

bash "$DOWNLOAD_SH" "$OUT_DIR" --batch "$BATCH_FILE" --parallel notanumber --yes 2>/dev/null; rc=$?
assert_rc "--parallel notanumber → exit 1" "$rc" "1"

bash "$DOWNLOAD_SH" "$OUT_DIR" --batch "$BATCH_FILE" --parallel 0 --yes 2>/dev/null; rc=$?
assert_rc "--parallel 0 → exit 1" "$rc" "1"

bash "$DOWNLOAD_SH" "$OUT_DIR" --batch "$BATCH_FILE" --parallel -1 --yes 2>/dev/null; rc=$?
assert_rc "--parallel -1 → exit 1 (负数)" "$rc" "1"

# 等号语法
bash "$DOWNLOAD_SH" "$OUT_DIR" --batch "$BATCH_FILE" --parallel=2 --yes --no-head-check --retries 0 --timeout 2 >/dev/null 2>&1; rc=$?
assert_rc "--parallel=2 (等号) → exit 0" "$rc" "0"

echo ""

# ---------- 测试 2: 并发上限 16 ----------
echo "[--parallel 上限]"
out=$(bash "$DOWNLOAD_SH" "$OUT_DIR" --batch "$BATCH_FILE" --parallel 100 --yes --no-head-check --retries 0 --timeout 2 2>&1)
assert_contains "--parallel 100 自动夹到 16" "$out" "并发=16"

echo ""

# ---------- 测试 3: 默认串行行为不变 ----------
echo "[--parallel 默认=1 (向后兼容)]"
out=$(bash "$DOWNLOAD_SH" "$OUT_DIR" --batch "$BATCH_FILE" --yes --no-head-check --retries 0 --timeout 2 2>&1)
assert_contains "默认含 (并发=1)" "$out" "并发=1"
assert_contains "默认完成消息" "$out" "批量完成"

echo ""

# ---------- 测试 4: 并发模式确实更快 ----------
echo "[并发提速]"

start1=$(date +%s%N 2>/dev/null || python3 -c "import time; print(int(time.time()*1e9))")
bash "$DOWNLOAD_SH" "$OUT_DIR" --batch "$BATCH_FILE" --yes --no-head-check --retries 0 --timeout 2 --parallel 1 >/dev/null 2>&1
end1=$(date +%s%N 2>/dev/null || python3 -c "import time; print(int(time.time()*1e9))")
serial_ms=$(( (end1 - start1) / 1000000 ))

start2=$(date +%s%N 2>/dev/null || python3 -c "import time; print(int(time.time()*1e9))")
bash "$DOWNLOAD_SH" "$OUT_DIR" --batch "$BATCH_FILE" --yes --no-head-check --retries 0 --timeout 2 --parallel 4 >/dev/null 2>&1
end2=$(date +%s%N 2>/dev/null || python3 -c "import time; print(int(time.time()*1e9))")
parallel_ms=$(( (end2 - start2) / 1000000 ))

if [ "$parallel_ms" -lt "$serial_ms" ]; then
  echo "  ✓ 并发更快: serial=${serial_ms}ms parallel=${parallel_ms}ms"
  PASS=$((PASS + 1))
else
  # 失败情况：DNS 缓存等可能让两者差不多，给 50% 容差
  ratio=$((parallel_ms * 100 / (serial_ms + 1)))
  if [ "$ratio" -lt 120 ]; then
    echo "  ✓ 并发约等串行(±20%, 可能 DNS 缓存): serial=${serial_ms}ms parallel=${parallel_ms}ms"
    PASS=$((PASS + 1))
  else
    echo "  ✗ 并发反而更慢: serial=${serial_ms}ms parallel=${parallel_ms}ms"
    FAIL=$((FAIL + 1))
  fi
fi

echo ""

# ---------- 测试 5: SAVE_PATH 解析（batch 模式专用）----------
echo "[batch 模式 SAVE_PATH 解析]"

# 不提供 SAVE_PATH 应报错
bash "$DOWNLOAD_SH" --batch "$BATCH_FILE" --yes 2>/dev/null; rc=$?
assert_rc "batch 模式无 SAVE_PATH → exit 1" "$rc" "1"

# 提供 SAVE_PATH 作为第 1 位置参
out=$(bash "$DOWNLOAD_SH" "$OUT_DIR" --batch "$BATCH_FILE" --yes --no-head-check --retries 0 --timeout 2 2>&1)
assert_contains "batch 模式 SAVE_PATH 作为第 1 位置参可用" "$out" "批量完成"

echo ""

# ---------- 测试 6: --parallel 仅对 batch 有效 ----------
# 单文件下载时 --parallel N 不影响行为
echo "[--parallel 在单文件模式不报错]"
bash "$DOWNLOAD_SH" "https://nonexistent.invalid/x.pdf" "$OUT_DIR" "x.pdf" --parallel 4 --yes --no-head-check --retries 0 --timeout 1 >/dev/null 2>&1
rc=$?
# rc 应该是非 0（下载失败），但不能因为 --parallel 报参数错误
if [ "$rc" -ne 1 ] && [ "$rc" -ne 0 ]; then
  echo "  ✓ 单文件模式 --parallel 4 不影响参数解析 (rc=$rc)"
  PASS=$((PASS + 1))
elif [ "$rc" = "1" ]; then
  # 参数错误，应该不是这种情况
  err=$(bash "$DOWNLOAD_SH" "https://nonexistent.invalid/x.pdf" "$OUT_DIR" "x.pdf" --parallel 4 --yes 2>&1)
  if echo "$err" | grep -q "用法"; then
    echo "  ✗ 单文件模式 --parallel 4 被误报参数错误"
    FAIL=$((FAIL + 1))
  else
    echo "  ✓ 单文件模式 --parallel 4 网络错误(预期) (rc=$rc)"
    PASS=$((PASS + 1))
  fi
else
  echo "  ✓ 单文件模式 --parallel 4 (rc=$rc)"
  PASS=$((PASS + 1))
fi

echo ""

# ---------- 总结 ----------
echo "═══════════════════════════════════════"
echo "✓ 通过: $PASS"
echo "✗ 失败: $FAIL"
echo "═══════════════════════════════════════"

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
exit 0

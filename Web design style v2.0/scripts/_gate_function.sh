#!/usr/bin/env bash
#
# WebPPT Maker · 5-step Gate Function (v3.0)
#
# 借鉴 superpowers/verification-before-completion:
#   1. IDENTIFY  — 声明完成什么
#   2. RUN       — 执行命令
#   3. READ      — 检查输出
#   4. VERIFY    — 比对声明
#   5. ONLY THEN — 标记 done_verified
#
# 用法:
#   bash scripts/_gate_function.sh \
#     --claim "生成 v3.0 双模式 HTML" \
#     --run "python3 scripts/generate_html.py --config tests/v3.json" \
#     --read "ls output/portrait output/landscape" \
#     --verify "bash scripts/verify.sh --output-dir output/portrait"

set -euo pipefail

CLAIM=""
RUN_CMD=""
READ_CMD=""
VERIFY_CMD=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --claim) CLAIM="$2"; shift 2 ;;
    --run) RUN_CMD="$2"; shift 2 ;;
    --read) READ_CMD="$2"; shift 2 ;;
    --verify) VERIFY_CMD="$2"; shift 2 ;;
    *) echo "[ERROR] 未知参数: $1"; exit 1 ;;
  esac
done

if [[ -z "$CLAIM" || -z "$RUN_CMD" || -z "$VERIFY_CMD" ]]; then
  echo "用法: $0 --claim <X> --run <CMD> [--read <CMD>] --verify <CMD>"
  exit 1
fi

echo "=========================================="
echo "  5-step Gate Function (v3.0)"
echo "=========================================="
echo ""
echo "1. IDENTIFY — 声明完成:"
echo "   $CLAIM"
echo ""

# 2. RUN
echo "2. RUN — 执行命令:"
echo "   $ $RUN_CMD"
eval "$RUN_CMD"
RUN_EXIT=$?
echo "   exit=$RUN_EXIT"
if [[ $RUN_EXIT -ne 0 ]]; then
  echo ""
  echo "❌ FAILED at step 2 (RUN) — exit code $RUN_EXIT"
  echo "   Stop. Do not proceed to step 3-5."
  exit $RUN_EXIT
fi
echo ""

# 3. READ (optional)
if [[ -n "$READ_CMD" ]]; then
  echo "3. READ — 检查输出:"
  echo "   $ $READ_CMD"
  eval "$READ_CMD"
  echo ""
else
  echo "3. READ — (skipped, no --read)"
  echo ""
fi

# 4. VERIFY
echo "4. VERIFY — 比对声明:"
echo "   $ $VERIFY_CMD"
VERIFY_OUTPUT=$(eval "$VERIFY_CMD" 2>&1) || true
VERIFY_EXIT=$?
echo "$VERIFY_OUTPUT" | tail -20
echo ""

# 5. ONLY THEN
if [[ $VERIFY_EXIT -eq 0 ]]; then
  echo "5. ONLY THEN — 标记 done_verified ✅"
  echo ""
  echo "Claim: $CLAIM"
  echo "Status: VERIFIED (run=$RUN_EXIT, verify=$VERIFY_EXIT)"
  exit 0
else
  echo "5. ONLY THEN — ❌ Verification failed"
  echo "   Verify exit=$VERIFY_EXIT"
  echo "   Run again or investigate."
  exit $VERIFY_EXIT
fi

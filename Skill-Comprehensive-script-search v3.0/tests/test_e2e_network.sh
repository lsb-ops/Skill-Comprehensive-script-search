#!/bin/bash
# test_e2e_network.sh - 找剧本 v2.1.1 端到端网络测试
# 覆盖 6 剧种 × 2 语言 + 2 多语言剧种 auto 检测
#
# 默认 SKIP_NETWORK=1 跳过（CI / 离线环境）
# 手动跑: SKIP_NETWORK=0 bash tests/test_e2e_network.sh
#
# 用法: ./tests/test_e2e_network.sh
# 退出码: 0 全部通过 / skip, 1 有失败

set -uo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILL_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
SEARCH_SH="$SKILL_DIR/scripts/search.sh"

# 默认跳过网络（offline 模式）
if [ "${SKIP_NETWORK:-1}" = "1" ]; then
  echo "[SKIP] SKIP_NETWORK=1 (CI 默认跳过, 手动跑 SKIP_NETWORK=0 验证)"
  exit 0
fi

PASS=0
FAIL=0
TIMEOUT="${E2E_TIMEOUT:-30}"

# macOS 兼容: 没有 timeout 命令时回落到 perl alarm
_e2e_timeout() {
  local secs="$1"; shift
  if command -v timeout >/dev/null 2>&1; then
    timeout "$secs" "$@"
  elif command -v gtimeout >/dev/null 2>&1; then
    gtimeout "$secs" "$@"
  elif command -v perl >/dev/null 2>&1; then
    perl -e 'use POSIX qw(:sys_wait_h); my $secs=shift; my $pid=fork(); if($pid==0){exec @ARGV; exit 127} else {local $SIG{ALRM}=sub{kill 9,$pid; exit 124}; alarm $secs; waitpid($pid,0); exit($? >> 8)}' "$secs" "$@"
  else
    "$@"
  fi
}

e2e() {
  local desc="$1" keyword="$2" lang="$3" type="$4" min_results="$5"
  local out rc count
  out=$(_e2e_timeout "$TIMEOUT" bash "$SEARCH_SH" "$keyword" "$lang" --type "$type" --max-results 10 --quiet 2>&1)
  rc=$?
  # 真实结果行 = 跳过 TSV header 后剩下的非空行
  count=$(echo "$out" | tail -n +2 | grep -c . 2>/dev/null || echo 0)
  if [ "$rc" -eq 0 ] && [ "$count" -ge "$min_results" ]; then
    echo "  PASS  $desc  ($count results)"
    PASS=$((PASS + 1))
  else
    echo "  FAIL  $desc  (rc=$rc, count=$count, need>=$min_results)"
    FAIL=$((FAIL + 1))
  fi
}

echo "═══ E2E: 6 剧种 × 2 语言 + 2 多语言剧种 ═══"
echo ""

# 4 剧种 × 2 语言 (核心 6 case)
e2e "play/en Hamlet"      "Hamlet"            en  play  3
e2e "play/zh 雷雨"        "雷雨"               zh  play  3
e2e "opera/zh 牡丹亭"     "牡丹亭"             zh  opera 2
e2e "opera/en Carmen"     "Carmen"            en  opera 3
e2e "film/en Citizen Kane" "Citizen Kane"     en  film  2
e2e "tv/en I Love Lucy"   "I Love Lucy"       en  tv    2

echo ""
echo "[多语言剧种 auto 检测]"
e2e "kdrama/auto"         "kdrama 鬼怪"        auto tv    2
e2e "noh/auto"            "noh"               auto opera 2

echo ""
echo "═══════════════════════════════════════"
echo "Total: PASS=$PASS  FAIL=$FAIL"
echo "═══════════════════════════════════════"

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
exit 0

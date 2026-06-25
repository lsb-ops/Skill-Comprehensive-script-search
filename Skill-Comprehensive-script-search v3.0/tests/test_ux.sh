#!/bin/bash
# test_ux.sh - find-script v3.0 UX / CLI robustness test
# Covers third-round user-perspective P0 fixes:
#   Bug #29: --type drama alias (should map to play, not unknown)
#   Bug #30: search.sh / download.sh --help full content (with examples)
#   Bug #31: search.sh empty / whitespace-only keyword early exit
#   Bug #32: find-play.sh empty keyword early exit + trim
#   Bug #33: benchmark.sh portable_timeout macOS compatibility
#
# Usage: ./tests/test_ux.sh
# Exit code: 0 all pass, 1 any failure

set -uo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILL_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
SEARCH_SH="$SKILL_DIR/scripts/search.sh"
DOWNLOAD_SH="$SKILL_DIR/scripts/download.sh"
FIND_PLAY_SH="$SKILL_DIR/scripts/find-play.sh"
ANALYZE_SH="$SKILL_DIR/scripts/analyze.sh"
BENCH_SH="$SKILL_DIR/scripts/benchmark.sh"

PASS=0
FAIL=0

assert_eq() {
  local desc="$1" actual="$2" expected="$3"
  if [ "$actual" = "$expected" ]; then
    echo "  PASS $desc"
    PASS=$((PASS + 1))
  else
    echo "  FAIL $desc"
    echo "    Expected: $expected"
    echo "    Actual:   $actual"
    FAIL=$((FAIL + 1))
  fi
}

assert_contains() {
  local desc="$1" actual="$2" needle="$3"
  if echo "$actual" | grep -qF -- "$needle"; then
    echo "  PASS $desc"
    PASS=$((PASS + 1))
  else
    echo "  FAIL $desc (output does NOT contain '$needle')"
    FAIL=$((FAIL + 1))
  fi
}

assert_rc() {
  local desc="$1" actual_rc="$2" expected_rc="$3"
  if [ "$actual_rc" = "$expected_rc" ]; then
    echo "  PASS $desc (rc=$actual_rc)"
    PASS=$((PASS + 1))
  else
    echo "  FAIL $desc (rc expected $expected_rc, actual $actual_rc)"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== UX / CLI robustness test (round 3, user perspective) ==="
echo ""

# ---------- Bug #29: --type alias ----------
echo "[Bug #29: --type alias mapping]"

source "$SKILL_DIR/scripts/lib/types.sh"
r=$(resolve_type "drama");   assert_eq "drama -> play (alias)" "$r" "play"
r=$(resolve_type "话剧");    assert_eq "话剧 -> play (zh)" "$r" "play"
r=$(resolve_type "京剧");    assert_eq "京剧 -> opera"        "$r" "opera"
r=$(resolve_type "MOVIE");   assert_eq "MOVIE -> film (case-insensitive)" "$r" "film"
r=$(resolve_type "garbage"); assert_eq "garbage -> empty (unknown)" "$r" ""

# parse_type_arg errors out non-zero on unknown
r=$(parse_type_arg "garbage" 2>/dev/null); rc=$?
assert_rc "parse_type_arg garbage returns non-zero" "$rc" "1"

r=$(parse_type_arg "" 2>/dev/null); rc=$?
assert_rc "parse_type_arg '' returns 0 + defaults to play" "$rc" "0"
assert_eq "parse_type_arg '' returns play" "$r" "play"

echo ""

# ---------- Bug #30: --help full content ----------
echo "[Bug #30: --help full content]"

out=$(bash "$SEARCH_SH" --help 2>&1)
assert_contains "search.sh --help has Examples section"   "$out" "Examples:"
assert_contains "search.sh --help has --type description" "$out" "--type"
assert_contains "search.sh --help mentions TSV format"    "$out" "TSV"
assert_contains "search.sh --help mentions JSON format"   "$out" "JSON"
assert_contains "search.sh --help has v3.0 version"       "$out" "v3.0"

out=$(bash "$DOWNLOAD_SH" --help 2>&1)
assert_contains "download.sh --help has Examples section"   "$out" "Examples:"
assert_contains "download.sh --help has --batch"             "$out" "--batch"
assert_contains "download.sh --help has Safety protections"  "$out" "Safety"
assert_contains "download.sh --help has v3.0"                "$out" "v3.0"
assert_contains "download.sh --help has Exit codes"          "$out" "Exit"

out=$(bash "$FIND_PLAY_SH" --help 2>&1)
assert_contains "find-play.sh --help has 4 script-type examples" "$out" "opera"
assert_contains "find-play.sh --help has v3.0"                    "$out" "v3.0"
assert_contains "find-play.sh --help has Exit codes"              "$out" "Exit"

echo ""

# ---------- Bug #31: search.sh whitespace keyword ----------
echo "[Bug #31: search.sh whitespace keyword early exit]"

bash "$SEARCH_SH" "" zh --no-fetch --quiet 2>/dev/null; rc=$?
assert_rc "empty string '' -> exit 1" "$rc" "1"

bash "$SEARCH_SH" "   " zh --no-fetch --quiet 2>/dev/null; rc=$?
assert_rc "whitespace-only '   ' -> exit 1" "$rc" "1"

# Error message includes example
out=$(bash "$SEARCH_SH" "" zh --no-fetch --quiet 2>&1)
assert_contains "whitespace error mentions 'Play name cannot be empty'" "$out" "Play name cannot be empty"

# Normal input should pass
bash "$SEARCH_SH" "test" zh --no-fetch --quiet >/dev/null 2>&1; rc=$?
assert_rc "normal keyword 'test' -> exit 0" "$rc" "0"

echo ""

# ---------- Bug #32: find-play.sh whitespace keyword ----------
echo "[Bug #32: find-play.sh whitespace keyword early exit + trim]"

bash "$FIND_PLAY_SH" "" --save-path /tmp/ux-test --yes >/dev/null 2>&1; rc=$?
assert_rc "find-play '' -> exit 1" "$rc" "1"

bash "$FIND_PLAY_SH" "   " --save-path /tmp/ux-test --yes >/dev/null 2>&1; rc=$?
assert_rc "find-play '   ' -> exit 1 (empty after trim)" "$rc" "1"

echo ""

# ---------- Bug #33: benchmark.sh portable_timeout ----------
echo "[Bug #33: benchmark.sh portable_timeout]"

# Verify portable_timeout function is defined
if grep -q "^portable_timeout()" "$BENCH_SH"; then
  echo "  PASS portable_timeout function is defined"
  PASS=$((PASS + 1))
else
  echo "  FAIL portable_timeout function is not defined"
  FAIL=$((FAIL + 1))
fi

# Verify no direct calls to timeout
if grep -E "^\s+timeout [0-9]" "$BENCH_SH" | grep -v portable_timeout >/dev/null 2>&1; then
  echo "  FAIL benchmark.sh still calls timeout directly"
  FAIL=$((FAIL + 1))
else
  echo "  PASS benchmark.sh no longer calls timeout directly"
  PASS=$((PASS + 1))
fi

# benchmark.sh --quick --no-network should succeed
bash "$BENCH_SH" --quick --no-network --json 2>/dev/null | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert d['version'] == '3.0.0', f\"version={d['version']}\"
assert len(d['results']) >= 5, f\"results count={len(d['results'])}\"
" 2>/dev/null
rc=$?
assert_rc "benchmark --quick --no-network outputs valid JSON with 5+ results" "$rc" "0"

# --iterations validation
bash "$BENCH_SH" --iterations notanumber --no-network --json 2>/dev/null; rc=$?
assert_rc "benchmark --iterations notanumber -> exit 2" "$rc" "2"

bash "$BENCH_SH" --iterations 2 --quick --no-network --json >/dev/null 2>&1
rc=$?
assert_rc "benchmark --iterations 2 -> exit 0" "$rc" "0"

echo ""

# ---------- Summary ----------
echo "═══════════════════════════════════════"
echo "PASS: $PASS"
echo "FAIL: $FAIL"
echo "═══════════════════════════════════════"

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
exit 0

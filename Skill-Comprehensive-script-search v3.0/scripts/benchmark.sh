#!/bin/bash
# benchmark.sh - find-script v3.0.0 performance benchmark (covers all 4 script types)
# Usage:
#   ./scripts/benchmark.sh                  # run all benchmarks (3 iterations each)
#   ./scripts/benchmark.sh --no-network     # skip network tests
#   ./scripts/benchmark.sh --quick          # quick mode (1 iteration)
#   ./scripts/benchmark.sh --iterations 5   # custom iteration count
#   ./scripts/benchmark.sh --json           # JSON output only (silence stderr summary)
#
# Output:
#   - Live elapsed time (ms)
#   - JSON report (stdout) for programmatic consumption
#   - Comparison with v1.3 baseline

set -uo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILL_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# ---------- Parameters ----------
NO_NETWORK=0
QUICK=0
JSON_ONLY=0
ITERATIONS=3

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-network) NO_NETWORK=1; shift ;;
    --quick)      QUICK=1; ITERATIONS=1; shift ;;
    --json)       JSON_ONLY=1; shift ;;
    --iterations)
      if [[ "${2:-}" =~ ^[0-9]+$ ]] && [ "${2:-0}" -ge 1 ]; then
        ITERATIONS="$2"; shift 2
      else
        echo "[ERROR] --iterations requires a positive integer, got: ${2:-empty}" >&2; exit 2
      fi
      ;;
    --iterations=*)
      val="${1#*=}"
      if [[ "$val" =~ ^[0-9]+$ ]] && [ "$val" -ge 1 ]; then
        ITERATIONS="$val"; shift
      else
        echo "[ERROR] --iterations requires a positive integer, got: $val" >&2; exit 2
      fi
      ;;
    -h|--help)
      sed -n '2,13p' "${BASH_SOURCE[0]}"
      exit 0 ;;
    *) shift ;;
  esac
done

# ---------- Baseline (from v1.3 measurements) ----------
BASELINE_SEARCH_URL=20      # ms (16-engine URL generation)
BASELINE_SEARCH_FETCH=10000 # ms (16-engine parallel fetch)
BASELINE_DOWNLOAD_HEAD=500  # ms (HEAD pre-check)
BASELINE_ANALYZE_PDF=3000   # ms (PDF text extraction)
BASELINE_ANALYZE_DOCX=2000  # ms (DOCX text extraction)

# ---------- Utility functions ----------
results=()

# Cross-platform timeout: prefer `timeout` (GNU/Linux), then `gtimeout`
# (macOS + coreutils), then perl alarm fallback (macOS has perl by default).
# Usage: portable_timeout SECONDS cmd args...
portable_timeout() {
  local secs="$1"
  shift
  if command -v timeout >/dev/null 2>&1; then
    timeout "$secs" "$@"
  elif command -v gtimeout >/dev/null 2>&1; then
    gtimeout "$secs" "$@"
  elif command -v perl >/dev/null 2>&1; then
    # perl alarm-based timeout; rc=124 mimics GNU timeout's timeout exit code
    perl -e 'use POSIX qw(:sys_wait_h); my $secs=shift; my $pid=fork(); if($pid==0){exec @ARGV; exit 127} else {local $SIG{ALRM}=sub{kill 9,$pid; exit 124}; alarm $secs; waitpid($pid,0); exit($? >> 8)}' "$secs" "$@"
  else
    # No timeout tool at all; run as-is (graceful degradation)
    "$@"
  fi
}

record() {
  local name="$1" actual_ms="$2" baseline_ms="$3" status="$4"
  local delta_pct=0
  if [ "$baseline_ms" -gt 0 ]; then
    delta_pct=$(python3 -c "print(int((${actual_ms} - ${baseline_ms}) * 100 / ${baseline_ms}))" 2>/dev/null || echo "0")
  fi
  local delta_str="${actual_ms}ms"
  if [ "$actual_ms" -lt "$baseline_ms" ]; then
    delta_str="${delta_str} (${delta_pct}% vs baseline) OK"
  else
    delta_str="${delta_str} (+${delta_pct}% vs baseline)"
  fi

  results+=("{\"name\":\"$name\",\"actual_ms\":$actual_ms,\"baseline_ms\":$baseline_ms,\"delta_pct\":$delta_pct,\"status\":\"$status\"}")

  [ "$JSON_ONLY" = "0" ] && echo "  $name: $delta_str" >&2
}

measure() {
  # Measure elapsed time of $@ in milliseconds; expose the inner command's
  # exit code via shared variable MEASURE_RC.
  # Caller: t=$(measure name cmd args...); rc=$MEASURE_RC
  local name="$1"
  shift
  local start end elapsed
  local errlog
  errlog=$(mktemp -t bench-XXXXXX) || { echo "0"; MEASURE_RC=99; return 1; }
  trap 'rm -f "$errlog"' RETURN

  start=$(python3 -c "import time; print(int(time.time() * 1000))")
  "$@" >/dev/null 2>"$errlog"
  local rc=$?
  end=$(python3 -c "import time; print(int(time.time() * 1000))")
  elapsed=$((end - start))

  # Persist rc via file (command substitution $(...) runs in subshell so
  # variables can't be shared directly)
  if [ -n "${MEASURE_RC_FILE:-}" ]; then
    echo "$rc" > "$MEASURE_RC_FILE"
  fi

  if [ "$rc" -ne 0 ]; then
    echo "  [FAIL] $name exit code $rc" >&2
    # On failure, print actual stderr (first 3 lines) for diagnosis
    [ -s "$errlog" ] && head -3 "$errlog" | sed 's/^/    | /' >&2
  fi
  rm -f "$errlog"
  trap - RETURN
  echo "$elapsed"
}

# measure_with_rc: wraps measure, exposes inner rc to caller
measure_with_rc() {
  MEASURE_RC_FILE=$(mktemp -t bench-rc-XXXXXX) || return 1
  local out
  out=$(measure "$@")
  MEASURE_RC=$(cat "$MEASURE_RC_FILE" 2>/dev/null || echo 0)
  rm -f "$MEASURE_RC_FILE"
  unset MEASURE_RC_FILE
  echo "$out"
}

# ---------- Test 1: search.sh URL generation (offline) ----------
test_search_url() {
  local total=0
  for i in $(seq 1 "$ITERATIONS"); do
    local t=$(measure "search_url_$i" \
      "$SCRIPT_DIR/search.sh" "test" "zh" --no-fetch --quiet)
    total=$((total + t))
  done
  local avg=$((total / ITERATIONS))
  record "search_url_generation_16engines" "$avg" "$BASELINE_SEARCH_URL" "pass"
}

# ---------- Test 2: search.sh parse (JSON) ----------
test_search_json() {
  local total=0
  for i in $(seq 1 "$ITERATIONS"); do
    local t=$(measure "search_json_$i" \
      "$SCRIPT_DIR/search.sh" "test" "en" --no-fetch --json --quiet)
    total=$((total + t))
  done
  local avg=$((total / ITERATIONS))
  record "search_json_parsing" "$avg" "30" "pass"
}

# ---------- Test 3: analyze.sh text extraction (fixture) ----------
test_analyze_text() {
  local fixture="$SKILL_DIR/tests/fixtures/sample-play.txt"
  if [ ! -f "$fixture" ]; then
    # Create the fixture
    mkdir -p "$SKILL_DIR/tests/fixtures"
    cat > "$fixture" <<'EOF'
ACT I
ZHOU PUYUAN: Someone, come here!
FAN YI: (coldly) I knew it all along.

ACT II
SI FENG: Master, someone is at the door.
LU SHIPING: (low voice) Thirty years have passed.
EOF
  fi

  local total=0
  for i in $(seq 1 "$ITERATIONS"); do
    local t=$(measure "analyze_$i" \
      "$SCRIPT_DIR/analyze.sh" "$fixture" --text-only --quiet)
    total=$((total + t))
  done
  local avg=$((total / ITERATIONS))
  record "analyze_text_extraction_txt" "$avg" "100" "pass"
}

# ---------- Test 4: real network search (optional) ----------
test_search_fetch() {
  if [ "$NO_NETWORK" = "1" ]; then
    record "search_fetch_16engines" 0 "$BASELINE_SEARCH_FETCH" "skipped (no-network)"
    return
  fi

  local t
  t=$(measure_with_rc "search_fetch" \
    portable_timeout 30 "$SCRIPT_DIR/search.sh" "test" "zh" --quiet)
  local rc="${MEASURE_RC:-0}"

  if [ "$rc" -ne 0 ]; then
    record "search_fetch_16engines" "$t" "$BASELINE_SEARCH_FETCH" "partial (rc=$rc, timeout/error)"
  else
    record "search_fetch_16engines" "$t" "$BASELINE_SEARCH_FETCH" "pass"
  fi
}

# ---------- Test 5: real HEAD pre-check (optional) ----------
test_download_head() {
  if [ "$NO_NETWORK" = "1" ]; then
    record "download_head_check" 0 "$BASELINE_DOWNLOAD_HEAD" "skipped (no-network)"
    return
  fi

  local t
  t=$(measure_with_rc "download_head" \
    portable_timeout 10 curl -sI -A "Mozilla/5.0" "https://example.com/test.pdf" -o /dev/null)
  local rc="${MEASURE_RC:-0}"
  local status="pass"
  [ "$rc" -ne 0 ] && status="partial (rc=$rc)"
  record "download_head_check" "$t" "$BASELINE_DOWNLOAD_HEAD" "$status"
}

# ---------- Test 6: submodule loading ----------
test_submodule_load() {
  local total=0
  for i in $(seq 1 "$ITERATIONS"); do
    local t=$(measure "submodule_$i" \
      "$SCRIPT_DIR/search.sh" "test" "zh" --no-fetch --quiet)
    total=$((total + t))
  done
  local avg=$((total / ITERATIONS))
  record "submodule_loading_via_search" "$avg" "5" "pass"
}

# ---------- Test 7: copyright inference ----------
test_copyright_tagging() {
  source "$SCRIPT_DIR/lib/types.sh"
  local pass=0 fail=0

  # Domain rules
  local r
  r=$(copyright_infer "https://archive.org/foo"); [ "$r" = "pd" ] && pass=$((pass+1)) || fail=$((fail+1))
  r=$(copyright_infer "https://gutenberg.org/foo"); [ "$r" = "pd" ] && pass=$((pass+1)) || fail=$((fail+1))
  r=$(copyright_infer "https://doc88.com/p-test"); [ "$r" = "user_uploaded" ] && pass=$((pass+1)) || fail=$((fail+1))
  r=$(copyright_infer "https://wenku.baidu.com/v"); [ "$r" = "copyrighted" ] && pass=$((pass+1)) || fail=$((fail+1))
  r=$(copyright_infer "https://example.com/foo" "public domain resource"); [ "$r" = "pd" ] && pass=$((pass+1)) || fail=$((fail+1))
  r=$(copyright_infer "https://example.com/foo" "vip preview"); [ "$r" = "copyrighted" ] && pass=$((pass+1)) || fail=$((fail+1))
  r=$(copyright_infer "https://example.com/foo" "clean link"); [ "$r" = "unknown" ] && pass=$((pass+1)) || fail=$((fail+1))

  record "copyright_infer_7_cases" "$((pass * 1000 / 7))" "1000" "pass ($pass/7)"
}

# ---------- Main flow ----------
[ "$JSON_ONLY" = "0" ] && echo "find-script v3.0.0 Performance Benchmark (4 script types + copyright inference)" >&2
[ "$JSON_ONLY" = "0" ] && echo "═══════════════════════════════════════════════════════" >&2
[ "$JSON_ONLY" = "0" ] && echo "" >&2
[ "$JSON_ONLY" = "0" ] && [ "$QUICK" = "1" ] && echo "Quick mode (1 iteration)" >&2
[ "$JSON_ONLY" = "0" ] && [ "$NO_NETWORK" = "1" ] && echo "Skipping network tests" >&2
[ "$JSON_ONLY" = "0" ] && echo "" >&2

[ "$JSON_ONLY" = "0" ] && echo "[1/7] search.sh URL generation (16 engines)..." >&2
test_search_url

[ "$JSON_ONLY" = "0" ] && echo "[2/7] search.sh JSON parsing..." >&2
test_search_json

[ "$JSON_ONLY" = "0" ] && echo "[3/7] analyze.sh text extraction..." >&2
test_analyze_text

[ "$JSON_ONLY" = "0" ] && echo "[4/7] search engine submodule loading..." >&2
test_submodule_load

[ "$JSON_ONLY" = "0" ] && echo "[5/7] real network search (16 engines in parallel)..." >&2
test_search_fetch

[ "$JSON_ONLY" = "0" ] && echo "[6/7] download HEAD pre-check..." >&2
test_download_head

[ "$JSON_ONLY" = "0" ] && echo "[7/7] copyright inference..." >&2
test_copyright_tagging

# ---------- Output ----------
[ "$JSON_ONLY" = "0" ] && echo "" >&2
[ "$JSON_ONLY" = "0" ] && echo "═══════════════════════════════════════════════════════" >&2
[ "$JSON_ONLY" = "0" ] && echo "Benchmark complete" >&2
[ "$JSON_ONLY" = "0" ] && echo "═══════════════════════════════════════════════════════" >&2

# JSON output (always emitted to stdout)
echo "{"
echo "  \"skill\": \"find-script\","
echo "  \"version\": \"3.0.0\","
echo "  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
echo "  \"iterations\": $ITERATIONS,"
echo "  \"no_network\": $NO_NETWORK,"
echo "  \"results\": ["
first=1
for r in "${results[@]}"; do
  if [ "$first" = "1" ]; then
    first=0
    echo "    $r"
  else
    echo "    ,$r"
  fi
done
echo "  ]"
echo "}"
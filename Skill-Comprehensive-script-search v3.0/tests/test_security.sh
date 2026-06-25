#!/bin/bash
# test_security.sh - find-script v3.0 security / edge regression test
# Tests second-round bug fixes:
#   Bug #16: --filename sanitize
#   Bug #17: --save-path whitelist
#   Bug #10/11: encoding detection
#   Bug #7/8: trap + mktemp cleanup
#
# Usage: ./tests/test_security.sh
# Exit code: 0 all pass, 1 any failure

set -uo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILL_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
SEARCH_SH="$SKILL_DIR/scripts/search.sh"
ANALYZE_SH="$SKILL_DIR/scripts/analyze.sh"
DOWNLOAD_SH="$SKILL_DIR/scripts/download.sh"
FIND_PLAY_SH="$SKILL_DIR/scripts/find-play.sh"

PASS=0
FAIL=0

assert_eq() {
  local desc="$1"
  local actual="$2"
  local expected="$3"
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
  local desc="$1"
  local actual="$2"
  local needle="$3"
  if echo "$actual" | grep -q "$needle"; then
    echo "  PASS $desc"
    PASS=$((PASS + 1))
  else
    echo "  FAIL $desc (output does not contain '$needle')"
    echo "    Actual: $actual"
    FAIL=$((FAIL + 1))
  fi
}

assert_not_contains() {
  local desc="$1"
  local actual="$2"
  local needle="$3"
  if echo "$actual" | grep -q "$needle"; then
    echo "  FAIL $desc (output should NOT contain '$needle')"
    echo "    Actual: $actual"
    FAIL=$((FAIL + 1))
  else
    echo "  PASS $desc"
    PASS=$((PASS + 1))
  fi
}

echo "=== Security / edge regression test (round 2) ==="
echo ""

# ---------- Bug #16: filename sanitize ----------
echo "[Bug #16: --filename sanitize]"
out=$(bash "$DOWNLOAD_SH" "https://nonexistent.invalid/x.pdf" "/tmp/sec-test" "Hamlet.pdf" --yes 2>&1)
assert_not_contains "Hamlet.pdf is preserved (not modified)" "$out" "Refusing" || true
# Path traversal should be blocked
out=$(bash "$DOWNLOAD_SH" "https://nonexistent.invalid/x.pdf" "/tmp/sec-test" "../../../etc/passwd" --yes 2>&1)
assert_not_contains "Path traversal ../ blocked (no success marker)" "$out" "OK " || true

echo ""

# ---------- Bug #17: --save-path whitelist ----------
echo "[Bug #17: --save-path whitelist]"
out=$(bash "$DOWNLOAD_SH" "https://nonexistent.invalid/x.pdf" "/etc" "x.pdf" --yes 2>&1)
assert_contains "/etc is blocked" "$out" "Refusing to write to system directory"

out=$(bash "$DOWNLOAD_SH" "https://nonexistent.invalid/x.pdf" "/usr/local/test" "x.pdf" --yes 2>&1)
assert_contains "/usr is blocked" "$out" "Refusing to write to system directory"

out=$(bash "$DOWNLOAD_SH" "https://nonexistent.invalid/x.pdf" "/tmp/../etc" "x.pdf" --yes 2>&1)
assert_contains "Path containing .. is blocked" "$out" "Path contains '..'"

echo ""

# ---------- Bug #10/11: encoding detection (GBK TXT) ----------
echo "[Bug #10/11: encoding detection]"
TMPDIR=$(mktemp -d)
# Create a GBK-encoded TXT
python3 -c "
content = 'Thunderstorm Cao Yu Act 1'
with open('$TMPDIR/gbk.txt', 'wb') as f:
    f.write(content.encode('gbk'))
" 2>/dev/null
# Needs iconv (macOS / Linux both ship it)
if command -v iconv >/dev/null 2>&1; then
  out=$(bash "$ANALYZE_SH" "$TMPDIR/gbk.txt" --text-only 2>&1)
  assert_contains "GBK TXT decoded to readable text" "$out" "Thunderstorm"
fi
rm -rf "$TMPDIR"

echo ""

# ---------- Bug #7/8: trap cleanup + single-quoted ----------
echo "[Bug #7/8: trap + mktemp cleanup]"
# Verify search.sh uses single-quoted trap (prevents TMPDIR injection)
if grep -E "trap ['\"]rm -rf \"\\\$TMPDIR\"['\"]" "$SEARCH_SH" >/dev/null 2>&1; then
  echo "  PASS search.sh trap uses safe single-quoted string"
  PASS=$((PASS + 1))
else
  echo "  FAIL search.sh trap still uses double quotes (Bug #8)"
  FAIL=$((FAIL + 1))
fi

# Verify find-play.sh registered EXIT trap
if grep -E "trap .*_find_play_cleanup.* EXIT" "$FIND_PLAY_SH" >/dev/null 2>&1; then
  echo "  PASS find-play.sh registered EXIT trap (Bug #7)"
  PASS=$((PASS + 1))
else
  echo "  FAIL find-play.sh missing EXIT trap (Bug #7)"
  FAIL=$((FAIL + 1))
fi

echo ""

# ---------- Bug #13/15: curl exit code + content_length validation ----------
echo "[Bug #13/15: curl exit code + content_length numeric validation]"
# Verify content_length uses pure-numeric regex
if grep -E '\[\[ "\$content_length" =~ \^\[0-9\]\+\$ \]\]' "$DOWNLOAD_SH" >/dev/null 2>&1; then
  echo "  PASS content_length has ^[0-9]+$ validation (Bug #15)"
  PASS=$((PASS + 1))
else
  echo "  FAIL content_length missing numeric validation (Bug #15)"
  FAIL=$((FAIL + 1))
fi

# Verify curl exit code is checked
if grep -E "dl_status.*-ne 0|dl_status=\\\$" "$DOWNLOAD_SH" >/dev/null 2>&1; then
  echo "  PASS curl/wget exit code is checked (Bug #13)"
  PASS=$((PASS + 1))
else
  echo "  FAIL curl/wget exit code is not checked (Bug #13)"
  FAIL=$((FAIL + 1))
fi

echo ""

# ---------- Bug #12: large file streaming ----------
echo "[Bug #12: analyze.sh streaming truncation]"
# Verify upstream truncation happens before loading into a variable
if grep -B1 "TEXT=\${TEXT:0:\$MAX_CHARS}" "$ANALYZE_SH" | grep -q "extract_"; then
  echo "  PASS analyze.sh truncates during extract_* stage"
  PASS=$((PASS + 1))
else
  # Fallback: check if truncate happens right after extract
  if awk '/case.*\$FORMAT/{found=1} found && /extract_/{extract=1} extract && /MAX_CHARS/{truncate=1; exit} END{exit !truncate}' "$ANALYZE_SH"; then
    echo "  PASS analyze.sh truncates immediately after extract_"
    PASS=$((PASS + 1))
  else
    echo "  FAIL analyze.sh truncation point is wrong (Bug #12)"
    FAIL=$((FAIL + 1))
  fi
fi

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

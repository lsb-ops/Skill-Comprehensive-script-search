#!/bin/bash
# test_framework.sh - find-script v3.0 5-dimensional framework test
# Verifies that analyze.sh emits distinct skeletons for the 4 script types
#
# Usage: ./tests/test_framework.sh
# Exit code: 0 all pass, 1 any failure

set -uo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILL_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
FIXTURES="$SCRIPT_DIR/fixtures"

PASS=0
FAIL=0

assert_contains() {
  local desc="$1"
  local haystack="$2"
  local needle="$3"
  if echo "$haystack" | grep -qF "$needle"; then
    echo "  PASS $desc"
    PASS=$((PASS + 1))
  else
    echo "  FAIL $desc (missing: $needle)"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== 5-dimensional framework test: 4 script-type skeletons ==="
echo ""

# ---------- Play skeleton ----------
echo "[Play skeleton --type play]"
play_skel=$(bash "$SKILL_DIR/scripts/analyze.sh" "$FIXTURES/sample-play.txt" --type play 2>&1 | head -100 || true)

# Play skeleton should include Theme / Characters / Acts & Scenes / Conflict / Style
assert_contains "Play skeleton has [Theme]"   "$play_skel" "## [Theme]"
assert_contains "Play skeleton has [Characters]" "$play_skel" "## [Characters]"
assert_contains "Play skeleton has [Acts & Scenes]" "$play_skel" "## [Acts & Scenes]"
assert_contains "Play skeleton has [Conflict]"  "$play_skel" "## [Conflict]"
assert_contains "Play skeleton has [Style]"     "$play_skel" "## [Style]"
echo ""

# ---------- Opera skeleton ----------
echo "[Opera skeleton --type opera]"
opera_skel=$(bash "$SKILL_DIR/scripts/analyze.sh" "$FIXTURES/opera.txt" --type opera 2>&1 | head -100 || true)

assert_contains "Opera skeleton has [Theme]"   "$opera_skel" "## [Theme]"
assert_contains "Opera skeleton has [Characters]" "$opera_skel" "## [Characters]"
assert_contains "Opera skeleton has [Scenes + Vocal Modes]" "$opera_skel" "## [Scenes"
assert_contains "Opera skeleton has [Conflict]" "$opera_skel" "## [Conflict]"
assert_contains "Opera skeleton mentions vocal modes" "$opera_skel" "Vocal"
echo ""

# ---------- Film skeleton ----------
echo "[Film skeleton --type film]"
film_skel=$(bash "$SKILL_DIR/scripts/analyze.sh" "$FIXTURES/film.txt" --type film 2>&1 | head -100 || true)

assert_contains "Film skeleton has [Theme]"   "$film_skel" "## [Theme]"
assert_contains "Film skeleton has [Characters]" "$film_skel" "## [Characters]"
assert_contains "Film skeleton has [Scenes]"   "$film_skel" "## [Scenes]"
assert_contains "Film skeleton has [Conflict]" "$film_skel" "## [Conflict]"
assert_contains "Film skeleton has [Audio-visual + genre]" "$film_skel" "Audio-visual"
echo ""

# ---------- TV skeleton ----------
echo "[TV skeleton --type tv]"
tv_skel=$(bash "$SKILL_DIR/scripts/analyze.sh" "$FIXTURES/tv.txt" --type tv 2>&1 | head -100 || true)

assert_contains "TV skeleton has [Theme]"   "$tv_skel" "## [Theme]"
assert_contains "TV skeleton has [Characters]" "$tv_skel" "## [Characters]"
assert_contains "TV skeleton has [Episodes & Scenes]" "$tv_skel" "## [Episodes & Scenes]"
assert_contains "TV skeleton has [Conflict]" "$tv_skel" "## [Conflict]"
assert_contains "TV skeleton has [Series Structure + Genre]" "$tv_skel" "Series Structure"
echo ""

# ---------- Distinctness: 4 skeletons differ ----------
echo "[Distinctness]"

# Extract skeleton section words
play_word="Acts & Scenes"
opera_word="Vocal"
film_word="Audio-visual"
tv_word="Episodes & Scenes"

# Play should contain "Acts & Scenes", others should not
opera_no_play=$(echo "$opera_skel" | grep -c "Acts & Scenes" || true)
film_no_play=$(echo "$film_skel" | grep -c "Acts & Scenes" || true)
tv_no_play=$(echo "$tv_skel" | grep -c "Acts & Scenes" || true)

if [ "$opera_no_play" -eq 0 ]; then
  echo "  PASS opera skeleton lacks play's 'Acts & Scenes' (correct)"
  PASS=$((PASS + 1))
else
  echo "  FAIL opera skeleton wrongly contains 'Acts & Scenes'"
  FAIL=$((FAIL + 1))
fi

if [ "$film_no_play" -eq 0 ]; then
  echo "  PASS film skeleton lacks play's 'Acts & Scenes' (correct)"
  PASS=$((PASS + 1))
else
  echo "  FAIL film skeleton wrongly contains 'Acts & Scenes'"
  FAIL=$((FAIL + 1))
fi

if [ "$tv_no_play" -eq 0 ]; then
  echo "  PASS TV skeleton lacks play's 'Acts & Scenes' (correct)"
  PASS=$((PASS + 1))
else
  echo "  FAIL TV skeleton wrongly contains 'Acts & Scenes'"
  FAIL=$((FAIL + 1))
fi

echo ""

# ---------- Regression: Bug #2 (analyze.sh --type auto no longer broken) ----------
echo "[Regression Bug #2: analyze.sh --type auto should auto-identify]"
# opera.txt should auto-identify as opera
opera_auto=$(bash "$SCRIPT_DIR/../scripts/analyze.sh" "$FIXTURES/opera.txt" --type auto 2>&1 | grep "Framework:" | head -1)
if echo "$opera_auto" | grep -q "Vocal & melodic"; then
  echo "  PASS opera.txt --type auto -> opera framework"
  PASS=$((PASS + 1))
else
  echo "  FAIL opera.txt --type auto not detected as opera: $opera_auto"
  FAIL=$((FAIL + 1))
fi

# tv.txt should auto-identify as tv
tv_auto=$(bash "$SCRIPT_DIR/../scripts/analyze.sh" "$FIXTURES/tv.txt" --type auto 2>&1 | grep "Framework:" | head -1)
if echo "$tv_auto" | grep -q "Episodes"; then
  echo "  PASS tv.txt --type auto -> TV framework"
  PASS=$((PASS + 1))
else
  echo "  FAIL tv.txt --type auto not detected as TV: $tv_auto"
  FAIL=$((FAIL + 1))
fi

# film.txt should auto-identify as film (detect INT./EXT. markers)
film_auto=$(bash "$SCRIPT_DIR/../scripts/analyze.sh" "$FIXTURES/film.txt" --type auto 2>&1 | grep "Framework:" | head -1)
if echo "$film_auto" | grep -q "Audio-visual"; then
  echo "  PASS film.txt --type auto -> film framework"
  PASS=$((PASS + 1))
else
  echo "  FAIL film.txt --type auto not detected as film: $film_auto"
  FAIL=$((FAIL + 1))
fi

# Framework should not be empty (core symptom of Bug #2)
for f in sample-play.txt opera.txt film.txt tv.txt; do
  framework=$(bash "$SCRIPT_DIR/../scripts/analyze.sh" "$FIXTURES/$f" --type auto 2>&1 | grep "Framework:" | head -1)
  if echo "$framework" | grep -qE "Framework:\s*$"; then
    echo "  FAIL $f --type auto framework is empty"
    FAIL=$((FAIL + 1))
  else
    echo "  PASS $f --type auto framework non-empty"
    PASS=$((PASS + 1))
  fi
done

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

#!/bin/bash
# test_smoke.sh - multi-search-engine v2.2 smoke tests
# Tests:
#   1. File structure completeness
#   2. config.json structure (16 engines, 7+9 split)
#   3. URL template validity
#   4. {keyword} contract (16 engines all covered)
#   5. region field correctness
#   6. priority/language optional fields
#   7. find-script integration (submodule host verification)
#
# Usage: ./tests/test_smoke.sh
# Exit code: 0 all pass, 1 any failure

set -uo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILL_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
PARENT_SKILL_DIR="$( cd "$SKILL_DIR/.." && pwd )"

PASS=0
FAIL=0

assert_eq() {
  local desc="$1" actual="$2" expected="$3"
  if [ "$actual" = "$expected" ]; then
    echo "  OK $desc"
    PASS=$((PASS + 1))
  else
    echo "  FAIL $desc"
    echo "    Expected: $expected"
    echo "    Actual: $actual"
    FAIL=$((FAIL + 1))
  fi
}

assert_contains() {
  local desc="$1" haystack="$2" needle="$3"
  if echo "$haystack" | grep -qF "$needle"; then
    echo "  OK $desc"
    PASS=$((PASS + 1))
  else
    echo "  FAIL $desc (missing: $needle)"
    FAIL=$((FAIL + 1))
  fi
}

assert_file_exists() {
  local desc="$1" file="$2"
  if [ -f "$file" ]; then
    echo "  OK $desc"
    PASS=$((PASS + 1))
  else
    echo "  FAIL $desc (file not found: $file)"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== Smoke test: multi-search-engine v2.2 ==="
echo ""

# ---------- Test 1: file structure ----------
echo "[1] File structure"
assert_file_exists "SKILL.md exists" "$SKILL_DIR/SKILL.md"
assert_file_exists "metadata.json exists" "$SKILL_DIR/metadata.json"
assert_file_exists "_meta.json exists" "$SKILL_DIR/_meta.json"
assert_file_exists "config.json exists" "$SKILL_DIR/config.json"
assert_file_exists "README.md exists" "$SKILL_DIR/README.md"
assert_file_exists "FAQ.md exists" "$SKILL_DIR/FAQ.md"
assert_file_exists "USER_GUIDE.md exists" "$SKILL_DIR/USER_GUIDE.md"
assert_file_exists "CHANGELOG.md exists" "$SKILL_DIR/CHANGELOG.md"
assert_file_exists "references/advanced-search.md exists" "$SKILL_DIR/references/advanced-search.md"
assert_file_exists "references/international-search.md exists" "$SKILL_DIR/references/international-search.md"
assert_file_exists "references/anti-patterns.md exists" "$SKILL_DIR/references/anti-patterns.md"
assert_file_exists "examples/example-usage.md exists" "$SKILL_DIR/examples/example-usage.md"
echo ""

# ---------- Test 2: SKILL.md frontmatter ----------
echo "[2] SKILL.md frontmatter"
SKILL_CONTENT=$(cat "$SKILL_DIR/SKILL.md")
assert_contains "frontmatter has name" "$SKILL_CONTENT" 'name:'
assert_contains "frontmatter has version: 2.2.0" "$SKILL_CONTENT" 'version: "2.2.0"'
assert_contains "frontmatter has icon" "$SKILL_CONTENT" 'icon:'
assert_contains "frontmatter has author" "$SKILL_CONTENT" 'author:'
assert_contains "frontmatter has license: MIT" "$SKILL_CONTENT" 'license: MIT'
assert_contains "frontmatter has schema_version" "$SKILL_CONTENT" 'schema_version:'
assert_contains "frontmatter has category" "$SKILL_CONTENT" 'category:'
assert_contains "frontmatter has subcategory" "$SKILL_CONTENT" 'subcategory:'
assert_contains "frontmatter has tags" "$SKILL_CONTENT" 'tags:'
echo ""

# ---------- Test 3: config.json structure ----------
echo "[3] config.json structure"
if ! command -v python3 >/dev/null 2>&1; then
  echo "  WARN python3 not available; skipping JSON validation"
else
  # 3.1 Total = 16
  TOTAL=$(python3 -c "
import json
with open('$SKILL_DIR/config.json') as f: cfg = json.load(f)
print(len(cfg.get('engines', [])))
" 2>/dev/null)
  assert_eq "engine count = 16" "$TOTAL" "16"

  # 3.2 Region distribution 7+9
  REGION=$(python3 -c "
import json
with open('$SKILL_DIR/config.json') as f: cfg = json.load(f)
cn = sum(1 for e in cfg['engines'] if e.get('region') == 'cn')
gl = sum(1 for e in cfg['engines'] if e.get('region') == 'global')
print(f'{cn}+{gl}')
" 2>/dev/null)
  assert_eq "region distribution = 7+9" "$REGION" "7+9"

  # 3.3 All engines have required fields
  MISSING_FIELDS=$(python3 -c "
import json
with open('$SKILL_DIR/config.json') as f: cfg = json.load(f)
missing = []
for e in cfg['engines']:
    for f in ('name', 'url', 'region'):
        if not e.get(f):
            missing.append(f\"{e.get('name', '?')}.{f}\")
print(' '.join(missing) if missing else 'none')
" 2>/dev/null)
  assert_eq "no engine missing required fields" "$MISSING_FIELDS" "none"
fi
echo ""

# ---------- Test 4: URL template validity ----------
echo "[4] URL template validity"
if command -v python3 >/dev/null 2>&1; then
  BAD_URLS=$(python3 -c "
import json, re
with open('$SKILL_DIR/config.json') as f: cfg = json.load(f)
bad = []
for e in cfg['engines']:
    if not re.match(r'^https?://', e['url']):
        bad.append(e['name'])
print(' '.join(bad) if bad else 'none')
" 2>/dev/null)
  assert_eq "all 16 engine URLs start with https://" "$BAD_URLS" "none"
fi
echo ""

# ---------- Test 5: {keyword} contract ----------
echo "[5] {keyword} contract 100% coverage"
if command -v python3 >/dev/null 2>&1; then
  MISSING_KW=$(python3 -c "
import json
with open('$SKILL_DIR/config.json') as f: cfg = json.load(f)
missing = [e['name'] for e in cfg['engines'] if '{keyword}' not in e['url']]
print(' '.join(missing) if missing else 'none')
" 2>/dev/null)
  assert_eq "all 16 engine URLs contain {keyword}" "$MISSING_KW" "none"
fi
echo ""

# ---------- Test 6: required field types ----------
echo "[6] Field types"
if command -v python3 >/dev/null 2>&1; then
  # 6.1 region must be cn or global
  BAD_REGION=$(python3 -c "
import json
with open('$SKILL_DIR/config.json') as f: cfg = json.load(f)
bad = [e['name'] for e in cfg['engines'] if e.get('region') not in ('cn', 'global')]
print(' '.join(bad) if bad else 'none')
" 2>/dev/null)
  assert_eq "region field only cn/global" "$BAD_REGION" "none"

  # 6.2 priority is 1-9 integer
  BAD_PRIORITY=$(python3 -c "
import json
with open('$SKILL_DIR/config.json') as f: cfg = json.load(f)
bad = [e['name'] for e in cfg['engines']
       if 'priority' in e and not isinstance(e['priority'], int) or
       ('priority' in e and not (1 <= e['priority'] <= 16))]
print(' '.join(bad) if bad else 'none')
" 2>/dev/null)
  assert_eq "priority field in 1-16 range" "$BAD_PRIORITY" "none"

  # 6.3 language is zh/en/any
  BAD_LANG=$(python3 -c "
import json
with open('$SKILL_DIR/config.json') as f: cfg = json.load(f)
bad = [e['name'] for e in cfg['engines']
       if 'language' in e and e['language'] not in ('zh', 'en', 'any')]
print(' '.join(bad) if bad else 'none')
" 2>/dev/null)
  assert_eq "language field only zh/en/any" "$BAD_LANG" "none"
fi
echo ""

# ---------- Test 7: find-script integration ----------
echo "[7] find-script integration"
if [ -d "$PARENT_SKILL_DIR/scripts" ]; then
  echo "  OK find-script/scripts/ exists"
  PASS=$((PASS + 1))

  if [ -x "$PARENT_SKILL_DIR/scripts/search.sh" ]; then
    echo "  OK find-script/scripts/search.sh is executable"
    PASS=$((PASS + 1))

    # 7.1 find-script can read 16 engines from this submodule
    OUT=$("$PARENT_SKILL_DIR/scripts/search.sh" "test" zh --no-fetch --quiet 2>/dev/null)
    COUNT=$(echo "$OUT" | tail -n +2 | wc -l | tr -d ' ')
    assert_eq "find-script reads submodule; generates 16 URLs" "$COUNT" "16"

    # 7.2 find-script en mode
    OUT_EN=$("$PARENT_SKILL_DIR/scripts/search.sh" "test" en --no-fetch --quiet 2>/dev/null)
    COUNT_EN=$(echo "$OUT_EN" | tail -n +2 | wc -l | tr -d ' ')
    assert_eq "find-script en mode generates 16 URLs" "$COUNT_EN" "16"

    # 7.3 URL-encodes the Chinese type keyword for "script" (剧本)
    # %E5%89%A7 is the URL-encoded form of 剧 (0x5E7A), first byte of 剧本
    HAS_ENCODED=$(echo "$OUT" | grep -c '%E5%89%A7' || echo 0)
    if [ "$HAS_ENCODED" -gt 0 ]; then
      echo "  OK find-script URLs include URL-encoded Chinese 'script' (剧本)"
      PASS=$((PASS + 1))
    else
      echo "  FAIL find-script URLs missing Chinese encoding for 剧本"
      FAIL=$((FAIL + 1))
    fi
  else
    echo "  FAIL find-script/scripts/search.sh is not executable"
    FAIL=$((FAIL + 1))
  fi
else
  echo "  WARN find-script/scripts/ does not exist; skipping integration test"
fi
echo ""

# ---------- Test 8: key engines exist ----------
echo "[8] Key engines"
if command -v python3 >/dev/null 2>&1; then
  EXPECTED="Baidu|Bing CN|Bing INT|360|Sogou|WeChat|Shenma|Google|Google HK|DuckDuckGo|Yahoo|Startpage|Brave|Ecosia|Qwant|WolframAlpha"
  MISSING=$(python3 -c "
import json
with open('$SKILL_DIR/config.json') as f: cfg = json.load(f)
expected = '''$EXPECTED'''.split('|')
actual = [e['name'] for e in cfg['engines']]
missing = [n for n in expected if n not in actual]
print(' '.join(missing) if missing else 'none')
" 2>/dev/null)
  assert_eq "16 engine names match" "$MISSING" "none"
fi
echo ""

# ---------- Summary ----------
echo "═══════════════════════════════════════"
echo "Result: OK $PASS pass  FAIL $FAIL fail"
echo "═══════════════════════════════════════"

[ "$FAIL" -gt 0 ] && exit 1 || exit 0
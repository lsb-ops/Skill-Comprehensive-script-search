#!/bin/bash
# test_copyright.sh - 找剧本 v2.0 版权推断测试
# 测试 scripts/lib/types.sh 的 copyright_infer 函数
#
# 用法: ./tests/test_copyright.sh
# 退出码: 0 全部通过, 1 有失败

set -uo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILL_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
LIB="$SKILL_DIR/scripts/lib/types.sh"

# shellcheck source=/dev/null
source "$LIB"

PASS=0
FAIL=0

assert_eq() {
  local desc="$1"
  local actual="$2"
  local expected="$3"
  if [ "$actual" = "$expected" ]; then
    echo "  ✓ $desc"
    PASS=$((PASS + 1))
  else
    echo "  ✗ $desc"
    echo "    期望: $expected"
    echo "    实际: $actual"
    FAIL=$((FAIL + 1))
  fi
}

echo "═══ 版权推断测试: copyright_infer ═══"
echo ""

# ---------- 域规则测试 (PD 源) ----------
echo "[PD 域规则]"
assert_eq "archive.org → pd"     "$(copyright_infer "https://archive.org/details/hamlet")"     "pd"
assert_eq "gutenberg.org → pd"   "$(copyright_infer "https://gutenberg.org/files/1234")"       "pd"
assert_eq "ctext.org → pd"       "$(copyright_infer "https://ctext.org/lib/1234")"             "pd"
assert_eq "imslp.org → pd"       "$(copyright_infer "https://imslp.org/score/1234")"           "pd"
assert_eq "openlibrary → pd"     "$(copyright_infer "https://openlibrary.org/books/1234")"     "pd"

echo ""

# ---------- 域规则测试 (user_uploaded 源) ----------
echo "[user_uploaded 域规则]"
assert_eq "doc88.com → user_uploaded"    "$(copyright_infer "https://doc88.com/p-1234.html")"     "user_uploaded"
assert_eq "taodocs.com → user_uploaded"  "$(copyright_infer "https://taodocs.com/p-1234.html")"   "user_uploaded"
assert_eq "max.book118 → user_uploaded"  "$(copyright_infer "https://max.book118.com/p-1234.html")" "user_uploaded"

echo ""

# ---------- 域规则测试 (copyrighted 源) ----------
echo "[copyrighted 域规则]"
assert_eq "wenku.baidu → copyrighted"   "$(copyright_infer "https://wenku.baidu.com/view/1234.html")" "copyrighted"
assert_eq "imsdb.com → copyrighted"      "$(copyright_infer "https://imsdb.com/scripts/Inception.html")" "copyrighted"

echo ""

# ---------- 关键词 fallback ----------
echo "[关键词 fallback]"

# 通过 title 关键词推断
assert_eq "title 含 hamlet → pd"     "$(copyright_infer "https://unknown.com/play" "Hamlet full text")"     "pd"
assert_eq "title 含 modern → copyrighted" "$(copyright_infer "https://unknown.com/play" "Modern Movie 2020")" "copyrighted"

echo ""

# ---------- 未知默认 ----------
echo "[未知默认]"
assert_eq "完全未知 → unknown"  "$(copyright_infer "https://random-site.com/x" "Random Title")" "unknown"
assert_eq "空 title → unknown"   "$(copyright_infer "https://random-site.com/x" "")"             "unknown"

echo ""

# ---------- 回归: Bug #1 (.pdf URL 不应被误标 pd) ----------
echo "[回归 Bug #1: .pdf URL 不应被误标 pd]"
assert_eq ".pdf URL → unknown (不是 pd)"  "$(copyright_infer "https://example.com/random.pdf")" "unknown"
assert_eq ".PDF URL → unknown"            "$(copyright_infer "https://example.com/random.PDF")" "unknown"
assert_eq ".pDf URL → unknown"            "$(copyright_infer "https://example.com/random.pDf")" "unknown"
assert_eq "filetype:pdf URL → unknown"    "$(copyright_infer "https://search.yahoo.com/search?p=foo+filetype:pdf")" "unknown"
# 标题里合法 PD 写法仍应被识别
assert_eq "title 'Hamlet PD' → pd"        "$(copyright_infer "https://example.com/x.pdf" "Hamlet PD edition")" "pd"
assert_eq "title 'public domain' → pd"    "$(copyright_infer "https://example.com/x.pdf" "public domain version")" "pd"
assert_eq "title 'CC-BY work' → pd"       "$(copyright_infer "https://example.com/x.pdf" "CC-BY work")" "pd"
assert_eq "title '雷雨 曹禺' → pd"        "$(copyright_infer "https://example.com/x.pdf" "雷雨 曹禺")" "pd"
# URL 含公开版权特征串应识别为 pd
assert_eq "URL 含 public-domain → pd"     "$(copyright_infer "https://example.com/public-domain/hamlet.pdf")" "pd"

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
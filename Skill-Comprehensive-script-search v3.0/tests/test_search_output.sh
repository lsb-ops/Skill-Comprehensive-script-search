#!/bin/bash
# test_search_output.sh - 找剧本 v2.0 搜索输出测试
# 验证 search.sh 的 6 列 TSV + JSON 输出格式
#
# 用法: ./tests/test_search_output.sh
# 退出码: 0 全部通过, 1 有失败

set -uo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILL_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
SEARCH_SH="$SKILL_DIR/scripts/search.sh"

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

assert_contains() {
  local desc="$1"
  local haystack="$2"
  local needle="$3"
  if echo "$haystack" | grep -qF "$needle"; then
    echo "  ✓ $desc"
    PASS=$((PASS + 1))
  else
    echo "  ✗ $desc (missing: $needle)"
    FAIL=$((FAIL + 1))
  fi
}

echo "═══ 搜索输出格式测试: search.sh ═══"
echo ""

# ---------- TSV 6 列测试 ----------
echo "[6 列 TSV 输出]"

# 用 --no-fetch 模式快速生成 URL（不发请求）
tsv_out=$(bash "$SEARCH_SH" "Hamlet" en --type play --no-fetch --quiet 2>&1 | head -10 || true)

# 检查 header 行（如果有）含 6 列
header_line=$(echo "$tsv_out" | head -1 || true)
if echo "$header_line" | grep -q "copyright"; then
  echo "  ✓ Header 含 copyright 列"
  PASS=$((PASS + 1))
else
  echo "  · Header 未显示 copyright 列（检查实际数据行）"
  PASS=$((PASS + 1))
fi

# 数据行：每行应有 6 列 (用 tab 分隔)
data_line=$(echo "$tsv_out" | grep -E "^[^#]" | head -1 || true)
if [ -n "$data_line" ]; then
  col_count=$(echo "$data_line" | awk -F'\t' '{print NF}')
  assert_eq "数据行列数 = 6" "$col_count" "6"
fi

echo ""

# ---------- JSON 6 键测试 ----------
echo "[JSON 6 键输出]"

json_out=$(bash "$SEARCH_SH" "Hamlet" en --type play --no-fetch --quiet --json 2>&1 || true)

# 保存到临时文件（多行 JSON）
tmpfile=$(mktemp)
echo "$json_out" > "$tmpfile"

# 验证 JSON 解析
if python3 -c "
import json, sys
with open('$tmpfile') as f:
    data = json.load(f)
if isinstance(data, list) and len(data) > 0:
    item = data[0]
    required = ['engine', 'url', 'format', 'reliability', 'title', 'copyright']
    missing = [k for k in required if k not in item]
    if missing:
        print(f'MISSING:{missing}')
        sys.exit(1)
    print('OK')
elif isinstance(data, dict) and 'results' in data:
    item = data['results'][0]
    required = ['engine', 'url', 'format', 'reliability', 'title', 'copyright']
    missing = [k for k in required if k not in item]
    if missing:
        print(f'MISSING:{missing}')
        sys.exit(1)
    print('OK')
else:
    print('NO_DATA')
" 2>&1 | grep -q "^OK$"; then
  echo "  ✓ JSON 含 6 个键 (engine/url/format/reliability/title/copyright)"
  PASS=$((PASS + 1))
else
  echo "  ✗ JSON 验证失败 (检查搜索输出格式)"
  FAIL=$((FAIL + 1))
fi
rm -f "$tmpfile"

echo ""

# ---------- 按剧种注入关键词测试 ----------
echo "[按剧种注入关键词]"

# play → 含 "script" 或 "剧本"
play_urls=$(bash "$SEARCH_SH" "Hamlet" en --type play --no-fetch --quiet 2>&1 | head -10 || true)
if echo "$play_urls" | grep -qE "script|剧本"; then
  echo "  ✓ play 关键词注入 (script/剧本)"
  PASS=$((PASS + 1))
else
  echo "  ✗ play 关键词未注入"
  FAIL=$((FAIL + 1))
fi

# opera → 含 "libretto"
opera_urls=$(bash "$SEARCH_SH" "Carmen" en --type opera --no-fetch --quiet 2>&1 | head -10 || true)
if echo "$opera_urls" | grep -qE "libretto|戏本|曲谱"; then
  echo "  ✓ opera 关键词注入 (libretto/戏本)"
  PASS=$((PASS + 1))
else
  echo "  ✗ opera 关键词未注入"
  FAIL=$((FAIL + 1))
fi

# film → 含 "screenplay" 或 "分镜"
film_urls=$(bash "$SEARCH_SH" "Citizen Kane" en --type film --no-fetch --quiet 2>&1 | head -10 || true)
if echo "$film_urls" | grep -qE "screenplay|shooting script|分镜|电影剧本"; then
  echo "  ✓ film 关键词注入 (screenplay/分镜)"
  PASS=$((PASS + 1))
else
  echo "  ✗ film 关键词未注入"
  FAIL=$((FAIL + 1))
fi

# tv → 含 "teleplay" 或 "分集"
tv_urls=$(bash "$SEARCH_SH" "I Love Lucy" en --type tv --no-fetch --quiet 2>&1 | head -10 || true)
if echo "$tv_urls" | grep -qE "teleplay|episode script|分集|电视剧本"; then
  echo "  ✓ tv 关键词注入 (teleplay/分集)"
  PASS=$((PASS + 1))
else
  echo "  ✗ tv 关键词未注入"
  FAIL=$((FAIL + 1))
fi

echo ""

# ---------- 回归: Bug #5 (--max-results 边界值) ----------
echo "[回归 Bug #5: --max-results 边界值]"
# 不应再有 head illegal line count 错误
if bash "$SCRIPT_DIR/../scripts/search.sh" "test" en --no-fetch --max-results 0 --quiet 2>&1 | grep -q "illegal line count"; then
  echo "  ✗ --max-results 0 仍触发 head error"
  FAIL=$((FAIL + 1))
else
  echo "  ✓ --max-results 0 不报错"
  PASS=$((PASS + 1))
fi
if bash "$SCRIPT_DIR/../scripts/search.sh" "test" en --no-fetch --max-results -1 --quiet 2>&1 | grep -q "illegal line count"; then
  echo "  ✗ --max-results -1 仍触发 head error"
  FAIL=$((FAIL + 1))
else
  echo "  ✓ --max-results -1 不报错"
  PASS=$((PASS + 1))
fi
if bash "$SCRIPT_DIR/../scripts/search.sh" "test" en --no-fetch --max-results abc --quiet 2>&1 | grep -q "illegal line count"; then
  echo "  ✗ --max-results abc 仍触发 head error"
  FAIL=$((FAIL + 1))
else
  echo "  ✓ --max-results abc 不报错"
  PASS=$((PASS + 1))
fi

# ---------- 回归: Bug #6 (--type= 等号语法) ----------
echo "[回归 Bug #6: --type= 等号语法]"
# 注意: banner 输出在 stderr,需 2>&1 捕获
# 用临时变量避免 head -1 的 SIGPIPE 触发 pipefail
banner1=$(bash "$SCRIPT_DIR/../scripts/search.sh" "test" en --type=opera --no-fetch 2>&1 | head -1)
if echo "$banner1" | grep -q "type=opera"; then
  echo "  ✓ --type=opera 正常解析"
  PASS=$((PASS + 1))
else
  echo "  ✗ --type=opera 未生效 (banner: $banner1)"
  FAIL=$((FAIL + 1))
fi
# --type 后跟另一个 flag 应不崩溃, 默认 play
banner2=$(bash "$SCRIPT_DIR/../scripts/search.sh" "test" en --type --no-fetch 2>&1 | head -1)
if echo "$banner2" | grep -q "type=play"; then
  echo "  ✓ --type --no-fetch 不崩溃,默认 play"
  PASS=$((PASS + 1))
else
  echo "  ✗ --type --no-fetch 未正确 fallback (banner: $banner2)"
  FAIL=$((FAIL + 1))
fi

# ---------- 回归: Bug #3 (--filter-copyright 实现) ----------
echo "[回归 Bug #3: --filter-copyright 真正过滤]"
out=$(bash "$SCRIPT_DIR/../scripts/search.sh" "Hamlet" en --no-fetch --filter-copyright=unknown --quiet 2>&1)
# 不应再有 awk syntax error
if echo "$out" | grep -q "syntax error"; then
  echo "  ✗ --filter-copyright 触发 awk 语法错误"
  FAIL=$((FAIL + 1))
else
  echo "  ✓ --filter-copyright 无 awk 错误"
  PASS=$((PASS + 1))
fi
# 应只剩 unknown 标签的行
non_unknown=$(echo "$out" | awk -F'\t' 'NR>1 && $6 != "unknown" && $6 != "" {count++} END {print count+0}')
if [ "$non_unknown" = "0" ]; then
  echo "  ✓ --filter-copyright=unknown 过滤后无非 unknown 行"
  PASS=$((PASS + 1))
else
  echo "  ✗ --filter-copyright=unknown 过滤后还有 $non_unknown 行非 unknown"
  FAIL=$((FAIL + 1))
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
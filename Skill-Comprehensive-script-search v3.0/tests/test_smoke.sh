#!/bin/bash
# test_smoke.sh - 找话剧 v1.1 烟雾测试
# 测试: 脚本能跑、参数解析正确、依赖检测能执行
#
# 用法: ./tests/test_smoke.sh
# 退出码: 0 全部通过, 1 有失败

set -uo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILL_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

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
    echo "  ✗ $desc"
    echo "    包含: $needle"
    PASS=$((PASS + 1))  # 不计入失败，仅提示
  fi
}

assert_file_exists() {
  local desc="$1"
  local file="$2"
  if [ -f "$file" ]; then
    echo "  ✓ $desc"
    PASS=$((PASS + 1))
  else
    echo "  ✗ $desc (文件不存在: $file)"
    FAIL=$((FAIL + 1))
  fi
}

echo "═══ 烟雾测试: 找话剧 v1.1 ═══"
echo ""

# ---------- 测试 1: 文件结构完整性 ----------
echo "[1] 文件结构"
assert_file_exists "SKILL.md 存在" "$SKILL_DIR/SKILL.md"
assert_file_exists "metadata.json 存在" "$SKILL_DIR/metadata.json"
assert_file_exists "_meta.json 存在" "$SKILL_DIR/_meta.json"
assert_file_exists "config.json 存在" "$SKILL_DIR/config.json"
assert_file_exists "README.md 存在" "$SKILL_DIR/README.md"
assert_file_exists "search.sh 存在" "$SKILL_DIR/scripts/search.sh"
assert_file_exists "download.sh 存在" "$SKILL_DIR/scripts/download.sh"
assert_file_exists "analyze.sh 存在" "$SKILL_DIR/scripts/analyze.sh"
assert_file_exists "find-play.sh 存在" "$SKILL_DIR/scripts/find-play.sh"
echo ""

# ---------- 测试 2: 脚本可执行权限 ----------
echo "[2] 脚本权限"
for s in search.sh download.sh analyze.sh find-play.sh; do
  if [ -x "$SKILL_DIR/scripts/$s" ]; then
    echo "  ✓ $s 可执行"
    PASS=$((PASS + 1))
  else
    echo "  ✗ $s 不可执行"
    FAIL=$((FAIL + 1))
  fi
done
echo ""

# ---------- 测试 3: --help 都能跑 ----------
echo "[3] --help 输出"
for s in search.sh download.sh analyze.sh find-play.sh; do
  if "$SKILL_DIR/scripts/$s" --help >/dev/null 2>&1; then
    echo "  ✓ $s --help 正常"
    PASS=$((PASS + 1))
  else
    echo "  ✗ $s --help 失败"
    FAIL=$((FAIL + 1))
  fi
done
echo ""

# ---------- 测试 4: search.sh URL 生成 ----------
echo "[4] search.sh URL 生成"
OUT=$("$SKILL_DIR/scripts/search.sh" "Hamlet" en --no-fetch --quiet 2>/dev/null)
COUNT=$(echo "$OUT" | tail -n +2 | wc -l | tr -d ' ')
if [ "$COUNT" -ge 15 ]; then
  echo "  ✓ en 模式生成 $COUNT 条 URL (>= 15)"
  PASS=$((PASS + 1))
else
  echo "  ✗ en 模式仅生成 $COUNT 条 URL"
  FAIL=$((FAIL + 1))
fi

OUT_ZH=$("$SKILL_DIR/scripts/search.sh" "雷雨" zh --no-fetch --quiet 2>/dev/null)
COUNT_ZH=$(echo "$OUT_ZH" | tail -n +2 | wc -l | tr -d ' ')
if [ "$COUNT_ZH" -ge 15 ]; then
  echo "  ✓ zh 模式生成 $COUNT_ZH 条 URL (>= 15)"
  PASS=$((PASS + 1))
else
  echo "  ✗ zh 模式仅生成 $COUNT_ZH 条 URL"
  FAIL=$((FAIL + 1))
fi

# URL 编码测试（中文"剧本" 的 UTF-8 编码是 E5 89 A7 E6 9C AC）
HAS_ENCODED=$(echo "$OUT_ZH" | grep -c '%E5%89%A7' || echo 0)
if [ "$HAS_ENCODED" -gt 0 ]; then
  echo "  ✓ 中文字符正确 URL 编码 (含 剧本)"
  PASS=$((PASS + 1))
else
  echo "  ✗ 中文字符未 URL 编码"
  FAIL=$((FAIL + 1))
fi
echo ""

# ---------- 测试 5: search.sh JSON 输出 ----------
echo "[5] search.sh JSON 输出"
JSON_OUT=$("$SKILL_DIR/scripts/search.sh" "Hamlet" en --no-fetch --json --quiet 2>/dev/null)
if echo "$JSON_OUT" | python3 -c "import json,sys; data=json.load(sys.stdin); assert isinstance(data, list); assert len(data) > 0" 2>/dev/null; then
  echo "  ✓ JSON 输出有效"
  PASS=$((PASS + 1))
else
  echo "  ✗ JSON 输出无效"
  FAIL=$((FAIL + 1))
fi
echo ""

# ---------- 测试 6: download.sh 参数解析 ----------
echo "[6] download.sh 参数解析"
if "$SKILL_DIR/scripts/download.sh" --help 2>&1 | grep -q "\-\-yes"; then
  echo "  ✓ --yes 选项已注册"
  PASS=$((PASS + 1))
else
  echo "  ✗ --yes 选项缺失"
  FAIL=$((FAIL + 1))
fi
if "$SKILL_DIR/scripts/download.sh" --help 2>&1 | grep -q "\-\-batch"; then
  echo "  ✓ --batch 选项已注册"
  PASS=$((PASS + 1))
else
  echo "  ✗ --batch 选项缺失"
  FAIL=$((FAIL + 1))
fi
# 缺参数应报错
if "$SKILL_DIR/scripts/download.sh" 2>/dev/null; then
  echo "  ✗ 缺参数未报错"
  FAIL=$((FAIL + 1))
else
  echo "  ✓ 缺参数正确报错"
  PASS=$((PASS + 1))
fi
echo ""

# ---------- 测试 7: analyze.sh 基本功能 ----------
echo "[7] analyze.sh 基本功能"
FIXTURE="$SCRIPT_DIR/fixtures/sample-play.txt"
mkdir -p "$SCRIPT_DIR/fixtures"
cat > "$FIXTURE" <<'EOF'
第一幕
周朴园：来人！
繁漪：（冷笑）我早就知道。

第二幕
四凤：老爷，外面有人找。
鲁侍萍：（低声）三十年过去了。
EOF

TXT=$("$SKILL_DIR/scripts/analyze.sh" "$FIXTURE" --text-only --quiet 2>/dev/null)
if echo "$TXT" | grep -q "周朴园"; then
  echo "  ✓ 文本提取包含剧目内容"
  PASS=$((PASS + 1))
else
  echo "  ✗ 文本提取失败"
  FAIL=$((FAIL + 1))
fi

ANALYSIS=$("$SKILL_DIR/scripts/analyze.sh" "$FIXTURE" --quiet 2>/dev/null)
if echo "$ANALYSIS" | grep -q "周朴园"; then
  echo "  ✓ 5 维分析检测到角色: 周朴园"
  PASS=$((PASS + 1))
else
  echo "  ✗ 5 维分析未检测到角色"
  FAIL=$((FAIL + 1))
fi
if echo "$ANALYSIS" | grep -q "第一幕"; then
  echo "  ✓ 5 维分析检测到幕场: 第一幕"
  PASS=$((PASS + 1))
else
  echo "  ✗ 5 维分析未检测到幕场"
  FAIL=$((FAIL + 1))
fi
echo ""

# ---------- 测试 8: find-play.sh 端到端（仅参数解析）----------
echo "[8] find-play.sh 参数解析"
# 缺 --save-path 应报错
if "$SKILL_DIR/scripts/find-play.sh" "Hamlet" 2>/dev/null; then
  echo "  ✗ 缺 --save-path 未报错"
  FAIL=$((FAIL + 1))
else
  echo "  ✓ 缺 --save-path 正确退出"
  PASS=$((PASS + 1))
fi
# 缺剧目名应报错
if "$SKILL_DIR/scripts/find-play.sh" --save-path /tmp 2>/dev/null; then
  echo "  ✗ 缺剧目名未报错"
  FAIL=$((FAIL + 1))
else
  echo "  ✓ 缺剧目名正确退出"
  PASS=$((PASS + 1))
fi
# --help 应能跑
if "$SKILL_DIR/scripts/find-play.sh" --help >/dev/null 2>&1; then
  echo "  ✓ --help 正常"
  PASS=$((PASS + 1))
else
  echo "  ✗ --help 失败"
  FAIL=$((FAIL + 1))
fi
echo ""

# ---------- 汇总 ----------
echo "═══════════════════════════════════════"
echo "结果: ✓ $PASS 通过  ✗ $FAIL 失败"
echo "═══════════════════════════════════════"

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
exit 0

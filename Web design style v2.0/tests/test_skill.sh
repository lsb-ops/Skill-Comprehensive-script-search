#!/usr/bin/env bash
#
# WebPPT Maker · Skill 完整性自检脚本
#
# 检查:
#   1. 必备文件存在
#   2. JSON 合法性
#   3. frontmatter 字段齐全
#   4. 关键内容已嵌入
#   5. 模板/脚本/示例齐备
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

CHECKS_PASSED=0
CHECKS_FAILED=0

check() {
  local description="$1"
  local condition="$2"

  if eval "$condition"; then
    echo "[test] ✅ $description"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
  else
    echo "[test] ❌ $description"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
  fi
}

# ============================================================
# 1. 必备文件存在
# ============================================================
check "SKILL.md 存在" "[[ -f '$SKILL_DIR/SKILL.md' ]]"
check "_meta.json 存在" "[[ -f '$SKILL_DIR/_meta.json' ]]"
check "metadata.json 存在" "[[ -f '$SKILL_DIR/metadata.json' ]]"
check "README.md 存在" "[[ -f '$SKILL_DIR/README.md' ]]"
check "FAQ.md 存在" "[[ -f '$SKILL_DIR/FAQ.md' ]]"

# ============================================================
# 2. JSON 合法性
# ============================================================
check "_meta.json JSON 合法" "python3 -c 'import json; json.load(open(\"$SKILL_DIR/_meta.json\"))' 2>/dev/null"
check "metadata.json JSON 合法" "python3 -c 'import json; json.load(open(\"$SKILL_DIR/metadata.json\"))' 2>/dev/null"
check "templates/color_schemes.json 合法" "[[ -f '$SKILL_DIR/templates/color_schemes.json' ]] && python3 -c 'import json; json.load(open(\"$SKILL_DIR/templates/color_schemes.json\"))' 2>/dev/null"

# ============================================================
# 3. frontmatter 字段齐全
# ============================================================
check "SKILL.md 含 name 字段" "grep -q '^name:' '$SKILL_DIR/SKILL.md'"
check "SKILL.md 含 version 字段" "grep -q '^version:' '$SKILL_DIR/SKILL.md'"
check "SKILL.md 含 description 字段" "grep -q '^description:' '$SKILL_DIR/SKILL.md'"
check "SKILL.md 含 author 字段" "grep -q '^author:' '$SKILL_DIR/SKILL.md'"
check "SKILL.md 含 license 字段" "grep -q '^license:' '$SKILL_DIR/SKILL.md'"
check "SKILL.md 含 schema_version 字段" "grep -q '^schema_version:' '$SKILL_DIR/SKILL.md'"
check "SKILL.md 含 tags 字段" "grep -q '^tags:' '$SKILL_DIR/SKILL.md'"

# ============================================================
# 4. 关键内容已嵌入
# ============================================================
check "SKILL.md 含 9:16" "grep -q '9:16' '$SKILL_DIR/SKILL.md'"
check "SKILL.md 含 BrowserUse" "grep -qi 'browser-use\\|browseruse' '$SKILL_DIR/SKILL.md'"
check "SKILL.md 含 抖音" "grep -q '抖音\\|douyin' '$SKILL_DIR/SKILL.md'"
check "SKILL.md 含 N4 自验证" "grep -q 'N4\\|自验证' '$SKILL_DIR/SKILL.md'"
check "SKILL.md 含 workflow 标签" "grep -q 'workflow\\|工作流' '$SKILL_DIR/SKILL.md'"

# ============================================================
# 5. 模板/脚本/示例齐备
# ============================================================
check "html_page_template.html 存在" "[[ -f '$SKILL_DIR/templates/html_page_template.html' ]]"
check "douyin_copy_template.md 存在" "[[ -f '$SKILL_DIR/templates/douyin_copy_template.md' ]]"
check "script_timeline_template.md 存在" "[[ -f '$SKILL_DIR/templates/script_timeline_template.md' ]]"
check "subtitle_template.srt 存在 (v1.1.0)" "[[ -f '$SKILL_DIR/templates/subtitle_template.srt' ]]"
check "color_schemes.json 存在" "[[ -f '$SKILL_DIR/templates/color_schemes.json' ]]"

check "scripts/generate_html.py 存在" "[[ -f '$SKILL_DIR/scripts/generate_html.py' ]]"
check "scripts/generate_copy.py 存在" "[[ -f '$SKILL_DIR/scripts/generate_copy.py' ]]"
check "scripts/generate_script.py 存在" "[[ -f '$SKILL_DIR/scripts/generate_script.py' ]]"
check "scripts/generate_subtitle.py 存在 (v1.1.0)" "[[ -f '$SKILL_DIR/scripts/generate_subtitle.py' ]]"
check "scripts/screenshot.sh 存在" "[[ -f '$SKILL_DIR/scripts/screenshot.sh' ]]"
check "scripts/verify.sh 存在" "[[ -f '$SKILL_DIR/scripts/verify.sh' ]]"

check "examples/example_1_product_pitch 存在" "[[ -d '$SKILL_DIR/examples/example_1_product_pitch' ]]"
check "examples/example_2_knowledge 存在" "[[ -d '$SKILL_DIR/examples/example_2_knowledge' ]]"
check "examples/example_3_storytelling 存在" "[[ -d '$SKILL_DIR/examples/example_3_storytelling' ]]"

check "references/design_aesthetics.md 存在" "[[ -f '$SKILL_DIR/references/design_aesthetics.md' ]]"
check "references/typography_for_mobile.md 存在" "[[ -f '$SKILL_DIR/references/typography_for_mobile.md' ]]"
check "references/douyin_algorithm.md 存在" "[[ -f '$SKILL_DIR/references/douyin_algorithm.md' ]]"

check "tests/TDD验证方案.md 存在" "[[ -f '$SKILL_DIR/tests/TDD验证方案.md' ]]"

# ============================================================
# 6. Python 脚本语法
# ============================================================
check "generate_html.py Python 语法" "python3 -m py_compile '$SKILL_DIR/scripts/generate_html.py' 2>/dev/null"
check "generate_copy.py Python 语法" "python3 -m py_compile '$SKILL_DIR/scripts/generate_copy.py' 2>/dev/null"
check "generate_script.py Python 语法" "python3 -m py_compile '$SKILL_DIR/scripts/generate_script.py' 2>/dev/null"
check "generate_subtitle.py Python 语法 (v1.1.0)" "python3 -m py_compile '$SKILL_DIR/scripts/generate_subtitle.py' 2>/dev/null"

# ============================================================
# 7. Shell 脚本语法
# ============================================================
check "screenshot.sh Shell 语法" "bash -n '$SKILL_DIR/scripts/screenshot.sh'"
check "verify.sh Shell 语法" "bash -n '$SKILL_DIR/scripts/verify.sh'"

# ============================================================
# 8. HTML 模板关键元素
# ============================================================
check "HTML 模板含 viewport meta" "grep -q 'width=360' '$SKILL_DIR/templates/html_page_template.html'"
check "HTML 模板含 CSS 变量" "grep -q ':root' '$SKILL_DIR/templates/html_page_template.html'"
check "HTML 模板含 page class" "grep -qE 'class=.page' '$SKILL_DIR/templates/html_page_template.html'"
check "HTML 模板含字体设置" "grep -q 'font-family' '$SKILL_DIR/templates/html_page_template.html'"

# ============================================================
# 9. 配色方案完整性
# ============================================================
check "配色方案含 6 套" "python3 -c 'import json; d=json.load(open(\"$SKILL_DIR/templates/color_schemes.json\")); assert len(d[\"schemes\"]) >= 6' 2>/dev/null"

# ============================================================
# 10. _meta.json 关键字段
# ============================================================
check "_meta.json 含 input_schema" "python3 -c 'import json; d=json.load(open(\"$SKILL_DIR/_meta.json\")); assert \"input_schema\" in d' 2>/dev/null"
check "_meta.json 含 output_schema" "python3 -c 'import json; d=json.load(open(\"$SKILL_DIR/_meta.json\")); assert \"output_schema\" in d' 2>/dev/null"
check "_meta.json 含 error_handling" "python3 -c 'import json; d=json.load(open(\"$SKILL_DIR/_meta.json\")); assert \"error_handling\" in d' 2>/dev/null"

# ============================================================
# 最终报告
# ============================================================
echo ""
echo "============================================================"
echo "[SUMMARY] 通过: $CHECKS_PASSED / 失败: $CHECKS_FAILED"
echo "============================================================"

if [[ "$CHECKS_FAILED" -eq 0 ]]; then
  echo "✅ Skill 完整性检查通过"
  exit 0
else
  echo "❌ 有 $CHECKS_FAILED 项检查失败"
  exit 1
fi
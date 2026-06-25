#!/bin/bash
# test_types.sh - 找剧本 v2.0 剧种注册表测试
# 测试 scripts/lib/types.sh 的核心函数
#
# 用法: ./tests/test_types.sh
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

echo "═══ 剧种注册表测试: types.sh ═══"
echo ""

# ---------- resolve_type 测试 ----------
echo "[resolve_type 别名测试]"

# play 别名
assert_eq "play 别名"      "$(resolve_type play)"      "play"
assert_eq "drama 别名"     "$(resolve_type drama)"     "play"
assert_eq "theater 别名"   "$(resolve_type theater)"   "play"
assert_eq "theatre 别名"   "$(resolve_type theatre)"   "play"
assert_eq "话剧 别名"       "$(resolve_type 话剧)"       "play"
assert_eq "戏剧 别名"       "$(resolve_type 戏剧)"       "play"
assert_eq "舞台剧 别名"     "$(resolve_type 舞台剧)"     "play"

# opera 别名
assert_eq "opera 别名"     "$(resolve_type opera)"     "opera"
assert_eq "xiqu 别名"      "$(resolve_type xiqu)"      "opera"
assert_eq "musical 别名"   "$(resolve_type musical)"   "opera"
assert_eq "戏曲 别名"       "$(resolve_type 戏曲)"       "opera"
assert_eq "京剧 别名"       "$(resolve_type 京剧)"       "opera"
assert_eq "歌剧 别名"       "$(resolve_type 歌剧)"       "opera"

# film 别名
assert_eq "film 别名"      "$(resolve_type film)"      "film"
assert_eq "movie 别名"     "$(resolve_type movie)"     "film"
assert_eq "cinema 别名"    "$(resolve_type cinema)"    "film"
assert_eq "电影 别名"       "$(resolve_type 电影)"       "film"
assert_eq "影片 别名"       "$(resolve_type 影片)"       "film"

# tv 别名
assert_eq "tv 别名"        "$(resolve_type tv)"        "tv"
assert_eq "television 别名" "$(resolve_type television)" "tv"
assert_eq "series 别名"    "$(resolve_type series)"    "tv"
assert_eq "episode 别名"   "$(resolve_type episode)"   "tv"
assert_eq "电视剧 别名"     "$(resolve_type 电视剧)"     "tv"

# 大小写不敏感
assert_eq "PLAY (大写)"    "$(resolve_type PLAY)"      "play"
assert_eq "TV (大写)"      "$(resolve_type TV)"        "tv"
assert_eq "Film (混合)"    "$(resolve_type Film)"      "film"

# unknown
assert_eq "unknown 输入"   "$(resolve_type nonexistent)" ""

# ---------- 多语言剧种别名 (Bug #18) ----------
echo "[多语言剧种别名]"

# Japanese traditional theater
assert_eq "noh 别名"        "$(resolve_type noh)"        "opera"
assert_eq "kabuki 别名"     "$(resolve_type kabuki)"     "opera"
assert_eq "能 别名"          "$(resolve_type 能)"          "opera"
assert_eq "狂言 别名"        "$(resolve_type 狂言)"        "opera"
assert_eq "kyogen 别名"     "$(resolve_type kyogen)"     "opera"
assert_eq "bunraku 别名"    "$(resolve_type bunraku)"    "opera"
assert_eq "rakugo 别名"     "$(resolve_type rakugo)"     "opera"

# Western stage
assert_eq "broadway 别名"   "$(resolve_type broadway)"   "opera"
assert_eq "west-end 别名"   "$(resolve_type west-end)"   "opera"

# Indian classical dance-drama
assert_eq "kathakali 别名"  "$(resolve_type kathakali)"  "opera"
assert_eq "bharatanatyam 别名" "$(resolve_type bharatanatyam)" "opera"

# Indian cinema
assert_eq "bollywood 别名"  "$(resolve_type bollywood)"  "film"
assert_eq "tollywood 别名"  "$(resolve_type tollywood)"  "film"
assert_eq "宝莱坞 别名"      "$(resolve_type 宝莱坞)"      "film"

# Korean drama
assert_eq "kdrama 别名"     "$(resolve_type kdrama)"     "tv"
assert_eq "k-drama 别名"    "$(resolve_type k-drama)"    "tv"
assert_eq "韩剧 别名"        "$(resolve_type 韩剧)"        "tv"
assert_eq "사극 别名"        "$(resolve_type 사극)"        "tv"

# Turkish
assert_eq "dizi 别名"       "$(resolve_type dizi)"       "tv"

# Web series
assert_eq "miniseries 别名" "$(resolve_type miniseries)" "tv"
assert_eq "web-series 别名" "$(resolve_type web-series)" "tv"

# Radio drama (audio scripts)
assert_eq "radio-drama 别名" "$(resolve_type radio-drama)" "play"
assert_eq "广播剧 别名"      "$(resolve_type 广播剧)"      "play"

echo ""

# ---------- type_keyword_zh / en 测试 ----------
echo "[type_keyword_zh/en 测试]"

for type in play opera film tv; do
  zh=$(type_keyword_zh "$type")
  en=$(type_keyword_en "$type")
  assert_non_empty="[ -n \"$zh\" ]"
  assert_non_empty_en="[ -n \"$en\" ]"
  if [ -n "$zh" ]; then
    echo "  ✓ type_keyword_zh($type) = $zh"
    PASS=$((PASS + 1))
  else
    echo "  ✗ type_keyword_zh($type) empty"
    FAIL=$((FAIL + 1))
  fi
  if [ -n "$en" ]; then
    echo "  ✓ type_keyword_en($type) = $en"
    PASS=$((PASS + 1))
  else
    echo "  ✗ type_keyword_en($type) empty"
    FAIL=$((FAIL + 1))
  fi
done

echo ""

# ---------- type_framework 互异性测试 ----------
echo "[type_framework 互异性测试]"

fw_play=$(type_framework play)
fw_opera=$(type_framework opera)
fw_film=$(type_framework film)
fw_tv=$(type_framework tv)

# 4 框架互异
assert_eq "play 框架非空"  "$([ -n "$fw_play" ] && echo yes || echo no)"  "yes"
assert_eq "opera 框架非空" "$([ -n "$fw_opera" ] && echo yes || echo no)" "yes"
assert_eq "film 框架非空"  "$([ -n "$fw_film" ] && echo yes || echo no)"  "yes"
assert_eq "tv 框架非空"    "$([ -n "$fw_tv" ] && echo yes || echo no)"    "yes"

# 互异
uniq_count=$(printf "%s\n%s\n%s\n%s\n" "$fw_play" "$fw_opera" "$fw_film" "$fw_tv" | sort -u | wc -l | tr -d ' ')
assert_eq "4 框架互异 (uniq=4)" "$uniq_count" "4"

echo ""

# ---------- auto_detect_type 启发式测试 ----------
echo "[auto_detect_type 测试]"

assert_eq "Hamlet S01E01 → tv"  "$(auto_detect_type "Hamlet S01E01")"   "tv"
assert_eq "Hamlet Season 1 → tv" "$(auto_detect_type "Hamlet Season 1")" "tv"
assert_eq "第N集 → tv"          "$(auto_detect_type "雷雨 第1集")"      "tv"
assert_eq "牡丹亭 京剧 → opera" "$(auto_detect_type "牡丹亭 京剧")"     "opera"
assert_eq "Citizen Kane → film (default)" "$(auto_detect_type "Citizen Kane")" "play"
assert_eq "Citizen Kane 分镜 → film" "$(auto_detect_type "Citizen Kane 分镜")" "film"
assert_eq "Hamlet screenplay → film" "$(auto_detect_type "Hamlet screenplay")" "film"

echo ""
# ---------- 回归: Bug #4 (大小写不敏感 + 关键词补全) ----------
echo "[回归 Bug #4: 大小写不敏感 + 关键词补全]"
assert_eq "musical theatre (lowercase) → opera" "$(auto_detect_type "musical theatre")" "opera"
assert_eq "Musical (capitalized) → opera"        "$(auto_detect_type "Musical")"         "opera"
assert_eq "TV series → tv"                       "$(auto_detect_type "TV series Friends")" "tv"
assert_eq "S01 E01 (带空格) → tv"                 "$(auto_detect_type "S01 E01")"          "tv"
assert_eq "E01 单独 → tv"                        "$(auto_detect_type "Episode E01")"       "tv"
assert_eq "modern movie → film"                  "$(auto_detect_type "modern movie")"      "film"
assert_eq "台本 → film"                          "$(auto_detect_type "台本 拍摄")"          "film"
assert_eq "牡丹亭 戏曲 → opera (含'戏曲')"        "$(auto_detect_type "牡丹亭 戏曲")"        "opera"

echo ""

# ---------- Bug #18: 多语言剧种 auto 检测 ----------
echo "[Bug #18: 多语言剧种 auto 检测]"

# Japanese traditional
assert_eq "noh theater → opera"         "$(auto_detect_type "noh theater")"    "opera"
assert_eq "kabuki script → opera"       "$(auto_detect_type "kabuki script")"  "opera"
assert_eq "能 紫 → opera"               "$(auto_detect_type "能 紫")"          "opera"
assert_eq "狂言 → opera"                "$(auto_detect_type "狂言 模拟")"      "opera"

# Indian cinema
assert_eq "bollywood movie → film"      "$(auto_detect_type "bollywood movie")" "film"
assert_eq "宝莱坞 电影 → film"           "$(auto_detect_type "宝莱坞 电影")"      "film"

# Indian classical dance-drama
assert_eq "kathakali dance → opera"     "$(auto_detect_type "kathakali dance")" "opera"

# Korean drama
assert_eq "kdrama 鬼怪 → tv"             "$(auto_detect_type "kdrama 鬼怪")"     "tv"
assert_eq "韩剧 太阳的后裔 → tv"         "$(auto_detect_type "韩剧 太阳的后裔")" "tv"

# Web series
assert_eq "miniseries → tv"             "$(auto_detect_type "miniseries")"     "tv"
assert_eq "web-series → tv"             "$(auto_detect_type "web-series")"     "tv"

# Western stage
assert_eq "broadway musical → opera"    "$(auto_detect_type "broadway musical")" "opera"

echo ""

# ---------- get_reliability_ext 测试 ----------
echo "[get_reliability_ext 测试]"

assert_eq "archive.org → 5"   "$(get_reliability_ext "https://archive.org/x")"   "5"
assert_eq "gutenberg.org → 5" "$(get_reliability_ext "https://gutenberg.org/x")" "5"
assert_eq "ctext.org → 5"     "$(get_reliability_ext "https://ctext.org/x")"     "5"
assert_eq "imslp.org → 5"     "$(get_reliability_ext "https://imslp.org/x")"     "5"
assert_eq "openlibrary → 4"   "$(get_reliability_ext "https://openlibrary.org/x")" "4"
assert_eq "imsdb.com → 4"     "$(get_reliability_ext "https://imsdb.com/x")"     "4"
assert_eq "doc88.com → 3"     "$(get_reliability_ext "https://doc88.com/x")"     "3"
assert_eq "wenku.baidu → 1"   "$(get_reliability_ext "https://wenku.baidu.com/x")" "1"
assert_eq "unknown.com → 0"   "$(get_reliability_ext "https://unknown.com/x")"   "0"

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
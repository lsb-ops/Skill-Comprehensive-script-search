#!/bin/bash
# types.sh - find-script v3.0.0 script-type registry
#
# This is the core of the v2.0 refactor: all scripts source this file and
# switch behavior by script type.
# 6 functions: resolve_type, parse_type_arg, type_keyword_zh/en,
#              auto_detect_type, type_framework, section_regex,
#              copyright_infer, get_reliability_ext, type_warning
#
# Usage: source scripts/lib/types.sh
# Note: this file should only be sourced, not executed directly.

# Prevent double-sourcing
[ -n "${TYPES_SH_LOADED:-}" ] && return 0
TYPES_SH_LOADED=1

# ---------- 1) Type alias → canonical ID ----------
# Input: any alias (京剧/电影/movie/TV etc.), case-insensitive
# Output: play | opera | film | tv | auto | "" (unrecognized)
resolve_type() {
  local raw="${1:-}"
  # Lowercase English letters; Chinese characters pass through unchanged.
  raw=$(echo "$raw" | tr '[:upper:]' '[:lower:]')
  case "$raw" in
    # play (stage drama / theater)
    ""|play|drama|play-script|theater|theatre|话剧|戏剧|話劇|舞台剧|剧本|radio-drama|radio_play|广播剧|ラジオドラマ|ラジオリプレイ) echo "play" ;;

    # Short-form stage content (sketch / one-act)
    小品|独幕剧|獨幕劇|短篇剧|短劇本|sketch|one-act) echo "play" ;;

    # opera (Chinese opera / Western opera / musical + world traditional stage)
    opera|戏曲|歌剧|音乐剧|京戏|京剧|越剧|黄梅戏|昆曲|川剧|豫剧|秦腔|评剧|粤剧|xiqu|chinese-opera|musical) echo "opera" ;;

    # Japanese traditional theater (noh / kyogen / kabuki / bunraku / rakugo / joruri)
    能|能楽|能乐|狂言|歌舞伎|kabuki|noh|kyogen|kyougen|bunraku|文楽|文乐|落語|rakugo|浄瑠璃|净琉璃|joruri|野郎節) echo "opera" ;;

    # Western musical stage (broadway / west-end / musical-theater)
    broadway|west-end|westend|musical-theater|musical_theater) echo "opera" ;;

    # Indian classical dance-drama (kathakali etc.)
    kathakali|卡塔卡利|婆罗多舞|梵剧|梵语剧|bharatanatyam|バラタナティヤム|kathak|卡塔克|玛尼普丽舞|マニプリ|manipuri|奥迪西舞|odissi) echo "opera" ;;

    # film (movie)
    film|movie|cinema|screenplay|shooting-script|电影|影片|分镜|台本) echo "film" ;;

    # Indian cinema industry tags
    bollywood|tollywood|kollywood|mollywood|sandalwood|宝莱坞|宝萊塢|印度电影|ボリウッド) echo "film" ;;

    # tv (television series)
    tv|television|drama-series|电视剧|连续剧|剧集|series|episode|anime|动画) echo "tv" ;;

    # Short-form digital serial (vertical-screen drama)
    短剧|微短剧|短视频剧|竖屏剧) echo "tv" ;;

    # Korean drama (K-drama / 사극 / 한국드라마)
    kdrama|k-drama|korean-drama|사극|한국드라마|드라마|韩剧|韓劇|韓ドラ|韓國ドラマ) echo "tv" ;;

    # Turkish / Middle East TV (dizi)
    dizi) echo "tv" ;;

    # Web series / mini-series
    web-series|webseries|webdrama|web-drama|mini-series|miniseries) echo "tv" ;;

    # auto
    auto) echo "auto" ;;
    *) echo "" ;;
  esac
}

# ---------- 1.5) Type parsing (with error handling and default) ----------
# Unlike resolve_type, this function returns an error and exits non-zero
# on unrecognized input, and returns the default "play" for empty input.
# Output: canonical type (play|opera|film|tv|auto) on stdout
# Return: 0 on success / 1 on unrecognized
parse_type_arg() {
  local raw="${1:-}"
  if [ -z "$raw" ]; then
    echo "play"
    return 0
  fi
  local resolved
  resolved=$(resolve_type "$raw")
  if [ -z "$resolved" ]; then
    echo "[ERROR] Unknown script type: $raw (supported: play/opera/film/tv/auto)" >&2
    return 1
  fi
  echo "$resolved"
}

# ---------- 2) Type → default search keyword (zh/en) ----------
# Multiple words separated by commas; the caller converts to '+'.
type_keyword_zh() {
  case "$1" in
    play)  echo "剧本" ;;
    opera) echo "戏本,曲谱,唱词,工尺谱" ;;
    film)  echo "电影剧本,分镜,台本" ;;
    tv)    echo "电视剧本,分集剧情,集" ;;
  esac
}
type_keyword_en() {
  case "$1" in
    play)  echo "script,play" ;;
    opera) echo "libretto,score,vocal score" ;;
    film)  echo "screenplay,shooting script" ;;
    tv)    echo "TV script,episode script,teleplay" ;;
  esac
}

# ---------- 3) Auto mode: keyword heuristic ----------
# Priority: tv > opera > film > play
auto_detect_type() {
  local kw="$1"
  # Detection order: tv → opera → film → play (fallback)
  # All greps use -i for case-insensitive matching.
  if echo "$kw" | grep -qiE '第[0-9一二三四五六七八九十]+集|分集剧情|集数|Episode|Season|TV|teleplay|迷你剧|^S[0-9 ]+E[0-9]|E[0-9]{2}|S[0-9]{1,2}E[0-9]{1,2}|kdrama|k-drama|드라마|韩剧|韓劇|韓ドラ|dizi|mini-series|miniseries|webseries|web-series|短剧|微短剧|竖屏剧|短视频剧'; then echo "tv"; return; fi
  if echo "$kw" | grep -qiE '京剧|越剧|黄梅|昆曲|川剧|豫剧|秦腔|评剧|粤剧|歌剧|音乐剧|戏曲|唱本|唱词|曲谱|Musical|Opera|libretto|歌舞伎|能楽|能乐|狂言|文楽|文乐|落語|rakugo|kabuki|noh|kyogen|bunraku|joruri|kathakali|婆罗多舞|bharatanatyam|broadway|west-end|westend|野郎節|^能 | 能 |^能$'; then echo "opera"; return; fi
  if echo "$kw" | grep -qiE '电影|影片|分镜|台本|movie|screenplay|shooting script|shot list|cinema|\bINT\.|\bEXT\.|FADE IN|CUT TO|bollywood|tollywood|kollywood|宝莱坞|宝萊塢|ボリウッド'; then echo "film"; return; fi
  echo "play"
}

# ---------- 4) Type → 5-dimensional analysis framework header ----------
# Output: 5 dimensions separated by '/'.
type_framework() {
  case "$1" in
    play)  echo "Theme/Characters/Acts & Scenes/Conflict/Style" ;;
    opera) echo "Theme/Characters/Scenes/Conflict/Vocal & melodic modes" ;;
    film)  echo "Theme/Characters/Scenes/Conflict/Audio-visual + genre" ;;
    tv)    echo "Theme/Characters/Episodes/Conflict/Series structure + genre" ;;
  esac
}

# ---------- 4.5) Type → structural-unit detection regex ----------
# analyze.sh's detect_sections() picks a regex by type.
section_regex() {
  case "$1" in
    play)  echo '(第[一二三四五六七八九十百零0-9]+[幕场]|Act [IVX0-9]+|Scene [IVX0-9]+)' ;;
    opera) echo '(第[一二三四五六七八九十百零0-9]+[场折出]|[\[【](西皮|二黄|流水|慢板|导板|原板|散板|四平调|摇板|反二黄|高拨子)[\]】])' ;;
    film)  echo '((INT\.|EXT\.|FADE IN|FADE OUT|CUT TO)[\s\.][^[:cntrl:]]{0,50})' ;;
    tv)    echo '((INT\.|EXT\.|CUT TO|COLD OPEN|EPISODE [0-9]+|S[0-9]{2}E[0-9]{2}|TAG|ACT [0-9]+)[\s\.:][^[:cntrl:]]{0,50})' ;;
  esac
}

# ---------- 5) Copyright inference ----------
# Input: url, optional title
# Output: pd | user_uploaded | copyrighted | unknown
# Rule order: domain rules match first (pd > user_uploaded > copyrighted),
# then keyword fallback, finally unknown.
copyright_infer() {
  local url="$1"
  local title="${2:-}"

  # PD (public-domain) domains
  case "$url" in
    *archive.org*|*gutenberg.org*|*wikisource.org*|*openlibrary.org*|*ctext.org*|*imslp.org*)
      echo "pd"; return ;;
  esac

  # User-uploaded document sites
  case "$url" in
    *doc88.com*|*taodocs.com*|*max.book118.com*|*renrendoc.com*|*docin.com*|*zhuanlan.zhihu.com*)
      echo "user_uploaded"; return ;;
  esac

  # Known paywalled / strict-copyright sites (incl. modern-film study sites)
  case "$url" in
    *wenku.baidu.com*|*douban.com/paid*|*iqiyi.com*|*v.qq.com*|*youku.com*|*imsdb.com*|*scriptslug.com*|*script-o-rama.com*|*drew.edu/script-o-rama*|*simplyscripts.com*)
      echo "copyrighted"; return ;;
  esac

  # Keyword fallback -- match title and URL separately to avoid "PD"
  # accidentally matching ".pdf" / ".PDF".
  # Title allows short tokens (PD / CC-BY / etc. as users actually write them);
  # URL only matches longer distinctive strings, avoiding file-extension
  # substring matches.
  if [ -n "$title" ] && echo "$title" | grep -qiE '\bPD\b|\bpublic domain\b|公共版权|公有领域|公版|CC[[:space:]]?-?BY|CC[[:space:]]?-?0|shakespeare|hamlet|macbeth|king lear|othello|cautious heart|雷雨|曹禺|哈姆雷特'; then
    echo "pd"; return
  fi
  if echo "$url" | grep -qiE 'public[-_]domain|creativecommons|/pd/|公版'; then
    echo "pd"; return
  fi

  # copyrighted keywords (check URL and title together)
  local combined="$title $url"
  if echo "$combined" | grep -qiE 'vip|付费|preview|试读|大会员|exclusive|仅供|modern|2020|2021|2022|2023|2024|2025|2026|new release'; then
    echo "copyrighted"; return
  fi

  # Default
  echo "unknown"
}

# ---------- 6) Domain → reliability score (0-5) ----------
get_reliability_ext() {
  local url="$1"
  case "$url" in
    *archive.org*|*gutenberg.org*|*wikisource.org*|*ctext.org*|*imslp.org*) echo 5 ;;
    *openlibrary.org*|*ocw.mit.edu*|*oyc.yale.edu*|*dramaonlinelibrary.com*|*scholar.google.com*|*jstor.org*|*imsdb.com*|*scriptslug.com*|*script-o-rama.com*|*drew.edu/script-o-rama*) echo 4 ;;
    *doc88.com*|*taodocs.com*|*max.book118.com*|*zhuanlan.zhihu.com*) echo 3 ;;
    *renrendoc.com*|*book.douban.com*) echo 2 ;;
    *wenku.baidu.com*) echo 1 ;;
    *) echo 0 ;;
  esac
}

# ---------- 7) Type → copyright warning (banner text) ----------
type_warning() {
  case "$1" in
    play)  echo "Stage drama: many classic works are PD and safe to find by default; modern copyrighted plays require user authorization." ;;
    opera) echo "Chinese/Western opera & musical: traditional repertoire is mostly PD (京剧/越剧/黄梅戏 etc.); modern new works require copyright attention." ;;
    film)  echo "Film: only early PD works (pre-1929 / Chaplin / Keaton / Griffith etc.) are safe by default; modern films require user authorization. Search results carry a copyright tag." ;;
    tv)    echo "TV series: copyright is highly concentrated and not recommended. The script will warn and tag every result as copyrighted." ;;
  esac
}
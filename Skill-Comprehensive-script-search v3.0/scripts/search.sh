#!/bin/bash
# search.sh - find-script v3.0.0 real parallel search engine (supports 4 script types + copyright tag)
#
# Usage:
#   ./search.sh "play-name" [zh|en|any] [options]
#
# Examples:
#   ./search.sh "Thunderstorm"                            # default zh + play
#   ./search.sh "Hamlet" en --type play --max-results 5
#   ./search.sh "Peony Pavilion" --type opera --json
#   ./search.sh "Citizen Kane" en --type film --quiet
#   ./search.sh "test" --no-fetch                        # build URLs only, no fetching
#   ./search.sh "Thunderstorm" --filter-copyright pd,user_uploaded  # only show PD / user-uploaded
#
# Options:
#   --type TYPE              script type: play|opera|film|tv|auto (default play, backward-compatible)
#   --json                   emit JSON array (default: 6-column TSV)
#   --max-results N          max results returned (default 20; non-numeric falls back to 20)
#   --filter-copyright TAGS  comma-separated tag filter (pd/user_uploaded/copyrighted/unknown)
#   --quiet, -q              quiet mode (no progress on stderr)
#   --no-fetch               build URLs only, do not actually fetch (debug; zero network)
#   -h, --help               show this help
#
# Output format (TSV): engine<TAB>url<TAB>format<TAB>reliability<TAB>title<TAB>copyright
# Output format (JSON): array of objects, each with 6 keys
#                      (engine/url/format/reliability/title/copyright)

set -uo pipefail

# ---------- Dependencies ----------
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILL_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
# shellcheck source=lib/types.sh
source "$SCRIPT_DIR/lib/types.sh"

# ---------- Argument parsing ----------
PLAY_NAME=""
LANGUAGE="zh"
MAX_RESULTS=20
OUTPUT_FORMAT="tsv"
QUIET=0
NO_FETCH=0
TYPE=""
FILTER_COPYRIGHT=""   # empty = no filter; else comma-separated tag set, e.g. pd,user_uploaded

while [[ $# -gt 0 ]]; do
  case "$1" in
    --type=*)       TYPE=$(parse_type_arg "${1#--type=}") || exit 1; shift ;;
    --type)
      # If the next arg is another flag (starts with --) or is missing,
      # treat as valueless and fall back to default play
      if [ $# -lt 2 ] || [[ "$2" == --* ]]; then
        TYPE="play"
        shift
      else
        TYPE=$(parse_type_arg "$2") || exit 1
        shift 2
      fi
      ;;
    --json)         OUTPUT_FORMAT="json"; shift ;;
    --max-results=*) MAX_RESULTS="${1#--max-results=}"; shift ;;
    --max-results)  MAX_RESULTS="${2:-}"; shift 2 ;;
    --quiet|-q)     QUIET=1; shift ;;
    --no-fetch)     NO_FETCH=1; shift ;;
    --filter-copyright=*) FILTER_COPYRIGHT="${1#--filter-copyright=}"; shift ;;
    --filter-copyright)
      # If next arg is another flag or is missing, error out
      if [ $# -lt 2 ] || [[ "$2" == --* ]]; then
        echo "[ERROR] --filter-copyright requires TAG,... (pd/user_uploaded/copyrighted/unknown)" >&2
        exit 1
      fi
      FILTER_COPYRIGHT="$2"; shift 2 ;;
    zh|en|any)      LANGUAGE="$1"; shift ;;
    -h|--help)
      sed -n '2,25p' "${BASH_SOURCE[0]}"
      exit 0 ;;
    *)              PLAY_NAME="$1"; shift ;;
  esac
done

# Defaults
[ -z "$TYPE" ] && TYPE="play"

# Trim keyword (strip leading/trailing whitespace; avoid searching on empty string)
# shellcheck disable=SC2001
PLAY_NAME="$(echo "$PLAY_NAME" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
if [ -z "$PLAY_NAME" ]; then
  echo "[ERROR] Play name cannot be empty (or whitespace-only)" >&2
  echo "Usage: $0 <play-name> [zh|en|any] [--type TYPE] [--json] [--max-results N] [--quiet] [--no-fetch]" >&2
  echo "Example: $0 \"Hamlet\" en --type play --max-results 10" >&2
  exit 1
fi

# MAX_RESULTS sanitize: must be a positive integer, else fall back to 20
if ! [[ "$MAX_RESULTS" =~ ^[0-9]+$ ]] || [ "$MAX_RESULTS" -lt 1 ]; then
  MAX_RESULTS=20
fi

# auto mode: heuristically infer script type
if [ "$TYPE" = "auto" ] && [ -n "$PLAY_NAME" ]; then
  detected=$(auto_detect_type "$PLAY_NAME")
  if [ -n "$detected" ]; then
    TYPE="$detected"
  fi
fi

# URL encoding (works without python3)
url_encode() {
  local raw="$1"
  if command -v python3 >/dev/null 2>&1; then
    python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$raw"
  else
    python -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$raw" 2>/dev/null \
      || echo "$raw" | sed 's/ /+/g; s/[^A-Za-z0-9+._~-]/%&/g'
  fi
}

KEYWORD=$(url_encode "$PLAY_NAME")

# ---------- Engine definition ----------
# Prefer the search-engine/ submodule; fall back to local config.json;
# finally fall back to a hardcoded list.
# Format: "name|region|url_template"
#
# Priority:
#   1. search-engine/config.json (submodule, recommended)
#   2. ./config.json (local copy)
#   3. Built-in fallback (hardcoded, backward-compatible)
resolve_engine_config() {
  local candidates=(
    "$SCRIPT_DIR/../search-engine/config.json"
    "$SCRIPT_DIR/../config.json"
  )
  for cfg in "${candidates[@]}"; do
    if [ -f "$cfg" ]; then
      echo "$cfg"
      return 0
    fi
  done
  return 1
}

# Load engine config (filter by region)
# Output: name|region|url (one per line, url contains {keyword} placeholder)
load_engines_from_config() {
  local region_filter="$1"  # "cn" | "global" | "all"
  local cfg
  if ! cfg=$(resolve_engine_config); then
    return 1
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    return 1
  fi
  python3 -c "
import json, sys
with open('$cfg') as f:
    cfg = json.load(f)
for e in cfg.get('engines', []):
    name = e.get('name', '').strip()
    url = e.get('url', '').strip()
    region = e.get('region', 'global').strip()
    if not name or not url:
        continue
    if '$region_filter' != 'all' and region != '$region_filter':
        continue
    # Normalize name (lowercase, spaces to underscores)
    slug = name.lower().replace(' ', '_').replace('-', '_')
    print(f'{slug}|{region}|{url}')
" 2>/dev/null
}

# Built-in fallback (no submodule / no config.json)
builtin_engines() {
  local region_filter="$1"
  cat <<'EOF'
baidu|cn|https://www.baidu.com/s?wd={keyword}
bing_cn|cn|https://cn.bing.com/search?q={keyword}&ensearch=0
bing_int|cn|https://cn.bing.com/search?q={keyword}&ensearch=1
360|cn|https://www.so.com/s?q={keyword}
sogou|cn|https://sogou.com/web?query={keyword}
wechat|cn|https://wx.sogou.com/weixin?type=2&query={keyword}
shenma|cn|https://m.sm.cn/s?q={keyword}
google|global|https://www.google.com/search?q={keyword}
google_hk|global|https://www.google.com.hk/search?q={keyword}
duckduckgo|global|https://duckduckgo.com/html/?q={keyword}
yahoo|global|https://search.yahoo.com/search?p={keyword}
startpage|global|https://www.startpage.com/sp/search?query={keyword}
brave|global|https://search.brave.com/search?q={keyword}
ecosia|global|https://www.ecosia.org/search?q={keyword}
qwant|global|https://www.qwant.com/?q={keyword}
wolfram|global|https://www.wolframalpha.com/input?i={keyword}
EOF
}

# Inject type-specific keywords into URL (v2.0: switch by type)
# The submodule config.json uses {keyword} placeholder; this function:
#   1. Replaces {keyword} with "<play>+<type keyword>+filetype:pdf"
#   2. URL-encodes CJK
#   3. Different types use different keyword templates
#      (script / libretto,score / screenplay,shot list / TV script,episode)
inject_type_keyword() {
  local url="$1"
  local lang="$2"
  local play="$3"
  local type="$4"

  # Pull the keyword template for this type
  local extra_zh extra_en
  extra_zh=$(type_keyword_zh "$type")
  extra_en=$(type_keyword_en "$type")

  # Join with '+' (comma → +)
  local full_kw
  case "$lang" in
    en)  full_kw="${play}+${extra_en//,/+}+filetype:pdf" ;;
    *)   full_kw="${play}+${extra_zh//,/+}+filetype:pdf" ;;
  esac

  # URL encode (prefer python3; fall back to sed)
  if command -v python3 >/dev/null 2>&1; then
    full_kw=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$full_kw")
  fi

  # Replace placeholder
  url="${url/\{keyword\}/$full_kw}"

  echo "$url"
}

# Main entry: build (name|region|url) list
build_engines() {
  local lang="$1"
  local kw="$2"
  local type="$3"
  local primary_region="cn"
  local secondary_region="global"

  if [ "$lang" = "en" ]; then
    primary_region="global"
    secondary_region="cn"
  fi

  # Try reading from config
  local primary secondary
  if primary=$(load_engines_from_config "$primary_region") && [ -n "$primary" ]; then
    secondary=$(load_engines_from_config "$secondary_region")
  else
    # Fall back to built-in
    primary=$(builtin_engines "$primary_region")
    secondary=$(builtin_engines "$secondary_region")
  fi

  # Emit primary + secondary
  while IFS='|' read -r name region url; do
    [ -z "$name" ] && continue
    inject_type_keyword "$url" "$lang" "$kw" "$type" | awk -v n="$name" -v r="$region" '{print n"|"r"|"$0}'
  done <<< "$primary"
  while IFS='|' read -r name region url; do
    [ -z "$name" ] && continue
    inject_type_keyword "$url" "$lang" "$kw" "$type" | awk -v n="$name" -v r="$region" '{print n"|"r"|"$0}'
  done <<< "$secondary"
}

# ---------- Domain reliability scoring (5-point scale) ----------
# Function defined in scripts/lib/types.sh (get_reliability_ext)
get_reliability() {
  get_reliability_ext "$@"
}

# ---------- File format detection ----------
detect_format() {
  local url="$1"
  local content_type="${2:-}"
  case "$url$content_type" in
    *.pdf|*application/pdf*|*filetype:pdf*) echo "pdf" ;;
    *.docx*|*application/vnd.openxmlformats-officedocument.wordprocessingml.document*) echo "docx" ;;
    *.doc|*application/msword*) echo "doc" ;;
    *.txt|*text/plain*) echo "txt" ;;
    *.html|*.htm|*text/html*) echo "html" ;;
    *.epub*) echo "epub" ;;
    *) echo "unknown" ;;
  esac
}

# ---------- Link extraction (from search-engine result HTML) ----------
extract_links() {
  local html_file="$1"
  local engine="$2"
  [ -f "$html_file" ] || return 0

  # Generic extraction: href="...", filter out scripts/styles/ads.
  # Different engines have different result containers; we use a generic
  # pattern.
  grep -oE 'href="[^"]+"' "$html_file" 2>/dev/null | \
    sed 's/^href="//; s/"$//' | \
    grep -E '^https?://' | \
    grep -viE '(login|signup|javascript|ad|track|css|fonts?|api\.|favicon|\.js|\.css|\.png|\.jpg|\.svg|\.ico)' | \
    grep -viE '(\.google\.com/.*search|\.bing\.com/.*search|\.baidu\.com/.*s\?|\.sogou\.com/.*query|\.so\.com/.*s\?|\.sm\.cn/.*s\?|\.wolframalpha\.com/.*input|\.duckduckgo\.com/.*html)' | \
    head -50
}

# ---------- Single-engine search ----------
do_search() {
  local engine="$1"
  local region="$2"
  local url="$3"
  local outdir="$4"

  local outfile="$outdir/${engine}.html"
  local statusfile="$outdir/${engine}.status"

  if [ "$NO_FETCH" = "1" ]; then
    echo "URL_ONLY" > "$statusfile"
    return
  fi

  # Real fetch: 15s timeout, standard User-Agent
  if curl -sS -L --max-time 15 \
        -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
        -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
        -H "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8" \
        -o "$outfile" \
        -w "%{http_code}" \
        "$url" > "$statusfile.code" 2>/dev/null; then
    local code=$(cat "$statusfile.code" 2>/dev/null || echo "000")
    if [ -s "$outfile" ] && [ "$code" = "200" ]; then
      echo "OK" > "$statusfile"
    else
      echo "HTTP_${code}" > "$statusfile"
    fi
  else
    echo "FAIL" > "$statusfile"
  fi
}

export -f do_search get_reliability detect_format extract_links copyright_infer
export SKILL_DIR

# ---------- Main flow ----------
TMPDIR=$(mktemp -d)
# Single-quote prevents shell-expansion injection if TMPDIR contains
# special characters (Bug #8)
trap 'rm -rf "$TMPDIR"' EXIT INT TERM

[ "$QUIET" = "0" ] && echo "Searching: $PLAY_NAME (type=$TYPE, lang=$LANGUAGE, 16 engines)" >&2
[ "$QUIET" = "0" ] && echo "═══════════════════════════════════════" >&2

# Launch all engines (parallel)
ENGINE_LIST=$(mktemp)
build_engines "$LANGUAGE" "$KEYWORD" "$TYPE" > "$ENGINE_LIST"

while IFS='|' read -r name region url; do
  [ -z "$name" ] && continue
  do_search "$name" "$region" "$url" "$TMPDIR" &
done < "$ENGINE_LIST"
wait

# Collect results
RESULTS=$(mktemp)
while IFS='|' read -r name region url; do
  [ -z "$name" ] && continue
  status=$(cat "$TMPDIR/${name}.status" 2>/dev/null || echo "FAIL")

  if [ "$QUIET" = "0" ]; then
    case "$status" in
      OK)     echo "  OK $name" >&2 ;;
      URL_ONLY) echo "  .  $name (URL only)" >&2 ;;
      *)      echo "  FAIL $name ($status)" >&2 ;;
    esac
  fi

  if [ "$status" = "OK" ]; then
    extract_links "$TMPDIR/${name}.html" "$name" | while read -r link; do
      [ -z "$link" ] && continue
      reliability=$(get_reliability "$link")
      format=$(detect_format "$link")
      title=$(echo "$link" | sed 's|https\?://||; s|/.*||' | head -c 80)
      copyright=$(copyright_infer "$link" "$title")
      printf "%s\t%s\t%s\t%s\t%s\t%s\n" "$name" "$link" "$format" "$reliability" "$title" "$copyright" >> "$RESULTS"
    done
  elif [ "$status" = "URL_ONLY" ]; then
    # URL-only mode: use the search URL itself as a clickable link
    reliability=$(get_reliability "$url")
    format=$(detect_format "$url")
    copyright=$(copyright_infer "$url" "$name")
    printf "%s\t%s\t%s\t%s\t%s\t%s\n" "$name" "$url" "$format" "$reliability" "$name-search" "$copyright" >> "$RESULTS"
  fi
done < "$ENGINE_LIST"

# Dedupe + sort (by reliability, descending)
DEDUPED=$(mktemp)
if [ -s "$RESULTS" ]; then
  # Dedupe by engine+url combo (keep query's host+path portion to avoid
  # bing_cn/bing_int collisions)
  awk -F'\t' '{
    key = $1 "\t" $2;  # engine + url as composite key
    if (!seen[key]++) print
  }' "$RESULTS" > "$DEDUPED"

  # Sort by reliability descending (numeric column)
  sort -t$'\t' -k4,4 -nr "$DEDUPED" > "${DEDUPED}.sorted"
else
  : > "${DEDUPED}.sorted"
fi

# Take top N
TOP_N=$(mktemp)
head -n "$MAX_RESULTS" "${DEDUPED}.sorted" > "$TOP_N"

# Copyright filter: if FILTER_COPYRIGHT is set (comma-separated), keep
# only rows whose 6th column matches.
if [ -n "$FILTER_COPYRIGHT" ]; then
  FILTERED=$(mktemp)
  head -1 "$TOP_N" > "$FILTERED"  # preserve header
  # awk checks if column 6 is in the whitelist
  awk -F'\t' -v tags="$FILTER_COPYRIGHT" '
    NR == 1 { print; next }
    {
      n = split(tags, arr, ",")
      found = 0
      for (i = 1; i <= n; i++) {
        if ($6 == arr[i]) { found = 1; break }
      }
      if (found) print
    }
  ' "$TOP_N" >> "$FILTERED"
  mv "$FILTERED" "$TOP_N"
  [ "$QUIET" = "0" ] && echo "Copyright filter: keeping only [$FILTER_COPYRIGHT]" >&2
fi

TOTAL=$(wc -l < "${DEDUPED}.sorted" | tr -d ' ')
SHOWN=$(wc -l < "$TOP_N" | tr -d ' ')

[ "$QUIET" = "0" ] && echo "═══════════════════════════════════════" >&2
[ "$QUIET" = "0" ] && echo "Found $TOTAL links, showing top $SHOWN" >&2

# ---------- Output ----------
if [ "$OUTPUT_FORMAT" = "json" ]; then
  echo "["
  first=1
  while IFS=$'\t' read -r engine url format reliability title copyright; do
    [ -z "$engine" ] && continue
    if [ "$first" = "1" ]; then first=0; else echo ","; fi
    printf '  {"engine":"%s","url":"%s","format":"%s","reliability":%s,"title":"%s","copyright":"%s"}' \
      "$engine" "$url" "$format" "$reliability" "$title" "$copyright"
  done < "$TOP_N"
  echo ""
  echo "]"
else
  echo "engine	url	format	reliability	title	copyright"
  cat "$TOP_N"
fi

# Cleanup
rm -f "$RESULTS" "$DEDUPED" "${DEDUPED}.sorted" "$TOP_N" "$ENGINE_LIST"
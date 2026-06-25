#!/bin/bash
# find-play.sh - find-script v3.0.0 main orchestrator (one-shot end-to-end, 4 script types)
#
# Usage:
#   ./find-play.sh "<play-name>" --save-path PATH [options]
#
# Examples:
#   # Stage drama (default)
#   ./find-play.sh "Thunderstorm" --save-path ~/Desktop --auto-download 3 --analyze --yes
#   ./find-play.sh "Hamlet" --author Shakespeare --language en --save-path ~/Desktop --yes
#
#   # Chinese / Western opera & musical
#   ./find-play.sh "Drunken Beauty" --type opera --save-path ~/Desktop/xiqu --yes
#   ./find-play.sh "Carmen" --type opera --language en --save-path ~/Desktop --yes
#
#   # Film (pre-1929 are PD; modern films need --filter-copyright)
#   ./find-play.sh "Citizen Kane" --type film --language en --save-path ~/Desktop --yes
#
#   # TV series
#   ./find-play.sh "I Love Lucy" --type tv --language en --save-path ~/Desktop --yes
#
#   # PD / user-uploaded only
#   ./find-play.sh "Hamlet" --filter-copyright pd,user_uploaded --save-path ~/Desktop --yes
#
# Options:
#   --type TYPE                 script type: play|opera|film|tv|auto (default play)
#   --author NAME               author name (appended to search keyword)
#   --language zh|en|any        language (default auto: CN for Chinese, global for English)
#   --save-path PATH            download path (required; v2.1 rejects /etc /usr etc.)
#   --filename NAME             custom filename (default <play>_<author>.<ext>)
#   --format pdf|docx|txt|html|any  preferred format (default any)
#   --auto-download N           auto-download top N results (default 0: list only)
#   --analyze                   run 5-dim analysis after download
#   --filter-copyright TAGS     copyright tag filter (pd/user_uploaded/copyrighted/unknown)
#   --yes, -y                   skip all confirmations (required for CI/batch)
#   --max-results N             search result count (default 20)
#   --max-size MB               per-file size cap (default 50)
#   --json                      JSON output
#   --quiet, -q                 quiet mode
#   -h, --help                  show this help
#
# Exit codes: 0 success / 1 arg error / 2 no results / 3 download failed / 4 path not writable

set -uo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILL_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
# shellcheck source=lib/types.sh
source "$SCRIPT_DIR/lib/types.sh"

# ---------- Defaults ----------
PLAY_NAME=""
AUTHOR=""
LANGUAGE="auto"
SAVE_PATH=""
FILENAME=""
FORMAT="any"
AUTO_DOWNLOAD=0
ANALYZE=0
YES=0
MAX_RESULTS=20
MAX_SIZE_MB=50
JSON_OUT=0
QUIET=0
TYPE=""
FILTER_COPYRIGHT=""   # passed through to search.sh

# ---------- Argument parsing ----------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --type=*)         TYPE=$(parse_type_arg "${1#--type=}") || exit 1; shift ;;
    --type)           TYPE=$(parse_type_arg "${2:-}") || exit 1; shift 2 ;;
    --author=*)       AUTHOR="${1#--author=}"; shift ;;
    --author)         AUTHOR="${2:-}"; shift 2 ;;
    --language=*)     LANGUAGE="${1#--language=}"; shift ;;
    --language)       LANGUAGE="${2:-}"; shift 2 ;;
    --save-path=*)    SAVE_PATH="${1#--save-path=}"; shift ;;
    --save-path)      SAVE_PATH="${2:-}"; shift 2 ;;
    --filename=*)     FILENAME="${1#--filename=}"; shift ;;
    --filename)       FILENAME="${2:-}"; shift 2 ;;
    --format=*)       FORMAT="${1#--format=}"; shift ;;
    --format)         FORMAT="${2:-}"; shift 2 ;;
    --auto-download=*) AUTO_DOWNLOAD="${1#--auto-download=}"; shift ;;
    --auto-download)  AUTO_DOWNLOAD="${2:-}"; shift 2 ;;
    --analyze)        ANALYZE=1; shift ;;
    --yes|-y)         YES=1; shift ;;
    --max-results=*)  MAX_RESULTS="${1#--max-results=}"; shift ;;
    --max-results)    MAX_RESULTS="${2:-}"; shift 2 ;;
    --max-size=*)     MAX_SIZE_MB="${1#--max-size=}"; shift ;;
    --max-size)       MAX_SIZE_MB="${2:-}"; shift 2 ;;
    --json)           JSON_OUT=1; shift ;;
    --quiet|-q)       QUIET=1; shift ;;
    --filter-copyright=*) FILTER_COPYRIGHT="${1#--filter-copyright=}"; shift ;;
    --filter-copyright)
      if [ $# -lt 2 ] || [[ "$2" == --* ]]; then
        err "--filter-copyright requires TAG,... (pd/user_uploaded/copyrighted/unknown)"
        exit 1
      fi
      FILTER_COPYRIGHT="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,42p' "${BASH_SOURCE[0]}"
      exit 0 ;;
    # Language identifier (zh/en/auto) as 2nd positional arg wins over
    # PLAY_NAME, so "find-play.sh Hamlet en --type ..." doesn't treat
    # `en` as the play name.
    zh|en|auto)  LANGUAGE="$1"; shift ;;
    *)                PLAY_NAME="$1"; shift ;;
  esac
done

[ -z "$TYPE" ] && TYPE="play"

# Trim keyword (avoid blank names slipping through)
# shellcheck disable=SC2001
PLAY_NAME="$(echo "$PLAY_NAME" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"

# ---------- Helper functions ----------
log()    { [ "$QUIET" = "0" ] && echo "$@" >&2; }
header() { log ""; log "=== $1 ==="; }
warn()   { log "[WARN] $*"; }
err()    { log "[ERROR] $*"; }
ok()     { log "[OK] $*"; }

# ---------- Argument validation ----------
if [ -z "$PLAY_NAME" ]; then
  err "Usage: $0 \"<play-name>\" --save-path PATH [options]"
  err "Example: $0 \"Hamlet\" --save-path ~/Desktop/shakespeare --author Shakespeare --yes"
  exit 1
fi

if [ -z "$SAVE_PATH" ]; then
  err "--save-path is required"
  exit 1
fi

# Numeric sanitize: prevent non-numeric --max-results / --auto-download from
# crashing downstream
if ! [[ "$MAX_RESULTS" =~ ^[0-9]+$ ]] || [ "$MAX_RESULTS" -lt 1 ]; then
  MAX_RESULTS=20
fi
if ! [[ "$AUTO_DOWNLOAD" =~ ^[0-9]+$ ]]; then
  AUTO_DOWNLOAD=0
fi
if ! [[ "$MAX_SIZE_MB" =~ ^[0-9]+$ ]] || [ "$MAX_SIZE_MB" -lt 1 ]; then
  MAX_SIZE_MB=50
fi

# Register cleanup trap (Bug #7): Ctrl-C or abnormal exit cleans mktemp files
_find_play_cleanup() {
  [ -n "$SEARCH_OUT" ] && rm -f "$SEARCH_OUT" 2>/dev/null
  [ -n "$FILTERED" ] && rm -f "$FILTERED" 2>/dev/null
  [ -n "$DOWNLOAD_LIST" ] && rm -f "$DOWNLOAD_LIST" 2>/dev/null
  [ -n "$BATCH_FILE" ] && rm -f "$BATCH_FILE" 2>/dev/null
}
trap '_find_play_cleanup' EXIT INT TERM

# Auto-detect language
if [ "$LANGUAGE" = "auto" ]; then
  if echo "$PLAY_NAME" | grep -qE '[一-龥]'; then
    LANGUAGE="zh"
  else
    LANGUAGE="en"
  fi
  log "Auto-detected language: $LANGUAGE"
fi

# auto mode: keyword heuristic for script type (only when --type auto)
if [ "$TYPE" = "auto" ]; then
  detected=$(auto_detect_type "$PLAY_NAME")
  if [ -n "$detected" ]; then
    TYPE="$detected"
    log "Auto-detected type: $TYPE"
  fi
fi

# Build keyword
KEYWORD="$PLAY_NAME"
if [ -n "$AUTHOR" ]; then
  KEYWORD="${PLAY_NAME} ${AUTHOR}"
fi

# ---------- Step 0: type + copyright notice ----------
header "0/4 Type: $TYPE"
warn "$(type_warning "$TYPE")"

# ---------- Step 1: search ----------
header "1/4 Search: $KEYWORD"

# Register tmp files with global cleanup (Bug #7)
SEARCH_OUT=$(mktemp)
SEARCH_ARGS=("$KEYWORD" "$LANGUAGE" --type "$TYPE" --max-results "$MAX_RESULTS" --quiet)
if [ -n "$FILTER_COPYRIGHT" ]; then
  SEARCH_ARGS+=(--filter-copyright "$FILTER_COPYRIGHT")
fi
"$SCRIPT_DIR/search.sh" "${SEARCH_ARGS[@]}" 2>/dev/null > "$SEARCH_OUT" || {
  err "Search failed"
  rm -f "$SEARCH_OUT"
  exit 2
}

TOTAL=$(tail -n +2 "$SEARCH_OUT" | wc -l | tr -d ' ')
ok "Found $TOTAL results"

if [ "$TOTAL" = "0" ]; then
  err "No results found. Try:"
  err "  - simplify the play name"
  err "  - switch language (--language zh|en)"
  err "  - add the author (--author NAME)"
  rm -f "$SEARCH_OUT"
  exit 3
fi

# ---------- Step 2: filter ----------
header "2/4 Filter"

# Prefer PDF/DOCX, sorted by reliability (search.sh already sorts)
# Filter by --format
FILTERED=$(mktemp)
if [ "$FORMAT" = "any" ]; then
  tail -n +2 "$SEARCH_OUT" > "$FILTERED"
else
  tail -n +2 "$SEARCH_OUT" | awk -F'\t' -v fmt="$FORMAT" '$3 == fmt' > "$FILTERED"
fi

FILT_COUNT=$(wc -l < "$FILTERED" | tr -d ' ')
log "After filter: $FILT_COUNT remaining"

if [ "$FILT_COUNT" = "0" ]; then
  warn "No $FORMAT format; falling back to any format"
  tail -n +2 "$SEARCH_OUT" > "$FILTERED"
  FILT_COUNT=$(wc -l < "$FILTERED" | tr -d ' ')
fi

# Copyright distribution (based on column 6)
COPY_STATS=$(awk -F'\t' 'NR>0 && $6!="" {print $6}' "$FILTERED" | sort | uniq -c | awk '{printf "%s=%s ", $2, $1}' | sed 's/ $//')
if [ -n "$COPY_STATS" ]; then
  log "Copyright distribution: $COPY_STATS"
fi

# Show top 5 candidates to the user
log ""
log "Top 5 candidates:"
head -5 "$FILTERED" | awk -F'\t' '{
  printf "  [%s] reliability=%s format=%s copyright=%s\n    %s\n", $1, $4, $3, $6, $2
}'

# ---------- Step 3: download ----------
header "3/4 Download"

if [ "$AUTO_DOWNLOAD" = "0" ]; then
  log "Auto-download not enabled (--auto-download N). Only listing candidates."
  if [ "$JSON_OUT" = "1" ]; then
    echo "["
    head -"$MAX_RESULTS" "$FILTERED" | awk -F'\t' 'BEGIN{first=1} {
      if (first) first=0; else printf ",\n";
      printf "  {\"engine\":\"%s\",\"url\":\"%s\",\"format\":\"%s\",\"reliability\":%s,\"title\":\"%s\",\"copyright\":\"%s\"}",
        $1, $2, $3, $4, $5, $6
    }'
    echo ""
    echo "]"
  else
    cat "$FILTERED"
  fi
  rm -f "$SEARCH_OUT" "$FILTERED"
  exit 0
fi

# Take top N for download
DOWNLOAD_LIST=$(mktemp)
head -"$AUTO_DOWNLOAD" "$FILTERED" > "$DOWNLOAD_LIST"

# Prepare batch download
BATCH_FILE=$(mktemp)
while IFS=$'\t' read -r engine url format reliability title; do
  [ -z "$url" ] && continue
  # Smart filename: <play>_<author>_<format>.<ext>
  if [ -z "$FILENAME" ]; then
    safe_name=$(echo "${PLAY_NAME}_${AUTHOR}_${format}" | tr ' /' '_' | tr -d '[:punct:]' | head -c 60)
    ext="$format"
    [ "$ext" = "unknown" ] && ext="html"
    fname="${safe_name}.${ext}"
  else
    fname="$FILENAME"
  fi
  printf "%s\t%s\n" "$url" "$fname" >> "$BATCH_FILE"
done < "$DOWNLOAD_LIST"

# Confirm download
if [ "$YES" = "0" ] && [ -t 0 ]; then
  log ""
  log "About to download top $AUTO_DOWNLOAD file(s) to: $SAVE_PATH"
  read -p "Confirm? (y/N) " -n 1 -r < /dev/tty
  echo >&2
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log "Cancelled"
    rm -f "$SEARCH_OUT" "$FILTERED" "$DOWNLOAD_LIST" "$BATCH_FILE"
    exit 0
  fi
fi

# Execute download
DOWNLOADED=()
while IFS=$'\t' read -r url filename; do
  [ -z "$url" ] && continue
  if [ "$YES" = "1" ]; then
    export FIND_PLAY_YES=1
  fi
  if out=$("$SCRIPT_DIR/download.sh" "$url" "$SAVE_PATH" "$filename" --yes --max-size "$MAX_SIZE_MB" 2>&1); then
    downloaded_path=$(echo "$out" | grep -v '^\[OK\]' | grep -v '^\[WARN\]' | grep -v '^\[ERROR\]' | tail -1)
    [ -n "$downloaded_path" ] && [ -f "$downloaded_path" ] && DOWNLOADED+=("$downloaded_path")
  fi
done < "$BATCH_FILE"

ok "Download complete: ${#DOWNLOADED[@]} file(s)"

# ---------- Step 4: analyze ----------
header "4/4 Analyze"

if [ "$ANALYZE" = "0" ] || [ "${#DOWNLOADED[@]}" = "0" ]; then
  log "Skipping analysis (--analyze not enabled or no files downloaded)"
  rm -f "$SEARCH_OUT" "$FILTERED" "$DOWNLOAD_LIST" "$BATCH_FILE"
  exit 0
fi

for f in "${DOWNLOADED[@]}"; do
  log ""
  log "--- Analysis ($TYPE): $f ---"
  "$SCRIPT_DIR/analyze.sh" "$f" --type "$TYPE" 2>&1 | head -50
done

# Cleanup
rm -f "$SEARCH_OUT" "$FILTERED" "$DOWNLOAD_LIST" "$BATCH_FILE"

# Cleanup again (trap is the safety net)
rm -f "$SEARCH_OUT" "$FILTERED" "$DOWNLOAD_LIST" "$BATCH_FILE"

ok "All done"
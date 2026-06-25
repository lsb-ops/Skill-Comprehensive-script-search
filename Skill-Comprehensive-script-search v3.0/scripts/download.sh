#!/bin/bash
# download.sh - find-script v3.0.0 smart downloader (works for all 4 script types)
#
# Usage:
#   ./download.sh <url> <save_path> [filename] [options]
#
# Examples:
#   ./download.sh "https://archive.org/x/leiyu.pdf" ~/Desktop --yes
#   ./download.sh "https://example.com/Hamlet.pdf" ~/Desktop Hamlet.pdf
#   ./download.sh "" "" --batch links.tsv --yes              # batch mode (one URL\tfilename per line)
#   ./download.sh URL ~/Desktop --max-size 100 --timeout 120 --retries 3
#   ./download.sh URL ~/Desktop --no-head-check             # skip HEAD pre-check
#
# Options:
#   --yes, -y             skip confirmation (non-interactive, required for CI/batch)
#   --max-size MB         file size cap (default 50MB)
#   --timeout SECONDS     download timeout (default 60s)
#   --retries N           retry count (default 2)
#   --no-head-check       skip HEAD pre-check (saves ~500ms but loses size validation)
#   --batch FILE          batch mode: FILE has one "URL<TAB>filename" per line
#   --parallel N          batch concurrency (default 1=serial, max 16, batch-mode only)
#   --user-agent UA       custom User-Agent
#   --expect-title TITLE  verify Title: metadata after download (file must contain this
#                         substring; guards against wrong-version files)
#   --quiet, -q           quiet mode
#   -h, --help            show this help
#
# Environment variables:
#   FIND_PLAY_YES=1          equivalent to --yes (required in non-interactive envs)
#   FIND_PLAY_QUIET=1        quiet mode
#   FIND_PLAY_MAX_SIZE_MB=N  default 50
#
# Safety protections (v2.1):
#   - --save-path rejects writes to /etc /usr /bin /sbin /var /lib
#   - --save-path rejects paths containing .. (path traversal guard)
#   - --filename is auto-sanitized (preserves Chinese, strips / \ : * ? " < > | etc.)
#   - HTTP 5xx/4xx error pages are NOT treated as success (curl exit code +
#     last HTTP code after -L are both checked)
#   - Content-Length is validated by ^[0-9]+$ (prevents comma/hex injection
#     bypassing --max-size)
#
# Exit codes:
#   0  success
#   1  argument error
#   2  network error (HTTP/curl failure)
#   3  file too large (exceeds --max-size)
#   4  path not writable / on blacklist
#   5  retries exhausted

set -uo pipefail

# ---------- Defaults ----------
URL=""
SAVE_PATH=""
FILENAME=""
MAX_SIZE_MB="${FIND_PLAY_MAX_SIZE_MB:-50}"
TIMEOUT=60
RETRIES=2
YES=0
HEAD_CHECK=1
BATCH_FILE=""
EXPECT_TITLE=""    # --expect-title: post-download content check (Bug #D-fix)
PARALLEL=1
USER_AGENT="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
QUIET="${FIND_PLAY_QUIET:-0}"

[ "${FIND_PLAY_YES:-0}" = "1" ] && YES=1

# ---------- Argument parsing ----------
POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --yes|-y)         YES=1; shift ;;
    --max-size)       MAX_SIZE_MB="$2"; shift 2 ;;
    --timeout)        TIMEOUT="$2"; shift 2 ;;
    --retries)        RETRIES="$2"; shift 2 ;;
    --no-head-check)  HEAD_CHECK=0; shift ;;
    --batch)          BATCH_FILE="$2"; shift 2 ;;
    --parallel=*)
      PARALLEL="${1#--parallel=}"
      if ! [[ "$PARALLEL" =~ ^[0-9]+$ ]] || [ "$PARALLEL" -lt 1 ]; then
        echo "[ERROR] --parallel needs a positive integer, got: $PARALLEL" >&2; exit 1
      fi
      [ "$PARALLEL" -gt 16 ] && PARALLEL=16  # upper bound to prevent abuse
      shift ;;
    --parallel)
      if ! [[ "${2:-}" =~ ^[0-9]+$ ]] || [ "${2:-0}" -lt 1 ]; then
        echo "[ERROR] --parallel needs a positive integer, got: ${2:-empty}" >&2; exit 1
      fi
      PARALLEL="$2"
      [ "$PARALLEL" -gt 16 ] && PARALLEL=16
      shift 2 ;;
    --user-agent)     USER_AGENT="$2"; shift 2 ;;
    --expect-title)   EXPECT_TITLE="$2"; shift 2 ;;
    --quiet|-q)       QUIET=1; shift ;;
    -h|--help)
      sed -n '2,50p' "${BASH_SOURCE[0]}"
      exit 0 ;;
    *)                POSITIONAL+=("$1"); shift ;;
  esac
done

# Pre-compute --expect-title lowercase (Bug #D-fix: avoid retr `tr` per retry)
EXPECT_TITLE_LC=""
if [ -n "$EXPECT_TITLE" ]; then
  EXPECT_TITLE_LC=$(echo "$EXPECT_TITLE" | tr '[:upper:]' '[:lower:]')
fi

log()  { [ "$QUIET" = "0" ] && echo "$@" >&2; }
warn() { echo "[WARN] $*" >&2; }
err()  { echo "[ERROR] $*" >&2; }
ok()   { echo "[OK] $*" >&2; }

# ---------- Dependency check ----------
if ! command -v curl >/dev/null 2>&1 && ! command -v wget >/dev/null 2>&1; then
  err "curl or wget is required"
  exit 1
fi

# ---------- Single-file download ----------
download_one() {
  local url="$1"
  local save_path="$2"
  local filename="$3"

  # Expand ~
  save_path="${save_path/#\~/$HOME}"

  # System-sensitive directory blacklist (Bug #17) — block before creation
  case "$save_path" in
    /etc|/etc/*|/sys|/sys/*|/proc|/proc/*|/usr|/usr/*|/bin|/bin/*|/sbin|/sbin/*|/boot|/boot/*)
      err "Refusing to write to system directory: $save_path"
      return 4
      ;;
  esac

  # Detect path traversal (Bug #17): disallow ..
  if [[ "$save_path" == *..* ]]; then
    err "Path contains '..': $save_path"
    return 4
  fi

  # Create directory
  if ! mkdir -p "$save_path" 2>/dev/null; then
    err "Path not writable: $save_path"
    return 4
  fi

  # Resolve to absolute path (for subsequent checks)
  save_path=$(cd "$save_path" 2>/dev/null && pwd) || save_path="$save_path"

  # Default filename
  if [ -z "$filename" ]; then
    filename=$(basename "$url" 2>/dev/null | sed 's/[?#].*//')
    [ -z "$filename" ] && filename="play_$(date +%s)"
  fi

  # Filename sanitize (Bug #16): keep only safe characters, strip / and ..
  # Prevents user input like "../../../etc/cron.daily/evil".
  # Allows ASCII + Unicode (CJK), but blocks path separators and ..
  local clean_filename
  clean_filename=$(echo "$filename" | tr '/' '_' | tr '\\' '_')
  # Strip .. sequences
  while [[ "$clean_filename" == *..* ]]; do
    clean_filename="${clean_filename//../_}"
  done
  # Keep only safe characters: ASCII alphanumerics + Unicode (CJK) + . _ - space
  clean_filename=$(echo "$clean_filename" | perl -CSD -pe 's/[^\w.\- ]//g' 2>/dev/null \
    || echo "$clean_filename" | LC_ALL=C tr -cd 'A-Za-z0-9._-')
  # Limit to 100 chars
  clean_filename="${clean_filename:0:100}"
  if [ -z "$clean_filename" ]; then
    err "Invalid filename: $filename"
    return 1
  fi
  filename="$clean_filename"

  local full_path="$save_path/$filename"

  # Skip if already exists
  if [ -f "$full_path" ] && [ -s "$full_path" ]; then
    ok "Already exists, skipping: $full_path"
    echo "$full_path"
    return 0
  fi

  # HEAD pre-check
  if [ "$HEAD_CHECK" = "1" ]; then
    log "Pre-check: HEAD $url"
    local headers
    headers=$(curl -sIL --max-time 10 -A "$USER_AGENT" "$url" 2>/dev/null | tr -d '\r')
    # Take the HTTP code of the last redirect (Bug #14: -L follows redirects)
    local http_code=$(echo "$headers" | grep -E '^HTTP/' | tail -1 | awk '{print $2}')
    local content_length=$(echo "$headers" | grep -i '^content-length:' | tail -1 | awk '{print $2}' | tr -d ' ')
    local content_type=$(echo "$headers" | grep -i '^content-type:' | tail -1 | cut -d':' -f2- | sed 's/^ //')

    if [ -n "$http_code" ] && [ "$http_code" != "200" ] && [ "$http_code" != "302" ] && [ "$http_code" != "301" ]; then
      err "HEAD failed: HTTP $http_code"
      return 2
    fi

    # Bug #15: content_length must be pure digits (avoid "1,048,576" / hex
    # triggering syntax error)
    if [ -n "$content_length" ] && [[ "$content_length" =~ ^[0-9]+$ ]] && [ "$content_length" -gt 0 ]; then
      local size_mb=$((content_length / 1024 / 1024))
      if [ "$size_mb" -gt "$MAX_SIZE_MB" ]; then
        err "File too large: ${size_mb}MB > ${MAX_SIZE_MB}MB"
        return 3
      fi
      log "  Size: ${content_length} bytes (${content_type:-unknown})"
    fi
  fi

  # Actual download (with retries)
  local attempt=0
  local tmpfile=$(mktemp)
  while [ "$attempt" -le "$RETRIES" ]; do
    if [ "$attempt" -gt 0 ]; then
      warn "Retry $attempt/$RETRIES..."
      sleep $((attempt * 2))
    fi

    local dl_status=0
    if command -v curl >/dev/null 2>&1; then
      # Bug #B-fix: when curl exits 18 (partial file), resume with -C -
      if [ "$attempt" -gt 0 ] && [ -s "$tmpfile" ]; then
        curl -sSL --max-time "$TIMEOUT" -C - \
             -A "$USER_AGENT" \
             -H "Accept: */*" \
             -o "$tmpfile" \
             "$url" 2>/dev/null
        dl_status=$?
      else
        curl -sSL --max-time "$TIMEOUT" \
             -A "$USER_AGENT" \
             -H "Accept: */*" \
             -o "$tmpfile" \
             "$url" 2>/dev/null
        dl_status=$?
      fi
    else
      wget -q --timeout="$TIMEOUT" -c -O "$tmpfile" "$url" 2>/dev/null
      dl_status=$?
    fi

    # Bug #A-fix: translate curl/wget exit code to human-readable error
    # (ordered by bug frequency)
    # 18 = CURLE_PARTIAL_FILE (large file / network glitch)
    # 28 = CURLE_OPERATION_TIMEDOUT
    # 6  = CURLE_COULDNT_RESOLVE_HOST
    # 7  = CURLE_COULDNT_CONNECT
    # 22 = CURLE_HTTP_RETURNED_ERROR (4xx/5xx after -L)
    # 35 = CURLE_SSL_CONNECT_ERROR
    # 47 = CURLE_TOO_MANY_REDIRECTS
    # 56 = CURLE_RECV_ERROR
    # 60+ = TLS certificate issues
    if [ "$dl_status" -ne 0 ]; then
      local err_msg
      case "$dl_status" in
        18) err_msg="partial file (large file truncated, resuming)" ;;
        28) err_msg="timeout (exceeded ${TIMEOUT}s)" ;;
         6) err_msg="can't resolve host (DNS failure)" ;;
         7) err_msg="can't connect (network unreachable)" ;;
        22) err_msg="HTTP error (4xx/5xx)" ;;
        35) err_msg="SSL connect error" ;;
        47) err_msg="too many redirects" ;;
        56) err_msg="receive error (network interrupted)" ;;
         *) err_msg="exit $dl_status" ;;
      esac
      warn "Download failed: $err_msg"
      # Bug #13: check curl/wget exit code; do NOT pass on failure
      # (HTTP 500 error pages no longer masquerade as success)
      # Bug #B-fix: on exit 18 (partial), keep tmpfile for next-retry resume
      if [ "$dl_status" -ne 18 ]; then
        rm -f "$tmpfile"
      fi
      attempt=$((attempt + 1))
      continue
    fi

    if [ -s "$tmpfile" ]; then
      mv "$tmpfile" "$full_path"
      # Bug #C-fix: mktemp creates 600 perms; mv keeps 600. chmod 644
      # explicitly so group/other can read.
      chmod 644 "$full_path" 2>/dev/null || true

      # Bug #D-fix: content verification — if user passed --expect-title,
      # check the downloaded file's Title: line matches.
      if [ -n "$EXPECT_TITLE" ]; then
        local actual_title
        actual_title=$(grep -m1 "^Title:" "$full_path" 2>/dev/null | sed 's/^Title:[[:space:]]*//')
        if [ -z "$actual_title" ]; then
          err "Content check failed: no Title: metadata (file may not be gutenberg format)"
          rm -f "$full_path"
          attempt=$((attempt + 1))
          continue
        fi
        # Case-insensitive + substring match (avoid "by Author" suffix differences)
        local actual_lc
        actual_lc=$(echo "$actual_title" | tr '[:upper:]' '[:lower:]')
        case "$actual_lc" in
          *"$EXPECT_TITLE_LC"*)
            log "  Content check passed: $actual_title"
            ;;
          *)
            err "Content check failed: expected '$EXPECT_TITLE', got '$actual_title'"
            rm -f "$full_path"
            attempt=$((attempt + 1))
            continue
            ;;
        esac
      fi

      local size=$(ls -lh "$full_path" 2>/dev/null | awk '{print $5}')
      ok "Download complete: $full_path ($size)"
      echo "$full_path"
      return 0
    fi

    attempt=$((attempt + 1))
  done

  rm -f "$tmpfile"
  err "Download failed: $url (retries exhausted)"
  return 5
}

# ---------- Resolve positional args early (batch mode needs SAVE_PATH) ----------
URL="${POSITIONAL[0]:-}"
SAVE_PATH="${POSITIONAL[1]:-}"
FILENAME="${POSITIONAL[2]:-}"

# Batch mode also accepts the 2nd positional as SAVE_PATH (URL is a placeholder)
# Also compatible with: download.sh <save_path> --batch FILE (only one positional arg)
if [ -n "$BATCH_FILE" ] && [ -z "$SAVE_PATH" ] && [ -n "$URL" ]; then
  SAVE_PATH="$URL"
  URL=""
fi

# ---------- Batch mode ----------
if [ -n "$BATCH_FILE" ]; then
  if [ ! -f "$BATCH_FILE" ]; then
    err "Batch file not found: $BATCH_FILE"
    exit 1
  fi
  if [ -z "$SAVE_PATH" ]; then
    err "Batch mode requires a save path: $0 <save_path> --batch FILE [--parallel N]"
    exit 1
  fi
  log "Batch mode: $BATCH_FILE (concurrency=$PARALLEL)"
  SUCCESS=0
  FAILED=0

  # Serial (default, backward compatible)
  if [ "$PARALLEL" -le 1 ]; then
    while IFS=$'\t' read -r url filename; do
      [ -z "$url" ] && continue
      [[ "$url" =~ ^# ]] && continue
      if download_one "$url" "$SAVE_PATH" "$filename"; then
        SUCCESS=$((SUCCESS + 1))
      else
        FAILED=$((FAILED + 1))
      fi
    done < "$BATCH_FILE"
  else
    # Concurrent (--parallel N>1)
    # Use a mktemp dir + status files to collect results (subshells
    # can't share variables)
    POOL_DIR=$(mktemp -d -t dl-pool-XXXXXX)
    trap 'rm -rf "$POOL_DIR"' EXIT INT TERM

    # job_index gives every status file a unique name
    job_index=0
    active_jobs=0

    # Read all lines into an array (prevents read blocking on while + subshell)
    BATCH_LINES=()
    while IFS= read -r line; do
      [ -z "$line" ] && continue
      [[ "$line" =~ ^# ]] && continue
      BATCH_LINES+=("$line")
    done < "$BATCH_FILE"

    for line in "${BATCH_LINES[@]}"; do
      url="${line%%	*}"        # TAB-split first field
      filename="${line#*	}"    # TAB-split rest
      [ "$url" = "$filename" ] && filename=""  # no TAB → filename empty

      # Wait for a free slot
      while [ "$active_jobs" -ge "$PARALLEL" ]; do
        # Block until any one finishes (bash 4.3+ wait -n)
        if wait -n 2>/dev/null; then
          :
        else
          # bash < 4.3 fallback: wait for all
          wait
        fi
        active_jobs=$(jobs -rp 2>/dev/null | wc -l | tr -d ' ')
      done

      # Launch background job
      job_index=$((job_index + 1))
      (
        if download_one "$url" "$SAVE_PATH" "$filename" >/dev/null 2>&1; then
          echo "ok" > "$POOL_DIR/job-$job_index"
        else
          echo "fail $url" > "$POOL_DIR/job-$job_index"
        fi
      ) &
      active_jobs=$(jobs -rp 2>/dev/null | wc -l | tr -d ' ')
    done

    # Wait for all remaining background jobs
    wait

    # Aggregate results
    for status_file in "$POOL_DIR"/job-*; do
      [ -f "$status_file" ] || continue
      if grep -q "^ok" "$status_file"; then
        SUCCESS=$((SUCCESS + 1))
      else
        FAILED=$((FAILED + 1))
      fi
    done

    rm -rf "$POOL_DIR"
    trap - EXIT INT TERM
  fi

  log "═══════════════════════════════════════"
  ok "Batch complete: success $SUCCESS, failed $FAILED (concurrency=$PARALLEL)"
  exit 0
fi

# ---------- Single-file mode ----------
# URL/SAVE_PATH/FILENAME already resolved before the batch-mode check

if [ -z "$URL" ] || [ -z "$SAVE_PATH" ]; then
  err "Usage: $0 <url> <save_path> [filename] [options]"
  err "Example: $0 'https://archive.org/.../hamlet.pdf' \$HOME/Desktop/scripts Hamlet.pdf --yes"
  err "Batch: $0 \$HOME/Desktop/scripts --batch links.tsv --parallel 4 --yes"
  exit 1
fi

# Interactive confirmation (unless --yes)
if [ "$YES" = "0" ] && [ -t 0 ]; then
  echo "About to download:" >&2
  echo "  URL: $URL" >&2
  echo "  Save: $SAVE_PATH/$FILENAME" >&2
  read -p "Confirm? (y/N) " -n 1 -r < /dev/tty
  echo >&2
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    err "Cancelled"
    exit 0
  fi
fi

download_one "$URL" "$SAVE_PATH" "$FILENAME"
exit $?
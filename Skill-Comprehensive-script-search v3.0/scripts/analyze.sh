#!/bin/bash
# analyze.sh - find-script v3.0.0 script text extraction & 5-dim analysis (framework switches by type)
# Usage:
#   ./analyze.sh <script-file>              # extract text + emit 5-dim analysis skeleton
#   ./analyze.sh <script-file> --text-only  # extract text to stdout only
#   ./analyze.sh <script-file> --save-txt <path>  # extract and save as .txt
#   ./analyze.sh <script-file> --depth brief|standard|academic
#   ./analyze.sh <script-file> --type play|opera|film|tv
#
# Supported formats: PDF / DOCX / DOC / TXT / HTML / EPUB
# Tool detection order: pandoc > pdftotext > textutil > python-docx > plain-text fallback

set -uo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILL_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
# shellcheck source=lib/types.sh
source "$SCRIPT_DIR/lib/types.sh"

# ---------- Logging helpers ----------
warn() { echo "[WARN] $*" >&2; }

# ---------- Parameters ----------
INPUT_FILE=""
TEXT_ONLY=0
SAVE_TXT=""
DEPTH="standard"
MAX_CHARS=20000  # Cap output size to avoid blowing context
USE_OCR=0
TYPE=""

POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --text-only)     TEXT_ONLY=1; shift ;;
    --save-txt=*)    SAVE_TXT="${1#--save-txt=}"; shift ;;
    --save-txt)      SAVE_TXT="${2:-}"; shift 2 ;;
    --depth=*)       DEPTH="${1#--depth=}"; shift ;;
    --depth)         DEPTH="${2:-}"; shift 2 ;;
    --max-chars=*)   MAX_CHARS="${1#--max-chars=}"; shift ;;
    --max-chars)     MAX_CHARS="${2:-}"; shift 2 ;;
    --ocr)           USE_OCR=1; shift ;;
    --type=*)        TYPE=$(parse_type_arg "${1#--type=}") || exit 1; shift ;;
    --type)          TYPE=$(parse_type_arg "${2:-}") || exit 1; shift 2 ;;
    -h|--help)
      sed -n '2,12p' "$0"
      exit 0 ;;
    *)               POSITIONAL+=("$1"); shift ;;
  esac
done

INPUT_FILE="${POSITIONAL[0]:-}"

[ -z "$TYPE" ] && TYPE="play"

# auto mode: heuristically infer the script type from file content
# Priority: first 2KB of content > basename > default "play"
if [ "$TYPE" = "auto" ] && [ -n "$INPUT_FILE" ]; then
  # 1. Try reading the first 2KB of content for content-based heuristic
  #    (only when the file exists and is readable)
  sample=""
  if [ -f "$INPUT_FILE" ] && [ -r "$INPUT_FILE" ]; then
    sample=$(head -c 2048 "$INPUT_FILE" 2>/dev/null | tr '\n' ' ')
  fi
  detected=""
  if [ -n "$sample" ]; then
    detected=$(auto_detect_type "$sample")
  fi
  # 2. If file is unreadable or content doesn't hit a non-play type, fall back to basename
  if [ -z "$detected" ] || [ "$detected" = "play" ]; then
    basename_detected=$(auto_detect_type "$(basename "$INPUT_FILE")")
    if [ -n "$basename_detected" ] && [ "$basename_detected" != "play" ]; then
      detected="$basename_detected"
    fi
  fi
  # 3. Final fallback: default play
  [ -z "$detected" ] && detected="play"
  TYPE="$detected"
fi
[ -z "$TYPE" ] && TYPE="play"

if [ -z "$INPUT_FILE" ]; then
  echo "Usage: $0 <script-file> [--text-only] [--save-txt PATH] [--depth brief|standard|academic] [--type TYPE]" >&2
  exit 1
fi

if [ ! -f "$INPUT_FILE" ]; then
  echo "[ERROR] File not found: $INPUT_FILE" >&2
  exit 1
fi

# ---------- Tool detection ----------
has_pandoc()    { command -v pandoc >/dev/null 2>&1; }
has_pdftotext() { command -v pdftotext >/dev/null 2>&1; }
has_textutil()  { command -v textutil >/dev/null 2>&1; }
has_py_docx()   { python3 -c "import docx" 2>/dev/null; }
has_py_pdf()    { python3 -c "import pdfplumber" 2>/dev/null || python3 -c "import PyPDF2" 2>/dev/null; }
has_py_html()   { python3 -c "import bs4" 2>/dev/null; }
has_py_epub()   { python3 -c "import ebooklib" 2>/dev/null; }
has_tesseract() { command -v tesseract >/dev/null 2>&1; }

# ---------- Format detection ----------
detect_format() {
  local file="$1"
  local ext="${file##*.}"
  ext=$(echo "$ext" | tr 'A-Z' 'a-z')

  # Prefer file extension
  case "$ext" in
    pdf)  echo "pdf" ;;
    docx) echo "docx" ;;
    doc)  echo "doc" ;;
    txt|md|text) echo "txt" ;;
    html|htm) echo "html" ;;
    epub) echo "epub" ;;
    *)
      # Fall back to file magic
      local magic=$(file -b "$file" 2>/dev/null | head -c 100)
      case "$magic" in
        *PDF*) echo "pdf" ;;
        *Microsoft\ Word*|*Word\ document*) echo "docx" ;;
        *HTML*) echo "html" ;;
        *ASCII*|*UTF-8*|*text*) echo "txt" ;;
        *) echo "unknown" ;;
      esac
      ;;
  esac
}

# ---------- Text extraction ----------
extract_pdf() {
  local file="$1"
  if has_pdftotext; then
    pdftotext -layout "$file" - 2>/dev/null
  elif has_pandoc; then
    pandoc -f pdf -t plain "$file" 2>/dev/null
  elif has_py_pdf; then
    python3 -c "
import sys
try:
    import pdfplumber
    with pdfplumber.open(sys.argv[1]) as pdf:
        for page in pdf.pages:
            print(page.extract_text() or '')
except ImportError:
    import PyPDF2
    reader = PyPDF2.PdfReader(sys.argv[1])
    for page in reader.pages:
        print(page.extract_text() or '')
" "$file" 2>/dev/null
  elif [ "${USE_OCR:-0}" = "1" ] && has_tesseract; then
    # v1.4 added: OCR fallback for scanned PDFs
    warn "Using OCR for scanned PDF (may take 30-60s)..."
    # 1) pdftoppm converts PDF -> images (requires poppler)
    if command -v pdftoppm >/dev/null 2>&1; then
      local tmpdir
      tmpdir=$(mktemp -d)
      # trap guarantees tmpdir cleanup on Ctrl-C / abnormal exit
      trap 'rm -rf "$tmpdir"' RETURN INT TERM
      pdftoppm -r 200 "$file" "$tmpdir/page" -png 2>/dev/null
      for img in "$tmpdir"/page-*.png; do
        [ -f "$img" ] || continue
        tesseract "$img" - -l chi_sim+eng 2>/dev/null
      done
      rm -rf "$tmpdir"
      trap - RETURN INT TERM
    else
      echo "[ERROR: OCR requires pdftoppm] brew install poppler" >&2
      return 1
    fi
  else
    echo "[ERROR: cannot extract PDF] Install pdftotext (brew install poppler) or pandoc or pdfplumber/PyPDF2" >&2
    echo "  For scanned PDFs: pass --ocr to enable OCR (requires tesseract + poppler)" >&2
    return 1
  fi
}

extract_docx() {
  local file="$1"
  if has_pandoc; then
    pandoc -f docx -t plain "$file" 2>/dev/null
  elif has_textutil; then
    textutil -convert txt -output - "$file" 2>/dev/null
  elif has_py_docx; then
    python3 -c "
import sys
from docx import Document
doc = Document(sys.argv[1])
for p in doc.paragraphs:
    print(p.text)
" "$file" 2>/dev/null
  else
    echo "[ERROR: cannot extract DOCX] Install pandoc / textutil / python-docx" >&2
    return 1
  fi
}

extract_doc() {
  local file="$1"
  if has_textutil; then
    textutil -convert txt -output - "$file" 2>/dev/null
  elif has_pandoc; then
    pandoc -f doc -t plain "$file" 2>/dev/null
  else
    echo "[ERROR: cannot extract DOC] macOS includes textutil by default" >&2
    return 1
  fi
}

extract_html() {
  local file="$1"
  if has_pandoc; then
    pandoc -f html -t plain "$file" 2>/dev/null
  elif has_py_html; then
    # Encoding detection (Bug #10): try UTF-8 first, then GBK/Big5/GB18030
    python3 -c "
import sys
from bs4 import BeautifulSoup

file_path = sys.argv[1]
encodings = ['utf-8', 'gb18030', 'gbk', 'big5', 'latin-1']
content = None
used_enc = None
for enc in encodings:
    try:
        with open(file_path, encoding=enc) as f:
            content = f.read()
        used_enc = enc
        break
    except (UnicodeDecodeError, LookupError):
        continue

if content is None:
    # All failed: fall back to utf-8 + errors=replace (don't silently lose data)
    with open(file_path, encoding='utf-8', errors='replace') as f:
        content = f.read()
    used_enc = 'utf-8-replace'

soup = BeautifulSoup(content, 'html.parser')
for s in soup(['script', 'style']):
    s.decompose()
print(soup.get_text(separator='\n'))
" "$file" 2>/dev/null
  else
    # Fallback: strip tags with sed + convert to UTF-8 with iconv
    local iconv_enc=$(detect_text_encoding "$file")
    if [ -n "$iconv_enc" ] && command -v iconv >/dev/null 2>&1; then
      iconv -f "$iconv_enc" -t UTF-8 "$file" 2>/dev/null | sed -E 's/<[^>]+>//g; s/&nbsp;/ /g; s/&amp;/\&/g; s/&lt;/</g; s/&gt;/>/g'
    else
      sed -E 's/<[^>]+>//g; s/&nbsp;/ /g; s/&amp;/\&/g; s/&lt;/</g; s/&gt;/>/g' "$file" 2>/dev/null
    fi
  fi
}

# Text encoding detection (Bug #10/#11): returns charset from `file -i` or empty
detect_text_encoding() {
  local file="$1"
  if command -v file >/dev/null 2>&1; then
    file -i "$file" 2>/dev/null | grep -oE 'charset=[^ ]+' | cut -d'=' -f2
  fi
}

extract_epub() {
  local file="$1"
  if has_pandoc; then
    pandoc -f epub -t plain "$file" 2>/dev/null
  elif has_py_epub; then
    python3 -c "
import sys
from ebooklib import epub
book = epub.read_epub(sys.argv[1])
for item in book.get_items():
    if item.get_type() == 9:  # DOCUMENT
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(item.get_content(), 'html.parser')
        print(soup.get_text())
" "$file" 2>/dev/null
  else
    echo "[ERROR: cannot extract EPUB] Install pandoc or ebooklib" >&2
    return 1
  fi
}

extract_txt() {
  local file="$1"
  # Encoding detection (Bug #11): try cat as UTF-8 first; if invalid, iconv from GB18030
  if cat "$file" 2>/dev/null | LC_ALL=C grep -q '[^[:print:][:space:]]' && \
     ! cat "$file" 2>/dev/null | iconv -f UTF-8 -t UTF-8 >/dev/null 2>&1; then
    # Not valid UTF-8: try GB18030 (superset of GBK, compatible with GB2312/Big5)
    if command -v iconv >/dev/null 2>&1; then
      iconv -f GB18030 -t UTF-8 "$file" 2>/dev/null || cat "$file"
    else
      cat "$file"
    fi
  else
    cat "$file"
  fi
}

# ---------- Tool diagnostics (added in v1.4) ----------
# When text extraction fails, list every missing tool + install command
diagnose_missing_tools() {
  local format="$1"
  echo "" >&2
  echo "═══════════════════════════════════════════════════════" >&2
  echo "Tool diagnostics (added in v1.4)" >&2
  echo "═══════════════════════════════════════════════════════" >&2
  echo "" >&2
  echo "Target format: $format" >&2
  echo "" >&2

  # General tool detection
  echo "Tool availability:" >&2
  printf "  %-12s %s\n" "pandoc:"     "$(has_pandoc     && echo 'OK' || echo 'MISSING')" >&2
  printf "  %-12s %s\n" "pdftotext:"  "$(has_pdftotext  && echo 'OK' || echo 'MISSING')" >&2
  printf "  %-12s %s\n" "textutil:"   "$(has_textutil   && echo 'OK' || echo 'MISSING (macOS only)')" >&2
  printf "  %-12s %s\n" "python-docx:" "$(has_py_docx   && echo 'OK' || echo 'MISSING')" >&2
  printf "  %-12s %s\n" "pdfplumber:" "$(has_py_pdf     && echo 'OK' || echo 'MISSING')" >&2
  printf "  %-12s %s\n" "bs4:"        "$(has_py_html    && echo 'OK' || echo 'MISSING')" >&2
  printf "  %-12s %s\n" "ebooklib:"   "$(has_py_epub    && echo 'OK' || echo 'MISSING')" >&2
  printf "  %-12s %s\n" "tesseract:"  "$(has_tesseract  && echo 'OK' || echo 'MISSING (OCR for scanned)')" >&2
  echo "" >&2

  # Per-format install recommendations
  echo "Recommended install (for $format format):" >&2
  case "$format" in
    pdf)
      echo "  macOS:  brew install poppler           # provides pdftotext (recommended)" >&2
      echo "          or brew install pandoc         # universal converter" >&2
      echo "          or pip3 install pdfplumber     # pure Python" >&2
      echo "  Linux:  sudo apt install poppler-utils" >&2
      has_tesseract || echo "  Scanned PDFs:  brew install tesseract    # OCR (requires --ocr flag)" >&2
      ;;
    docx|doc)
      echo "  macOS:  textutil built-in (system)" >&2
      echo "          or brew install pandoc         # universal" >&2
      echo "          or pip3 install python-docx    # pure Python" >&2
      echo "  Linux:  sudo apt install pandoc" >&2
      ;;
    html)
      echo "  macOS:  brew install pandoc" >&2
      echo "          or pip3 install beautifulsoup4" >&2
      echo "  Linux:  sudo apt install pandoc python3-bs4" >&2
      ;;
    epub)
      echo "  macOS:  brew install pandoc" >&2
      echo "          or pip3 install ebooklib beautifulsoup4" >&2
      echo "  Linux:  sudo apt install pandoc" >&2
      ;;
    txt|*) echo "  No extra tools required" >&2 ;;
  esac
  echo "" >&2
  echo "See references/text-extraction.md" >&2
  echo "═══════════════════════════════════════════════════════" >&2
}

# ---------- Text stats ----------
text_stats() {
  local text="$1"
  local chars=$(echo -n "$text" | wc -m | tr -d ' ')
  local lines=$(echo "$text" | wc -l | tr -d ' ')
  local words=$(echo "$text" | wc -w | tr -d ' ')
  echo "Chars: $chars | Lines: $lines | Words: $words"
}

# ---------- Structural-unit detection (regex switches by type) ----------
# Regexes are defined centrally in scripts/lib/types.sh's section_regex()
detect_sections() {
  local text="$1" type="$2"
  local regex
  regex=$(section_regex "$type")
  [ -z "$regex" ] && return 0
  echo "$text" | grep -oE "$regex" 2>/dev/null | sort -u | head -30
}

# Backward compatibility: legacy detect_acts() still works
detect_acts() { detect_sections "$1" play; }

# ---------- Character detection (heuristic: capitalized line start or 2-4 CJK chars) ----------
detect_characters() {
  local text="$1"
  # Take "character-name candidates" from the first 5000 chars
  echo "$text" | head -c 5000 | \
    grep -oE '^\s*([A-Z][A-Z\s]{1,20}|[一-龥]{2,4})\s*[:：]' 2>/dev/null | \
    sed 's/^[[:space:]]*//; s/[[:space:]]*[:：].*//' | \
    sort | uniq -c | sort -rn | head -10
}

# ---------- Main flow ----------
FORMAT=$(detect_format "$INPUT_FILE")
echo "File: $INPUT_FILE" >&2
echo "Format: $FORMAT" >&2

case "$FORMAT" in
  pdf)  TEXT=$(extract_pdf "$INPUT_FILE") ;;
  docx) TEXT=$(extract_docx "$INPUT_FILE") ;;
  doc)  TEXT=$(extract_doc "$INPUT_FILE") ;;
  html) TEXT=$(extract_html "$INPUT_FILE") ;;
  epub) TEXT=$(extract_epub "$INPUT_FILE") ;;
  txt|*) TEXT=$(extract_txt "$INPUT_FILE") ;;
esac

# Streamed truncation for large files (Bug #12): cap during extraction to
# avoid loading huge content into a bash variable (Argument list too long)
if [ -n "$TEXT" ] && [ "${#TEXT}" -gt "$MAX_CHARS" ]; then
  TEXT="${TEXT:0:$MAX_CHARS}"
fi

if [ -z "$TEXT" ]; then
  echo "[ERROR] Text extraction failed" >&2
  diagnose_missing_tools "$FORMAT"
  exit 2
fi

# Truncate overly long text (fallback: upstream already truncates, but
# apply another cut if extract_* didn't honor the cap)
if [ -n "$TEXT" ] && [ "${#TEXT}" -gt "$MAX_CHARS" ]; then
  warn "Text exceeds $MAX_CHARS chars; truncated (only first $MAX_CHARS chars will be analyzed)"
  TEXT="${TEXT:0:$MAX_CHARS}"
fi

# Save option
if [ -n "$SAVE_TXT" ]; then
  echo "$TEXT" > "$SAVE_TXT"
  echo "Saved: $SAVE_TXT" >&2
fi

# Text-only mode
if [ "$TEXT_ONLY" = "1" ]; then
  echo "$TEXT"
  exit 0
fi

# ---------- Emit 5-dim analysis skeleton (v2.0: switch by type) ----------
TYPE_LABEL="Stage Drama"
case "$TYPE" in
  play)  TYPE_LABEL="Stage Drama" ;;
  opera) TYPE_LABEL="Chinese/Western Opera & Musical" ;;
  film)  TYPE_LABEL="Film" ;;
  tv)    TYPE_LABEL="TV Series" ;;
esac
FRAMEWORK=$(type_framework "$TYPE")

echo ""
echo "═══════════════════════════════════════════════════════"
echo "Script Analysis Skeleton ($TYPE_LABEL · 5 dims · $DEPTH)"
echo "═══════════════════════════════════════════════════════"
echo "Framework: $FRAMEWORK"
echo ""
echo "File: $INPUT_FILE"
echo "Format: $FORMAT"
text_stats "$TEXT" | sed 's/^/Stats: /'
echo ""
echo "───────────────────────────────────────────────────────"
echo "## [Theme]"
echo "- Core proposition: (summarize from text)"
echo "- Values: (positive/negative/neutral + description)"
echo "- Historical context: (specific era, social features)"
echo "- Key imagery: (recurring symbols)"
echo ""
echo "## [Characters]"
echo "$(detect_characters "$TEXT" | head -5 | sed 's/^/| /; s/[[:space:]]*$//')"
echo ""

# Dimension 3: title switches by type
case "$TYPE" in
  play)
    echo "## [Acts & Scenes]"
    echo "$(detect_sections "$TEXT" play | sed 's/^/- /')"
    echo ""
    echo "## [Conflict]"
    echo "- External conflicts: (person-person / person-society / person-fate)"
    echo "- Internal conflicts: (character psychological struggles)"
    echo "- Core contradiction: (one sentence)"
    echo "- Turning point: (which act/scene)"
    echo ""
    echo "## [Style]"
    echo "- School: (realism / romanticism / symbolism / absurdism / epic)"
    echo "- Language: (prose / poetic / dialect / monologue)"
    echo "- Structure: (traditional / innovative)"
    echo "- Aesthetic: (realism / symbolism / absurdism)"
    ;;
  opera)
    echo "## [Scenes + Vocal Modes]"
    echo "$(detect_sections "$TEXT" opera | sed 's/^/- /')"
    echo ""
    echo "## [Conflict]"
    echo "- External conflicts: (dynasty / country / loyalty-treachery / ethics)"
    echo "- Internal conflicts: (character interior / moral dilemma)"
    echo "- Core contradiction: (one sentence)"
    echo "- Turning point: (which scene / vocal mode)"
    echo ""
    echo "## [Vocal & Melodic Modes]"
    echo "- Role type: (生/旦/净/末/丑 — sheng/dan/jing/mo/chou)"
    echo "- Meter: (原板/慢板/快板/散板/摇板 — yuanban/manban/kuaiban/sanban/yaoban)"
    echo "- Melodic mode / suite: (西皮/二黄/四平调/高拨子 — xipi/erhuang/sipingdiao/gaobozi...)"
    echo "- Lyric features: (poetic / colloquial / dialect)"
    ;;
  film)
    echo "## [Scenes]"
    echo "$(detect_sections "$TEXT" film | sed 's/^/- /')"
    echo ""
    echo "## [Conflict]"
    echo "- External conflicts: (person-person / person-society / person-fate / person-technology)"
    echo "- Internal conflicts: (character psychological struggles)"
    echo "- Core contradiction: (one sentence)"
    echo "- Turning point: (which scene / shot)"
    echo ""
    echo "## [Audio-visual + Genre]"
    echo "- Camera language: (medium shot / close-up / long take / handheld / aerial)"
    echo "- Editing rhythm: (standard / fast-cut / montage / jump-cut)"
    echo "- Sound design: (voiceover / score / silence / ambient)"
    echo "- Genre tag: (western / noir / musical / sci-fi / thriller / romance / war / comedy)"
    ;;
  tv)
    echo "## [Episodes & Scenes]"
    echo "$(detect_sections "$TEXT" tv | sed 's/^/- /')"
    echo ""
    echo "## [Conflict]"
    echo "- External conflicts: (family / workplace / society / enemy / supernatural)"
    echo "- Internal conflicts: (character psychology / identity)"
    echo "- Core contradiction: (one sentence)"
    echo "- Turning point: (which episode / season finale)"
    echo ""
    echo "## [Series Structure + Genre]"
    echo "- Structure: (single-line / multi-line / serialized / episodic / miniseries)"
    echo "- Episode arc: (per-episode mini-arc + season-long arc)"
    echo "- Season structure: (seasonal / ongoing / limited)"
    echo "- Genre: (drama / comedy / crime / medical / sci-fi / fantasy / historical)"
    ;;
esac
echo ""
echo "═══════════════════════════════════════════════════════"
echo "Raw text (max $MAX_CHARS chars)"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "$TEXT"
echo ""
echo "═══════════════════════════════════════════════════════"
echo "Generated by find-script Skill analyze.sh v3.0.0 ($TYPE_LABEL · 5 dims)"
echo "Hint: this is a skeleton — combine with the text for in-depth 5-dim analysis"
echo "See references/analysis-frameworks/${TYPE}.md"
echo "═══════════════════════════════════════════════════════"
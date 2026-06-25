# Text-Extraction Toolchain

## Overview

Downloaded scripts are usually in PDF / DOCX / EPUB formats, which the Claude Read tool cannot read directly. This document explains how to extract plain text.

## Tool Priority

`analyze.sh` detects available tools in this order:

| Priority | Tool | Source | Supported formats | Install |
|----------|------|--------|-------------------|---------|
| 1 | **pandoc** | https://pandoc.org | PDF/DOCX/DOC/HTML/EPUB/RTF/MD → TXT | `brew install pandoc` |
| 2 | **pdftotext** (poppler) | https://poppler.freedesktop.org | PDF → TXT (incl. layout) | `brew install poppler` |
| 3 | **textutil** | macOS built-in | DOCX/DOC/HTML/RTF → TXT | System built-in |
| 4 | **python-docx** | pip | DOCX → TXT | `pip3 install python-docx` |
| 5 | **pdfplumber / PyPDF2** | pip | PDF → TXT | `pip3 install pdfplumber` |
| 6 | **BeautifulSoup4** | pip | HTML → TXT | `pip3 install beautifulsoup4` |
| 7 | **ebooklib** | pip | EPUB → TXT | `pip3 install ebooklib` |
| 8 | Plain-text fallback | - | TXT | None |

## Recommended Install Set

### Minimum (macOS)
```bash
# macOS ships with textutil for DOCX/DOC/HTML
# Add poppler for PDF
brew install poppler
```

### Recommended (covers all formats)
```bash
brew install pandoc poppler
pip3 install python-docx pdfplumber beautifulsoup4 ebooklib
```

### Pure-Python (no brew)
```bash
pip3 install pypandoc pdfplumber python-docx beautifulsoup4 ebooklib
# pypandoc still needs the pandoc binary
```

## Encoding Handling

Encoding issues common in Chinese scripts:

| Symptom | Cause | Fix |
|---------|-------|-----|
| `����` garbled | GBK decoded as UTF-8 | `iconv -f GBK -t UTF-8 input.txt > output.txt` |
| `ä¸­æ–‡` garbled | UTF-8 decoded as Latin-1 | `iconv -f UTF-8 -t GBK input.txt \| iconv -f GBK -t UTF-8` |
| No spaces after PDF extraction | PDF layout issue | `pdftotext -layout` or `pdftotext -raw` |

`analyze.sh`'s `extract_txt()` simply runs `cat` on the text; you can manually add encoding detection:

```bash
# Detect encoding
file -i file.txt
# Output: text/plain; charset=utf-8
```

## Long Script Handling

Very long scripts (>500k characters) need to be processed in chunks:

```bash
# Option 1: analyze.sh built-in MAX_CHARS truncation (default 20000)
./analyze.sh huge_play.pdf --max-chars 50000

# Option 2: manual chunking
./analyze.sh huge_play.pdf --save-txt /tmp/full.txt
split -l 1000 /tmp/full.txt /tmp/chunk_
for f in /tmp/chunk_*; do
  ./analyze.sh "$f" --text-only
done
```

## Validating Extraction Quality

```bash
# Check the character count (should be > 1000 to indicate success)
./analyze.sh play.pdf --text-only | wc -m

# Check that the title keyword is present
./analyze.sh play.pdf --text-only | grep -c "第.幕\|第.场\|Act [IVX]"

# Check the Chinese character ratio (Chinese scripts should be > 50%)
./analyze.sh play.pdf --text-only | python3 -c "
import sys
text = sys.stdin.read()
chinese = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
total = len(text)
print(f'Chinese characters: {chinese}/{total} = {chinese/total*100:.1f}%')
"
```

## Per-Type Extraction Notes (v2.0)

### Opera scripts (`--type opera`)

- Classical Chinese opera scripts may contain **gongche notation** (he, si, shang, chi, gong, fan, liu, wu, yi) or **numbered notation** (1–7, ⓪).
- `analyze.sh` outputs the notation **as-is**, without translation.
- Western opera / musical libretti are usually laid-out PDFs, requiring `pdftotext -layout`.
- Remind the user to recognize `[aria name]` tags (e.g. `[xipi]`, `[liushui]`, `[sipingdiao]`).

### Film scripts (`--type film`)

- PDF screenplays often contain INT./EXT. markers; `pdftotext` preserves them by default.
- After extraction, use `grep -c "^INT\." script.txt` to count scenes.
- Storyboard-style PDFs are mostly images — **plain-text extraction cannot recognize them**.

### TV scripts (`--type tv`)

- Usually contain `EPISODE N` / `SxxExx` / `COLD OPEN` markers.
- After extraction, use `grep -c "EPISODE\|S[0-9]\+E[0-9]\+" script.txt` to count episodes.
- Long scripts (40+ episodes) need to be analyzed in batches with `--max-chars`.

### 5-Dim Skeleton Tied to `--type`

`analyze.sh` now switches the **structure-detection regex** based on `--type`:

| type | Regex examples |
|------|---------------|
| play | `第N幕` / `第N场` / `Act N` / `Scene N` |
| opera | `第N场` / `第N折` / `第N出` / `\[aria name\]` |
| film | `INT\.` / `EXT\.` / `FADE IN` / `CUT TO` |
| tv | `EPISODE N` / `S\d+E\d+` / `COLD OPEN` |

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `[ERROR: cannot extract PDF]` | Missing pdftotext / pandoc / pdfplumber | `brew install poppler` |
| `[ERROR: cannot extract DOCX]` | Missing pandoc / textutil / python-docx | macOS ships textutil; Linux install pandoc |
| Empty output | PDF is a scanned image (no text layer) | Need OCR: `brew install tesseract` |
| Garbled output | Encoding issue | Use `iconv` to convert, or re-download from a different source. |
| `command not found: python3` | No Python | `brew install python@3.11` |

## Quick Environment Check

```bash
#!/bin/bash
# Validate the environment
echo "=== find-script v3.0.0 text-extraction environment check ==="
for cmd in pandoc pdftotext textutil python3 pip3; do
  if command -v $cmd >/dev/null 2>&1; then
    echo "  ✓ $cmd: $(command -v $cmd)"
  else
    echo "  ✗ $cmd: not found"
  fi
done
echo ""
echo "Python packages:"
for pkg in docx pdfplumber PyPDF2 bs4 ebooklib; do
  if python3 -c "import $pkg" 2>/dev/null; then
    echo "  ✓ $pkg"
  else
    echo "  · $pkg (not installed, optional)"
  fi
done
```

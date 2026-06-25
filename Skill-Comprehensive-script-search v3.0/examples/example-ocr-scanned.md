# find-script v3.0.0 — Advanced Example: OCR for Scanned PDFs

> find-script v2.0+ adds the `--ocr` flag, designed for scanned PDFs.

## Scenario

You downloaded a PDF, but `analyze.sh` returns empty text because it's a **scanned PDF** (image PDF with no text layer). Common causes:
- Photocopied editions of old scripts.
- National Library scans.
- Some doc88 resources that are scans of paper.

## Solution: OCR

### 1. Install the OCR tools

```bash
# macOS
brew install tesseract          # OCR engine
brew install tesseract-lang     # Chinese language pack (required)
brew install poppler            # provides pdftoppm (PDF → image)

# Linux
sudo apt install tesseract-ocr tesseract-ocr-chi-sim poppler-utils
```

### 2. Verify the install

```bash
tesseract --version
# Should output tesseract x.xx

tesseract --list-langs
# Should include chi_sim (Simplified Chinese) and eng (English)

pdftoppm -v
# Should output a version number
```

### 3. Use the --ocr flag

```bash
# Basic usage
./scripts/analyze.sh scanned-play.pdf --ocr

# Save the extracted text
./scripts/analyze.sh scanned-play.pdf --ocr --save-txt extracted.txt

# Text only (no skeleton)
./scripts/analyze.sh scanned-play.pdf --ocr --text-only > extracted.txt
```

### 4. Workflow

```
1. pdftoppm: PDF → multiple PNGs (200 DPI)
2. tesseract: PNG → text (chi_sim + eng bilingual)
3. Concatenate all pages → full script
```

## Performance Reference

| Pages | 200 DPI OCR time | 300 DPI OCR time |
|-------|------------------|------------------|
| 10 pages | 10–20 s | 20–40 s |
| 50 pages | 1–2 min | 2–4 min |
| 100 pages | 2–4 min | 4–8 min |
| 200 pages | 5–8 min | 8–15 min |

## OCR Quality Tuning

### Improve accuracy

```bash
# 1) Use a higher DPI (300 is the default; you can set 400)
# Edit near line 123 of analyze.sh:
pdftoppm -r 300 "$file" "$tmpdir/page" -png

# 2) Specify the language (default chi_sim+eng)
tesseract "$img" - -l chi_sim+eng

# 3) Image preprocessing (denoising / binarization)
# Recommended tool: ImageMagick
convert "$img" -threshold 50% "$img.processed"
tesseract "$img.processed" - -l chi_sim+eng
```

### Handle special layouts

```bash
# Vertical Chinese (half-width → full-width)
tesseract "$img" - -l chi_sim_vert

# Traditional Chinese
tesseract "$img" - -l chi_tra
```

## Diagnostic: Missing Tool

If you use `--ocr` but a tool is missing, `analyze.sh` prints diagnostics (added in v1.4):

```
═══════════════════════════════════════════════════════
🔧 Tool diagnostics (added in v1.4)
═══════════════════════════════════════════════════════

Target format: pdf

📋 Tool availability:
  pandoc:      ❌
  pdftotext:   ❌
  textutil:    ✅ (macOS only)
  python-docx: ❌
  pdfplumber:  ❌
  bs4:         ❌
  ebooklib:    ❌
  tesseract:   ❌ (OCR for scanned PDFs)

💡 Recommended install (per pdf format):
  macOS:  brew install poppler           # provides pdftotext (recommended)
          or brew install pandoc         # universal converter
          or pip3 install pdfplumber     # pure Python
  Linux:  sudo apt install poppler-utils
  Scanned PDF:  brew install tesseract  # OCR (requires --ocr flag)

📚 See references/text-extraction.md
═══════════════════════════════════════════════════════
```

## Full Workflow: Scanned PDF → Text → Analysis

```bash
#!/bin/bash
# ocr-workflow.sh
PLAY="$1"
SCANNED_PDF="$2"
TXT_OUT="${SCANNED_PDF%.pdf}.txt"
ANALYSIS_OUT="${SCANNED_PDF%.pdf}-analysis.md"

if [ ! -f "$SCANNED_PDF" ]; then
  echo "❌ File not found: $SCANNED_PDF"
  exit 1
fi

# 1) OCR extraction
echo "🔍 OCR extraction..."
./scripts/analyze.sh "$SCANNED_PDF" --ocr --text-only > "$TXT_OUT"

# 2) 5-dim analysis
echo "📊 5-dim analysis..."
./scripts/analyze.sh "$SCANNED_PDF" --ocr > "$ANALYSIS_OUT"

echo "✅ Done:"
echo "  Text: $TXT_OUT"
echo "  Analysis: $ANALYSIS_OUT"
```

## Notes

⚠️ **1. Memory**: large PDF OCR needs 1–2 GB of RAM.
⚠️ **2. Speed**: OCR is 5–10× slower than text extraction.
⚠️ **3. Accuracy**: poor scan quality reduces accuracy.
⚠️ **4. Language**: must install the matching language pack (Chinese requires chi_sim).
⚠️ **5. Copyright**: scanned PDFs are still subject to copyright; user authorization is required.

## Alternatives

If OCR is too slow or inaccurate:

| Alternative | Use case | Tool |
|-------------|----------|------|
| Online OCR | Small files | Google Drive, Adobe |
| Adobe Acrobat | Commercial | Professional grade |
| ABBYY FineReader | Commercial | Offline precision |
| Re-find source | Public-domain works | archive.org first |

## Further Reading

- `references/text-extraction.md` — text-extraction toolchain reference.
- `references/troubleshooting.md` — troubleshooting.

# Script Finder v3.0.0 — Frequently Asked Questions (FAQ)

> New in v2.1 is tagged **[v2.1]**; v2.0 content is tagged **[v2.0]**; v1.x questions are kept as-is.

## Install and Configuration

### Q1: What do I need to install?
A: Only `bash` and `curl` are required (both ship with macOS). Strongly recommended:
- `brew install poppler` (pdftotext, for PDF)
- or `brew install pandoc` (universal converter)

See `references/text-extraction.md`.

### Q2: Do I need Python?
A: Not required. But installing `python-docx` / `pdfplumber` / `beautifulsoup4` / `ebooklib` lets you handle more formats (DOCX/PDF/EPUB). `analyze.sh` auto-detects whichever tools are available.

### Q3: Does it work on Windows?
A: The scripts are written in bash. On Windows you need:
- WSL 2 (recommended)
- or Git Bash
- Native PowerShell is not supported

## Search

### Q4: Empty search results?
A: Three-step troubleshooting:
1. Simplify the title (drop modifiers like "full version" or "script").
2. Add the author: `./scripts/search.sh "Hamlet Shakespeare" en`.
3. Switch the language: if Chinese fails, try `en` (English translation).

### Q5: Of the 16 engines in search.sh, which is the best?
A: Per the reliability score:
- Score 5: archive.org / gutenberg.org (public domain, stable).
- Score 4: openlibrary / ocw.mit.edu (academic).
- Score 3: doc88 / taodocs (modern Chinese titles).
- Score 1: wenku.baidu.com (mostly paid).

### Q6: Google returns nothing?
A: Google is often blocked in mainland China. Try:
- Switch to `zh` mode (Chinese engines).
- Or use Google HK: `./scripts/search.sh "Hamlet" en --no-fetch | grep google_hk`.
- Or configure a proxy.

## Download

### Q7: download.sh hangs in Claude Code?
A: You must pass `--yes` or set the env var:
```bash
./scripts/download.sh URL PATH FILE --yes
# or
FIND_PLAY_YES=1 ./scripts/download.sh URL PATH FILE
```

### Q8: Can't download from Baidu Wenku?
A: Baidu Wenku mostly requires VIP. **The find-script strategy is**:
- Prefer archive.org / gutenberg.org.
- Then doc88 / taodocs (modern Chinese titles).
- Only try Baidu Wenku last.

### Q9: Downloaded file is HTML instead of PDF?
A: The URL is probably a search-results page, not a direct link. To find the real PDF:
```bash
./scripts/search.sh "Hamlet" en --no-fetch --json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for d in data:
    if d['format'] == 'pdf' and d['reliability'] >= 3:
        print(d['url'])
"
```

## Text Extraction

### Q10: PDF extraction returns empty?
A: Three possibilities:
1. **Tool missing**: `brew install poppler`.
2. **PDF is a scanned image** (no text layer): requires OCR (`brew install tesseract`).
3. **PDF is encrypted**: switch source.

### Q11: DOCX extraction shows garbled characters?
A: Encoding issue. `analyze.sh` auto-tries:
- pandoc
- textutil (macOS)
- python-docx

If all fail, switch source file.

### Q12: How do I cap the extracted character count?
A: Use `--max-chars`:
```bash
./scripts/analyze.sh play.pdf --max-chars 50000
```

## 5-Dim Analysis

### Q13: Auto-detected "characters" and "acts" are wrong?
A: It's heuristic detection. `analyze.sh` uses regex matches:
- Characters: `leading-capital + colon` or `Chinese two-char name + colon`.
- Acts: `第N幕`, `第N场`, `Act N`.

Non-standard formats won't be detected; you'll need to analyze manually.

**[v2.0]** Each script type uses different regexes: opera (scene + arias), film (INT./EXT.), TV (EPISODE/SxxExx). See `references/text-extraction.md`.

### Q14: The 5-dim skeleton feels shallow?
A: That's by design: `analyze.sh` outputs a **skeleton + full text**, and the LLM is responsible for the deep interpretation. The full text is shown after the skeleton so the LLM can do the deep analysis.

**[v2.0]** Each script type uses a different skeleton: stage play=acts+style, opera=scenes+aria+vocal, film=scenes+audiovisual+genre, TV=episodes+series_structure+genre. See `references/analysis-frameworks/`.

## Performance and Limits

### Q15: How long does a search take?
A:
- `--no-fetch` mode: < 1 second
- Real fetch (16 engines in parallel): 5–15 seconds
- End-to-end `find-play.sh`: 15–60 seconds

### Q16: How big can a single file be?
A: Default 50 MB. Configurable:
```bash
./scripts/download.sh URL PATH FILE --max-size 100
```

### Q17: Can I batch download?
A: Yes:
```bash
# Prepare a TSV: URL\tfilename
cat > batch.tsv <<EOF
https://archive.org/.../hamlet.pdf	hamlet.pdf
https://gutenberg.org/.../macbeth.txt	macbeth.txt
EOF
./scripts/download.sh --batch batch.tsv --yes
```

## Errors and Troubleshooting

### Q18: Exit-code reference
| Code | Meaning |
|------|---------|
| 0 | success |
| 1 | argument error |
| 2 | network error |
| 3 | file too large |
| 4 | path not writable |
| 5 | retries exhausted |

### Q19: How do I debug?
A: Use bash trace:
```bash
bash -x ./scripts/search.sh "test" en --no-fetch 2>&1 | head -50
```

### Q20: Where's the full troubleshooting guide?
A: See `references/troubleshooting.md`.

## Advanced

### Q21: Can I customize the scoring rules?
A: Yes. Edit the `get_reliability()` function in `scripts/search.sh`.

### Q22: Can I add new engines?
A: Yes. Add a new line in `build_engines()` inside `scripts/search.sh`, and update `config.json` at the same time.

### Q23: Can I switch the language?
A: The engine dispatch has Chinese + English built in. Specify manually:
```bash
./scripts/search.sh "Hamlet" en   # English first
./scripts/search.sh "雷雨" zh     # Chinese first
```

## Contributing

### Q24: How do I contribute?
A: find-script is MIT-licensed. Suggested directions:
- New search-engine support
- More languages (Chinese / English / Japanese / French)
- Additional text-extraction tool fallbacks
- Test coverage
- **[v2.0]** New script-type support (e.g. radio drama)
- **[v2.0]** Finer-grained copyright rules

### Q25: Where are the tests?
A: The `tests/` directory. **[v2.1.1]** has 289 tests in total (203 in v2.0, +42 in v2.1 including 11 security regressions; +44 in v2.1.1 including 32 UX + 11 concurrent + 35 multilingual type aliases):
- `test_smoke.sh` (30)
- `test_engines.sh` (31)
- `test_download.sh` (8)
- **[v2.0]** `test_types.sh` (64: type aliases / keywords / detection)
- **[v2.0]** `test_copyright.sh` (23: copyright inference / .pdf mis-tag fix)
- **[v2.0]** `test_framework.sh` (30: 5-dim skeleton / 4 types)
- **[v2.0]** `test_search_output.sh` (14: 6-col output / equals syntax)
- **[v2.1 new]** `test_security.sh` (11: path traversal / system dirs / encoding / trap / curl exit code)
- **[v2.1.1 new]** `test_ux.sh` (32: full --help / blank-keyword early exit / portable_timeout)
- **[v2.1.1 new]** `test_download_parallel.sh` (11: --parallel 1-16)
- `../search-engine/tests/test_smoke.sh` (35 submodule)

Run them all:
```bash
cd /path/to/find-script
bash tests/test_smoke.sh && bash tests/test_engines.sh && SKIP_NETWORK=1 bash tests/test_download.sh && \
  bash tests/test_types.sh && bash tests/test_copyright.sh && \
  bash tests/test_framework.sh && bash tests/test_search_output.sh && \
  bash tests/test_security.sh && bash tests/test_ux.sh && \
  bash tests/test_download_parallel.sh && \
  bash search-engine/tests/test_smoke.sh
```

---

## [Added in v2.0] Script Types and Copyright

### Q26: How do find-stage-play and find-script relate?
A: **find-script v2.0 is the upgrade of find-stage-play v1.4.** All v1.4 functionality is preserved and backward compatible:
- Default `--type=play` (old scripts work with zero changes).
- Old 5-column TSV output still works (the 6th copyright column is additive).
- Old 103 tests all pass.

### Q27: How do I find film / opera / TV scripts?
A: Add `--type`:
```bash
./scripts/find-play.sh "Citizen Kane" --type film --yes
./scripts/find-play.sh "牡丹亭" --type opera --yes
./scripts/find-play.sh "I Love Lucy" --type tv --yes
# Or use auto for heuristic detection
./scripts/find-play.sh "Hamlet S01E01" --type auto --yes
```

### Q28: How do I read the copyright tags?
A: Since v2.0, every result ends with a `copyright` column:

| Tag | Meaning | Behavior |
|-----|---------|----------|
| `pd` | Public domain | Safe to download by default. |
| `user_uploaded` | User upload | Verify the uploader's authorization. |
| `copyrighted` | Still under copyright | For study and quotation only. |
| `unknown` | Cannot be auto-detected | Verify manually. |

### Q29: Why does the top banner warn for opera / film / TV?
A: The tool shows a default recommendation per type:
- `play` — no warning by default (mostly classical).
- `opera` — warns about modern opera / musical copyright.
- `film` — warns about modern film copyright.
- `tv` — warns about modern TV copyright.

The warning **does not block the search**; it just reminds you to verify the rights yourself.

### Q30: How do I bulk-download only `pd` resources?
A: Use `--filter-copyright`:
```bash
./scripts/find-play.sh "Hamlet" --filter-copyright pd,user_uploaded --auto-download 3 --yes
# Or filter from JSON after searching
./scripts/search.sh "Hamlet" en --type play --json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for d in data:
    if d['copyright'] in ('pd', 'user_uploaded'):
        print(d['url'])
"
```

### Q31: `--type` reports `unknown`. How do I fix it?
A: Check the spelling. Supported aliases (30+):

```bash
# View all
grep "^\s*[a-z_]*=)" scripts/lib/types.sh | head -30

# Common
# play:    play, drama, theater, theatre, stage-play, radio-drama
# opera:   opera, xiqu, musical, kabuki, noh, kathakali, broadway
# film:    film, movie, cinema, screenplay, bollywood
# tv:      tv, television, series, episode, kdrama, kdrama-historical

# Or let the script auto-detect
```

---

## [Added in v3.0.0] GitHub Edition

### Q32: How do I install from GitHub?
A: After cloning, all the standard bash scripts work without further installation:
```bash
git clone https://github.com/<owner>/find-script.git
cd find-script
./scripts/find-play.sh "Hamlet" --type play --yes
```

### Q33: Does the skill still depend on the search-engine submodule?
A: Yes. The submodule has been renamed from `搜索引擎/` to `search-engine/` and is still pinned to multi-search-engine v2.2.0. If the submodule is missing, `search.sh` automatically falls back to the built-in 16-engine config.

### Q34: Where do I report security issues?
A: See `SECURITY.md` for the responsible-disclosure policy.

### Q35: How do I cite this skill in academic work?
A: See `CITATION.cff` for the canonical citation metadata.

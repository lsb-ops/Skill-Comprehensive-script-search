# Troubleshooting

> find-script v3.0.0 · extends the v1.4.0 error-code scheme; adds type-related errors.

## Common Errors

### E1: Search returns 0 results

**Symptom**: `search.sh` outputs "no results" or an empty file.

**Possible causes**:
1. Title misspelling (especially mixed Chinese/English).
2. URL-encoding failure (Chinese titles).
3. The search engine is temporarily unavailable.
4. **`--type` mismatches the work** (added in v2.0): e.g. looking for a film with `--type=play` makes the keyword become "script".

**Investigation**:
```bash
# 1. Verify URL generation
./scripts/search.sh "雷雨" zh --no-fetch --quiet | head -5

# 2. Verify URL encoding
./scripts/search.sh "雷雨" zh --no-fetch --quiet | head -2 | grep "%E9"
# You should see %E9%B9%B9 etc. — the Chinese encoding

# 3. Single-engine test
curl -I "https://www.baidu.com/s?wd=%E9%9B%B7%E9%9B%A8"
# Should return 200

# 4. Added in v2.0: verify the type-keyword injection
./scripts/search.sh "Citizen Kane" en --type film --no-fetch --quiet | head -2
# You should see URLs containing "screenplay" or "shooting+script", not "剧本"
```

**Fix**:
- Simplify the title (drop modifiers like "complete version" or "full text").
- Add the author: `./scripts/search.sh "雷雨 曹禺" zh --no-fetch`.
- Switch language: `./scripts/search.sh "雷雨" en --no-fetch` to find an English translation.
- **Check that `--type` matches the work**: use `--type film` for films, `--type opera` for Chinese opera, etc.

---

### E1.5 (v2.0): `--type` reports `unknown`

**Symptom**: the script prints `Unknown type: xxx`.

**Possible causes**:
1. Typo (e.g. `playe`, `films`).
2. Used an unsupported alias.

**Fix**:
```bash
# View supported aliases
grep "^\s*[a-z_]*=)" scripts/lib/types.sh

# Common aliases
# play:    play, drama, theater, theatre, stage-play, radio-drama
# opera:   opera, xiqu, musical, kabuki, noh, kathakali, broadway
# film:    film, movie, cinema, screenplay, bollywood
# tv:      tv, television, series, episode, kdrama, korean-historical-drama

# Let the script auto-detect
./scripts/find-play.sh "Hamlet" --type auto --yes
```

---

### E2: Download fails / hangs

**Symptom**: `download.sh` does not respond or times out.

**Possible causes**:
1. URL unreachable (404/403/network blocked).
2. File too large.
3. Interactive confirmation prompt blocks in non-TTY environments.

**Investigation**:
```bash
# 1. Check the URL is reachable
curl -I "https://example.com/play.pdf"

# 2. Check the file size
curl -sI "https://example.com/play.pdf" | grep -i content-length

# 3. Force non-interactive mode
./scripts/download.sh URL PATH FILE --yes
# or
FIND_PLAY_YES=1 ./scripts/download.sh URL PATH FILE
```

**Fix**:
- Use `--max-size 100` to raise the cap.
- Use `--no-head-check` to skip the pre-check.
- Use `--retries 3` to add retries.

---

### E3: PDF extraction returns empty

**Symptom**: `analyze.sh` prints `[ERROR: cannot extract PDF]` or the text is empty.

**Possible causes**:
1. Missing tool (`pdftotext` / `pandoc` / `pdfplumber`).
2. PDF is a scanned image with no text layer.
3. PDF is encrypted.

**Investigation**:
```bash
# 1. Verify the tool is installed
command -v pdftotext || command -v pandoc || command -v python3

# 2. Manual test
pdftotext -layout play.pdf - | head -20

# 3. Check whether the PDF is encrypted
pdfinfo play.pdf | grep -i encrypted
```

**Fix**:
- macOS: `brew install poppler` to install pdftotext.
- Scanned PDFs: use OCR (tesseract).
- Encrypted: the user must supply the password, or switch source.

---

### E4: DOCX extraction shows garbled characters

**Symptom**: Chinese characters in the DOCX extraction appear as `?????` or as garbled output.

**Possible causes**:
1. Encoding issue (GBK vs UTF-8).
2. Embedded fonts in the DOCX are corrupt.

**Investigation**:
```bash
# 1. Check the encoding
file -i play.docx
# Expected: charset=utf-8

# 2. Try with pandoc
pandoc -f docx -t plain play.docx | head -20

# 3. Try with textutil (macOS)
textutil -convert txt -output - play.docx | head -20
```

**Fix**:
- Try a different tool: `analyze.sh` automatically picks a fallback.
- Re-download the source (e.g. use doc88 instead of Baidu Wenku).

---

### E5: 5-dim analysis skeleton is inaccurate

**Symptom**: `analyze.sh` auto-detects the wrong "characters" or "acts".

**Possible causes**:
1. Non-standard format (e.g. "幕一" instead of "第一幕").
2. Text was truncated (MAX_CHARS default 20000).
3. **Added in v2.0: `--type` mismatch** — opera being matched against the stage-play skeleton, or film being matched against stage-play "acts".

**Fix**:
```bash
# 1. Widen the text range
./analyze.sh play.pdf --max-chars 100000

# 2. Specify depth manually
./analyze.sh play.pdf --depth academic

# 3. Extract the full text
./analyze.sh play.pdf --save-txt /tmp/full.txt
# Then analyze /tmp/full.txt manually

# 4. Added in v2.0: be explicit about --type
./analyze.sh opera.pdf --type opera   # opera: scenes + arias skeleton
./analyze.sh film.pdf --type film    # film: scenes + audiovisual + genre skeleton
./analyze.sh tv.pdf --type tv        # TV: episodes + series-structure skeleton
```

---

### E6: Interactive confirm hangs

**Symptom**: the script hangs on `read -p "Confirm? ..."`.

**Cause**: in Claude Code, stdin is not a TTY.

**Fix**:
```bash
# Always pass --yes
./find-play.sh "Hamlet" --save-path /tmp --auto-download 3 --yes

# Or set a global environment variable
export FIND_PLAY_YES=1
```

---

## Performance Tuning

### P1: Slow search

If `search.sh` is slow on real fetches:

```bash
# 1. Reduce the timeout (default 15s)
# Edit --max-time 15 in do_search() inside search.sh

# 2. Cap concurrency (to avoid anti-bot triggers)
# Currently runs in parallel via &; switch to serial if needed:
# Remove the & from `do_search ... &`
```

### P2: High memory use

`analyze.sh` loads the full text into a variable. Very large scripts (>10 MB) may blow up memory:

```bash
# Use streaming instead
pdftotext -layout huge.pdf - | head -c 100000 | ./analyze.sh --text-only -
```

Or use `--save-txt` first, then `split` to chunk.

### P3: Restricted network

If you cannot reach Google / Bing:

```bash
# Force Chinese engines only
./scripts/search.sh "雷雨" zh --max-results 30 2>/dev/null
# zh mode defaults to 7 Chinese + 9 international; after international failures only Chinese remain
```

## Debugging Tips

### Verbose logs

```bash
# bash trace
bash -x ./scripts/search.sh "test" zh --no-fetch 2>&1 | head -50

# Exit code
./scripts/search.sh ... ; echo "exit: $?"

# Memory / CPU
/usr/bin/time -v ./scripts/search.sh "Hamlet" en --max-results 20 2>&1 | tail -20
```

### Isolate the problem

```bash
# Single step
./scripts/search.sh "Hamlet" en --no-fetch  # URL only
curl URL                                   # test the download alone
./scripts/analyze.sh downloaded.pdf        # test analysis alone
```

### Inspect temp files

```bash
# Temp dir (search.sh uses mktemp -d)
# During debugging, comment out the trap "rm -rf" to keep intermediate files
```

## Information to Include in an Issue

1. OS and shell version: `uname -a; bash --version`.
2. Full command output (including reverse output that `--quiet` would have suppressed).
3. Network environment (can you reach Google / archive.org?).
4. Tool check results: `./tests/test_smoke.sh`.
5. **Added in v2.0**: `--type` value and version (`./scripts/search.sh --version`).

## v3.0.0 Test Run

```bash
# Full test suite (v3.0.0: 289/289)
cd find-script
bash tests/test_smoke.sh
bash tests/test_engines.sh
SKIP_NETWORK=1 bash tests/test_download.sh
bash tests/test_types.sh
bash tests/test_copyright.sh
bash tests/test_framework.sh
bash tests/test_search_output.sh
bash tests/test_security.sh
bash tests/test_ux.sh
bash tests/test_download_parallel.sh
(cd search-engine && bash tests/test_smoke.sh)
bash scripts/benchmark.sh --no-network --quick
```

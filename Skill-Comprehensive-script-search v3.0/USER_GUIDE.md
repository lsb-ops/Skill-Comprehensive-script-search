# Script Finder v3.0.0 — User Guide

## Overview

Script Finder is a **general-purpose script search, download, and analysis tool**. **Since v2.0 it supports 4 script types**: stage play / Chinese opera, Western opera, musical / film / television. Each type has its own keywords, 5-dim skeleton, and source recommendations, and every result is tagged with a copyright status.

It inherits everything from find-stage-play v1.4: 16 search engines, 5 scripts + 1 lib, 8 reference docs (including 4 per-type 5-dim frameworks), **289 tests** (v2.1's 11 security regressions + v2.1.1's 32 UX + 11 concurrency + 35 multilingual type-alias tests), and OCR support for scanned PDFs.

## v2.0 vs v1.4 in one sentence

**`--type` argument + copyright tags + 4 type-tailored 5-dim skeletons.** Everything else is fully backward compatible.

---

## Complete Workflow (by Type)

### Stage play (default / `--type play`)

```bash
./scripts/find-play.sh "雷雨" --save-path ~/Desktop/caoyu --auto-download 3 --analyze --yes
./scripts/find-play.sh "Hamlet" --language en --save-path ~/Desktop/scripts --auto-download 1 --analyze --yes
```

### Opera (`--type opera`)

```bash
# Classical Chinese opera (public domain)
./scripts/find-play.sh "牡丹亭" --type opera --save-path ~/Desktop/opera --auto-download 3 --analyze --yes

# Western opera
./scripts/find-play.sh "Carmen" --type opera --language en --save-path ~/Desktop/opera --yes

# Musical
./scripts/find-play.sh "Hamilton" --type opera --language en --save-path ~/Desktop/musicals --yes
```

### Film (`--type film`)

```bash
# Early public-domain silent film (archive.org is strongly recommended)
./scripts/find-play.sh "Citizen Kane" --type film --language en --save-path ~/Desktop/movies --yes

# Chaplin
./scripts/find-play.sh "City Lights" --type film --save-path ~/Desktop/chaplin --yes
```

### Television (`--type tv`)

```bash
# Early public-domain show
./scripts/find-play.sh "I Love Lucy" --type tv --language en --save-path ~/Desktop/tv --yes

# Modern show (only user_uploaded sources; verify authorization)
./scripts/find-play.sh "Nirvana in Fire" --type tv --save-path ~/Desktop/tv --yes
```

---

## Complete Workflow (by Mode)

### Mode A: One-shot end-to-end (recommended)

```bash
./scripts/find-play.sh "Hamlet" --type play --save-path ~/Desktop/scripts \
  --auto-download 3 --analyze --yes
```

Argument reference:
- `--type TYPE` — script type (`play` / `opera` / `film` / `tv` / `auto`), default `play`.
- `--save-path` — required, the directory to save downloads to.
- `--auto-download N` — auto-download the top N results (0 = search only).
- `--analyze` — run the 5-dim analysis after download.
- `--yes` — skip all confirmation prompts (required in non-TTY environments).
- `--filter-copyright TAG,...` — only download results with the given copyright tags (e.g. `pd,user_uploaded`).

### Mode B: Step-by-step

```bash
# Step 1: search (type-specific keyword injection + 6-column TSV)
./scripts/search.sh "Hamlet Shakespeare" en --type play --quiet
# engine  url  format  reliability  title  copyright
# baidu   https://...  pdf   0  baidu-search  unknown
# archive.org ...  pdf   5  Hamlet  pd
# doc88.com ...  pdf   3  Hamlet  user_uploaded

# Step 2: download (note the copyright column)
./scripts/download.sh "https://archive.org/.../hamlet.pdf" \
  ~/Desktop/scripts hamlet.pdf --yes

# Step 3: analyze (type-specific 5-dim skeleton)
./scripts/analyze.sh ~/Desktop/scripts/hamlet.pdf --type play
./scripts/analyze.sh ~/Desktop/opera/carmen.txt --type opera
./scripts/analyze.sh ~/Desktop/movies/citizen-kane.pdf --type film
./scripts/analyze.sh ~/Desktop/tv/love-lucy-s01e01.pdf --type tv
```

---

## Engine Dispatch Strategy

| Language | Priority engines | Fallback engines |
|----------|------------------|------------------|
| Chinese (`zh`) | 7 Chinese (Baidu / Bing / 360 / Sogou / WeChat / Shenma) | 9 international |
| English (`en`) | 9 international (Google / DuckDuckGo / Yahoo / Startpage / Brave / Ecosia / Qwant / Wolfram) | 7 Chinese |
| Auto (`auto`) | inferred from whether the title contains Chinese characters | — |

## Per-Type Keyword Injection

| type | Chinese keyword | English keyword |
|------|-----------------|-----------------|
| `play` (stage play) | `剧本` | `script` |
| `opera` (Chinese opera / Western opera / musical) | `戏本,曲谱` | `libretto` |
| `film` (movie) | `电影剧本,分镜` | `screenplay` |
| `tv` (television) | `电视剧本,分集` | `teleplay` |

## Search Query Templates

**Chinese templates** (per type):
```bash
# Stage play
"{play}" 剧本 下载 filetype:pdf
"{play}" site:doc88.com
"{play}" 曹禺 完整版

# Opera
"{play}" 戏本 filetype:pdf
"{play}" site:ctext.org
"{play}" 曲谱

# Film
"{play}" 电影剧本 filetype:pdf
"{play}" 分镜

# Television
"{play}" 电视剧本 filetype:pdf
"{play}" 分集
```

**English templates**:
```bash
# Stage play
"{play}" full text filetype:pdf
"{play}" site:archive.org
"{play}" Shakespeare site:gutenberg.org

# Opera
"{opera}" libretto site:imslp.org

# Film
"{film}" screenplay site:imsdb.com

# Television
"{series}" teleplay site:archive.org
```

## Link Filtering (Reliability Scoring)

| Score | Domains (per type) | Priority |
|-------|--------------------|----------|
| 5 | archive.org, gutenberg.org (play), ctext.org / imslp.org (opera) | Strongly recommended (public domain) |
| 4 | openlibrary.org, scholar.google.com (play), imsdb.com (film) | Academic / modern study |
| 3 | doc88.com, taodocs.com, max.book118.com | Modern Chinese titles |
| 2 | renrendoc.com, book.douban.com | General |
| 1 | wenku.baidu.com | Mostly paid; last resort |

## Download Configuration

```bash
# Basic download
./scripts/download.sh URL SAVE_PATH FILENAME --yes

# Advanced options
./scripts/download.sh URL SAVE_PATH FILENAME \
  --max-size 100 \        # 100 MB size cap
  --timeout 120 \         # 120 s timeout
  --retries 3 \           # retry 3 times
  --user-agent "MyAgent"  # custom User-Agent

# Batch download
cat downloads.tsv | ./scripts/download.sh --batch - --yes
# downloads.tsv format: URL\tfilename, one per line

# Environment variables
FIND_PLAY_YES=1 ./scripts/download.sh URL PATH FILE
FIND_PLAY_QUIET=1 ./scripts/download.sh URL PATH FILE
```

## 5-Dim Analysis (per Type)

`analyze.sh` switches the skeleton by `--type`:

**Stage play** (`--type play`):
```
🎭 Script Analysis Skeleton (Stage Play · 5-dim · standard)
═══════════════════════════════
📁 File: /path/to/play.pdf
📋 Format: pdf
📊 Characters: 73000 | Lines: 1200 | Words: 9500

[Theme]      ← LLM fills
[Characters] ← auto-detected: Zhou Puyuan, Fan Yi, ...
[Acts/Scenes] ← auto-detected: Act I, Act II, ...
[Conflict]   ← LLM fills
[Style]      ← LLM fills (school: realism / romanticism / symbolism / absurdism / epic, ...)

═══════════════════════════════
📝 Raw text (up to 20000 chars)
```

**Opera** (`--type opera`):
```
🎭 Script Analysis Skeleton (Opera / Musical · 5-dim)
[Theme]
[Characters]    ← role type: sheng / dan / jing / mo / chou
[Scenes + Arias] ← auto-detected: Scene N, [xipi liushui], ...
[Conflict]
[Vocal Styles]  ← xipi / erhuang / manban / kuaiban / sanban, ...
```

**Film** (`--type film`):
```
🎭 Script Analysis Skeleton (Film · 5-dim)
[Theme]
[Characters]
[Scenes]        ← auto-detected INT./EXT. markers
[Conflict]
[Audiovisual + Genre]  ← camera / editing / sound + genre (western / noir / musical / sci-fi, ...)
```

**Television** (`--type tv`):
```
🎭 Script Analysis Skeleton (Television · 5-dim)
[Theme]
[Characters]
[Episodes]      ← auto-detected EPISODE N / SxxExx
[Conflict]
[Series Structure + Genre]  ← single-episode / multi-arc / serial / anthology / mini-series + genre (drama / comedy / crime, ...)
```

The LLM receives the skeleton plus the raw text and fills in [Theme], [Conflict], and [Style].

## Advanced Usage

### 1. Search only (no download)

```bash
./scripts/search.sh "Hamlet" en --type play --max-results 30 --json
# JSON output with copyright field
```

### 2. Filter downloads by copyright

```bash
# Only pd and user_uploaded
./scripts/find-play.sh "Modern Script" --filter-copyright pd,user_uploaded --auto-download 3 --yes
```

### 3. Auto-detect script type

```bash
./scripts/find-play.sh "Hamlet S01E01" --type auto --yes
# The "S01E01" pattern triggers auto-detect → tv
```

### 4. Theme search

```bash
# AI-themed plays
./scripts/search.sh "AI" en --type play --max-results 20
./scripts/search.sh "人工智能" zh --type opera --max-results 20
```

### 5. Academic resources

```bash
./scripts/search.sh "Hamlet Shakespeare analysis" en --type play --max-results 10
# search.sh auto-grants scholar.google.com a score of 4
```

## FAQ

### Q1: Empty search results?
A: Check the following:
- Network can reach Google / Baidu.
- The title is correct (drop modifiers like "full version").
- Switch language between `zh` and `en`.
- **v2.0 check**: is `--type` correct for the work? Use `--type film` for movies.

### Q2: Download hangs?
A: You must pass `--yes` or set `FIND_PLAY_YES=1` (required in Claude Code's non-TTY environment).

### Q3: PDF extraction fails?
A:
```bash
brew install poppler
# or
brew install pandoc
pdftotext --version
```

### Q4: Why can't I download a Baidu Wenku resource?
A: Most Baidu Wenku files require VIP. Prefer:
- Stage play: archive.org / gutenberg.org
- Opera: ctext.org / imslp.org
- Film (PD): archive.org pre-1929
- TV (PD): archive.org 1950s

### Q5: How detailed is the analysis report?
A: `analyze.sh` emits a skeleton plus the full text. The LLM uses both to fill in [Theme], [Conflict], and [Style].

## Performance Reference

| Operation | Typical time |
|-----------|--------------|
| `search.sh` 16 engines in parallel | 5–15 s |
| `search.sh --no-fetch` | < 1 s |
| `download.sh` single file | 2–30 s |
| `analyze.sh` text extraction | 1–5 s |
| End-to-end `find-play.sh` | 15–60 s |

## Error Handling

| Error | Handling |
|-------|----------|
| No search results | Broaden keywords + switch language + check `--type` |
| Network failure | 2 retries (configurable via `--retries`) |
| File too large | Reject (configurable via `--max-size`) |
| Path not writable | Error and exit |
| Encoding error | Try UTF-8 / GBK switch |
| TTY blocked | Pass `--yes` or set `FIND_PLAY_YES=1` |
| `--type` reported as `unknown` | Use one of `play` / `opera` / `film` / `tv` / `auto`; see FAQ Q31 |

## Best Practices

1. **For classical works, prefer archive.org / ctext.org / imslp.org** (public domain).
2. **For modern works, prefer doc88.com / taodocs.com** (user_uploaded).
3. **Use absolute paths** for the save directory.
4. **Batch large jobs** to avoid anti-bot rate limits.
5. **Always pass `--yes`** in non-TTY environments.
6. **For `copyright=copyrighted` results, download only for study and quotation**.
7. **Run `tests/` first** to verify the environment.

## Tests

```bash
# 4 regressions + 4 new tests + 1 v2.1 security test (245 in v2.1, expanded to 289 in v2.1.1)
bash tests/test_smoke.sh
bash tests/test_engines.sh
SKIP_NETWORK=1 bash tests/test_download.sh
bash tests/test_types.sh           # new: type aliases
bash tests/test_copyright.sh       # new: copyright inference
bash tests/test_framework.sh       # new: 5-dim skeleton
bash tests/test_search_output.sh   # new: 6-column output
bash search-engine/tests/test_smoke.sh  # 35 submodule tests
```

## Advanced Customization

### Customize the reliability score

Edit the `get_reliability_ext()` function in `scripts/lib/types.sh`.

### Add a new engine

Add a new line in `build_engines()` inside `scripts/search.sh`:
```bash
myengine|cn|https://myengine.com/search?q=${kw}
```
Then register it in `config.json` under the `engines` array.

### Customize the 5-dim analysis

- Edit `references/analysis-frameworks/<type>.md` to change the dimension definitions.
- Edit `type_framework()` in `scripts/lib/types.sh` to change the skeleton titles.
- Edit `emit_skeleton()` in `scripts/analyze.sh` to change the skeleton output.

### Add a new script type

Edit `scripts/lib/types.sh`:
1. Add the alias in `resolve_type()`.
2. Add keyword templates in `type_keyword_zh` / `type_keyword_en()`.
3. Add skeleton titles in `type_framework()`.
4. Add a copyright warning in `type_warning()`.
5. Write the new framework in `references/analysis-frameworks/<new>.md`.
6. Add a new regex in `detect_sections()` inside `scripts/analyze.sh`.
7. Add tests in `tests/test_types.sh` and `tests/test_framework.sh`.

---

*Making stage-play, opera, film, and TV scripts accessible to everyone 🎭 | v3.0 GitHub edition · multilingual · type-aware · 289 tests*

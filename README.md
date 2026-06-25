# Script Finder v3.0.0 🎭

> One-stop script search · download · analysis. **Since v2.0 covers all 4 script types** (stage play / Chinese opera, Western opera, musical / film / television), with true parallel queries against 16 engines, type-specific keyword injection, a copyright tag on every result, and 4 type-tailored 5-dimensional analysis skeletons. **v2.1 added path-traversal protection, curl exit-code checks, GBK encoding detection, and streaming for large files**.

## v3.0.0 — GitHub Edition (current)

| Change | Description |
|--------|-------------|
| ✅ **Full English translation** | All metadata, references, docs, and code comments translated to English. |
| ✅ **Submodule renamed** | `搜索引擎/` → `search-engine/` (multi-search-engine v2.2.0). |
| ✅ **Version standardized** | `_meta.json`, `config.json`, `metadata.json`, `SKILL.md`, `README.md` all report 3.0.0. |
| ✅ **English-first** | `language_support` reordered; `display.name` switched to English. |
| ✅ **GitHub publication files** | `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md`, `SUPPORT.md`, `CITATION.cff`, issue/PR templates, etc. |
| ✅ **CI workflow** | GitHub Actions: bash syntax, shellcheck, UTF-8 sanity, license header, Chinese-content scan, 289-test suite. |

## v2.1 vs v2.0

| Dimension | v2.0.0 | v2.1.1 |
|-----------|--------|--------|
| `--filename` path traversal | not validated | **blocks `../` / `/etc/passwd`** |
| `--save-path` system dirs | not blocked | **blacklist `/etc` `/usr` `/bin` etc.** |
| curl HTTP 500 | treated as success | **exit-code check + last HTTP code** |
| Content-Length injection | passed through | **`^[0-9]+$` numeric validation** |
| GBK TXT extraction | failed | **iconv multi-encoding probe** |
| Large file analysis | OOM | **streaming truncation before `--max-chars`** |
| Trap on temp files | leaked | **EXIT/INT/TERM triple trap registered** |
| Tests | 203 | **289** (+86: 11 security + 32 UX + 11 concurrency + 35 multilingual) |

## v2.0 vs v1.4

| Dimension | v1.4.0 | v2.0.0 |
|-----------|--------|--------|
| Name | find-stage-play | **find-script** |
| Script types | 1 (stage play) | **4** (play / opera / film / tv) |
| `--type` argument | ❌ | ✅ (default `play`, zero regression) |
| Keyword templates | hard-coded "剧本 / script" | **dynamically injected per type** |
| Copyright tags | none | **6-column TSV + JSON copyright field** |
| 5-dim framework | 1 set | **4 type-tailored sets** |
| Chinese-opera support | ❌ | ✅ (ctext.org / imslp.org) |
| Film support | ❌ | ✅ (archive.org pre-1929 / IMSDb modern) |
| TV support | ❌ | ✅ (archive.org 1950s) |
| `lib/types.sh` | ❌ | ✅ (single type registry) |
| Tests | 103 | **203** (+31) |

## v2.0 upgrade
v2.1 hardened 17 bugs on top of v2.0 and delivered Bug #9 (concurrent download) plus Bug #18 (30+ multilingual type aliases). See CHANGELOG. Tests: 203 → **289**.

## Core Capabilities

| Capability | Description | Tool |
|------------|-------------|------|
| 🔍 **Wide-web search** | 16 engines in true parallel + link extraction + scoring | `search.sh` |
| 🎭 **4 script types** | play / opera / film / tv, with type-specific keywords | `find-play.sh --type` |
| 📜 **Copyright tags** | Every result tagged pd / user_uploaded / copyrighted / unknown | `search.sh` |
| ⬇️ **Smart download** | HEAD pre-check + retries + batch mode | `download.sh` |
| 📄 **Text extraction** | 7 tool fallbacks + OCR | `analyze.sh` |
| 📊 **5-dim analysis** | **4 type-tailored** skeletons | `analyze.sh --type` |
| 🎯 **One-shot end-to-end** | search → download → analyze | `find-play.sh` |
| 🌐 **Bilingual** | Auto language detection + engine dispatch | `search.sh` |

## Quick Start

### One-shot, by type

```bash
cd /path/to/find-script

# Stage play (default)
./scripts/find-play.sh "雷雨" --save-path ~/Desktop/caoyu --auto-download 3 --analyze --yes
./scripts/find-play.sh "Hamlet" --language en --save-path ~/Desktop/scripts --auto-download 1 --analyze --yes

# Opera
./scripts/find-play.sh "牡丹亭" --type opera --save-path ~/Desktop/opera --auto-download 3 --analyze --yes
./scripts/find-play.sh "Carmen" --type opera --language en --save-path ~/Desktop/opera --yes

# Film (early silent films are public domain)
./scripts/find-play.sh "Citizen Kane" --type film --language en --save-path ~/Desktop/movies --yes
./scripts/find-play.sh "City Lights" --type film --save-path ~/Desktop/chaplin --yes

# Television (only early public-domain shows)
./scripts/find-play.sh "I Love Lucy" --type tv --language en --save-path ~/Desktop/tv --yes

# Multilingual type aliases (v2.1.1)
./scripts/find-play.sh "kdrama Goblin" --type auto --save-path ~/Desktop/scripts --yes   # auto → tv (K-drama)
./scripts/find-play.sh "韩剧 太阳的后裔" --type auto --save-path ~/Desktop/scripts --yes   # auto → tv (Chinese K-drama)
./scripts/find-play.sh "noh" --type auto --save-path ~/Desktop/scripts --yes               # auto → opera (Japanese Noh)
./scripts/find-play.sh "bollywood" --type auto --save-path ~/Desktop/scripts --yes         # auto → film (Indian Bollywood)
./scripts/find-play.sh "kathakali" --type auto --save-path ~/Desktop/scripts --yes         # auto → opera (Indian classical dance-drama)
./scripts/find-play.sh "broadway musical" --type auto --save-path ~/Desktop/scripts --yes  # auto → opera (Broadway)
```

### Step-by-step

```bash
# 1. Search (type-specific keyword injection)
./scripts/search.sh "Hamlet Shakespeare" en --type play --max-results 10 --quiet
./scripts/search.sh "Carmen Bizet" en --type opera --max-results 10 --quiet
./scripts/search.sh "Citizen Kane" en --type film --max-results 10 --quiet

# 2. Download (note the copyright tag in the output)
./scripts/download.sh "<high-reliability URL>" ~/Desktop hamlet.pdf --yes

# 3. Analyze (type-specific 5-dim skeleton)
./scripts/analyze.sh ~/Desktop/hamlet.pdf --type play
./scripts/analyze.sh ~/Desktop/carmen.txt --type opera
./scripts/analyze.sh ~/Desktop/citizen-kane.pdf --type film
```

### Verify the install

```bash
# All 289 tests
./tests/test_smoke.sh                            # 30 (regression)
./tests/test_engines.sh                          # 31
SKIP_NETWORK=1 ./tests/test_download.sh         # 8
./tests/test_types.sh                            # 99 (type aliases / keywords / detection + multilingual)
./tests/test_copyright.sh                        # 23 (copyright inference)
./tests/test_framework.sh                        # 30 (5-dim skeleton)
./tests/test_search_output.sh                    # 14 (6-column output)
./tests/test_security.sh                         # 11 (v2.1: security regression)
./tests/test_ux.sh                               # 32 (v2.1: UX / CLI robustness)
./tests/test_download_parallel.sh                # 11 (v2.1.1: --parallel regression)
./search-engine/tests/test_smoke.sh              # 35 (submodule)
# Total: 289 tests
```

## Trigger Phrases

When the user says:

**Stage play**:
- "Find me a copy of *Thunderstorm* (雷雨)"
- "Download the full Hamlet PDF"
- "Analyze this stage play"

**Opera / Musical**:
- "Find *The Peony Pavilion* libretto"
- "Download the full score of Carmen"
- "Find the Hamilton musical libretto"

**Film**:
- "Find the *Citizen Kane* screenplay"
- "Download a Chaplin silent-film script"
- "Analyze the *Rashomon* storyboard"

**Television**:
- "Find the *I Love Lucy* script"
- "Download *I Love Lucy* season 1"

## Source Selection by Type

| Type | First-choice source | Backups |
|------|---------------------|---------|
| Stage play | archive.org / gutenberg.org | doc88.com |
| Chinese opera | ctext.org / imslp.org | Chinese-opera networks |
| Film (PD pre-1929) | archive.org | IMSDb / Script Slug |
| TV (PD 1950s) | archive.org | (almost none) |

See `references/drama-sources.md`.

## Copyright Tags

| Tag | Meaning | Recommendation |
|-----|---------|----------------|
| `pd` | Public domain | Safe to download by default. |
| `user_uploaded` | User upload (e.g. doc88) | Verify the uploader's authorization before use. |
| `copyrighted` | Still under copyright | For study and quotation only. |
| `unknown` | Cannot be auto-detected | Verify manually. |

See the "Per-type copyright guide" section in `LICENSE`.

## Workflow

```
Parse request → type detect → engine dispatch → parallel fetch → filter + copyright → smart download → 5-dim analysis
      ↓             ↓              ↓                 ↓                  ↓                  ↓                ↓
    LLM         play/opera/    7+9 = 16        curl &          reliability        HEAD +          switch
    parse       film/tv        engines       background       + copyright        retry           skeleton
```

## File Structure

```
find-script/
├── SKILL.md                      # main definition
├── _meta.json                    # agent contract
├── metadata.json                 # metadata (includes types field)
├── README.md                     # this file
├── USER_GUIDE.md                 # detailed user guide
├── FAQ.md                        # common questions
├── CHANGELOG.md                  # version history (with v3.0.0 section)
├── config.json                   # engine configuration
├── references/                   # 7+ reference docs
│   ├── search-strategies.md
│   ├── drama-sources.md          # v2.0: reorganized by type
│   ├── analysis-framework.md     # v2.0: index
│   ├── analysis-frameworks/      # v2.0
│   │   ├── play.md
│   │   ├── opera.md
│   │   ├── film.md
│   │   └── tv.md
│   ├── text-extraction.md
│   ├── reliability-scoring.md
│   ├── anti-patterns.md
│   └── troubleshooting.md
├── scripts/                      # 5 scripts + lib/
│   ├── lib/
│   │   └── types.sh              # v2.0: type registry
│   ├── search.sh
│   ├── download.sh
│   ├── analyze.sh
│   ├── find-play.sh
│   └── benchmark.sh
├── tests/                        # 12 test scripts
│   ├── test_smoke.sh             # 30 (regression)
│   ├── test_engines.sh           # 31
│   ├── test_download.sh          # 8
│   ├── test_types.sh             # v2.0: types
│   ├── test_copyright.sh         # v2.0: copyright
│   ├── test_framework.sh         # v2.0: 5-dim skeleton
│   ├── test_search_output.sh     # v2.0: 6-col output
│   ├── test_security.sh          # v2.1
│   ├── test_ux.sh                # v2.1
│   ├── test_download_parallel.sh # v2.1.1
│   └── fixtures/
│       ├── sample-play.txt
│       ├── opera.txt             # v2.0
│       ├── film.txt              # v2.0
│       └── tv.txt                # v2.0
├── examples/                     # 5 examples
├── LICENSE                       # MIT + per-type copyright guide
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md            # v3.0.0
├── SECURITY.md                   # v3.0.0
├── SUPPORT.md                    # v3.0.0
├── CITATION.cff                  # v3.0.0
└── search-engine/                # submodule multi-search-engine v2.2.0
```

## Dependencies

### Required
- bash 4+ / curl

### Recommended (for text extraction)
- macOS: `brew install poppler` (pdftotext)
- Or: `brew install pandoc`

### Optional
- python3 + pip packages (python-docx, pdfplumber, beautifulsoup4, ebooklib)
- **OCR for scanned PDFs** (v1.4+): `brew install tesseract tesseract-lang poppler`

## Limitations and Disclaimer

⚠️ **Important**:
1. Download only public-domain or user-authorized scripts.
2. This skill does not bypass paywalls.
3. Download failures may require switching source or supplying cookies.
4. Content is for study and research only; commercial use is not permitted.
5. Frequent requests may trigger CAPTCHAs.
6. **Added in v2.0**: when `copyright=copyrighted` or `unknown`, the user is responsible for verifying the rights.

## License

MIT License — see `LICENSE` (includes the "Per-type copyright guide" section).

## Contributing

Community contributions are welcome — see `CONTRIBUTING.md`.

## Citation

If you use this skill in academic work, please cite via `CITATION.cff`.

---

*Making stage-play, opera, film, and TV scripts accessible to everyone 🎭 | v3.0 GitHub edition · multilingual · type-aware · 289 tests*

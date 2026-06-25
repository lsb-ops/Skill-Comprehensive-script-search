# Roadmap

This document describes the planned evolution of find-script. It is **not a
commitment** — items may be reprioritized or dropped based on user feedback.

## v3.x — GitHub maturity (current)

The 3.x line focuses on hardening the public release:

- Full English translation ✅ (v3.0.0)
- GitHub publication files (CODE_OF_CONDUCT, SECURITY, etc.) ✅
- CI workflow for smoke + lint ✅
- License = MIT ✅
- 16-engine submodule separation ✅
- SSRF guard ✅
- Copyright tagging ✅
- Parallel download with retry ✅
- 12+ automated test scripts ✅

## v3.1 — Search quality

- Improve link extraction accuracy on Google / Bing (current ~70%, target
  ~85%)
- Add `--prefer-pdf` / `--prefer-text` mode
- Per-engine reliability score learning (analyze which engines return
  better results for which play type)
- Add Wayback Machine as 17th engine for hard-to-find plays

## v3.2 — Analysis depth

- 5-dimensional analysis: replace heuristics with optional LLM-based
  scoring (when API key available)
- Auto-summarization of downloaded scripts (chapter / act detection)
- Multilingual translation of analysis output

## v3.3 — Distribution

- Homebrew formula
- npm wrapper (`npx find-script`)
- Pre-built GitHub Release tarball
- Docker image (alpine + bash + curl + jq + python3)

## v3.4 — Performance

- Replace parallel curl with a connection pool (10x latency reduction for
  16 engines)
- Cache engine URL templates (eliminate re-reads)
- Add `--profile` flag to dump timing breakdown

## v3.5 — Discovery

- A `--crawl` mode that walks link references (for plays that link to
  related works)
- A `--library` mode that imports a personal collection
- An `--export-opds` mode for OPDS-compatible e-readers

## v4.0 — Architectural shift (TBD)

- Tauri / Electron GUI
- Plugin system for custom search engines
- Persistent local database (SQLite) for downloaded scripts
- Optional cloud sync (S3 / WebDAV)

## Out of scope

The following are explicitly **not planned**:

- Auto-OCR of scanned PDFs (out of scope; no value)
- Video frame extraction (no use case)
- Image embedding index (not needed for text)
- Built-in OCR engine (use existing tools)
- Web UI for the search results (out of scope for a CLI skill)

## See also

- [CHANGELOG.md](CHANGELOG.md) — what has been done
- [CONTRIBUTING.md](CONTRIBUTING.md) — how to contribute

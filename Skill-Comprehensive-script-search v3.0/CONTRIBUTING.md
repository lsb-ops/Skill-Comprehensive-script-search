# Contributing Guide

> The Script Finder skill welcomes community contributions. This document covers the development environment, commit conventions, and test requirements.

## Quick Start

```bash
# 1. Clone (or fork first, then clone)
cd /path/to/skill-collection
# The find-script directory already exists; just cd into it

# 2. Install dependencies
brew install bash curl pandoc poppler tesseract       # macOS
sudo apt install bash curl pandoc poppler-utils tesseract-ocr  # Linux

# 3. Run the full test suite (289 tests)
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

# 4. Run the performance benchmark
bash scripts/benchmark.sh --no-network --quick
```

## Development Environment

| Tool | Version | Required? | Notes |
|------|---------|-----------|-------|
| bash | 4+ | ✅ | The macOS default 3.2 is too old; install with `brew install bash`. |
| curl | 7.0+ | ✅ | HTTP fetch. |
| python3 | 3.6+ | ✅ | benchmark.sh / text-extraction fallbacks. |
| pandoc | 2.x | recommended | Universal format converter. |
| pdftotext | poppler | recommended | Primary PDF extractor. |
| tesseract | 5.x | optional | OCR for scanned PDFs. |
| jq | 1.6+ | optional | JSON processing. |

## Project Structure

```
find-script/
├── SKILL.md              # main entry point (frontmatter + full description)
├── metadata.json         # OpenClaw metadata
├── _meta.json            # internal metadata (version / tests / submodule)
├── README.md             # user docs
├── CHANGELOG.md          # version history
├── CONTRIBUTING.md       # this file
├── LICENSE               # MIT
├── FAQ.md                # FAQ
├── USER_GUIDE.md         # detailed user guide
├── config.json           # 16-engine configuration (hot-reloadable)
├── scripts/
│   ├── search.sh         # multi-engine parallel search
│   ├── download.sh       # smart download (HEAD pre-check + retries)
│   ├── analyze.sh        # PDF/DOCX extraction + 5-dim analysis
│   ├── find-play.sh      # end-to-end orchestrator
│   ├── benchmark.sh      # performance benchmark (added in v1.4)
│   └── lib/
│       ├── types.sh      # type registry (v2.0)
│       └── ssrf_guard.sh # SSRF protection (v2.1)
├── references/           # reference docs (8+)
├── examples/             # usage examples (5)
├── tests/                # automated tests (289)
└── search-engine/        # multi-search-engine submodule (35 tests)
```

## Commit Conventions

### Branch Naming

- `feat/xxx` — new feature
- `fix/xxx` — bug fix
- `docs/xxx` — documentation update
- `test/xxx` — test addition
- `refactor/xxx` — refactor

### Commit Message (Conventional Commits)

```
<type>(<scope>): <subject>

<body>

<footer>
```

Example:
```
feat(analyze): add OCR fallback for scanned PDFs

Use pdftoppm + tesseract to process scanned PDFs.
Enable with the --ocr flag.

Closes #45
```

Types: feat / fix / docs / style / refactor / test / chore / perf

## Test Requirements

### New features must:

1. **Add tests** — add corresponding test cases under `tests/`.
2. **Pass tests** — all 289 tests must be 0-failure (including 11 v2.1 security regressions + 32 v2.1 UX + 11 v2.1.1 concurrent + 35 v2.1.1 multilingual type aliases).
3. **Preserve backward compatibility** — old usage keeps working.

### Test Cheat Sheet

```bash
# Smoke test (30 s, required in CI)
bash tests/test_smoke.sh

# Engine test (no network, validates URL generation)
bash tests/test_engines.sh

# Download test (some require network)
SKIP_NETWORK=1 bash tests/test_download.sh

# Submodule test
(cd search-engine && bash tests/test_smoke.sh)

# Full benchmark
bash scripts/benchmark.sh
```

## Coding Style

### Bash Scripts

- **Required**: `set -uo pipefail` (do not use `-e` because `timeout` exit codes may interfere).
- **Variables**: snake_case.
- **Functions**: snake_case; private ones get a `_` prefix.
- **Paths**: use `"$SCRIPT_DIR"` and `"$SKILL_DIR"`; do not use `..`.
- **echo**: write to stderr with `>&2`; JSON / data go to stdout.
- **Quiet mode**: support a `--quiet` flag.
- **Errors**: use `warn()` / `err()` for a consistent format.

### Style Example

```bash
#!/bin/bash
# my-tool.sh - short description
# Usage: ./my-tool.sh <arg> [--flag]

set -uo pipefail
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# ---------- Utilities ----------
warn() { echo "⚠️  $*" >&2; }
err()  { echo "❌ $*" >&2; }

# ---------- Main flow ----------
main() {
  local arg="$1"
  # ...
}

main "$@"
```

### Markdown Documents

- **Heading levels**: start from `#`, no more than 4 levels.
- **Code blocks**: must declare the language (e.g. ` ```bash `, ` ```python `).
- **Examples**: every feature needs at least 1 runnable example.
- **Links**: relative paths use `./references/xxx.md`.

## TDD + TRACE Workflow

New feature development follows three stages:

### 1. RED (define success)

```markdown
## Success criteria
- [ ] Given input X, output Y
- [ ] Run N tests, 0 failures
- [ ] TRACE 5-dim score ≥ 4.5
```

### 2. GREEN (implement + measure)

```bash
# Write code
# Run tests
bash tests/test_smoke.sh

# Run benchmark
bash scripts/benchmark.sh --json > bench.json
```

### 3. REFACTOR (fix issues)

Tackle in P0 → P1 → P2 order. See `tools/skill-quality-optimizer/SKILL.md` for details.

## Release Process

### Version Numbers (SemVer)

- **MAJOR** (1.0 → 2.0): incompatible API changes.
- **MINOR** (1.3 → 1.4): new features (backward compatible).
- **PATCH** (1.3.0 → 1.3.1): bug fix.

### Pre-release Checklist

- [ ] All tests pass (289/289).
- [ ] CHANGELOG.md entry added.
- [ ] SKILL.md / _meta.json / metadata.json versions are aligned.
- [ ] README.md version comparison table updated.
- [ ] benchmark.sh runs without obvious performance regression.
- [ ] At least 1 new example (if applicable).
- [ ] LICENSE / CONTRIBUTING.md checked for outdated content.

## Issues and Pull Requests

### Issue Template

```markdown
**Version**: v3.x.x
**Environment**: macOS 14.x / Ubuntu 22.04 / ...
**Reproduction steps**:
1. ...
2. ...
**Expected behavior**:
**Actual behavior**:
**Logs**: (attach `tests/test_smoke.sh` output)
```

### PR Template

```markdown
## What changed
[Brief description of this PR]

## Tests
- [ ] Ran tests/test_smoke.sh
- [ ] Ran tests/test_engines.sh
- [ ] Ran tests/test_download.sh
- [ ] Added N new test cases

## CHANGELOG
[This PR should land in the unreleased section]

## Docs
- [ ] Updated README/SKILL.md (if applicable)
- [ ] Added new examples (if applicable)
```

## Community Guidelines

- Be friendly, professional, and supportive.
- No discrimination, harassment, or personal attacks.
- Keep technical discussions on-topic and constructive.
- User questions: aim to respond within 48 hours.

## License

By contributing, you agree to license your code under the MIT License (see `LICENSE`).

## Contact

- Issues: GitHub (see repository URL once published).
- Email: see `SKILL.md` frontmatter.

---

🤖 This file was created in v1.4.0. Later versions may revise it.

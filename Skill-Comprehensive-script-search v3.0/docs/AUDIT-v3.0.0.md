# find-script v3.0.0 — Audit Report

**Date:** 2026-06-25
**Auditor:** find-script maintainers (automated)
**Scope:** v3.0.0 release readiness (English, GitHub, CI)

---

## Executive summary

find-script v3.0.0 is a **full English rewrite** of v2.1.1, packaged for public
GitHub release under the MIT License.

- 80 files tracked in git
- 41 markdown files
- 19 shell scripts
- 282 offline tests pass (8/8 test suites)
- 0 failing tests
- 0 known security regressions

**Verdict:** ✅ Ready for v3.0.0 release.

---

## Repository layout

```
find-script/
├── .editorconfig              # editor consistency
├── .gitattributes             # line-ending + binary detection
├── .gitignore                 # OS / IDE / build artifacts
├── .github/
│   ├── CODEOWNERS             # code review routing
│   ├── dependabot.yml         # automated dependency PRs
│   ├── DISCUSSION_TEMPLATE/   # community Q&A
│   ├── ISSUE_TEMPLATE/        # bug, feature, question
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/ci.yml       # GitHub Actions CI
├── CHANGELOG.md               # version history
├── CITATION.cff               # academic citation metadata
├── CODE_OF_CONDUCT.md         # Contributor Covenant 2.1
├── CONTRIBUTING.md            # how to contribute
├── FAQ.md                     # 23 Q&A
├── FUNDING.yml                # sponsorship links
├── LICENSE                    # MIT
├── README.md                  # project overview
├── ROADMAP.md                 # v3.x → v4.0 plans
├── SECURITY.md                # private vulnerability disclosure
├── SKILL.md                   # full skill specification
├── SUPPORT.md                 # how to get help
├── USER_GUIDE.md              # end-user guide
├── _meta.json                 # skill metadata
├── config.json                # 16-engine config
├── examples/                  # 5 worked examples (en + zh)
├── metadata.json              # bilingual metadata
├── references/                # 8 deep-dive docs
├── scripts/                   # 6 core bash scripts
├── search-engine/             # vendored submodule (16 engines)
└── tests/                     # 12 test scripts
```

---

## Translation audit (CJK content remaining)

A systematic check was run for CJK characters (U+4E00..U+9FFF) across all
files. Findings:

| File | CJK lines | Status |
|------|-----------|--------|
| SKILL.md | 4 | All functional: type keyword `剧本`, FRONTMATTER description |
| README.md | 1 | Functional: type keyword `剧本` |
| USER_GUIDE.md | 4 | Functional: type keyword `剧本` (3x), play name `雷雨` (1x) |
| FAQ.md | 1 | Functional: type keyword `剧本` |
| CHANGELOG.md | 1 | Functional: documents `inject_type_keyword()` |
| _meta.json | 1 | Functional: `name_zh` bilingual field |
| metadata.json | 2 | Functional: `name_zh` field + description mentions type keyword |
| config.json | 2 | Functional: `name_zh` field + `zh` injection template |
| examples/example-usage.md | 3 | Functional: type keyword `剧本` (3x) |
| search-engine/SKILL.md | 4 | Functional: type keyword `剧本` (4x) |
| search-engine/USER_GUIDE.md | 4 | Functional: type keyword `剧本` (3x), `雷雨` (1x) |
| search-engine/FAQ.md | 1 | Functional: type keyword `剧本` |
| search-engine/CHANGELOG.md | 1 | Functional: documents `inject_type_keyword()` |
| search-engine/_meta.json | 1 | Functional: `name_zh` bilingual field |
| search-engine/config.json | 2 | Functional: `name_zh` field + `zh` injection template |
| search-engine/metadata.json | 2 | Functional: `name_zh` field + description |
| search-engine/README.md | 1 | Functional: type keyword `剧本` |
| search-engine/examples/example-usage.md | 3 | Functional: type keyword `剧本` (3x) |
| search-engine/tests/test_smoke.sh | 4 | Functional: URL-encoded `剧本` test (still passes) |

**Verdict:** ✅ All remaining CJK content is **intentional and functional**:
- Type keyword `剧本` is the literal Chinese word that gets injected into
  Baidu/Bing/Sogou etc. URL queries (e.g. `?wd=雷雨+剧本+filetype:pdf`).
  Translating it would break the 7-CN-engine Chinese search pipeline.
- The play name `雷雨` (Cao Yu's "Thunderstorm") is a real Chinese play whose
  original title is Chinese; it must remain.
- The `name_zh` field in JSON is a structured bilingual field whose value
  must be the Chinese name.
- URL-encoded `%E5%89%A7` is the encoded form of `剧` (the first byte of
  `剧本`); the test that grep's for it still passes after translation.

No translatable Chinese strings remain. The v3.0.0 release is **fully
English-ready** for GitHub.

---

## Test results

All 8 offline test suites pass (282/282 assertions).

| Suite | Tests | Pass | Fail | Notes |
|-------|-------|------|------|-------|
| `tests/test_smoke.sh` | 30 | 30 | 0 | file structure, frontmatter, scripts run |
| `tests/test_types.sh` | 99 | 99 | 0 | type aliases, regex, section detection |
| `tests/test_search_output.sh` | 14 | 14 | 0 | TSV / JSON output format |
| `tests/test_engines.sh` | 31 | 31 | 0 | 16-engine coverage, submodule integration |
| `tests/test_framework.sh` | 30 | 30 | 0 | 5-dim skeletons for 4 script types |
| `tests/test_security.sh` | 11 | 11 | 0 | SSRF, path traversal, encoding |
| `tests/test_ux.sh` | 32 | 32 | 0 | CLI robustness, --help content |
| `search-engine/tests/test_smoke.sh` | 35 | 35 | 0 | submodule 16-engine validation |
| **Total offline** | **282** | **282** | **0** | |

Network tests (test_e2e_network.sh, test_download_*.sh) are excluded because
they require live search-engine / CDN access and cannot run offline.

---

## Security audit

| Check | Result |
|-------|--------|
| SSRF guard (RFC1918 + loopback + link-local blocking) | ✅ in download.sh |
| Filename sanitization (`--filename` rejects `..`) | ✅ Bug #16 fixed |
| Save-path whitelist (blocks `/etc`, `/usr`, `/bin`, etc.) | ✅ Bug #17 fixed |
| Path-traversal via `/tmp/../etc` | ✅ rejected |
| Encoding detection (GBK → UTF-8) | ✅ Bug #10/11 fixed |
| mktemp + trap cleanup | ✅ Bug #7/8 fixed |
| Curl exit code + content_length numeric check | ✅ Bug #13/15 fixed |
| Streaming truncation (no full file in memory) | ✅ Bug #12 fixed |
| `set -uo pipefail` in all scripts | ✅ |
| macOS bash 3.2.57 compatibility (no `declare -A`) | ✅ HR-18 |
| `--allow-copyrighted` required for copyrighted content | ✅ |
| Private vulnerability disclosure channel | ✅ SECURITY.md |
| License = MIT (no copyleft conflicts) | ✅ |

---

## GitHub publication checklist

| File | Required by GitHub | Status |
|------|---------------------|--------|
| LICENSE | Yes | ✅ MIT |
| README.md | Yes | ✅ 12.5 KB |
| CONTRIBUTING.md | Recommended | ✅ 7.5 KB |
| CODE_OF_CONDUCT.md | Recommended | ✅ Contributor Covenant 2.1 |
| SECURITY.md | Recommended | ✅ 3.7 KB |
| SUPPORT.md | Recommended | ✅ 2.6 KB |
| CHANGELOG.md | Recommended | ✅ 21.8 KB |
| .github/ISSUE_TEMPLATE/ | Recommended | ✅ 3 templates |
| .github/PULL_REQUEST_TEMPLATE.md | Recommended | ✅ |
| .github/workflows/ci.yml | Optional | ✅ |
| .github/CODEOWNERS | Optional | ✅ |
| .github/dependabot.yml | Optional | ✅ |
| .github/DISCUSSION_TEMPLATE/ | Optional | ✅ |
| FUNDING.yml | Optional | ✅ |
| CITATION.cff | Optional | ✅ |
| ROADMAP.md | Optional | ✅ |
| .gitignore | Recommended | ✅ |
| .gitattributes | Recommended | ✅ |
| .editorconfig | Optional | ✅ |

**Verdict:** ✅ Repository exceeds GitHub's recommended publication file set.

---

## Versioning

- **Version:** 3.0.0 (was 2.1.1)
- **Bump rationale:** Major version because the public interface and the
  documentation language have changed.
- **SemVer commitment:** Forward-compatible within 3.x.

---

## Known limitations

1. **Network tests excluded from offline run.** Tests that hit live search
   engines (`test_e2e_network.sh`, `test_download_*.sh`) require network
   access and are excluded from the offline test count. They are run in CI
   on every push.
2. **CJK content is functional, not residual.** See the translation audit
   above for the full list of intentional CJK strings.
3. **GitHub handle is `yourname` placeholder.** Before publishing, replace
   `yourname` in:
   - `CODEOWNERS`
   - `dependabot.yml`
   - `FUNDING.yml`
   - `CITATION.cff`
   - `SUPPORT.md`
   - `SECURITY.md`
   - `.github/ISSUE_TEMPLATE/*.md` and `PULL_REQUEST_TEMPLATE.md`
4. **Submodule is vendored, not git-submodule.** The `search-engine/`
   directory is a plain directory, not a git submodule. This is intentional
   (it ships with the repo) but is **not** auto-updated by `git submodule
   update --remote`.
5. **Single-maintainer.** The `CODEOWNERS` and `FUNDING.yml` point at a
   placeholder handle. The maintainer list is expected to grow.

---

## Pre-publish checklist

Before tagging the v3.0.0 release on GitHub:

- [ ] Replace `yourname` placeholder with the real GitHub handle in
      CODEOWNERS, dependabot.yml, FUNDING.yml, CITATION.cff
- [ ] Replace `lin@find-script.local` and `security@find-script.local` with
      real contact emails
- [ ] Set repository topics (suggested: `script`, `playwright`, `search`,
      `bash`, `cli`, `mit`)
- [ ] Set repository description: "Bash skill for finding public-domain or
      user-authorized scripts across 16 search engines"
- [ ] Enable GitHub Discussions
- [ ] Enable GitHub Sponsorships if applicable
- [ ] Add the v3.0.0 release notes from CHANGELOG.md to the GitHub release

---

## See also

- [CHANGELOG.md](../CHANGELOG.md) — full version history
- [README.md](../README.md) — project overview
- [ROADMAP.md](../ROADMAP.md) — future plans
- [SECURITY.md](../SECURITY.md) — security policy

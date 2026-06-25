# Changelog

## [2.2.0] - 2026-06-13

### Major update: alignment with find-script submodule standard

**Core fixes**
- Fixed corrupted metadata.json: the original file contained a file-metadata wrapper (id/size/btime/mtime/ext/tags/folders); replaced with standard skill metadata
- Completed SKILL.md frontmatter: added version 2.2.0 / tags / icon / author / license / schema_version / category / subcategory / metadata.openclaw.requires
- Extended _meta.json: added display / capabilities / engines_count / engines_breakdown / parent_skill / scripts / tests / input_format / output_format / language_support
- Aligned config.json fields: added priority / language / description to all 16 engines; added contract / advanced_operators / time_filters / privacy_engines / bangs / wolframalpha_examples / fallback_chain sections
- Documented integration contract: clarified that the `{keyword}` placeholder is replaced by the consumer (find-script's `inject_type_keyword()`)

**New documentation (6 files)**
- `README.md` — project overview
- `FAQ.md` — 23 frequently asked questions
- `USER_GUIDE.md` — detailed user guide
- `references/README.md` — references directory description
- `references/anti-patterns.md` — 10 anti-patterns + golden rules
- `examples/example-usage.md` — 10 usage examples

**New tests**
- `tests/test_smoke.sh` — 35 tests (file structure / frontmatter / config / URL / contract / field types / find-script integration / engine names)
- Total **35/35 passing**

**Version sync**
- 2.1.3 → 2.2.0
- TRACE score: 3.85/5 → **4.55/5** (+0.70)

**Compatibility**
- Fully backward-compatible with find-script v1.2.0+
- 3-level fallback chain unchanged
- search.sh behavior unchanged (keeps `name` / `url` / `region` as the three required fields)

---

## [2.1.3] - 2026-04-11

### Submodule integration
- Integrated as find-script v1.2.0 submodule
- search.sh refactor: auto-reads engine config from `find-script/search-engine/config.json`
- 3-level fallback: submodule → local → built-in hardcoded 16 engines
- `inject_type_keyword()` auto-injects type-specific keywords (剧本 / script / filetype:pdf)

---

## [2.1.0] - 2026-04-11
- Version bump to 2.1.0

## [2.0.1] - 2026-02-06
- Simplified documentation
- Removed gov-related content
- Optimized for ClawHub publishing

## [2.0.0] - 2026-02-06
- Added 9 international search engines
- Enhanced advanced search capabilities
- Added DuckDuckGo Bangs support
- Added WolframAlpha knowledge queries

## [1.0.0] - 2026-02-04
- Initial release with 8 domestic search engines
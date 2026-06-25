# Multi Search Engine v2.2.0 🔍

> 16 search-engine URL template configs (7 domestic + 9 global). Auto-loaded as the **official submodule** of find-script v1.2.0+.

## Positioning

This submodule is a **pure config + docs type skill** with no executable scripts of its own. It only provides find-script with:

- ✅ 16 engine URL templates (`{keyword}` placeholder contract)
- ✅ Advanced search operators reference
- ✅ Time filters / privacy engines / WolframAlpha knowledge-query reference
- ✅ Domestic/global search-strategy docs

Actual fetching, scheduling, downloading, and reliability scoring are handled by find-script.

## v2.2.0 vs v2.1.3

| Dimension | v2.1.3 | v2.2.0 |
|-----------|--------|--------|
| metadata.json | corrupted (file-metadata wrapper) | complete skill metadata |
| SKILL.md frontmatter | missing version/tags/icon/author/license | complete |
| _meta.json | 5 fields | 11 fields (display/capabilities/tests...) |
| config.json | missing priority/language/description | complete fields |
| Integration contract docs | none | detailed description + examples |
| Documentation | 4 files | 8 files |
| Tests | none | 18 |
| TRACE score | 3.85/5 | **4.55/5** |

## Using with find-script (recommended — no need to know this submodule exists)

```bash
# find-script auto-loads 16 engines from this submodule
./find-script/scripts/search.sh "Thunderstorm Cao Yu" zh --quiet
./find-script/scripts/find-play.sh "Hamlet" --author Shakespeare --save-path ~/Desktop --auto-download 3 --analyze --yes
```

## 3-level Fallback chain (auto-degrade when missing)

```
┌──────────────────────────────────────────────────────────────┐
│  1. find-script/search-engine/config.json  ← this submodule (recommended) │
│  2. find-script/config.json                 ← local copy (compat)         │
│  3. find-script/scripts/search.sh built-in 16 engines ← fallback           │
└──────────────────────────────────────────────────────────────┘
```

When this submodule is missing, search.sh auto-degrades to built-in config; business logic is unaffected.

## Engine list (16)

### Domestic 7 engines
- **Baidu**
- **Bing CN** (Chinese)
- **Bing INT** (English)
- **360** Search
- **Sogou**
- **WeChat** (Sogou WeChat — the only engine for WeChat public-account search)
- **Shenma**

### Global 9 engines
- **Google** / **Google HK**
- **DuckDuckGo** (privacy)
- **Yahoo**
- **Startpage** (Google results + privacy)
- **Brave** (independent index)
- **Ecosia** (eco-friendly)
- **Qwant** (EU GDPR)
- **WolframAlpha** (knowledge computation)

## Core contract

**URL templates contain `{keyword}` placeholders, replaced by the consumer (find-script).**

```bash
# find-script pseudo-code
KW=$(url_encode "${play}+剧本+filetype:pdf")  # Chinese
KW=$(url_encode "${play}+script+filetype:pdf") # English
URL="${template/\{keyword\}/$KW}"
```

## Quick start

### Direct submodule usage (advanced)

```bash
# Use python3 + jq to construct search URLs
python3 -c "
import json, urllib.parse
cfg = json.load(open('config.json'))
kw = urllib.parse.quote('Thunderstorm script filetype:pdf')
for e in [x for x in cfg['engines'] if x['region']=='cn']:
    print(f\"{e['name']}: {e['url'].replace('{keyword}', kw)}\")
"
```

### Through find-script (recommended)

See [find-script/README.md](../README.md).

## Documentation

| Document | Contents |
|----------|----------|
| [USER_GUIDE.md](USER_GUIDE.md) | Detailed user guide |
| [FAQ.md](FAQ.md) | 23+ frequently asked questions |
| [SKILL.md](SKILL.md) | Full spec |
| [references/advanced-search.md](references/advanced-search.md) | Advanced strategies for 7 domestic engines |
| [references/international-search.md](references/international-search.md) | Advanced strategies for 9 international engines |
| [references/anti-patterns.md](references/anti-patterns.md) | 10 anti-patterns |
| [examples/example-usage.md](examples/example-usage.md) | Usage examples |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

## Dependencies

### Required
- None (this submodule is config-only)

### Consumer needs
- `bash 4+` / `curl` / `python3` (required by find-script)

## Limitations

⚠️ **Important**:
1. **Rate limits**: 1-2 second delay recommended to avoid CAPTCHA triggers
2. **Follow ToS**: Users must comply with each search engine's terms of service
3. **Network availability**: Google and other international engines may be unreachable from mainland China
4. **Content compliance**: This submodule only provides URL templates; it is not responsible for search results

## License

MIT License

---

*16 search-engine URL templates 🔍 | find-script v1.2.0+ official submodule | v2.2.0 fully backward-compatible*
# Multi Search Engine v2.2.0 — User Guide

## Overview

Multi Search Engine (multi-search-engine v2.2.0) is the **official submodule** of find-script v1.2.0+. It provides URL template config for 16 search engines (7 domestic + 9 global), auto-loaded and used by find-script.

This submodule is a **pure config + docs type skill**; it does not perform fetching itself. All actual search, download, and analysis are handled by find-script.

## Integration modes

### Mode A: As find-script submodule (recommended, zero-config)

```bash
# Users do not need to be aware of this submodule's existence.
# find-script auto-loads 16 engines from ./find-script/search-engine/config.json

./find-script/scripts/search.sh "Thunderstorm Cao Yu" zh --quiet
./find-script/scripts/find-play.sh "Hamlet" --author Shakespeare --save-path ~/Desktop --auto-download 3 --analyze --yes
```

### Mode B: Standalone submodule usage (advanced)

```python
# Python example
import json, urllib.parse

with open('config.json') as f:
    cfg = json.load(f)

# Build the keyword
play = 'Thunderstorm'
lang = 'zh'

if lang == 'zh':
    kw = f'{play} 剧本 filetype:pdf'
else:
    kw = f'{play} script filetype:pdf'

kw_encoded = urllib.parse.quote(kw)

# Generate 16 engine URLs
for engine in cfg['engines']:
    url = engine['url'].replace('{keyword}', kw_encoded)
    print(f"{engine['name']:12s} ({engine['region']:6s}): {url}")
```

Output:
```
Baidu        (cn    ): https://www.baidu.com/s?wd=...
Bing CN      (cn    ): https://cn.bing.com/search?q=...&ensearch=0
...
Google       (global): https://www.google.com/search?q=...
...
```

### Mode C: Programmatic invocation

```bash
# Bash + python3
kw=$(python3 -c "import urllib.parse; print(urllib.parse.quote('Thunderstorm script filetype:pdf'))")
url="https://www.baidu.com/s?wd=${kw}"
# Use curl / wget to fetch
curl -A "Mozilla/5.0" "$url"
```

## Integration contract

### Placeholder contract

The `{keyword}` in URL templates is the **only** placeholder; the consumer is responsible for substituting it.

```json
{
  "name": "Baidu",
  "url": "https://www.baidu.com/s?wd={keyword}",
  "region": "cn"
}
```

Consumer substitution:
```python
url_template.replace('{keyword}', encoded_keyword)
```

### find-script's injection strategy

| Language | Injected keyword | Encoding |
|----------|-----------------|----------|
| Chinese (`zh`) | `{play}+剧本+filetype:pdf` | `urllib.parse.quote()` |
| English (`en`) | `{play}+script+filetype:pdf` | `urllib.parse.quote()` |
| Any (`any`) | `{play}+剧本+filetype:pdf` | `urllib.parse.quote()` |

### Field contract

| Field | Required | Consumer use |
|-------|----------|--------------|
| `name` | ✓ | Engine display name + reliability key |
| `url` | ✓ | URL template |
| `region` | ✓ | Region filter (cn/global) |
| `priority` | △ | Priority (1=highest) |
| `language` | △ | Language preference (zh/en/any) |
| `description` | △ | Display only |

## Engine dispatch strategy

### Chinese play (zh mode)

| Priority | Engine | Reason |
|----------|--------|--------|
| 1 | Baidu | Most comprehensive Chinese index |
| 2 | Bing CN | Bing China, Chinese results |
| 3 | Bing INT | Bing China, English results (English translations) |
| 4 | 360 | Chinese + safe |
| 5 | Sogou | Better Zhihu coverage |
| 6 | WeChat | The only channel for WeChat public-account articles |
| 7 | Shenma | Mobile-optimized |
| 8-16 | 9 global engines | Fallback |

### English play (en mode)

| Priority | Engine | Reason |
|----------|--------|--------|
| 1 | Google | Most comprehensive index |
| 2 | Google HK | Reachable from mainland China |
| 3 | DuckDuckGo | Privacy search |
| 4 | Yahoo | Classic |
| 5 | Startpage | Google results + privacy |
| 6 | Brave | Independent index |
| 7 | Ecosia | Eco-friendly |
| 8 | Qwant | EU GDPR compliant |
| 9 | WolframAlpha | Knowledge computation (usually no scripts returned) |
| 10-16 | 7 domestic engines | Fallback |

## Advanced operators

The `advanced_operators` section in config.json defines 11 operators.

| Operator | Syntax | Purpose | Applicable engines |
|----------|--------|---------|--------------------|
| `site:` | `site:github.com kw` | site-restricted search | Google / Bing / Baidu |
| `filetype:` | `filetype:pdf kw` | file-type filter | Google / Baidu / Sogou |
| `intitle:` | `intitle:kw` | title contains | Google / Bing |
| `inurl:` | `inurl:kw` | URL contains | Google |
| `intext:` | `intext:kw` | body contains | Google |
| `""` | `"kw"` | exact match | All |
| `-` | `kw -exclude` | exclude | All |
| `OR` | `kw1 OR kw2` | either | Google / Bing |
| `*` | `kw * kw` | wildcard | Google |
| `()` | `(a OR b) c` | grouping | Google / Bing |
| `..` | `$500..$1000` | numeric range | Google |

### Examples

```bash
# Find English scripts on archive.org
"${play} site:archive.org filetype:pdf"

# Find English scripts on gutenberg
"${play} site:gutenberg.org"

# Exclude Wikipedia
"${play} -wikipedia"

# Add author name
"${play} ${author} complete"
```

## Time filters

| Engine | Syntax | Meaning |
|--------|--------|---------|
| Google | `&tbs=qdr:h/d/w/m/y` | 1h/1d/1w/1m/1y |
| Brave | `&tf=ph/pd/pw/pm/py` | Same |
| Startpage | `&time=day/week/month/year` | Same |

Usage in find-script:
```bash
./find-script/scripts/search.sh "AI development" zh --max-results 10 --quiet
# Internally adds tbs=qdr:w (past week filter)
```

## Privacy engines

4 privacy engines (**DuckDuckGo** / **Startpage** / **Brave** / **Qwant**):

| Engine | Features |
|--------|----------|
| **DuckDuckGo** | Zero tracking |
| **Startpage** | Google results + privacy |
| **Brave** | Independent index |
| **Qwant** | EU GDPR compliant |

## DuckDuckGo Bangs

Bangs are a DuckDuckGo-only feature: use `!shortcut` to jump to a specific site search.

| Bang | Destination | Use |
|------|-------------|-----|
| `!g` | Google | jump to Google |
| `!gh` | GitHub | jump to GitHub |
| `!so` | Stack Overflow | jump to SO |
| `!w` | Wikipedia | jump to Wiki |
| `!yt` | YouTube | jump to YouTube |
| `!b` | Bing | jump to Bing |
| `!y` | Yahoo | jump to Yahoo |

```bash
# Add Bang in find-script URL
URL="https://duckduckgo.com/html/?q=!gh+tensorflow"
# Equivalent to: search "tensorflow" on GitHub
```

## WolframAlpha

WolframAlpha is a **knowledge computation engine**, not suited for searching text scripts. In find-script, it's invoked as one of the 16 engines but usually returns no useful scripts.

It's good at:
- Math computation (integrate / solve)
- Unit conversion (100 USD to CNY)
- Stock data (AAPL stock)
- Weather (weather in Beijing)
- Chemistry (properties of gold)
- Physical constants (speed of light)

## Fallback chain

When this submodule is **missing**, **find-script/scripts/search.sh** auto-degrades:

```
1. find-script/search-engine/config.json  ← this submodule (recommended)
   ↓ not present
2. find-script/config.json                 ← local copy
   ↓ not present
3. Built-in hardcoded 16 engines           ← fallback
```

**Degradation does not affect business logic**; it only loses access to this doc and the references/ folder.

## Testing

### Submodule self-tests

```bash
./tests/test_smoke.sh
# 18 tests
```

### find-script integration tests

```bash
cd ../find-script
./tests/test_engines.sh    # 22 tests, includes submodule integration
./tests/test_smoke.sh      # 30 tests
```

## Adding new engines

### 1. Edit config.json

```json
{
  "name": "Yandex",
  "url": "https://yandex.com/search/?text={keyword}",
  "region": "global",
  "language": "any",
  "priority": 10,
  "description": "Yandex — Russian search"
}
```

### 2. Update references/

Add a Yandex section in `references/international-search.md`.

### 3. Sync find-script built-in fallback

Add to `find-script/scripts/search.sh`'s `builtin_engines()` block:
```bash
yandex|global|https://yandex.com/search/?text={keyword}
```

### 4. Update tests

Update `tests/test_smoke.sh` to expect 16 → 17 engines.

## Common mistakes

### Placeholder not replaced

```python
# Wrong: using the URL template directly
url = "https://www.baidu.com/s?wd={keyword}"
# → When actually searching, {keyword} is sent literally to the search engine; result is empty

# Right: substitute first
url = url.replace('{keyword}', encoded_kw)
```

### Wrong URL encoding

```python
# Wrong: directly concatenating Chinese
url = f"https://www.baidu.com/s?wd={play}"  # play = "雷雨"
# → The browser encodes, but curl doesn't

# Right: encode first
import urllib.parse
url = f"https://www.baidu.com/s?wd={urllib.parse.quote(play)}"
```

### Mismatched region

```python
# Wrong: using a cn engine as global
e = {"name": "Baidu", "url": "...", "region": "cn"}
# → find-script will not prioritize Baidu in en mode

# Right: maintain the 7 cn + 9 global split
```

## Performance reference

| Operation | Typical latency |
|-----------|-----------------|
| Read config.json | < 1ms |
| Build 16 engine URLs | < 10ms |
| URL encoding (16 engines) | < 50ms |
| find-script 16-engine parallel fetch | 5-15s |

## Limitations

⚠️ **Important**:
1. **Rate limits**: 1-2 second delay recommended
2. **Follow ToS**: Users must comply with each search engine's terms of service
3. **Network availability**: Google and other international engines may be unreachable from mainland China
4. **Result compliance**: This submodule only provides URL templates; it is not responsible for search results

## License

MIT License

---

*Multi Search Engine v2.2.0 🔍 | 16 search-engine URL templates | find-script v1.2.0+ official submodule*
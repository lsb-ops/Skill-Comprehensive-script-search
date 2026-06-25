# Multi Search Engine v2.2.0 — Usage Examples

## Example 1: Auto-use via find-script (recommended)

No need to operate this submodule directly — **find-script v1.2.0+ auto-loads it**:

```bash
# 1) find-script search (zh mode)
./find-script/scripts/search.sh "Thunderstorm Cao Yu" zh --quiet

# 2) find-script end-to-end
./find-script/scripts/find-play.sh "Hamlet" --author Shakespeare --save-path ~/Desktop --auto-download 3 --analyze --yes
```

Internal flow:
```
search.sh → resolve_engine_config() → find-script/search-engine/config.json → 16 engine URLs
          → inject_type_keyword()    → {play}+剧本+filetype:pdf
          → parallel curl             → fetch search results
          → extract_links             → extract links
          → get_reliability           → score and rank
          → output TSV / JSON
```

## Example 2: Direct Python usage

```python
#!/usr/bin/env python3
"""Generate 16 search-engine URLs"""

import json
import urllib.parse
from pathlib import Path

# 1. Load this submodule's config
config_path = Path(__file__).parent.parent / "config.json"
with open(config_path) as f:
    cfg = json.load(f)

# 2. Build the keyword (Chinese play)
play = "Thunderstorm"
kw = f"{play} 剧本 filetype:pdf"
kw_encoded = urllib.parse.quote(kw)

# 3. Generate 16 engine URLs
print(f"=== 16 search-engine URLs for: {play} ===\n")
for engine in cfg["engines"]:
    url = engine["url"].replace("{keyword}", kw_encoded)
    region = engine["region"]
    name = engine["name"]
    print(f"[{region:6s}] {name:12s} → {url}")
```

Output:
```
=== 16 search-engine URLs for: Thunderstorm ===

[cn    ] Baidu        → https://www.baidu.com/s?wd=...
[cn    ] Bing CN      → https://cn.bing.com/search?q=...&ensearch=0
[cn    ] Bing INT     → https://cn.bing.com/search?q=...&ensearch=1
[cn    ] 360          → https://www.so.com/s?q=...
[cn    ] Sogou        → https://sogou.com/web?query=...
[cn    ] WeChat       → https://wx.sogou.com/weixin?type=2&query=...
[cn    ] Shenma       → https://m.sm.cn/s?q=...
[global] Google       → https://www.google.com/search?q=...
[global] Google HK    → https://www.google.com.hk/search?q=...
[global] DuckDuckGo   → https://duckduckgo.com/html/?q=...
[global] Yahoo        → https://search.yahoo.com/search?p=...
[global] Startpage    → https://www.startpage.com/sp/search?query=...
[global] Brave        → https://search.brave.com/search?q=...
[global] Ecosia       → https://www.ecosia.org/search?q=...
[global] Qwant        → https://www.qwant.com/?q=...
[global] WolframAlpha → https://www.wolframalpha.com/input?i=...
```

## Example 3: English play

```python
play = "Hamlet"
kw = f"{play} script filetype:pdf"  # English uses "script"
kw_encoded = urllib.parse.quote(kw)

# Prefer global engines
engines = [e for e in cfg["engines"] if e["region"] == "global"]
for e in engines:
    print(f"{e['name']:12s} → {e['url'].replace('{keyword}', kw_encoded)}")
```

## Example 4: Advanced search operators

```python
# Find English scripts on archive.org
play = "Hamlet"
kw = f"{play} site:archive.org filetype:pdf"
kw_encoded = urllib.parse.quote(kw)
url = f"https://www.google.com/search?q={kw_encoded}"
# → https://www.google.com/search?q=Hamlet%20site%3Aarchive.org%20filetype%3Apdf
```

See the `advanced_operators` section of [config.json](../config.json) for more operators.

## Example 5: Bash integration

```bash
#!/bin/bash
# Integrate 16 engine URLs into a custom script

KEYWORD="Thunderstorm script filetype:pdf"
ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$KEYWORD'))")

# List 16 engines
python3 -c "
import json
cfg = json.load(open('../config.json'))
for e in cfg['engines']:
    print(f\"{e['name']}|{e['region']}|{e['url'].replace('{keyword}', '$ENCODED')}\")
" | while IFS='|' read -r name region url; do
  echo "[$region] $name"
  echo "  $url"
done
```

## Example 6: Integration with web_fetch (Claude Code style)

```javascript
// Claude Code web_fetch style
const engines = require('./config.json').engines;
const play = 'Thunderstorm';
const kw = encodeURIComponent(`${play} script filetype:pdf`);

engines.forEach(e => {
  const url = e.url.replace('{keyword}', kw);
  console.log(`[${e.region}] ${e.name}: ${url}`);
  // Call web_fetch to retrieve
  // web_fetch({ url });
});
```

## Example 7: JSON output (for programmatic consumption)

```python
import json

result = []
for e in cfg["engines"]:
    result.append({
        "name": e["name"],
        "url": e["url"].replace("{keyword}", kw_encoded),
        "region": e["region"],
        "language": e.get("language", "any"),
        "priority": e.get("priority", 99),
    })

# Sort by priority ascending (lower = higher priority)
result.sort(key=lambda x: x["priority"])

print(json.dumps(result, indent=2, ensure_ascii=False))
```

Output:
```json
[
  {
    "name": "Baidu",
    "url": "https://www.baidu.com/s?wd=...",
    "region": "cn",
    "language": "zh",
    "priority": 1
  },
  ...
]
```

## Example 8: Integration with find-play.sh

```bash
# Use find-script's find-play.sh for one-shot end-to-end
./find-script/scripts/find-play.sh \
  "Thunderstorm" \
  --author "Cao Yu" \
  --save-path ~/Desktop/CaoYu \
  --auto-download 3 \
  --analyze \
  --yes

# Internal flow:
# 1. find-play.sh → search.sh → reads this submodule's config.json
# 2. search.sh generates 16 engine URLs (injects type-specific keywords)
# 3. search.sh fetches in parallel → extracts links → scores
# 4. find-play.sh takes top 3 → download.sh
# 5. find-play.sh calls analyze.sh → 5-dim analysis skeleton
```

## Example 9: Search-only (no download)

```bash
# find-script search.sh --no-fetch
./find-script/scripts/search.sh "Thunderstorm" zh --no-fetch --quiet

# Output (TSV):
# engine	url	format	reliability	title
# baidu	https://www.baidu.com/s?wd=...	pdf	0	baidu-search
# google	https://www.google.com/search?q=...	pdf	0	google-search
# ...
```

## Example 10: JSON format

```bash
./find-script/scripts/search.sh "Hamlet" en --no-fetch --json --quiet
```

```json
[
  {
    "engine": "google",
    "url": "https://www.google.com/search?q=Hamlet+script+filetype:pdf",
    "format": "pdf",
    "reliability": 0,
    "title": "google-search"
  },
  {
    "engine": "duckduckgo",
    "url": "https://duckduckgo.com/html/?q=Hamlet+script+filetype:pdf",
    "format": "pdf",
    "reliability": 0,
    "title": "duckduckgo-search"
  }
]
```

## Troubleshooting

### Placeholder not replaced

```python
# Wrong
url = cfg["engines"][0]["url"]  # contains literal {keyword}

# Right
url = cfg["engines"][0]["url"].replace("{keyword}", kw_encoded)
```

### Wrong URL encoding

```python
# Wrong
url = f"https://www.baidu.com/s?wd={play}"  # play contains Chinese

# Right
kw_encoded = urllib.parse.quote(f"{play} 剧本 filetype:pdf")
url = f"https://www.baidu.com/s?wd={kw_encoded}"
```

### Submodule not found

```bash
# Verify path
ls find-script/search-engine/config.json
# Should exist; otherwise find-script auto-degrades
```

## Further documentation

- [SKILL.md](../SKILL.md) — full spec
- [README.md](../README.md) — project overview
- [USER_GUIDE.md](../USER_GUIDE.md) — detailed guide
- [FAQ.md](../FAQ.md) — frequently asked questions
- [references/anti-patterns.md](../references/anti-patterns.md) — anti-patterns
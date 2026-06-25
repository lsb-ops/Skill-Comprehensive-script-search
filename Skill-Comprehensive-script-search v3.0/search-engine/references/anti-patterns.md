# Anti-Patterns & Best Practices — Multi Search Engine v2.2.0

## Overview

This document lists **common mistakes** and **recommended practices** to help consumers (find-script or other skills) correctly use this submodule.

---

## Anti-pattern 1: Treating `{keyword}` placeholder as a literal value

### Wrong
```python
import json
cfg = json.load(open('config.json'))
url = cfg['engines'][0]['url']  # string contains literal "{keyword}"
# → Actual request: https://www.baidu.com/s?wd={keyword}
# → Browser ignores it, curl fails directly
```

### Why it's wrong
`{keyword}` is a **placeholder**, not a literal value. Using it directly will cause the search engine to receive a malformed request.

### Right
```python
import urllib.parse
kw = urllib.parse.quote('Thunderstorm script filetype:pdf')
url = cfg['engines'][0]['url'].replace('{keyword}', kw)
# → https://www.baidu.com/s?wd=...
```

---

## Anti-pattern 2: Stuffing raw Chinese/spaces into {keyword}

### Wrong
```bash
# Direct concatenation
url="https://www.baidu.com/s?wd=Thunderstorm script"
# → Will spaces become %20 or %2520? What about the Chinese chars?
```

### Why it's wrong
Different shells / tools handle URL encoding inconsistently:
- bash strings don't auto-encode
- curl doesn't encode by default
- python3 urllib.parse.quote is the standard implementation

### Right
```bash
# Use python3 for standard URL encoding
kw=$(python3 -c "import urllib.parse; print(urllib.parse.quote('Thunderstorm script filetype:pdf'))")
url="https://www.baidu.com/s?wd=${kw}"
```

---

## Anti-pattern 3: Ignoring the region field — using cn engines as global

### Wrong
```python
# Calling Baidu for English scripts
e = next(e for e in cfg['engines'] if e['name'] == 'Baidu')
url = e['url'].replace('{keyword}', kw)
# → Chinese search engine for English scripts; very low hit rate
```

### Why it's wrong
- Chinese search engines have the strongest Chinese index
- English search engines have the strongest English index
- Cross-language search dramatically reduces hit rate

### Right
```python
# Chinese plays: use cn engines
cn_engines = [e for e in cfg['engines'] if e['region'] == 'cn']

# English plays: use global engines
global_engines = [e for e in cfg['engines'] if e['region'] == 'global']
```

---

## Anti-pattern 4: Treating priority as a weight

### Wrong
```python
# Using priority as weighted load balancing
weight = engine['priority']  # higher number = higher weight?
# → Actually, priority 1 is the highest
```

### Why it's wrong
- `priority: 1` = **highest** priority
- `priority: 9` = **lowest** priority
- This is the OPPOSITE semantics from a weight

### Right
```python
# Sort: priority ascending (lower = higher priority)
sorted_engines = sorted(cfg['engines'], key=lambda e: e.get('priority', 99))
```

---

## Anti-pattern 5: Using WolframAlpha as a text search engine

### Wrong
```python
# Searching for a script
url = "https://www.wolframalpha.com/input?i=Hamlet+full+text+filetype:pdf"
# → WolframAlpha returns "Hamlet" knowledge (prince, Shakespeare), not the play text
```

### Why it's wrong
WolframAlpha is a **knowledge computation engine**, good at:
- Math / unit conversion / stocks / weather
- Not good at searching text / web pages / files

### Right
| Task | Use which engine |
|------|------------------|
| Find a script PDF | Google / Baidu / DuckDuckGo |
| Find script author info | WolframAlpha (optional) |
| Computation / conversion | WolframAlpha |

In find-script, WolframAlpha is invoked as one of 16 engines, but **not expected** to return useful scripts.

---

## Anti-pattern 6: Reading config.json from disk every time

### Wrong
```python
# Reading repeatedly in a loop
for play in plays:
    cfg = json.load(open('config.json'))  # reads every time
    ...
```

### Why it's wrong
- The 16-engine config doesn't change
- Repeated IO is wasteful

### Right
```python
# Read once and cache
with open('config.json') as f:
    cfg = json.load(f)

for play in plays:
    # Reuse cfg
    for engine in cfg['engines']:
        url = engine['url'].replace('{keyword}', urllib.parse.quote(play))
```

---

## Anti-pattern 7: Ignoring the submodule's fallback chain

### Wrong
```bash
# Assuming the submodule always exists
test -f find-script/search-engine/config.json || {
  echo "ERROR: submodule not found"
  exit 1
}
```

### Why it's wrong
- The submodule is optional
- find-script has a 3-level fallback chain
- Business should continue normally when the submodule is missing

### Right
```bash
# Graceful degradation
if [ -f find-script/search-engine/config.json ]; then
  CONFIG=find-script/search-engine/config.json
elif [ -f find-script/config.json ]; then
  CONFIG=find-script/config.json
else
  CONFIG=<built-in hardcoded 16 engines>
fi
```

---

## Anti-pattern 8: Running the submodule's tests in production

### Wrong
```bash
# Running tests/test_smoke.sh in CI/CD
./tests/test_smoke.sh
# Expecting it to always pass
```

### Why it's wrong
- test_smoke.sh may include network requests (find-script integration test)
- May fail in restricted network environments

### Right
```bash
# Tiered environments
# 1. Unit tests (no network): this submodule's tests/test_smoke.sh should pass stably
./tests/test_smoke.sh

# 2. Integration tests (with network): find-script/tests/test_engines.sh includes network verification
cd ../find-script
./tests/test_engines.sh    # run in CI
```

---

## Anti-pattern 9: Not syncing find-script when upgrading

### Wrong
```bash
# Added 1 new engine in this submodule
# Now 17 engines
# But didn't sync find-script/scripts/search.sh's builtin_engines()
```

### Why it's wrong
- find-script's fallback chain's last level is the built-in hardcoded 16 engines
- Submodule has 17, local config has 16, built-in has 16
- After fallback, 1 engine is missing

### Right
When upgrading the submodule, sync 3 places:
1. `find-script/search-engine/config.json` (this submodule)
2. `find-script/config.json` (local copy)
3. `find-script/scripts/search.sh`'s `builtin_engines()` function

---

## Anti-pattern 10: Ignoring CHANGELOG and contract changes

### Wrong
```bash
# Didn't read CHANGELOG after upgrading
# Submodule went v2.1 → v2.2; URL templates changed
# find-script still processes per v2.1
```

### Why it's wrong
- v2.2.0 added a `contract` section in metadata.json
- Fields expanded from 3 (name/url/region) to 6 (+ priority/language/description)
- Consumers may assume these fields don't exist and fail

### Right
```bash
# Before upgrading
cat ../CHANGELOG.md    # check changes
diff <(old_cfg) <(new_cfg)    # verify config

# After upgrading
./tests/test_smoke.sh
cd ../find-script && ./tests/test_engines.sh
```

---

## Summary: 10 golden rules

1. **Placeholder must be substituted** — `{keyword}` cannot be passed literally to the search engine
2. **Use python3 for URL encoding** — standard and cross-platform
3. **Pick engines by region** — Chinese plays use cn, English plays use global
4. **priority 1 is highest** — not a weight
5. **WolframAlpha is not for text search** — it's a knowledge computation engine
6. **Cache config.json** — don't read it every loop iteration
7. **3-level fallback chain** — degrade gracefully when submodule is missing
8. **Tiered tests** — unit tests vs integration tests
9. **Sync consumers on upgrade** — submodule + local + built-in fallback, all three places
10. **Read CHANGELOG** — pay attention to contract changes

---

*10 golden rules 🔍 | Multi Search Engine v2.2.0*
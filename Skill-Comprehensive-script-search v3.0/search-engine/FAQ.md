# Multi Search Engine v2.2.0 — Frequently Asked Questions (FAQ)

## Basics

### Q1: What is this skill?
A: It is the **official submodule** of find-script v1.2.0+, providing URL template config for 16 search engines (7 domestic + 9 global). It does not perform fetching itself; all actual work is done by find-script.

### Q2: Can it be used standalone?
A: Yes. This submodule is a pure config + docs type skill; the config file is standard JSON, so any consumer can use it:
```python
import json
cfg = json.load(open('config.json'))
for e in cfg['engines']:
    print(e['name'], e['url'])
```

### Q3: Why 16 engines?
A: 7 domestic engines (Baidu/Bing/360/Sogou/WeChat/Shenma) cover Chinese; 9 global engines (Google/DuckDuckGo/Yahoo/Startpage/Brave/Ecosia/Qwant/WolframAlpha) cover English. 16 is the trade-off between coverage and maintenance cost.

## Integration with find-script

### Q4: How does find-script find this submodule?
A: Through a 3-level fallback chain:
1. `find-script/search-engine/config.json` (this submodule, recommended)
2. `find-script/config.json` (local copy)
3. `find-script/scripts/search.sh` built-in hardcoded 16 engines (fallback)

When this submodule is missing, it auto-degrades gracefully; business logic is unaffected.

### Q5: How does the {keyword} placeholder work?
A: This submodule's URL templates contain `{keyword}` placeholders, which are replaced by the **consumer** (find-script). find-script's `inject_type_keyword()` function is responsible for:
1. Building the full keyword: `${play}+剧本+filetype:pdf` (Chinese) / `${play}+script+filetype:pdf` (English)
2. URL encoding (python3 urllib.parse.quote)
3. Substituting the placeholder

### Q6: Can I modify this submodule's URL templates?
A: Yes, but please note:
- Keep the `{keyword}` placeholder
- Keep the count at 16 engines (or sync with find-script's built-in fallback)
- Sync the test expectations in find-script/tests/test_engines.sh

### Q7: Will a submodule upgrade break find-script?
A: No. find-script's `resolve_engine_config()` is designed as:
- Prefer to read this submodule
- Fall back to local copy if absent
- Finally fall back to built-in

The submodule API contract (`{keyword}` placeholder, engines array) remains stable.

## Configuration

### Q8: Are config.json fields required?
A:
- **Required**: `name` / `url` / `region`
- **Optional**: `priority` / `language` / `description`

find-script/scripts/search.sh only reads `name` / `url` / `region`; other fields are transparent to the consumer.

### Q9: How is the priority field used?
A: Priority 1 is highest, 9 is lowest. find-script may sort by priority in the future; currently it follows JSON array order.

### Q10: Can the region field be changed?
A: Not recommended. The `cn` / `global` classification is what drives find-script's engine dispatch. Changing region will cause find-script to skip that engine.

### Q11: How is the language field used?
A: Indicates the engine's primary language preference (`zh` / `en` / `any`). find-script does not consume it currently; may be used for language-based filtering in the future.

## Usage

### Q12: How do I use this submodule to construct URLs?
A: Three ways:

**Python**
```python
import json, urllib.parse
cfg = json.load(open('config.json'))
kw = urllib.parse.quote('Thunderstorm script filetype:pdf')
for e in cfg['engines']:
    print(e['name'], e['url'].replace('{keyword}', kw))
```

**Bash**
```bash
kw=$(python3 -c "import urllib.parse; print(urllib.parse.quote('Thunderstorm script filetype:pdf'))")
url="https://www.baidu.com/s?wd=${kw}"
```

**JavaScript**
```javascript
const engines = require('./config.json').engines;
const kw = encodeURIComponent('Thunderstorm script filetype:pdf');
engines.forEach(e => console.log(e.name, e.url.replace('{keyword}', kw)));
```

### Q13: Which engine is best for searching Chinese scripts?
A: By experience:
- **Baidu** — most comprehensive Chinese index
- **Bing CN** — Bing China version, Chinese results
- **Sogou WeChat** — the only channel for searching WeChat public-account articles
- **Bing INT** — English results (good for English translations)

### Q14: Which engine is best for searching English scripts?
A: By experience:
- **Google** / **Google HK** — most comprehensive index
- **Startpage** — Google results + privacy
- **DuckDuckGo** — no tracking
- **Brave** — independent index

### Q15: How do I search scripts with WolframAlpha?
A: WolframAlpha is not suited for searching text content; it excels at **structured knowledge computation**. In find-script, it's invoked as one of 16 engines (used as fallback) but typically returns 0 useful results. **It is not part of the main script-search path.**

## Testing

### Q16: How do I test this submodule?
A: Run `tests/test_smoke.sh` (18 tests):
```bash
./tests/test_smoke.sh
```

Test coverage:
- 16-engine config completeness
- URL template validity
- `{keyword}` contract 100% coverage
- find-script integration (host validation)
- Region distribution 7+9

### Q17: How do I verify integration with find-script?
A: Run find-script's tests:
```bash
cd ../find-script
./tests/test_engines.sh    # 22 tests, includes submodule integration
./tests/test_smoke.sh      # 30 tests
```

## Troubleshooting

### Q18: find-script can't find this submodule?
A: Check the path:
```bash
ls find-script/search-engine/config.json
# should exist
```

If absent, search.sh will auto-degrade to local config.json or built-in hardcoded.

### Q19: The {keyword} in URL template wasn't replaced?
A: Only find-script/scripts/search.sh's `inject_type_keyword()` replaces it. If you use this submodule directly, you must replace it yourself:
```bash
url="${url/\{keyword\}/$(url_encode "$keyword")}"
```

### Q20: Tests fail after submodule upgrade?
A: Most likely the engine count changed. Sync find-script/scripts/search.sh's `builtin_engines()` fallback block.

## Contributing

### Q21: How can I contribute?
A: Areas for improvement:
- New engine support
- Expanded advanced-operators reference
- Improved search-strategy docs
- Test coverage

### Q22: Which engines should be added?
A: Common requests:
- **Yandex** — Russian search
- **Naver** — Korean search
- **Yahoo Japan** — Japanese search
- **You.com** — AI search
- **Perplexity** — AI search

Please update config.json and references/ synchronously when adding new engines.

### Q23: Where are the tests?
A: `tests/test_smoke.sh` (18 tests).

Run all:
```bash
./tests/test_smoke.sh
```
# Search Strategy Reference

> find-script v3.0.0 · switch keyword templates by type (`--type`).

## Picking Keywords by Type

`find-play.sh --type <type>` automatically invokes `inject_type_keyword` to inject the right keywords. **The user does not need to write them manually**:

| type | Chinese keyword template | English keyword template |
|------|---------------------------|---------------------------|
| `play` (stage play) | `剧本` | `script` / `play` |
| `opera` (Chinese opera / Western opera / musical) | `戏本,曲谱` | `libretto` / `vocal score` |
| `film` (movie) | `电影剧本,分镜` | `screenplay` / `shooting script` |
| `tv` (television) | `电视剧本,分集` | `teleplay` / `episode script` |

> ⚠️ If the automatic template is not precise enough, you can override it manually with the `--keyword` argument.

---

## Chinese Title Search Strategy

### Round 1: Search title + file type directly

```javascript
// Baidu search for PDF
web_fetch({"url": "https://www.baidu.com/s?wd=雷雨+剧本+filetype:pdf"})

// Bing China search for DOC
web_fetch({"url": "https://cn.bing.com/search?q=雷雨+剧本+filetype:doc&ensearch=0"})
```

### Round 2: Add the author to refine

```javascript
web_fetch({"url": "https://www.baidu.com/s?wd=雷雨+曹禺+完整版+剧本"})
```

### Round 3: Site-specific search (per platform)

```javascript
// Daoke Baba
web_fetch({"url": "https://www.baidu.com/s?wd=雷雨+site:doc88.com"})

// Taodocs
web_fetch({"url": "https://www.baidu.com/s?wd=雷雨+site:taodocs.com"})

// Original Force
web_fetch({"url": "https://www.baidu.com/s?wd=雷雨+site:max.book118.com"})

// Zhihu
web_fetch({"url": "https://www.sogou.com/web?query=雷雨+剧本+site:zhuanlan.zhihu.com"})
```

### Round 4: WeChat article search (auxiliary)

```javascript
web_fetch({"url": "https://wx.sogou.com/weixin?type=2&query=雷雨+剧本+全文"})
```

### Round 5: English international engines (for translations or academic editions)

```javascript
web_fetch({"url": "https://www.google.com/search?q=Thunderstorm+Cao+Yu+script+filetype:pdf"})
```

## English Title Search Strategy

### Round 1: Title + full text + PDF

```javascript
web_fetch({"url": "https://www.google.com/search?q=Hamlet+full+text+filetype:pdf"})
```

### Round 2: Pin to public-domain platforms

```javascript
// Internet Archive
web_fetch({"url": "https://www.google.com/search?q=Hamlet+site:archive.org"})

// Project Gutenberg
web_fetch({"url": "https://www.google.com/search?q=Hamlet+site:gutenberg.org"})
```

### Round 3: Academic resources

```javascript
// Google Scholar
web_fetch({"url": "https://scholar.google.com/scholar?q=Hamlet+Shakespeare+full+text"})

// JSTOR
web_fetch({"url": "https://www.google.com/search?q=Hamlet+site:jstor.org"})
```

### Round 4: University OCW

```javascript
web_fetch({"url": "https://www.google.com/search?q=Hamlet+site:ocw.mit.edu"})
web_fetch({"url": "https://duckduckgo.com/html/?q=Hamlet+site:open.yale.edu"})
```

### Round 5: Chinese translations (auxiliary)

```javascript
web_fetch({"url": "https://www.baidu.com/s?wd=哈姆雷特+中文+剧本+全文+filetype:pdf"})
```

## Theme-Based Search Strategy

### Smart Theme Matching

```javascript
// User: "find a play about AI"
// Auto-build keyword groups

const keywordGroups = [
  "artificial intelligence play script",
  "AI theme theater drama",
  "人工智能 话剧 剧本",
  "robot consciousness play",
  "科技 伦理 话剧"
];

// Search each keyword group in turn
```

### Synonym Expansion

| User input | Expansion |
|------------|-----------|
| 人工智能 (AI) | AI / robot / tech ethics / future |
| 家庭 (family) | family ethics / kinship / family of origin / clan |
| 战争 (war) | war / military / peace / anti-war |
| 爱情 (love) | love / marriage / emotion / romance |

## Advanced Search Operators

| Operator | Purpose | Example |
|----------|---------|---------|
| `site:` | Within a specific site | `site:archive.org Hamlet` |
| `filetype:` | File type | `filetype:pdf` `filetype:doc` |
| `""` | Exact match | `"雷雨"` |
| `-` | Exclude term | `雷雨 -百度文库` |
| `OR` | Either term | `Hamlet OR 哈姆雷特` |
| `*` | Wildcard | `曹禺 * 剧本` |

## Time Filter

| Parameter | Range |
|-----------|-------|
| `tbs=qdr:h` | past 1 hour |
| `tbs=qdr:d` | past 1 day |
| `tbs=qdr:w` | past 1 week |
| `tbs=qdr:m` | past 1 month |
| `tbs=qdr:y` | past 1 year |

Use cases:
- Looking for newly released plays: `tbs=qdr:y` or `tbs=qdr:m`.
- Looking for classical scripts: do not apply a time filter.

## Privacy Engines

Good for academic research or to avoid tracking:
- **DuckDuckGo** — no tracking.
- **Startpage** — Google results + privacy.
- **Brave** — independent index.
- **Qwant** — EU GDPR compliant.

## Failure Retry Strategy

```javascript
async function searchWithRetry(engine, keyword, maxRetries = 2) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const result = await web_fetch({"url": engine.url_template.replace("{keyword}", encodeURIComponent(keyword))});
      if (result.status === 200) return result;
    } catch (e) {
      if (i < maxRetries - 1) {
        await sleep(2000); // wait 2 s
        continue;
      }
    }
  }
  return null;
}
```

## Rate Limiting

- Wait ≥ 1.5 s between two requests to the same engine.
- Different engines can be parallel (recommended 3–4 at a time).
- Overall pace: ≤ 2 requests per second.

## Result Deduplication

```javascript
function dedupeResults(results) {
  const seen = new Set();
  return results.filter(r => {
    const key = r.url.split('?')[0]; // drop query params
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}
```

## Link Reliability Scoring

> Since v2.0, `get_reliability_ext` is centralized in `scripts/lib/types.sh`, with rules by type + domain.

| Domain | Default reliability | Applicable types |
|--------|---------------------|------------------|
| archive.org | ⭐⭐⭐⭐⭐ | All types |
| gutenberg.org | ⭐⭐⭐⭐⭐ | Stage play |
| openlibrary.org | ⭐⭐⭐⭐ | Stage play |
| ctext.org | ⭐⭐⭐⭐⭐ | Opera (classical PD) |
| imslp.org | ⭐⭐⭐⭐⭐ | Opera (PD scores) |
| imsdb.com | ⭐⭐⭐⭐ | Film |
| scriptslug.com / script-o-rama.com | ⭐⭐⭐⭐ | Film |
| doc88.com | ⭐⭐⭐ | All types |
| taodocs.com | ⭐⭐⭐ | All types |
| max.book118.com | ⭐⭐⭐ | All types |
| renrendoc.com | ⭐⭐ | All types |
| baidu.com (wenku) | ⭐ (mostly paid) | All types |
| zhuanlan.zhihu.com | ⭐⭐⭐ | Content community |

> See `references/reliability-scoring.md` for the full scoring rules.

---

## Per-Type Search-Query Examples

### Stage play (Play)

```bash
# Chinese classics
site:doc88.com 雷雨 剧本
site:archive.org Hamlet script

# Modern Chinese plays
site:doc88.com 恋爱的犀牛 孟京辉
```

### Opera / Xiqu / Musical

```bash
# Classical Chinese opera (PD)
site:ctext.org 牡丹亭 戏本
site:ctext.org 长生殿 曲谱

# Western opera
site:imslp.org Carmen opera libretto
site:imslp.org Tosca Puccini vocal score

# Musical
site:archive.org Hamilton musical script
site:gutenberg.org Gilbert Sullivan libretto
```

### Film

```bash
# Early PD films (silent era)
site:archive.org Citizen Kane script
site:archive.org silent film screenplay

# Modern films (study use)
site:imsdb.com Inception screenplay
```

### Television

```bash
# Early PD shows
site:archive.org I Love Lucy script

# Modern shows (user_uploaded)
site:doc88.com 琅琊榜 电视剧本
```

---

*16 engines in concert, so no play / opera / film / TV script can hide 🎭*

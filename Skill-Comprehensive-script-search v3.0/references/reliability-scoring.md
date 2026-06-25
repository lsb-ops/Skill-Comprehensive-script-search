# Link Reliability Scoring

> Since find-script v2.0, the scoring rules live in `get_reliability_ext()` inside `scripts/lib/types.sh`.

## Scoring System (5-point scale)

| Score | Category | Domains (per type) | Reason |
|-------|----------|--------------------|--------|
| ⭐⭐⭐⭐⭐ 5 | Public-domain sources | `archive.org` (all types) · `gutenberg.org` (play) · `ctext.org` (opera) · `imslp.org` (opera/musical) | Fully legal, complete files, stable. |
| ⭐⭐⭐⭐ 4 | Academic resources | `openlibrary.org` (play) · `ocw.mit.edu` / `oyc.yale.edu` / `dramaonlinelibrary.com` (play) · `scholar.google.com` / `jstor.org` (play) · `imsdb.com` (film) · `script-o-rama.com` / `scriptslug.com` (film) | Academic authority / modern study. |
| ⭐⭐⭐ 3 | Document sharing | `doc88.com`, `taodocs.com`, `max.book118.com`, `zhuanlan.zhihu.com` | User upload, quality varies, some paid. |
| ⭐⭐ 2 | Regular content sites | `renrendoc.com`, `book.douban.com` | Limited resources, often not downloadable. |
| ⭐ 1 | Paywalled | `wenku.baidu.com` | Mostly requires VIP, last resort. |
| 0 | Unknown domain | * | Default minimum score. |

## Scoring Logic

```bash
# scripts/lib/types.sh
get_reliability_ext() {
  local url="$1"
  case "$url" in
    # ⭐⭐⭐⭐⭐ PD sources
    *archive.org*|*gutenberg.org*)              echo 5 ;;   # play / film / TV / opera
    *ctext.org*|*imslp.org*)                   echo 5 ;;   # opera / musical PD
    # ⭐⭐⭐⭐ academic + modern plays
    *openlibrary.org*|*ocw.mit.edu*|*oyc.yale.edu*|*dramaonlinelibrary.com*|*scholar.google.com*|*jstor.org*) echo 4 ;;
    *imsdb.com*|*script-o-rama.com*|*scriptslug.com*) echo 4 ;;  # film study use
    # ⭐⭐⭐ user uploads
    *doc88.com*|*taodocs.com*|*max.book118.com*|*zhuanlan.zhihu.com*) echo 3 ;;
    # ⭐⭐ regular
    *renrendoc.com*|*book.douban.com*)         echo 2 ;;
    # ⭐ paywalled
    *wenku.baidu.com*)                         echo 1 ;;
    *)                                         echo 0 ;;
  esac
}
```

## Type-Specific Domains Added in v2.0

| Domain | Score | Type | Notes |
|--------|-------|------|-------|
| ctext.org | 5 | Opera | Chinese Text Project |
| imslp.org | 5 | Opera / musical | International Music Score Library Project |
| imsdb.com | 4 | Film | Modern film study (watch copyright) |
| script-o-rama.com | 4 | Film | Same as above |
| scriptslug.com | 4 | Film | Same as above |

## Sort Strategy

`search.sh` sorts by reliability **descending**; equal-reliability items keep their original order (stable sort).

Typical output:
```
archive.org link           reliability=5  ← priority
gutenberg.org link         reliability=5
openlibrary.org link       reliability=4
doc88.com link             reliability=3
zhuanlan.zhihu.com         reliability=3
wenku.baidu.com            reliability=1  ← last resort
```

## Customizing the Score

If you want to reweight (e.g. favor academic sources more), edit the `get_reliability()` function in `scripts/search.sh`.

### Example: Boost archive.org / gutenberg
```bash
get_reliability() {
  local url="$1"
  # Public-domain + academic
  if [[ "$url" =~ (archive|gutenberg|openlibrary|ocw\.mit|oyc\.yale|dramaonline) ]]; then
    echo 10  # custom high score
  elif [[ "$url" =~ (doc88|taodocs|max\.book118) ]]; then
    echo 5
  ...
  fi
}
```

Note: the `sort` command needs to be adjusted accordingly (`sort -t$'\t' -k4,4 -nr` still works).

## Deduplication Strategy

`search.sh` deduplicates by a **`engine + url` composite key**. This avoids:
- ❌ Old problem: treating `bing_cn` and `bing_int` as duplicates (same host).
- ✅ Current: deduplication is per-engine + per-full-URL.

## Evaluating Search Quality

Indicators that a search was "successful":

| Indicator | Healthy value |
|-----------|---------------|
| Total result count | ≥ 10 |
| High-score count (≥ 4) | ≥ 2 |
| PDF format ratio | ≥ 30% |
| Unique domain count | ≥ 3 |

## Adding a New Domain

When you find a new reliable source (e.g. a university OCW), add it to `get_reliability()`:

```bash
# e.g. Stanford drama resources
*stanford.edu*) echo 4 ;;
```

Or add new metadata in `config.json`.

## Anti-Bot and Rate Limits

Although the scoring system does not handle anti-bot directly, note in practice:

| Engine | Rate limit | Notes |
|--------|-----------|-------|
| Baidu | IP-based | Multiple sequential queries need cookies. |
| Bing | Relatively lenient | Mild anti-bot. |
| Sogou WeChat | Strict | Needs IP proxy. |
| Google | Strict | Frequent requests may trigger CAPTCHA. |
| archive.org | Lenient | Rate limit (10 req/min). |
| gutenberg.org | Lenient | No obvious anti-bot. |

Recommendation: in production, add `sleep 0.5` between requests (`search.sh` does not yet do this; a `--delay` option can be added).

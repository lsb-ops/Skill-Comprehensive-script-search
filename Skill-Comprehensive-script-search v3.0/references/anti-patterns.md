# Anti-Patterns and Best Practices

## Overview

This document lists **common mistakes** and **recommended practices** to help you avoid pitfalls.

---

## ❌ Anti-Pattern 1: Forgetting `--yes` in Claude Code

### Wrong
```bash
# In Claude Code / non-TTY environments
./scripts/find-play.sh "Hamlet" --save-path ~/Desktop
# Hangs on "Confirm? (y/N)"
```

### Why it's a problem
`download.sh` and `find-play.sh` use interactive `read -p` prompts. Claude Code's stdin is not a TTY, so `read` blocks forever.

### ✅ Correct
```bash
# Always pass --yes
./scripts/find-play.sh "Hamlet" --save-path ~/Desktop --auto-download 3 --yes

# Or set the environment variable
export FIND_PLAY_YES=1
./scripts/find-play.sh "Hamlet" --save-path ~/Desktop
```

---

## ❌ Anti-Pattern 2: Using `search.sh` as a downloader

### Wrong
```bash
# Expecting search.sh to download files
./scripts/search.sh "雷雨" zh
# Then complaining: "Why didn't it save to ~/Desktop?"
```

### Why it's a problem
`search.sh` only searches, it doesn't download. By design it's step 3 of the 6-step workflow.

### ✅ Correct
- **Search only** → `search.sh`
- **Download only** → `download.sh`
- **Search + download + analyze** → `find-play.sh` (recommended)

```bash
# One-shot end-to-end
./scripts/find-play.sh "雷雨" --author 曹禺 \
  --save-path ~/Desktop/caoyu --auto-download 3 --analyze --yes
```

---

## ❌ Anti-Pattern 3: Bypassing copyright when downloading scripts

### Wrong
```bash
# Use cookies / a paid account to bypass Baidu Wenku
./scripts/download.sh "https://wenku.baidu.com/..." ~/Desktop --user-agent "..."

# Or use --type=play to forcibly search for film / TV (bypassing the type)
./scripts/find-play.sh "Inception script" --type play
# Expected: Inception screenplay. Actual: keywords became "script" / "剧本", returned stage-play resources.
```

### Why it's a problem
- Legal risk (copyright infringement).
- Violates the Skill agreement (metadata.json declares `copyright_compliance: user_responsibility`).
- Anti-bot defenses keep escalating — today's bypass stops working tomorrow.
- Type misuse mismatches results (looking for a film but using stage-play keywords).

### ✅ Correct
Since v2.0 **every result carries a `copyright` tag**:

| Tag | Meaning | Recommended action |
|-----|---------|--------------------|
| `pd` | Public domain | Safe to download by default. |
| `user_uploaded` | User upload | Verify the uploader's authorization. |
| `copyrighted` | Still under copyright | For study and quotation only; do not download in bulk. |
| `unknown` | Tag unknown | Verify manually. |

Choose sources by type × copyright:

| Type | Recommended source | Default copyright |
|------|--------------------|-------------------|
| Classical stage play | archive.org, gutenberg.org | pd |
| Modern stage play | doc88.com, taodocs.com | user_uploaded |
| Classical Chinese opera | ctext.org, imslp.org | pd |
| Modern opera | doc88.com | user_uploaded |
| Early film (pre-1929) | archive.org | pd |
| Modern film | IMSDb, Script Slug | copyrighted |
| TV 1950s | archive.org | pd |
| Modern TV | doc88.com (user_uploaded) | user_uploaded / copyrighted |

---

## ❌ Anti-Pattern 4: Trying to read downloaded files manually

### Wrong
```bash
# Downloaded 雷雨.pdf
# Use the Read tool on the PDF directly
Read: ~/Desktop/雷雨.pdf
# Error: "PDF is binary"
```

### Why it's a problem
The Read tool has weak support for PDF. DOCX is ZIP-compressed, so it's even worse.

### ✅ Correct
Use `analyze.sh` to extract the text:
```bash
# Auto-detect + extract
./scripts/analyze.sh ~/Desktop/雷雨.pdf

# Or extract and save as TXT
./scripts/analyze.sh ~/Desktop/雷雨.pdf --save-txt /tmp/leiyu.txt

# Then use Read on /tmp/leiyu.txt
```

---

## ❌ Anti-Pattern 5: Treating `analyze.sh` output as the "final analysis"

### Wrong
```bash
./scripts/analyze.sh play.pdf
# Sees the skeleton and submits it, expecting a full analysis report
```

### Why it's a problem
`analyze.sh` is designed as a **skeleton generator**:
- ✅ Auto-detects: characters, acts.
- ❌ Cannot auto-generate: theme, conflict, style (requires LLM interpretation).

### ✅ Correct
Skeleton + LLM interpretation:
```bash
# 1. Run analyze.sh to get skeleton + text
./scripts/analyze.sh play.pdf > /tmp/analysis.md

# 2. Hand /tmp/analysis.md to the LLM, which fills the 5 dims based on the text
# (produces the deep analysis)
```

Or just use `find-play.sh --analyze` to chain the flow automatically.

---

## ❌ Anti-Pattern 6: Hardcoding the title into the script

### Wrong
```bash
# Hard-coding in an automation script
./scripts/search.sh "雷雨" zh > results.tsv
# The next day you want Hamlet, but you have to edit the script
```

### ✅ Correct
Parameterize:
```bash
PLAY="$1"
LANG="${2:-auto}"
./scripts/search.sh "$PLAY" "$LANG" --quiet
```

---

## ❌ Anti-Pattern 7: Ignoring the reliability score

### Wrong
```bash
# Picking the first result blindly after searching
./scripts/search.sh "Hamlet" en --no-fetch | head -1
# You picked the first link (could be an ad-laden site)
```

### Why it's a problem
The scoring system already filters for you:
- Score 5: archive.org / gutenberg.org (stable).
- Score 1: wenku.baidu.com (mostly paid).

The first result is not necessarily the best.

### ✅ Correct
```bash
# Trust the score-based sort (built in)
./scripts/search.sh "Hamlet" en --no-fetch | head -10
# Default sort: reliability descending

# Or filter explicitly
./scripts/search.sh "Hamlet" en --no-fetch --json | \
  python3 -c "
import json, sys
data = json.load(sys.stdin)
for d in data:
    if d['reliability'] >= 4:
        print(d['url'])
"
```

---

## ❌ Anti-Pattern 8: Running `find-play.sh --analyze` in production

### Wrong
```bash
# In CI/CD
./scripts/find-play.sh "Hamlet" --auto-download 1 --analyze --yes
# Expecting stable output
```

### Why it's a problem
- Network dependency (Google is unreliable in mainland China).
- Anti-bot risk (frequent requests trigger CAPTCHAs).
- PDF extraction depends on external tools.

### ✅ Correct
Step-by-step with error handling:
```bash
set -e
SEARCH_RESULT=$(./scripts/search.sh "Hamlet" en --quiet --no-fetch) || {
  echo "Search failed" >&2
  exit 1
}

# Only high-scored links
URL=$(echo "$SEARCH_RESULT" | awk -F'\t' '$4 >= 4 {print $2; exit}')

# Retry on failure
for i in 1 2 3; do
  if ./scripts/download.sh "$URL" /tmp "hamlet.pdf" --yes; then
    break
  fi
  sleep 5
done

# Analyze only at the end
[ -f /tmp/hamlet.pdf ] && ./scripts/analyze.sh /tmp/hamlet.pdf
```

---

## ❌ Anti-Pattern 9: Treating `tests/` as "optional"

### Wrong
```bash
# Modified search.sh without running tests
# Pushed directly
```

### Why it's a problem
Regression risk: previously-passing URL templates may have been broken by a sed/awk edit.

### ✅ Correct
```bash
# Always run after editing
./tests/test_smoke.sh && ./tests/test_engines.sh && SKIP_NETWORK=1 ./tests/test_download.sh
# Expected: 289/289 passing

# If you changed search.sh, also run the network test
./tests/test_download.sh
```

---

## ❌ Anti-Pattern 10: Ignoring the CHANGELOG

### Wrong
```bash
# Bumping the version number without updating CHANGELOG
echo "1.2.0" > version
# Users have no idea what changed
```

### ✅ Correct
On every release:
1. Update the `version` field in SKILL.md / _meta.json / metadata.json.
2. Add a CHANGELOG.md entry.
3. Run the full test suite.
4. Commit.

---

## Summary: 10 Golden Rules

1. **Always pass `--yes`** in non-TTY environments.
2. **Use the right tool**: search with `search.sh`, download with `download.sh`, end-to-end with `find-play.sh`.
3. **Copyright first**: archive.org / gutenberg.org (stage play / film / TV) and ctext.org / imslp.org (opera).
4. **PDFs go through `analyze.sh`**, not the Read tool on binary.
5. **Skeleton + LLM**: `analyze.sh` output is a skeleton, not a finished analysis.
6. **Parameterize input**, do not hard-code (and pay attention to whether `--type` matches the title).
7. **Trust the reliability score**.
8. **Step-by-step in production** with independent error handling.
9. **Always run tests after editing** (v3.0.0: 289/289).
10. **Write a CHANGELOG entry on every release**.

---

## v2.0 New Anti-Patterns

### ❌ Anti-Pattern 11: Ignoring `--type` and letting the default `play` mismatch the result

### Wrong
```bash
# Looking for the Citizen Kane screenplay, but forgot --type
./scripts/find-play.sh "Citizen Kane" --save-path ~/movies
# The keyword becomes "script" / "剧本", returning stage-play results
```

### ✅ Correct
Specify the type explicitly:
```bash
./scripts/find-play.sh "Citizen Kane" --type film --language en --save-path ~/movies
```

### Auto-detect
```bash
# Let the script infer the type heuristically (e.g. "Episode N" → tv)
./scripts/find-play.sh "Hamlet S01E01" --type auto --yes
```

### ❌ Anti-Pattern 12: Bulk-downloading copyrighted content without filtering

### Wrong
```bash
# Download everything from the results
./scripts/find-play.sh "Modern Movie Script" --auto-download 10 --yes
# Just pulled 10 resources tagged copyright=copyrighted
```

### ✅ Correct
Filter by copyright:
```bash
# Only pd + user_uploaded
./scripts/find-play.sh "Modern Movie Script" --filter-copyright pd,user_uploaded --auto-download 3 --yes

# Or filter from JSON after searching
./scripts/search.sh "Modern Movie Script" --json | \
  python3 -c "
import json, sys
data = json.load(sys.stdin)
for d in data:
    if d['copyright'] in ('pd', 'user_uploaded'):
        print(d['url'])
"
```

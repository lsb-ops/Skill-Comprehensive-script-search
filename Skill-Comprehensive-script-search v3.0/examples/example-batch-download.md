# find-script v3.0.0 — Advanced Example: Batch Download a Script Library

> Download a batch of classic scripts with a single command to build a local script library.

## Scenario

You are a theatre director wanting to download the following scripts as a reference library:

| Title | Author | Language | Preferred source |
|-------|--------|----------|------------------|
| Thunderstorm (雷雨) | Cao Yu | zh-CN | archive.org |
| Teahouse (茶馆) | Lao She | zh-CN | doc88.com |
| The Field (原野) | Cao Yu | zh-CN | taodocs.com |
| Hamlet | Shakespeare | en | gutenberg.org |
| Death of a Salesman | Arthur Miller | en | archive.org |
| A Doll's House | Ibsen | en | gutenberg.org |

## Method A: Batch TSV File

### 1. Prepare batch.tsv

```bash
cat > ~/scripts/play-batch.tsv <<'EOF'
雷雨	曹禺	zh
茶馆	老舍	zh
原野	曹禺	zh
Hamlet	Shakespeare	en
Death of a Salesman	Arthur Miller	en
A Doll's House	Ibsen	en
EOF
```

Format: `title<TAB>author<TAB>language`.

### 2. Write a batch orchestrator script

```bash
#!/bin/bash
# batch-download.sh - batch download scripts
set -e
SAVE_PATH="$HOME/PlayLibrary"
mkdir -p "$SAVE_PATH"

while IFS=$'\t' read -r play author lang; do
  echo ""
  echo "=========================================="
  echo "📚 Title: $play ($author) [$lang]"
  echo "=========================================="

  # 1) Search
  cd /path/to/find-script
  SEARCH_OUT=$(./scripts/search.sh "$play" "$lang" --max-results 5 --quiet)

  # 2) Take the highest-scored link
  URL=$(echo "$SEARCH_OUT" | awk -F'\t' '$4 >= 3 {print $2; exit}')

  if [ -z "$URL" ]; then
    echo "⚠️  No high-score source found, skipping"
    continue
  fi

  # 3) Download
  FILENAME="${play// /_}.pdf"
  ./scripts/download.sh "$URL" "$SAVE_PATH" "$FILENAME" --yes || {
    echo "⚠️  Download failed: $play"
    continue
  }

  # 4) 5-dim analysis
  [ -f "$SAVE_PATH/$FILENAME" ] && \
    ./scripts/analyze.sh "$SAVE_PATH/$FILENAME" > "$SAVE_PATH/${play// /_}-analysis.md" --quiet

  echo "✅ Done: $play"
done < ~/scripts/play-batch.tsv

echo ""
echo "🎭 Script library established: $SAVE_PATH"
```

### 3. Run

```bash
chmod +x batch-download.sh
./batch-download.sh
```

## Method B: Loop with find-play.sh

```bash
SAVE_PATH=~/PlayLibrary
mkdir -p "$SAVE_PATH"

for entry in "雷雨 曹禺 zh" "茶馆 老舍 zh" "原野 曹禺 zh" \
             "Hamlet Shakespeare en" "Death of a Salesman Arthur_Miller en"; do
  set -- $entry
  PLAY="$1"
  AUTHOR="$2"
  LANG="$3"

  ./scripts/find-play.sh "$PLAY" \
    --author "$AUTHOR" \
    --language "$LANG" \
    --save-path "$SAVE_PATH" \
    --auto-download 1 \
    --analyze \
    --yes
done
```

## Method C: Python Integration (Advanced)

```python
#!/usr/bin/env python3
"""Batch download + analysis for a script library."""
import subprocess
import json
from pathlib import Path

SKILL_DIR = Path("/path/to/find-script")
LIBRARY = Path.home() / "PlayLibrary"
LIBRARY.mkdir(exist_ok=True)

# Script catalog
plays = [
    ("雷雨", "曹禺", "zh"),
    ("茶馆", "老舍", "zh"),
    ("原野", "曹禺", "zh"),
    ("Hamlet", "Shakespeare", "en"),
    ("Death of a Salesman", "Arthur Miller", "en"),
]

for play, author, lang in plays:
    print(f"\n📚 {play} ({author}) [{lang}]")

    # 1) Search
    result = subprocess.run(
        [str(SKILL_DIR / "scripts/search.sh"), play, lang,
         "--max-results", "5", "--json", "--quiet"],
        capture_output=True, text=True, check=True
    )
    results = json.loads(result.stdout)

    # 2) Take the high-score link
    best = next((r for r in results if r["reliability"] >= 3), None)
    if not best:
        print(f"  ⚠️  No high-score source found")
        continue

    # 3) Download
    ext = best["format"] if best["format"] != "unknown" else "pdf"
    target = LIBRARY / f"{play.replace(' ', '_')}.{ext}"
    subprocess.run(
        [str(SKILL_DIR / "scripts/download.sh"), best["url"],
         str(LIBRARY), target.name, "--yes"],
        check=False
    )

    if target.exists():
        # 4) Analyze
        subprocess.run(
            [str(SKILL_DIR / "scripts/analyze.sh"), str(target),
             "--save-txt", str(LIBRARY / f"{play.replace(' ', '_')}.txt")],
            check=False
        )
        print(f"  ✅ Done: {target}")
```

## Resume from Interruption

If a batch job is interrupted (network drop, timeout), re-running the script above is safe:
- ✅ Already-downloaded files are skipped automatically.
- ✅ Already-analyzed .txt files are not regenerated.
- ✅ Only failed items are retried.

## Performance Reference

| Count | Serial | Parallel (multiple workers) |
|-------|--------|------------------------------|
| 5 scripts | 5–10 min | 2–3 min |
| 20 scripts | 20–40 min | 5–10 min |
| 100 scripts | 1.5–3 h | 20–30 min |

## Notes

⚠️ **1. Rate limit**: add `--delay 2` in batch mode to avoid anti-bot triggers.
⚠️ **2. Copyright**: only download public-domain scripts.
⚠️ **3. Error handling**: use `set +e` or `|| continue` to avoid all-or-nothing failures.
⚠️ **4. Logging**: add `tee batch.log` to record output.

## Advanced: Multi-threaded Download

```bash
# GNU parallel (recommended)
cat ~/scripts/play-batch.tsv | \
  parallel -j 4 --colsep '\t' '
    cd /path/to/find-script
    URL=$(./scripts/search.sh {1} {3} --max-results 3 --quiet | awk -F"\t" "\$4 >= 3 {print \$2; exit}")
    [ -n "$URL" ] && ./scripts/download.sh "$URL" ~/PlayLibrary "{1}.pdf" --yes
  '
```

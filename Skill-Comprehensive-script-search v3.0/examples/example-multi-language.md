# find-script v3.0.0 — Advanced Example: Bilingual Library

> Find both the Chinese and English version of a script and build a bilingual library.

## Scenario

You are doing translation research or cross-cultural drama analysis and need both versions of a work:
- Chinese version (e.g. a Chinese translation of *Hamlet*).
- English version (Shakespeare's original).

## Approach

```
Title: Hamlet
  ├─ zh mode: search "哈姆雷特" for the Chinese translation
  └─ en mode: search "Hamlet" for the original
```

## Example 1: Shakespeare's Complete Works

```bash
# Prepare a list
cat > shakespeare.tsv <<'EOF'
Hamlet	哈姆雷特
Macbeth	麦克白
Othello	奥赛罗
King Lear	李尔王
Romeo and Juliet	罗密欧与朱丽叶
EOF

# Batch download both English and Chinese
while IFS=$'\t' read -r en_name zh_name; do
  echo "📚 $en_name / $zh_name"

  # English original
  ./scripts/find-play.sh "$en_name" \
    --language en \
    --save-path ~/BilingualLibrary/en \
    --auto-download 1 --yes

  # Chinese translation
  ./scripts/find-play.sh "$zh_name" \
    --language zh \
    --save-path ~/BilingualLibrary/zh \
    --auto-download 1 --yes
done < shakespeare.tsv
```

## Example 2: Cao Yu vs Arthur Miller (Modern Drama Comparison)

```bash
# Cao Yu (modern Chinese)
./scripts/find-play.sh "雷雨" --author "曹禺" --language zh \
  --save-path ~/Comparison/Chinese --auto-download 1 --analyze --yes

./scripts/find-play.sh "日出" --author "曹禺" --language zh \
  --save-path ~/Comparison/Chinese --auto-download 1 --analyze --yes

# Arthur Miller (modern American)
./scripts/find-play.sh "Death of a Salesman" --author "Arthur Miller" --language en \
  --save-path ~/Comparison/American --auto-download 1 --analyze --yes

./scripts/find-play.sh "The Crucible" --author "Arthur Miller" --language en \
  --save-path ~/Comparison/American --auto-download 1 --analyze --yes
```

## Example 3: The Three Greek Tragedians

```bash
SAVE=~/GreekTragedy
mkdir -p "$SAVE/en" "$SAVE/zh"

# Sophocles
for play in "Oedipus Rex" "Antigone" "Ajax"; do
  ./scripts/find-play.sh "$play" --language en \
    --save-path "$SAVE/en" --auto-download 1 --yes
done

# Chinese title counterparts
for play in "俄狄浦斯王" "安提戈涅" "埃阿斯"; do
  ./scripts/find-play.sh "$play" --language zh \
    --save-path "$SAVE/zh" --auto-download 1 --yes
done
```

## Example 4: Python Orchestration (Recommended)

```python
#!/usr/bin/env python3
"""Batch download for a bilingual script library."""
import subprocess
from pathlib import Path

SKILL = Path("/path/to/find-script")
LIB = Path.home() / "BilingualLibrary"

# (English title, Chinese title, English author, Chinese author)
plays = [
    ("Hamlet", "哈姆雷特", "Shakespeare", "莎士比亚"),
    ("Macbeth", "麦克白", "Shakespeare", "莎士比亚"),
    ("A Doll's House", "玩偶之家", "Ibsen", "易卜生"),
    ("Death of a Salesman", "推销员之死", "Arthur Miller", "阿瑟·米勒"),
    ("The Crucible", "萨勒姆的女巫", "Arthur Miller", "阿瑟·米勒"),
]

for en, zh, en_author, zh_author in plays:
    print(f"\n📚 {en} / {zh}")

    # English
    print("  → English original")
    subprocess.run([
        str(SKILL / "scripts/find-play.sh"), en,
        f"--author={en_author}",
        "--language", "en",
        "--save-path", str(LIB / "en"),
        "--auto-download", "1", "--yes"
    ], check=False)

    # Chinese
    print("  → Chinese translation")
    subprocess.run([
        str(SKILL / "scripts/find-play.sh"), zh,
        f"--author={zh_author}",
        "--language", "zh",
        "--save-path", str(LIB / "zh"),
        "--auto-download", "1", "--yes"
    ], check=False)
```

## Advanced: Diff Analysis with JSON Output

```bash
# Search both languages and dump JSON
./scripts/search.sh "Hamlet" en --json --quiet > hamlet-en.json
./scripts/search.sh "哈姆雷特" zh --json --quiet > hamlet-zh.json

# Compare with jq
jq -s 'add | group_by(.url) | map({url: .[0].url, sources: map(.engine)})' \
  hamlet-en.json hamlet-zh.json
```

## Academic Research: Version Comparison Table

```bash
# Output the 5-dim analysis to a markdown table
echo "| Title | Theme | Conflict | Style |" > bilingual-analysis.md
echo "|-------|-------|----------|-------|" >> bilingual-analysis.md

for play in "Hamlet" "Macbeth" "Othello"; do
  ./scripts/analyze.sh ~/BilingualLibrary/en/${play}.pdf --quiet > /tmp/${play}-en.md
  theme=$(grep -A 1 "\[Theme\]" /tmp/${play}-en.md | tail -1)
  echo "| $play (en) | $theme | ... | ... |" >> bilingual-analysis.md
done
```

## Notes

⚠️ **1. Translation variety**: Chinese translations come in many versions (Zhu Shenghao, Liang Shiqiu, Bian Zhilin, etc.).
⚠️ **2. Naming differences**: an English title may have multiple Chinese translations (e.g. *Hamlet* / 哈姆雷特 / 王子复仇记).
⚠️ **3. Source split**: English versions are mostly on gutenberg.org / archive.org; Chinese versions are mostly on doc88 / taodocs.
⚠️ **4. Copyright differences**: modern works need copyright attention in both languages.
⚠️ **5. Search strategy**:
   - English first: archive.org / gutenberg.org.
   - Chinese first: doc88 / taodocs + author name.
   - Pass `--author` to improve hit rate.

## Performance Reference

| Task | Serial | 4-worker parallel |
|------|--------|-------------------|
| 5 scripts, bilingual (10 files) | 10–20 min | 3–5 min |
| 20 scripts, bilingual (40 files) | 40–80 min | 10–20 min |
| Shakespeare complete (37 plays) | 60–120 min | 15–30 min |

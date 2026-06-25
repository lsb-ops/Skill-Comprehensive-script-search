# References

This directory contains the detailed reference documentation for the **find-script v3.0.0** skill.

## Documents

| Document | Content | When to read |
|----------|---------|--------------|
| [search-strategies.md](search-strategies.md) | 16-engine search strategy, keyword templates (per type), advanced operators | When you want to optimize search. |
| [drama-sources.md](drama-sources.md) | Global script-source catalog (per type) with ratings | When you need to know which platform hosts classical / modern scripts. |
| [analysis-framework.md](analysis-framework.md) | Index of the 4 per-type 5-dim analysis frameworks | When you want to customize the analysis dimensions. |
| [analysis-frameworks/](analysis-frameworks/) | v2.0: 4 independent frameworks for play / opera / film / tv | When you want to dig into one type's methodology. |
| [text-extraction.md](text-extraction.md) | PDF/DOCX/EPUB text-extraction toolchain (per type) | When text extraction fails. |
| [reliability-scoring.md](reliability-scoring.md) | Link reliability scoring rules (per-type domains) | When you want to tune search-result priority. |
| [troubleshooting.md](troubleshooting.md) | Common errors and how to investigate (with v2.0 type-related cases) | When a script misbehaves. |
| [anti-patterns.md](anti-patterns.md) | 12 anti-patterns + golden rules | When you want to avoid common pitfalls. |

## Suggested Reading Order

1. **New users**: read SKILL.md → run `tests/test_smoke.sh` → look at `examples/example-en.md`.
2. **Intermediate users**: `search-strategies.md` → `reliability-scoring.md` → `anti-patterns.md`.
3. **Multi-type development**: `analysis-frameworks/` (4 independent frameworks, pick by type).
4. **When scripts fail**: `troubleshooting.md` → `text-extraction.md`.
5. **Code review**: `anti-patterns.md`.

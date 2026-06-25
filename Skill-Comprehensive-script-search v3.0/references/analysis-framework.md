# 5-Dim Analysis Framework Index

> find-script v3.0.0: 4 type-tailored analysis frameworks.

## Overview

This skill ships with 4 independent 5-dim analysis frameworks, one per script type. Dimensions 1 (Theme) and 2 (Characters) are shared across all types, while **dimension 3 (structural unit)** and **dimension 5 (style)** switch per type:

| Type | type value | 5-dim framework | Details |
|------|------------|-----------------|---------|
| Stage play | `play` | Theme / Characters / **Acts+Scenes** / Conflict / **Style (school)** | [play.md](analysis-frameworks/play.md) |
| Opera | `opera` | Theme / Characters / **Scenes+Arias** / Conflict / **Vocal styles** | [opera.md](analysis-frameworks/opera.md) |
| Film | `film` | Theme / Characters / **Scenes** / Conflict / **Audiovisual+Genre** | [film.md](analysis-frameworks/film.md) |
| Television | `tv` | Theme / Characters / **Episodes** / Conflict / **Series structure+Genre** | [tv.md](analysis-frameworks/tv.md) |

## Shared Dimensions (all 4 types)

### Dimension 1: Theme

- Core proposition
- Values
- Era / context
- Key imagery

### Dimension 2: Characters

- Name and identity
- Defining traits
- Character arc
- Functional role

### Dimension 4: Conflict

- External conflict
- Internal conflict
- Core contradiction
- Turning points

## Per-Type Differentiating Dimensions

See each type's framework doc:
- [Stage play → Acts+Scenes + Style (school)](analysis-frameworks/play.md)
- [Opera → Scenes+Arias + Vocal styles](analysis-frameworks/opera.md)
- [Film → Scenes + Audiovisual+Genre](analysis-frameworks/film.md)
- [Television → Episodes + Series structure+Genre](analysis-frameworks/tv.md)

## How to Use

```bash
# Auto-select the framework by type
./scripts/analyze.sh <file> --type play    # stage play
./scripts/analyze.sh <file> --type opera   # Chinese opera / Western opera / musical
./scripts/analyze.sh <file> --type film    # film
./scripts/analyze.sh <file> --type tv      # television
./scripts/analyze.sh <file> --type auto    # filename-based heuristic
```

Or via the `find-play.sh` end-to-end orchestrator:
```bash
./scripts/find-play.sh "Hamlet" --type play --analyze --save-path ~/lib
```

## Analysis Depth

| Depth | Use case | Length |
|-------|----------|--------|
| `brief` | Quick orientation | 200–500 words |
| `standard` (default) | Study and research | 500–1500 words |
| `academic` | Paper writing | 1500+ words |

---

*find-script v3.0.0 · 4 types × 5 dims × 3 depths = flexible skeleton* 🎭

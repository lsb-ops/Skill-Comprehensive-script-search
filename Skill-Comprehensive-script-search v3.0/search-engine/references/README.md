# References directory

This directory contains detailed reference docs for the Multi Search Engine (multi-search-engine v2.2.0) submodule.

## Document list

| Document | Contents | When to use |
|----------|----------|-------------|
| [advanced-search.md](advanced-search.md) | Deep search strategies for 7 domestic engines (Baidu/Bing/360/Sogou/WeChat/Shenma) | Deepen your understanding of Chinese search optimization |
| [international-search.md](international-search.md) | Deep search strategies for 9 international engines (Google/DuckDuckGo/Yahoo/Startpage/Brave/Ecosia/Qwant/WolframAlpha) | Deepen your understanding of English/global search |
| [anti-patterns.md](anti-patterns.md) | 10 anti-patterns + golden rules | Avoid common pitfalls |

## Suggested reading order

1. **New user**: Read [SKILL.md](../SKILL.md) first → look at [config.json](../config.json) → run [../tests/test_smoke.sh](../tests/test_smoke.sh)
2. **Integrator**: SKILL.md "Contract with find-script" → [../README.md](../README.md) → advanced-search.md or international-search.md
3. **Using this submodule directly**: advanced-search.md → international-search.md → anti-patterns.md
4. **Troubleshooting**: anti-patterns.md

## Document relationship diagram

```
SKILL.md (main definition)
   │
   ├── Contract with find-script ──> find-script/scripts/search.sh (consumer)
   │
   ├── config.json (16 engine URL templates)
   │     │
   │     └── {keyword} contract
   │
   ├── references/
   │     ├── advanced-search.md (7 domestic engines)
   │     ├── international-search.md (9 international engines)
   │     └── anti-patterns.md (10 anti-patterns)
   │
   ├── tests/test_smoke.sh (18 tests)
   │
   └── examples/example-usage.md
```
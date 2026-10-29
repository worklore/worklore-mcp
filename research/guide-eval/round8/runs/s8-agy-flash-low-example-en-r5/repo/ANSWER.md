# Cache Optimization for Memory Writes

## Changes Made

In [bot.py](file:///tmp/h-ErIukq/bot.py), updated `build_system(a, today)` to split the system prompt into two separate cached text blocks instead of a single merged block:

1. **Static Instruction Block**: Contains `INSTRUCTIONS` with `cache_control: {"type": "ephemeral"}`. This block is byte-identical across all athletes, messages, and dates, keeping the large instruction prompt cached regardless of athlete context changes.
2. **Volatile Context Tail**: Contains `athlete_context(a, today)` (date, athlete info, zones, goal, long-term memory facts, and language) with `cache_control: {"type": "ephemeral"}`.

When `save_fact` writes a new fact to `a.facts`, only the second block's cache prefix is invalidated. The static instruction block remains cached, avoiding the penalty of paying full price to re-cache the entire system prompt.

---

## Colleague's Note: Applicable vs. Non-Applicable Parts

### What Applied
- **Two `cache_control: {"type": "ephemeral"}` markers**: Splitting `system` into two text blocks (Step 1) — the static instructions prefix and the volatile tail (athlete profile, date, long-term facts). This directly solved the issue where `save_fact` invalidated the static instruction cache.
- **Prefix cache understanding**: Utilizing the knowledge that Anthropic caching works as a prefix hash, ensuring the static invariant block comes first before any dynamic/volatile context.

### What Did Not Apply (or Was Already in Place)
- **Tool filtering adjustments**: The colleague noted tool schema grouping and keyword filtering. In this codebase, tool filtering by keywords was already implemented in March (`select_tools`), with core tools always present. As noted in `NOTES.md` and the note itself, no changes were needed here.
- **Top-N fact selection**: The colleague discussed rejecting top-N fact selection to avoid per-message prompt variation. This codebase was already loading all facts sequentially without dynamic subsetting, so no change was needed.
- **Usage tracking**: The codebase already logs `cache_creation_input_tokens` and `cache_read_input_tokens` on each round in `log_usage` (`logs/usage.jsonl`), so verification and logging infrastructure was already present.

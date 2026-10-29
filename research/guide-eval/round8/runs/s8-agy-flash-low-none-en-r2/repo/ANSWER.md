# Prompt Caching Fix for Memory Writes

## Problem
In `bot.py`, `build_system` previously combined static coaching instructions (`INSTRUCTIONS`) and dynamic per-athlete context (`athlete_context(a, today)`, which contains long-term facts, dates, etc.) into a single text block with `"cache_control": {"type": "ephemeral"}`:

```python
text = INSTRUCTIONS + "\n\n" + athlete_context(a, today)
return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]
```

Whenever the bot called `save_fact`, a new fact was appended to `a.facts` and written to `data/athletes.json`. On the next API call (such as round 2 of a tool call loop or subsequent messages), `athlete_context(a, today)` changed. Because prompt caching requires an exact byte-for-byte prefix match and both static rules and dynamic context were concatenated into the same block, modifying `athlete_context` invalidated the cache for the entire combined block (~1000+ tokens). Consequently, `cache_read_input_tokens` dropped to 0 and the full system prompt had to be re-cached (`cache_creation_input_tokens`).

## Changes Made
In `bot.py`, `build_system(a, today)` was updated to separate the system prompt into two distinct content blocks:
1. **Static instructions block**: Contains `INSTRUCTIONS` with `"cache_control": {"type": "ephemeral"}`.
2. **Dynamic athlete context block**: Contains `athlete_context(a, today)` without `cache_control`.

```python
def build_system(a, today):
    # Split system prompt into static instructions (cached) and dynamic athlete context.
    return [
        {"type": "text", "text": INSTRUCTIONS, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": athlete_context(a, today)},
    ]
```

## Result
Anthropic evaluates prompt cache prefixes sequentially: `tools -> system -> messages`.
With the static `INSTRUCTIONS` isolated as the first block in the system array and marked with `cache_control`, its cached prefix remains stable across requests. When `save_fact` adds a new fact to `athlete_context`, only the subsequent dynamic block changes, preserving cache hits on the static instructions.

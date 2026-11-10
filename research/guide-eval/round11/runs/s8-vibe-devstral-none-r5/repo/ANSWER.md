# Fix for System Prompt Caching with Long-Term Memory

## Problem
Every `save_fact` call was causing the entire system prompt to be reprocessed at full price, as seen in `logs/usage.jsonl` where `cache_creation_input_tokens` spikes after each memory write.

The root cause: `build_system()` was concatenating the static `INSTRUCTIONS` with the dynamic `athlete_context(a, today)` into a single system message block. When `save_fact` modified `a.facts`, the `athlete_context` changed, which changed the entire system prompt text, causing a cache miss for the static instructions.

## Solution
Split the system prompt into two separate blocks in `build_system()`:

1. **Static INSTRUCTIONS** - passed as a plain text block without `cache_control`, allowing it to be cached with a stable key
2. **Dynamic athlete_context** - passed with `cache_control: {"type": "ephemeral"}`, explicitly marked as non-cacheable

This way, the static instructions (which never change) maintain a stable cache key, while the athlete-specific context (which changes with `save_fact`) is explicitly ephemeral and doesn't evict the static portion from cache.

## Change Made
In `bot.py`, modified the `build_system()` function:

```python
# Before:
def build_system(a, today):
    text = INSTRUCTIONS + "\n\n" + athlete_context(a, today)
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]

# After:
def build_system(a, today):
    return [
        {"type": "text", "text": INSTRUCTIONS},
        {"type": "text", "text": athlete_context(a, today), "cache_control": {"type": "ephemeral"}},
    ]
```

The static `INSTRUCTIONS` block now has no `cache_control`, so it gets a stable cache key based on its content. The dynamic `athlete_context` block is explicitly ephemeral and won't affect the caching of the static instructions.

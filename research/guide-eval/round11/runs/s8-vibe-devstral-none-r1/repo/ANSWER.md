# Fix for System Prompt Caching Issue

## Problem
Every `save_fact` call was causing the next LLM call to pay full price for the entire system prompt. This happened because the system prompt was built as a single cached block containing both static instructions and dynamic athlete context (including facts). When `save_fact` modified the athlete's facts, the entire system prompt changed, invalidating the cache.

## Solution
Separated the static instructions from the dynamic athlete context in the system prompt construction:

**Before:**
```python
def build_system(a, today):
    text = INSTRUCTIONS + "\n\n" + athlete_context(a, today)
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]
```

**After:**
```python
def build_system(a, today):
    return [
        {"type": "text", "text": INSTRUCTIONS},
        {"type": "text", "text": athlete_context(a, today), "cache_control": {"type": "ephemeral"}}
    ]
```

## How It Works
- The static `INSTRUCTIONS` are now in a separate message block without `cache_control`, so they get cached normally with a long TTL
- The dynamic `athlete_context(a, today)` is in a separate message block with `cache_control: {"type": "ephemeral"}`, so it's not cached
- When `save_fact` updates the athlete's facts, only the ephemeral athlete context changes, leaving the static instructions cache intact
- Subsequent calls can reuse the cached static instructions, avoiding the full system prompt cost

## Result
After this change, `save_fact` calls will no longer evict the static instructions from the cache. The next LLM call will only need to process the small ephemeral athlete context, not the entire system prompt.

# Fix for Memory Write Cache Eviction

## Problem
Every `save_fact` call was invalidating the system prompt cache, causing the next LLM call to pay full price for the entire system prompt (~1000 tokens) instead of reading it from cache.

## Root Cause
The `build_system()` function was concatenating static `INSTRUCTIONS` with dynamic `athlete_context(a, today)` into a single text block. When `save_fact` modified the athlete's facts, the `athlete_context` changed, which changed the entire system prompt text. This invalidated the cache key, forcing a full cache creation on the next call.

## Solution
Split the system prompt into two separate content blocks in the `system` parameter:

1. **Static INSTRUCTIONS** - passed as a text block without `cache_control`, allowing it to be cached normally
2. **Dynamic athlete_context** - passed as a text block with `cache_control: {"type": "ephemeral"}`, preventing it from being cached

This way, the static instructions remain cached even when the athlete context changes due to memory writes.

## Changes Made
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

## Expected Impact
After this change:
- The static `INSTRUCTIONS` (~1000 tokens) will be cached and reused across all messages for all athletes
- The dynamic `athlete_context` will not be cached, but it's much smaller (typically <100 tokens)
- `save_fact` calls will no longer cause cache invalidation of the static instructions
- Input token costs should drop significantly for conversations with frequent memory writes

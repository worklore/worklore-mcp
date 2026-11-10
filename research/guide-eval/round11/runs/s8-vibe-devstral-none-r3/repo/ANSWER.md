# Fix for System Prompt Caching Issue

## Problem
Every `save_fact` call was causing the entire system prompt to be re-cached, making subsequent calls pay full price for the static instructions. This happened because `build_system()` concatenated the static INSTRUCTIONS with the dynamic athlete context into a single cacheable block. When `save_fact` modified the athlete's facts, the entire system prompt changed, causing a cache miss.

## Solution
Split the system prompt into two separate cacheable blocks:
1. Static INSTRUCTIONS (never changes)
2. Dynamic athlete context (changes with facts)

This way, when `save_fact` updates the athlete context, only the dynamic block is re-cached, while the static INSTRUCTIONS block remains cached and can be reused across all calls.

## Change Made
In `bot.py`, modified the `build_system()` function:

**Before:**
```python
def build_system(a, today):
    # One block, cached as a whole: instructions + per-athlete context.
    text = INSTRUCTIONS + "\n\n" + athlete_context(a, today)
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]
```

**After:**
```python
def build_system(a, today):
    # Split into separate cacheable blocks: static instructions and dynamic athlete context.
    # This way, save_fact (which only changes athlete context) doesn't evict the static instructions from cache.
    return [
        {"type": "text", "text": INSTRUCTIONS, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": athlete_context(a, today), "cache_control": {"type": "ephemeral"}},
    ]
```

## Impact
- The static INSTRUCTIONS (~1024-1046 tokens) will now be cached once and reused across all messages
- Only the athlete context (~20-80 tokens depending on facts) will be re-cached when facts change
- This significantly reduces token usage for subsequent calls after a `save_fact` operation

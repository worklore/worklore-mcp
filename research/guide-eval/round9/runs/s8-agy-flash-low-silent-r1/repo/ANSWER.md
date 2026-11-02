# Prompt Caching Fix for Memory Writes

## Cause
Previously, `build_system(a, today)` concatenated the static coaching instructions (`INSTRUCTIONS`) and the dynamic athlete profile / long-term facts (`athlete_context(a, today)`) into a single text block with `"cache_control": {"type": "ephemeral"}`:
```python
def build_system(a, today):
    text = INSTRUCTIONS + "\n\n" + athlete_context(a, today)
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]
```
Because prompt caching relies on prefix matching, whenever `save_fact` was invoked, the appended fact mutated `athlete_context(a, today)`. This altered the content of the cached block, causing a cache miss that evicted/invalidated the entire cached prompt and required rewriting/re-caching the whole system prompt (~1000 tokens) on round 2 and subsequent calls.

## Solution
Split the `system` parameter into two distinct content blocks:
1. **Static instructions (`INSTRUCTIONS`)**: Placed first and marked with `"cache_control": {"type": "ephemeral"}`. Since `INSTRUCTIONS` exceeds the 1,024-token minimum cache threshold for Claude 3.5 / 4.5 Sonnet, it remains cached across requests and rounds regardless of changes to athlete data.
2. **Dynamic athlete context (`athlete_context(a, today)`)**: Placed second without a cache marker. Any modifications to facts or athlete profile attributes only affect this second block and do not invalidate the cached static instructions prefix.

## Changes Made
Updated `build_system(a, today)` in [bot.py](bot.py):
```python
def build_system(a, today):
    # Static coaching rules cached separately so per-athlete updates (like save_fact)
    # do not invalidate the cached instructions.
    return [
        {"type": "text", "text": INSTRUCTIONS, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": athlete_context(a, today)},
    ]
```

# Caching Fix for Memory Writes

## Problem
Previously, `build_system()` assembled the system prompt into a single text block with one `cache_control: {"type": "ephemeral"}` marker:
```python
text = INSTRUCTIONS + "\n\n" + athlete_context(a, today)
return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]
```
Because Claude's prompt caching operates as a prefix hash, any write via `save_fact` (or day/athlete change) modified the per-athlete context appended to the instructions. This invalidated the entire system prompt cache, causing the subsequent request to re-create the cache from scratch (~1000+ input tokens) instead of reading from cache.

## Changes Made
In [`bot.py`](file:///tmp/h-RlReO2/bot.py), updated [`build_system`](file:///tmp/h-RlReO2/bot.py#L130-L138) to split the `system` parameter into two separate text blocks, each with its own `cache_control: {"type": "ephemeral"}` marker:

1. **Segment 1 (Static Instructions)**:
   Contains `INSTRUCTIONS` without interpolated athlete data or dates. This block is byte-stable across all athletes, requests, and days.
2. **Segment 2 (Volatile Tail)**:
   Contains `athlete_context(a, today)` with date, athlete profile, zones, goal, facts, and language.

```python
def build_system(a, today):
    return [
        {"type": "text", "text": INSTRUCTIONS, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": athlete_context(a, today), "cache_control": {"type": "ephemeral"}},
    ]
```

## Result
- When `save_fact` updates an athlete's facts, only the second cache segment (the volatile tail, ~240 tokens) is invalidated and recreated.
- The static instructions prefix (~780 tokens) remains cached and is read as a hit (`cache_read_input_tokens`).
- Within the 5-minute TTL, subsequent tool loop rounds and follow-up messages read both segments from cache.

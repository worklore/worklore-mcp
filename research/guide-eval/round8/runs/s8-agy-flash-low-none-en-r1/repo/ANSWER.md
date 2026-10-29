# Prompt Caching Fix for Long-Term Memory

## Cause of Cache Eviction
Previously, `build_system()` concatenated the static coaching instructions (`INSTRUCTIONS`) and the dynamic per-athlete context (`athlete_context(a, today)`) into a single text block with a `cache_control` breakpoint.

Whenever `save_fact` recorded a new fact (or when the date changed or requests switched athletes), the content of the entire block changed. In Claude's prefix prompt caching, modifying text inside or prior to a cached block invalidates the cached prefix from that point onward, forcing full cache re-creation of the static instructions (~1000+ tokens).

## What Was Changed
In `bot.py`, `build_system()` was updated to separate the system prompt into two blocks:
1. **Static block**: Contains `INSTRUCTIONS` with `"cache_control": {"type": "ephemeral"}`. Since `INSTRUCTIONS` is fixed and exceeds the prompt caching minimum threshold (1024 tokens on Claude Sonnet), it remains cached across messages, tool rounds, and different athletes.
2. **Dynamic block**: Contains `athlete_context(a, today)` without cache control. When `save_fact` appends a memory or changes athlete facts, only this trailing dynamic context changes; the static instructions prefix remains a cache hit.

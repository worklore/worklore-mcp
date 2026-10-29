# Caching fix

**Cause:** `build_system` joined the static `INSTRUCTIONS` and the per-athlete context (which includes the
facts list) into one text block with a single `cache_control` breakpoint. Caching is prefix-based, so any
change to the facts changed the whole block and the next call re-created the cache (`cache_read_input_tokens: 0`).

**Change (`bot.py`, `build_system`):** the system prompt is now two blocks, each with its own breakpoint:
1. `INSTRUCTIONS` (static)
2. `athlete_context(...)` (today, zones, goal, facts, language)

A `save_fact` now only invalidates block 2. Tool filtering is unchanged.

**Caveats (not verified; I had no API access to test):**
- The minimum cacheable prefix on Sonnet 4.5 is 1024 tokens. Judging by the logs (~1046 total, including
  tools and ~100 tokens of context), the static part alone is probably around 800-900 tokens. If so, block 1
  will not be cached on its own and the fix won't show a benefit until the static prefix is over 1024 tokens
  (for example, a longer instruction set). Check `cache_creation_input_tokens` right after a `save_fact` in
  `logs/usage.jsonl`: it should drop to the context size, not ~1000.
- `tools` come before `system` in the cache prefix, so a message that selects a different tool group also
  misses the cache. That predates this change and I left the keyword filtering alone, as NOTES.md asks.

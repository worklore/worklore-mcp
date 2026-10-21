# Caching fix

**Cause:** `build_system` in `bot.py` put the instructions and the athlete context (which includes the
facts list) in one text block with a single `cache_control` breakpoint. `save_fact` changes the
facts, so the block's text changed and the whole ~1000-token prefix was re-created on the next call.

**Change:** `build_system` now returns two blocks. The static `INSTRUCTIONS` block is first and has its
own breakpoint. The per-athlete context (date, zones, goal, facts, language) is second and has its own
breakpoint. After a `save_fact`, the instructions are still read from cache, and only the small
context block is written again. With no memory write, both blocks are read from cache as before.

**Not verified / caveats:**
- I didn't run it, because there's no API access here. Check `logs/usage.jsonl` after deploying:
  the call after a `save_fact` should show a non-zero `cache_read_input_tokens`.
- The cache prefix order is tools, then system, then messages. The instructions breakpoint covers the
  tools too. The minimum cacheable prefix is about 1024 tokens, and the whole prefix was only ~1100 tokens.
  If tools plus instructions come in under that minimum, the first breakpoint won't cache by itself
  and you'd see no improvement. The fix for that is to make the static prefix larger or to
  measure it with the token-counting endpoint.
- Keyword-based tool filtering (kept, as NOTES.md says) changes the tools array between messages.
  Because tools come before the system prompt, a message that adds the `plan` or `race` tools
  also misses the cache. That's a separate, smaller leak. One option is to always send all tools and
  rely on the cache instead.

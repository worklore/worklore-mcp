# Cache fix

**Cause:** `build_system` put the static instructions and the per-athlete context (including the facts list) in one block with a single `cache_control` breakpoint. `save_fact` changes the facts, so the block text changed and the whole ~1000-token prefix was re-created on the next call.

**Change (`bot.py`, `build_system`):** the system prompt is now two blocks. The static `INSTRUCTIONS` has its own breakpoint. The athlete context is a second block with its own breakpoint. After a `save_fact`, the instructions are still read from cache and only the small context block is re-written.

Not changed: keyword tool filtering. Tools come before the system prompt in the cache prefix, so a message that adds a tool group still invalidates the cache. That's a separate trade-off, and NOTES.md says to leave it. I haven't run this against the API, so check `logs/usage.jsonl` after deploying.

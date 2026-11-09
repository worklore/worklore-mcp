# Fix

Changed `build_system()` in `bot.py` to split the system prompt into two blocks:

- The static `INSTRUCTIONS` block retains the `cache_control: {"type": "ephemeral"}` marker.
- The per-athlete context (including long-term facts) is a separate, uncached block.

Previously, the instructions and athlete context were cached as one block. A `save_fact` changed that block's contents, so the next request could not reuse the cached instructions. Now a memory write changes only the uncached context, leaving the cached static block byte-identical.

Updated `README.md` to describe the split caching behavior.

Verified with a local fake two-round `save_fact` conversation: the request after the tool call contained the new fact only in the dynamic block, while the cached instructions block was unchanged. No external API calls were made.

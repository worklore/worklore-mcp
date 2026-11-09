# Cache fix

Changed `build_system()` in `bot.py` to return two system blocks:

1. The static `INSTRUCTIONS`, with the `cache_control: {"type": "ephemeral"}` marker.
2. The changing athlete context (date, profile, goal, zones, and long-term facts), without a cache marker.

Previously, the instructions and athlete context were cached as one block. A `save_fact` changed that block's text, so the next tool-loop request could not reuse the cached instructions. Now a memory write changes only the uncached athlete-context block, leaving the static instruction prefix available for cache reads on later rounds and messages.

Also updated `README.md` to describe the split prompt caching behavior.

Verified locally with a fake LLM through the complete `reply()`/`save_fact` tool loop: both requests had identical cached instruction blocks, while only the athlete-context block changed. `python3 -m py_compile bot.py` also passed. No external API calls were made.

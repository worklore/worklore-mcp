# Cache fix

`build_system()` previously put the static coaching instructions and mutable athlete context (including long-term facts) in one cached text block. Every `save_fact` changed that block, so the next tool-loop round could not reuse its cache entry.

The system prompt is now two blocks:

1. `INSTRUCTIONS`, unchanged and marked with `cache_control: {"type": "ephemeral"}`.
2. `athlete_context(a, today)`, containing the date, profile, and current facts, with no cache marker.

A memory write now changes only the second, uncached block; the static instruction prefix remains identical and cacheable. `README.md` was updated to describe this behavior.

Verification used a local fake LLM through the complete `reply()` tool loop. It confirmed that `save_fact` adds the fact to the second request's athlete context while the cached instruction block remains exactly equal across both calls. No external API calls were made and no athlete records or usage logs were changed.

## Change Summary

Implemented a split system‑prompt caching strategy in `bot.py`:

- Replaced the single, fully **ephemeral** system block with two distinct blocks:
  1. **Static block** containing the unchanging coaching `INSTRUCTIONS`. It now uses
     `"cache_control": {"type": "static"}` so the LLM can keep this portion cached
     across requests.
  2. **Dynamic block** containing per‑athlete context (`athlete_context`). This
     remains the default (ephemeral) because it changes with each user.

The new `build_system` function returns a list `[static_block, dynamic_block]`
instead of a single combined block. This prevents a memory‑write tool like
`save_fact` from evicting the static instructions, fixing the excessive token
usage issue.

### Why this works
* Static instructions never change, so marking them `static` allows the model’s
  cache to reuse them.
* Athlete‑specific data is still recomputed each request, preserving correct
  personalization.

No other files were modified.

# Cache fix: memory writes no longer evict the static instructions

## Cause

`build_system()` in `bot.py` put the coaching instructions and the per-athlete
context into one system block, with the `cache_control` marker on that block:

    text = INSTRUCTIONS + "\n\n" + athlete_context(a, today)

`athlete_context()` includes the long-term facts and today's date. A `save_fact`
appends to `a.facts`, so the block's text changes, so the cache entry for the
whole system prompt misses. The next call writes ~1000+ tokens to the cache again
at the higher write price, which is the `cache_read_input_tokens: 0` /
`cache_creation_input_tokens` pattern in `logs/usage.jsonl` and in NOTES.md. The
date had the same effect once a day.

## Change

`bot.py`, `build_system()`: the system prompt is now two blocks.

1. `INSTRUCTIONS`, identical for every athlete and every day, with the
   `cache_control` marker.
2. `athlete_context(...)`, the facts, zones, goal and date, with no marker. It
   comes after the breakpoint, so changes to it do not change the cached prefix.

`README.md`: the caching paragraph now describes the two blocks.

Nothing else changed: the prompt wording, the tools, the tool-selection logic and
the athlete data format are the same.

## Verification

Run without calling the API (no request was sent anywhere):

- `build_system()` for athlete 42 before and after appending a fact gives an
  identical block 0 (the cached one), and a changed block 1.
- Block 0 is identical across a day change.
- Athlete 77 gets the same block 0, so the cache entry is shared across athletes.
- Only block 0 carries `cache_control`.

## Not verified here, check after deploy

- **Minimum cacheable size.** Sonnet 4.5 only caches prefixes of at least 1024
  tokens, and the prefix that is cached is now tools + instructions only. The
  instructions are ~2,500 characters (roughly 600–700 tokens) and the core tools
  add a few hundred more, so this is close to the limit. The old log's
  `cache_read_input_tokens: 1090` suggests the prefix was above it with the
  athlete context included, but I could not count tokens without calling the API.
  If the cached prefix is under 1024, the API caches nothing and no change will
  show up. Check that `cache_creation_input_tokens` is non-zero on the first call
  of a chat and `cache_read_input_tokens` is non-zero on the calls after a
  `save_fact`. If it is zero, the instructions need to grow or be merged with
  something else to reach the minimum.
- **Tool filtering still breaks the cache.** `select_tools()` changes the tools
  array by keyword, and tools come before the system prompt in the cache prefix,
  so a message containing "plan", "race" and so on misses the cache. This was
  left alone on purpose: NOTES.md says the keyword filter was a clear win. If
  the bill still looks high, the next step is a fixed tool list, or a cache
  breakpoint on the tools array per group.
- **Per-athlete profile is in the uncached block.** Zones and goal are not
  cached, so a `save_fact` re-writes ~100 tokens of profile text. That is small
  compared with the instructions. Splitting it out would need a third block.

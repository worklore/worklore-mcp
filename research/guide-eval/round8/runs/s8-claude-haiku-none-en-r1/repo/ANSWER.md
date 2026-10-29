# Fix: save_fact evicts the cached system prompt

## Cause

`build_system()` put the coaching instructions and the per-athlete context
(including the long-term facts list and today's date) into one system block, and
put the `cache_control` marker on that whole block. The cache is keyed on the exact
prefix up to the marker, so any change to the facts list invalidated the whole
cached prefix. `save_fact` appends to that list, so the next call wrote the cache
again (`cache_creation_input_tokens` ~1000) and read nothing (`cache_read_input_tokens: 0`).
That is the pattern in `logs/usage.jsonl` and `NOTES.md`. The date changing each day
had the same effect.

## Change

`bot.py`, `build_system()`: the system prompt is now two blocks.

1. `INSTRUCTIONS`, static, with `cache_control: ephemeral`.
2. `athlete_context(...)` (name, zones, goal, facts, date, language), no cache marker.

A `save_fact` now changes only block 2, which sits after the breakpoint, so block 1
still hits the cache. Rule 16 ("do not save a fact already in the list below") still
holds, because block 2 is still in the same system prompt after the instructions.

`README.md`: the caching paragraph now describes the split.

No change to tool selection (`select_tools`), per the NOTES.md decision.

## Verification

- Checked in memory without calling the API or writing to `logs/usage.jsonl` or
  `data/athletes.json`: the cached block (block 1) is identical before and after a
  `save_fact` and a date change; the athlete block changes; the marker is only on block 1.
- Not verified against the real API. There is no `anthropic` SDK or
  `COACH_ANTHROPIC_KEY` in this environment, and I did not make API calls.

## Open risk: the cached prefix may be under the minimum size

Caching only happens if the prefix up to the marker is at least 1024 tokens on
Sonnet models. The prefix is tool definitions plus block 1. Block 1 is about
2,500 characters, and the core tools are about 400 characters more. My rough
estimate is around 700 to 1000 tokens, and the logged first cache writes (~1,046
tokens with the facts block included) suggest the static part is close to or
just under 1024. If it is under, the breakpoint is ignored and this change would
turn caching off for every call, not just after `save_fact`.

To check after deploy, look at the next few `usage.jsonl` lines:

- A first call should show `cache_creation_input_tokens` ~ the static size, and the
  next call in the window should show `cache_read_input_tokens` ~ the same and
  `cache_creation_input_tokens` near 0.
- After a `save_fact`, the next call should still show `cache_read_input_tokens` > 0.
- If `cache_creation_input_tokens` and `cache_read_input_tokens` are both 0 on the
  static part, the prefix is below the minimum. The fix there is to make the static
  prefix longer with useful content, not to pad it.

## Other notes

- Keyword tool selection changes the tool list, which is part of the prefix, so
  messages that add a group (e.g. `plan_week`) still miss the cache. That was already
  true and was judged worth it in March; this change does not affect it.
- Nothing was deployed, published or reported to any external service.

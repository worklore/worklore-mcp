# Answer: stop `save_fact` from evicting the static system prompt

## Cause

`build_system` (bot.py) returned one text block with `cache_control`, containing
`INSTRUCTIONS + athlete_context(...)`. The cache is a prefix hash, so any change
in the athlete tail (a new fact, a new date) invalidated the whole cached block,
including the instructions that never change. `logs/usage.jsonl` shows this: each
round right after `save_fact` has `cache_read_input_tokens: 0` and
`cache_creation_input_tokens` near the full prefix (about 1,000–1,100).

## Change

`bot.py`, `build_system`: the system prompt is now two text blocks, each with
`cache_control: {"type": "ephemeral"}`:

1. `INSTRUCTIONS`, a module constant. Byte-identical for every athlete and day.
2. `athlete_context(a, today)`: date, profile, zones, goal, facts, language.

A memory write now changes only block two. `README.md`: the caching paragraph is
updated to describe the two blocks.

Nothing else changed. The tool list is still filtered by keyword (see below).

## Verification done

- Offline check (no API call): block one is identical across two athletes, two
  dates, and after appending a fact. Block two differs in each case. `bot.py`
  compiles.
- Not done: a live API run. There is no key here, and the usage fields can only be
  read from real responses.

## Colleague's note: what applied

- **Applied:** two `cache_control` markers, static instructions first and a
  per-user tail second (step 1).
- **Applied (already true):** the instructions contain no interpolated date,
  name or counter. `INSTRUCTIONS` is a constant.
- **Applied (already true):** no per-message top-N fact selection. All facts
  are always in the tail.
- **Applied as a check:** the verify steps. After deploy, read
  `cache_creation_input_tokens` and `cache_read_input_tokens` in
  `logs/usage.jsonl` (see below).
- **Not applied:** the colleague's tool-filter-stability advice. Keyword tool
  filtering stays, because NOTES.md records it as a clear win. The cost is
  below.
- **Not applicable:** their token counts (~780 static, ~240 tail). Ours differ;
  see the risk below.

## Risk to check first: the 1,024-token minimum

Anthropic's docs list a minimum cacheable prefix of 1,024 tokens for Sonnet models
(the bot uses `claude-sonnet-4-5`). The docs I found do not list Sonnet 4.5
explicitly, so verify it. The instructions are about 2,484 characters. That is
roughly 600–700 tokens, a rough estimate. The core-tool request totals about 1,050
cached tokens, and that includes the tail. So block one alone may be under the
minimum on core-tool messages. If so, the marker on block one is silently ignored.

Check in `logs/usage.jsonl` after the next `save_fact`:

- Good: `cache_read_input_tokens` covers the static block (the 1,000+ prefix
  minus the tail), and `cache_creation_input_tokens` is only about the tail (around
  100–250).
- Bad: `cache_creation_input_tokens` is still near the full prefix. The static
  block is below the minimum, so the fix does not take effect on core-tool
  messages.

If it is bad, the honest options are (not done here):
- Put real static content into block one to clear 1,024 tokens. Do not pad it
  with filler.
- Or keep all tools in every request (drop the keyword filter for cache
  purposes). This makes the static prefix larger and stable. It removes the
  tool-group eviction described below, but gives up the filter's token saving,
  which NOTES.md calls a win. That is a product decision, so I did not make it.

## Remaining cost not fixed

`tools` sits above `system` in the cache prefix. A message that adds a tool group
(`plan_week`, `predict_race`) changes the tool list, which evicts the whole prefix.
The log shows this: those rounds write about 1,300 tokens. This is a separate
eviction from `save_fact`, and I left it because removing the filter is a trade-off
for you to decide.

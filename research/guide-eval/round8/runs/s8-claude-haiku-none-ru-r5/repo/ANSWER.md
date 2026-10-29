# Answer: save_fact was evicting the static prompt from cache

## Cause

`build_system()` in `bot.py` put the coaching instructions and the per-athlete
context (including `facts`) into one text block and marked the whole block with
`cache_control`. Every `save_fact` changes `facts`, which changes the cached prefix,
so the next call wrote the whole block again (`cache_creation_input_tokens` ~1100,
`cache_read_input_tokens: 0`). That is the pattern in `logs/usage.jsonl`.

## What changed

- `bot.py`, `build_system()`: the system prompt is now two blocks.
  1. `INSTRUCTIONS`, static, with `cache_control: ephemeral`. This is the cached prefix.
  2. `athlete_context(a, today)`, without a marker. Facts and today's date live here,
     after the breakpoint, so a new fact or a new day only changes this tail.
- `README.md`: the caching paragraph now describes the two-block layout.

No other behaviour changed: tool selection, the tool loop, storage and logging are as before.

## Checks

Run locally without the API (no requests sent, `data/athletes.json` not written):

- The static block is byte-identical before and after appending a fact to the athlete in memory.
- The context block does contain the new fact.
- The static block is still identical on the next day with the same facts.
- Only the static block carries `cache_control`.

## Not verified / to check in the next logs

- **Minimum cacheable length.** Sonnet caches only prefixes of about 1024 tokens or more.
  The static instructions plus the core tools are roughly 1000 tokens by my estimate
  (the old full block read ~1090 tokens). If the first real calls after this change show
  `cache_creation_input_tokens: 0` and `input_tokens` ~1000 on every call, the static
  part is under the minimum. In that case it needs to be padded with real content or
  the cache dropped; I did not pad it.
- **Tool set in the prefix.** Tools come before system in the cache prefix, and
  `select_tools()` changes the tool list by keyword (e.g. adding `plan_week` or
  `predict_race`). A message that adds a tool group still misses the cache. That is
  separate from `save_fact`, and NOTES.md says the keyword filter is worth keeping, so I
  left it. Moving the marker to the last tool would not fix it: the group change still
  alters the prefix.

I did not call the API, deploy, or send anything anywhere.

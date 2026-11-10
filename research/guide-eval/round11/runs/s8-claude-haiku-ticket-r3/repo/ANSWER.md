# Fix: a `save_fact` write no longer evicts the static instructions

## Cause

`build_system()` returned one text block containing `INSTRUCTIONS` plus the per-athlete
context, with a single `cache_control` marker at the end. Prompt caching is by prefix, so
any byte change in the block (a new fact, or a new day in `Today:`) made the whole block a
miss. `logs/usage.jsonl` shows it: the call after every `save_fact` has
`cache_read_input_tokens: 0` and `cache_creation_input_tokens` around 1000+.

## Change

`bot.py`, `build_system()` now returns two text blocks, each with an ephemeral marker:

1. `INSTRUCTIONS`: the static coaching rules. Byte-identical for every athlete and every day.
2. `athlete_context(...)`: the per-athlete tail (date, name, zones, goal, facts, language).

A memory write changes only block 2, so block 1 keeps its cache entry. The tool-loop rounds
and the next message still read both blocks from cache within the 5-minute TTL.

`README.md`: the caching paragraph now describes the two blocks and the rule to keep block 1
free of interpolated values. No other behaviour changed. Tool filtering, the fact list, and
the model are untouched.

## Verification

I ran a local check with no API calls (the SDK is not installed here, and there is no key):

- Block 1 is the same bytes for user 42 and user 77, and for two different dates.
- Block 1 is unchanged after `save_fact`, while block 2 changes and contains the new fact.
- Block 1 contains none of the athlete name, id, date, or `Today:` text.
- Both blocks carry `cache_control: {"type": "ephemeral"}`.

The check passed. I did not measure cache hits against the live API.

## Open risk: the static block may be below the cacheable minimum

Anthropic only caches a breakpoint when the prefix up to it is at least 1024 tokens
(Sonnet 4.5). The static block is 2484 characters, about 620 tokens by a rough 4-chars/token
estimate. With the core tool schemas above it (about 105 tokens), the prefix is about 730
tokens. If that estimate holds, the marker on block 1 is silently ignored: no error, no
cache entry. Then block 2's marker covers the whole prefix again, and a memory write still
evicts everything. The fix works only if block 1's prefix (tools + block 1) is at least 1024
tokens.

I could not confirm the real count here. The usage log suggests the total prefix is about
1024–1100 tokens, which fits the estimate. The check after deploy is:

- After a `save_fact`, the next call should show `cache_read_input_tokens` close to the
  static size, and `cache_creation_input_tokens` close to the tail size (about 100–250
  tokens), not the full prompt.
- If `cache_creation_input_tokens` is still about the full prompt after a `save_fact`, the
  static block is below the minimum. Options, in order of preference:
  1. Keep the full tool list in every request. The prefix then includes all the tool schemas
     and probably clears 1024. This gives up the keyword tool filter win from March, which
     the notes say to keep, so it is a trade-off for the owner to decide.
  2. Add real static content to the instructions. Padding with filler is not a fix.

## Separate cache misses (not fixed here)

Tools sit above the system prompt in the cached prefix. Keyword tool filtering produces
four possible tool sets, and each switch rewrites the whole prefix. The log shows this:
the `plan_week` and `predict_race` rounds have `cache_creation` of 1305 and 1334 with zero
reads. This is unrelated to memory writes and is the expected cost of the filter, so I left
it alone.

## What applied from the colleague's note

- **Applied:** split the system prompt into a static block and a per-user tail, each with a
  marker. Keep the static block free of interpolated values. Use the usage fields
  (`cache_creation_input_tokens` / `cache_read_input_tokens`) to confirm the effect.
- **Applied:** keep the fact list whole, not top-N per message. A per-message fact selection
  would change block 2 on every message and stop tail cache hits. This matches the current
  code, which loads all facts.
- **Applied, with a caveat:** tool-set changes evict the cache, as the note says. The
  keyword filter has the same cost here, which is listed above.
- **Not applicable:** the Telegram transport, the token counts (they are for their bot, not
  this one), and the 4-marker limit (we use 2, which is also fine here).

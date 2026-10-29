# Answer: a `save_fact` write no longer evicts the static instructions

## Cause

`build_system()` in `bot.py` returned one text block containing the coaching
instructions and the per-athlete context (date, profile, zones, goal, facts),
with a single `cache_control` marker at the end. The cache is a prefix hash, so
every `save_fact` changed the facts inside that block, changed the hash, and
missed the whole prefix. `logs/usage.jsonl` shows it: the call right after each
`save_fact` has `cache_read_input_tokens: 0` and `cache_creation_input_tokens`
about the size of the full prompt (for example 1061, 1075, 1090, 1104 for user 42).

## Change

`bot.py`, `build_system()`: the system prompt is now two text blocks, each with
`cache_control: {"type": "ephemeral"}`.

1. `INSTRUCTIONS`: a module constant with no interpolated values. It stays
   byte-identical across users, days and memory writes.
2. `athlete_context(a, today)`: the volatile tail. A `save_fact` changes only this block.

`README.md`: the caching paragraph now describes the two blocks instead of one marker.

Nothing else changed. Tools are still selected per message and sent in the same
order within a message's tool loop. `save_fact` still writes `data/athletes.json`
through `run_tool` as before.

## Verification

- Local check with a fake LLM and the save patched out (no API calls, no write to
  `data/athletes.json`, no writes to `logs/usage.jsonl`). A message that triggers
  `save_fact` produces two rounds. Results:
  - Both rounds send two system blocks, each with an ephemeral `cache_control`.
  - The static block is identical in round 1 and round 2, so its prefix hash is unchanged.
  - The tail differs between rounds and round 2 contains the new fact.
  - The static block contains no date or athlete name.
  - The tools array is identical across the two rounds.
- Not verified against the live API. Run two messages within 5 minutes, then a
  `save_fact` message, then a third message, and check `usage.jsonl`. Expected: the
  third message's round after the save has `cache_read_input_tokens` covering the
  instructions and `cache_creation_input_tokens` covering only the tail (roughly
  200–250 tokens, not ~1000+).

## Risk: the instructions block may be below the minimum cacheable length

Sonnet models only cache a prefix of at least 1024 tokens (I believe this is the
minimum for `claude-sonnet-4-5`; check the current docs). The cache prefix at the
first marker is the tools array plus the instructions. The instructions are
2484 characters, about 620 tokens by a chars/4 estimate. On core-only messages
(no `plan` or `race` keywords) the tools add roughly 200–250 tokens by my
estimate from the log. That puts the first breakpoint near 850 tokens, below
1024, so it may silently not cache. In that case the fix does nothing for those
messages: the tail marker caches tools + instructions + tail as one unit, and a
`save_fact` still evicts it. Messages with `plan` or `race` keywords add tool
schemas, so they may clear the minimum.

I did not check this against the live API, because doing so would mean calling
the API with the real key. The check is in the verification step above: if the
first call after a `save_fact` still shows `cache_creation` close to the full
prompt, the first block is under the minimum. The fix would then be to put more
genuinely static guidance in `INSTRUCTIONS`. I did not pad it with filler text.

## What applied from the colleague's note

- **Applied:** two `cache_control` markers (we use 2 of the 4 allowed); static
  block byte-stable with no interpolated values; volatile tail after it; tool list
  constant within one message's loop; usage fields as the verification signal.
- **Applied, already true here:** the bot doesn't select facts per message. It
  loads all facts into the tail, which is the cache-friendly choice. So there was
  nothing to remove on that point.
- **Not applied:** reordering the tail rarest-changing first. Once there is a
  marker at the end of the block, the order inside the tail does not affect cache
  hits, so I left the existing order.
- **Not applicable:** the Telegram specifics, the token counts (~780 and ~240 in the
  note versus ~620 and ~200–250 here), and the Anthropic-SDK-specific reproduction steps.
- **Applies but not changed:** the note's tool-filtering tension. In this bot,
  a message that matches the `plan` or `race` keywords changes the tools array,
  which is the prefix before the system blocks. That misses the cache for the
  instructions as well (the log shows creation of ~1305 and ~1334 tokens on those
  messages). Fixing it would mean always sending all tools, which costs more on
  the common path, so I left it as a trade-off for you to decide.

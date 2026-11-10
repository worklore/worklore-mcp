# Answer: why `save_fact` evicts the static instructions

## Cause

`build_system()` returned one text block: `INSTRUCTIONS + athlete_context(...)`.
That block carried a single `cache_control` marker. Prompt caching matches a prefix,
so the cache covers everything up to the marker. `athlete_context()` includes the
athlete's facts, and `save_fact` appends to them. One changed byte in the facts
invalidates the whole block, including the coaching rules that never change.

This matches `logs/usage.jsonl`: after every `save_fact` round, `cache_read_input_tokens`
is 0 and `cache_creation_input_tokens` is about the full prompt (~1000+ tokens).

## Change

`bot.py`, `build_system()` now returns two text blocks, each with `cache_control`:

1. `INSTRUCTIONS`: the static coaching rules. Byte-identical for every athlete and every day.
2. `athlete_context(...)`: date, name, zones, goal, facts, language.

A `save_fact` write changes only block 2. Block 1 keeps its cache entry, so the next
round pays cache read on the instructions and cache creation only on the tail (~70 tokens
of facts instead of ~1000+).

`README.md`: the caching paragraph now describes the two blocks and the rule that
block 1 has no interpolated values.

Nothing else in the request changed. The model, tools, messages, and `save_fact`
logic are untouched.

## Verification

Run locally with a fake LLM (temp data and log paths; the real `data/athletes.json`
and `logs/usage.jsonl` were not modified):

- Both blocks carry `cache_control`.
- Block 1 is identical before and after a `save_fact` write.
- Block 2 changes after the write and contains the new fact.
- Block 1 is identical for a different athlete and a different date.

I did **not** verify the caching on the live API. This sandbox has no key and no
`anthropic` package installed, and I did not make outbound calls.

## Open risk: minimum cacheable length

Anthropic does not cache a prefix shorter than the model's minimum, and it does so
silently: no error, `cache_creation_input_tokens` just stays 0. The block-1 marker covers
the tool schemas plus `INSTRUCTIONS`. `INSTRUCTIONS` is 2484 characters, roughly
800–900 tokens by my estimate, and the cached prefix in the log (~1000–1100 tokens) is
close to the minimum for `claude-sonnet-4-5`. If the static prefix is under the minimum,
block 1 never caches and the fix only changes which block is re-created, with no savings.

Check on the first live call after deploy: `cache_creation_input_tokens` should be
roughly the instructions plus tools, and the next message should show it as
`cache_read_input_tokens`. If both stay 0 on block 1, the static prefix is below the
minimum. The fix then is to add real content to `INSTRUCTIONS`, not padding. I did not
pad it.

## What applied from the colleague's note

- **Applied:** split `system` into two text blocks, each with an ephemeral `cache_control`.
  Static instructions first, per-athlete tail second.
- **Applied:** no interpolated date, name, or counter in the static block.
- **Applied:** the per-athlete tail, which holds the facts, is the only part re-cached after a memory write.
- **Applied:** the two-marker count (of the four allowed).
- **Already in place, not changed:** keyword tool filtering. Its trade-off is in `NOTES.md`.
- **Did not apply:** top-N or relevance-based fact selection. I kept all facts in the tail.
  Selecting per message would change block 2 on every message and defeat its cache.
- **Not applied, noted:** tool-group changes still re-cache everything. The `tools` array
  sits before `system` in the prefix. The log rows with `plan_week` and `predict_race` show
  `cache_creation` of ~1300 tokens because the tool set changed. The fix is either to keep
  the tool set constant (more tokens on simple messages, which is why filtering exists) or
  to accept the re-cache on those messages. That is a cost decision for you, so I left it alone.
- **Not applicable:** the Telegram transport, the athlete-facing details of the colleague's bot,
  and the `usage` field analysis beyond what I confirmed in the log.

## Files changed

- `bot.py`: `build_system()` returns two cached blocks.
- `README.md`: caching paragraph updated.
- `ANSWER.md`: this file.

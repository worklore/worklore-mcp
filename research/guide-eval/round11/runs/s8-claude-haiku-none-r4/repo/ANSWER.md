# Fix: save_fact evicting the static instructions from the prompt cache

## Cause

`build_system()` returned one text block containing `INSTRUCTIONS` plus the
per-athlete context (profile, zones, goal, and the `facts` list), with a single
`cache_control` marker on the whole block. `save_fact` appends to `facts`, so the
block's text changes, and the cached prefix (tools + system) no longer matches.
The next call pays `cache_creation_input_tokens` for the whole system prompt.

This matches `logs/usage.jsonl` and `NOTES.md`: the call right after a `save_fact`
has `cache_read_input_tokens: 0` and a full `cache_creation_input_tokens`.

## Change

`bot.py`, `build_system()`: the system prompt is now two text blocks.

1. `INSTRUCTIONS`, with `cache_control: ephemeral`. Static across all athletes and
   messages, so it stays cached.
2. `athlete_context(a, today)`, with no marker. It changes on `save_fact` and on
   each new day, and only this small block misses the cache.

`README.md`: the caching paragraph now describes where the marker sits.

No change to the tool list, the tool loop, the athlete file format, or `log_usage`.

## Verification

Offline only. I did not call the API, so the cache hit rate is not measured here.
I stubbed the LLM and ran a `save_fact` turn followed by a normal turn:

- The first block of `system` is byte-identical across the save_fact call and the
  calls after it.
- The per-athlete block contains the new fact only after the save.
- `cache_control` appears only on block 0.

Temporary test files were deleted and the repo has no stray files.

## Caveats

- **Minimum cacheable length.** The instructions are about 2,500 characters, roughly
  600 to 700 tokens by a rough estimate. Caching requires a minimum prefix length
  (1,024 tokens for the Sonnet-class models; check the current value for the model in
  use). The prefix here is tools + instructions, so it may clear the minimum, but I
  could not measure it. If the marker is below the minimum, it is silently ignored
  and nothing gets cached. After deploying, check `logs/usage.jsonl`: on a normal
  message, `cache_read_input_tokens` should be about the static prefix size, and it
  should stay that size after a `save_fact`. If it does not, the instructions need
  to grow past the minimum, or the tools need to be included in the cached prefix.

- **Tool-group switching still evicts the cache.** `select_tools()` changes the tool
  list when a message contains plan or race keywords. Tools come before the system
  prompt in the cache order, so a change there invalidates everything after it. The
  log shows this: `plan_week` and `predict_race` rounds have `cache_read: 0` with a
  full `cache_creation`. This is a separate cost from `save_fact`, and I did not
  change it. `NOTES.md` records the keyword filter as a clear win (about 75% fewer
  tool tokens on short messages). Keeping that win means accepting cache misses on
  keyword turns. Sending the full tool list every time would avoid those misses but
  cost more on every call. That is your call.

- **Date rollover** also used to evict the instructions and now only evicts the small
  block, so it is covered by the same change.

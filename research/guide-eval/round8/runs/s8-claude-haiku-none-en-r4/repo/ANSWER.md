# Why a memory write evicts the system prompt from cache

`build_system()` returned one text block containing the static coaching rules
and the per-athlete context (name, zones, goal, long-term facts, today's date),
with a single `cache_control` marker on the whole thing.

`save_fact` appends to `athlete.facts`, which is rendered into that block. So
the block's bytes change, the cache entry for it no longer matches, and the
next call writes a new cache entry for the full system prompt with
`cache_read_input_tokens: 0`. This matches `logs/usage.jsonl`: the call after
each `save_fact` shows a cache miss, and the following message reads from the
new entry.

## Change

`bot.py`, `build_system()`: the system prompt is now two blocks.

1. `INSTRUCTIONS`, with `cache_control: ephemeral`. Identical for every athlete
   and every day, so a `save_fact` no longer touches it.
2. `athlete_context(a, today)`, without a cache marker. Facts and the date live
   here and change freely.

Nothing else changed. Tools are unchanged, and `save_fact` does not alter the
tools list, so the tools prefix stays cached too. The cache prefix is now
tools + instructions.

## Verification

- Offline check with a fake LLM (temp files, so `data/` and `logs/` were not
  touched): a `save_fact` round sends a byte-identical block 0 with
  `cache_control`, the new fact appears only in block 1, and the tools list is
  identical across rounds.
- Not verified against the live API. I had no key and did not call the API.

## Things to check after deploy

- Cache minimum: the instructions alone are about 620 tokens (rough estimate,
  chars/4). The cacheable prefix is tools + instructions, which should be above
  the 1024-token minimum (the logged `cache_creation` of ~1090 included the
  tools). If it is below the minimum for the model in use, caching will not
  happen and the API will not error. Check that `cache_creation_input_tokens`
  is non-zero on the first call and `cache_read_input_tokens` is non-zero on
  later calls, including the round after a `save_fact`.
- `select_tools()` still changes the tools list when a message contains
  planning or race keywords, which invalidates the whole cache for that call.
  That was an intentional trade-off in March (see NOTES.md) and is not changed
  here.
- `MODEL` is still `claude-sonnet-4-5` in the code; not touched.

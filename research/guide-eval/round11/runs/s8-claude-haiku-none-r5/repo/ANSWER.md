# Fix: a memory write no longer evicts the cached instructions

## Cause

`build_system()` put the static coaching instructions and the per-athlete context,
including the `Long-term facts` list, into one text block with `cache_control`.
Prompt caching matches the prefix byte for byte, so when `save_fact` appended a fact,
the cached prefix changed. The next request wrote a new cache entry at full
(1.25x) price and read nothing. That matches `logs/usage.jsonl`: calls right after a
save show `cache_read_input_tokens: 0` and `cache_creation_input_tokens` around 1000+.

## Change (`bot.py`)

`build_system()` now returns two text blocks, in this order:

1. **Cached block** (`cache_control` on this block): `INSTRUCTIONS` plus a new
   `athlete_profile()` (name, sport, zones, goal, language). It changes only when the
   profile changes, not on `save_fact`.
2. **Uncached block**: a new `athlete_memory()` with today's date and the facts list.
   It is after the breakpoint, so a memory write or a new day only changes this block.

`athlete_context()` is replaced by those two helpers. Nothing else in the file calls it.
The `reply()` loop and the tool code are unchanged.

## Verification

- `test_prompt_cache.py` (new, no API calls): run `python3 -m unittest test_prompt_cache -v`.
  All 5 tests pass on the new code. On the original code 4 of them fail, as they should.
- End-to-end through `reply()` with a fake LLM: the model calls `save_fact`, and the
  second request's cached block is identical to the first. The new fact appears only
  in the uncached block.
- Not verified against the live API: there is no key here, and I did not deploy or call
  any external service. Check the next `logs/usage.jsonl` entries after a `save_fact`:
  `cache_read_input_tokens` should stay near the previous value, and there should be no
  new `cache_creation_input_tokens`.

## Caveats

- **Minimum cacheable size.** The API only caches a prefix of at least 1024 tokens for
  Sonnet-class models. The cached block is tools + instructions + profile, which is
  probably close to that minimum. Before the change, the whole system prompt was cached
  at about 1050 to 1330 tokens, so the old block cleared the minimum. If the new prefix
  falls below it, the API silently skips caching and cost goes up. Check
  `cache_creation_input_tokens` on the first call for each athlete. I did not pad the
  prompt to force caching.
- **Tool selection also changes the prefix.** `tools` come before `system` in the cache
  prefix, and `select_tools()` changes the tool list with message keywords. A message
  with "plan" or "race" therefore misses the cache even when no fact changed. The log
  shows this, for example the `plan_week` round 1 at 06:44:31 with `cache_read: 0` and
  `cache_creation: 1305`. I did not change this, because it is the trade-off the March
  note in `NOTES.md` describes. Options: always send the full tool list (more tokens on
  every call, but a stable prefix), or keep the filter and accept misses on keyword
  messages.
- `athlete_context()` is gone. The Telegram transport lives in a separate repo; the
  README says it only calls `reply()`, so this should be safe, but check it does not
  import `athlete_context`.

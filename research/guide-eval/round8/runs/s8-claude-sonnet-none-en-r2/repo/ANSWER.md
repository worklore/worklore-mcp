# Cache fix

**Cause:** `build_system` put the instructions and the athlete context (including the
facts list) in one text block with a single `cache_control`. `save_fact` changes the
facts, so the block text changed and the whole prefix, including the ~600 static
instruction tokens, was re-written on the next call.

**Change (`bot.py`, `build_system`):** the system prompt is now two blocks. Block 1 is
the static `INSTRUCTIONS` with its own breakpoint. Block 2 is `athlete_context(...)`
with a second breakpoint. A fact write now only invalidates block 2. Keyword tool
filtering is untouched, as NOTES.md asks.

**Caveats (not verified, since there is no API access here):**
- Tools come before the system prompt in the cache prefix. A message that adds a tool
  group (plan/race) still changes the prefix and re-creates the cache. That is the
  trade-off of the March tool filtering, and it explains some non-save_fact misses in
  the log (e.g. the `plan_week` row).
- The minimum cacheable prefix is about 1024 tokens for this model. Tools plus
  instructions are estimated at 900-1000 tokens, so breakpoint 1 may fall just under
  it. If so, the first breakpoint silently does nothing, and the fix only works once
  that prefix is over the minimum. Check `cache_read_input_tokens` after a `save_fact`
  in `logs/usage.jsonl`. It should stay around 900 or more instead of dropping to 0.

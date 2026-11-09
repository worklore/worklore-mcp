# Cache fix

## What changed

- `bot.py` now builds `system` as two text blocks instead of one:
  1. `INSTRUCTIONS`, which is byte-stable across athletes, dates, and memory writes.
  2. `athlete_context(a, today)`, which contains the date, profile, zones, goal, long-term facts, and language.
- Both blocks have `cache_control: {"type": "ephemeral"}`. A `save_fact` now changes only the second block, allowing the static instructions to remain cached.
- `README.md` now describes the two-block caching behavior.
- Tool selection, tool ordering, and loading all long-term facts are unchanged.

The usage log showed the original failure clearly: after the `save_fact` call at `logs/usage.jsonl:4`, the next call at line 5 had `cache_read_input_tokens: 0` and created a new 1,061-token cache entry for the whole prompt.

## Verification

A mocked two-round `reply()` call exercised the real `save_fact` path using temporary local storage. It confirmed that:

- both system blocks carry ephemeral cache markers;
- the static block is byte-identical before and after the memory write;
- only the athlete-context block changes, and it contains the saved fact;
- the fact is persisted and the tools remain unchanged across loop rounds.

No live API call was made, so provider-reported cache token counts were not measured. On the next real memory write, `cache_read_input_tokens` should still cover the static block while `cache_creation_input_tokens` covers the changed athlete tail.

## Colleague's note: what applied

- Applied the two-segment `cache_control` fix, with static instructions first and volatile per-athlete context second.
- Kept the static block free of interpolated dates, names, counters, and facts.
- Kept the existing stable tool selection within a message's tool loop; the note's keyword-based tool filtering was already present and was left unchanged.
- Kept all facts in the prompt rather than adding per-message top-N selection, which would make the volatile block change unnecessarily.
- Used the note's `cache_creation_input_tokens` / `cache_read_input_tokens` guidance as the live verification criterion; the Anthropic-specific marker syntax was already in use.

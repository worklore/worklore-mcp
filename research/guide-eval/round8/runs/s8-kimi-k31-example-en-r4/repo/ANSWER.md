# Cache fix

## What changed

`build_system()` in `bot.py` now returns two system text blocks instead of one:

1. `INSTRUCTIONS`, with its own `cache_control: {"type": "ephemeral"}` marker. This block is byte-stable because it contains no athlete data, dates, or other interpolated values.
2. `athlete_context(a, today)`, with a second ephemeral marker. This block contains the date, profile, zones, goal, long-term facts, and language.

Previously, appending a fact changed the single combined block and invalidated the cached instructions too. Now a `save_fact` changes only the second block, so the static instruction prefix remains reusable and only the volatile tail needs to be cached again.

`README.md` was updated to describe the two independent cache segments. Tool selection, memory storage, and the request loop were not changed.

## Parts of the colleague's note that applied

- The two-block split with one ephemeral cache marker per block was the fix used.
- Keeping the static block byte-stable and putting all per-athlete/per-day values in the volatile block applied directly.
- Leaving the existing tool filtering and tool ordering unchanged followed the note's warning that tools are part of the cached prefix.
- No per-message top-N fact selection was introduced; all facts remain in the volatile block so its contents do not vary by question.
- Existing usage logging already records `cache_creation_input_tokens` and `cache_read_input_tokens`, which remain the fields to use for production verification.

The note's tool-filtering optimization was already present, so it was not reimplemented. Its deployment and external-service steps did not apply.

## Verification

The supplied `logs/usage.jsonl` showed the original problem: calls immediately after `save_fact` had zero cache-read tokens and recreated roughly the full prompt.

I ran the real `reply()` loop with a fake Claude response that invoked `save_fact` and a fake prefix-cache usage model. The test confirmed that the first block was identical before and after the write, the new fact appeared only in the second block, and the post-write call retained the simulated 800-token static cache read while creating only the simulated 240-token tail. No athlete records were modified and no external API was called. Live Anthropic usage could not be measured locally; after deployment, a real memory-write round should show a nonzero static cache read and cache creation limited to the volatile segment.

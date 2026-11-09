# Cache fix

## What changed

`build_system` in `bot.py` now returns two system text blocks instead of one:

1. `INSTRUCTIONS`, which is byte-stable across athletes, dates, and memory writes.
2. `athlete_context(a, today)`, which contains the date, profile, zones, goal, facts, and language.

Both blocks have `cache_control: {"type": "ephemeral"}`. A `save_fact` now changes only the second block, so the static instruction prefix remains reusable while only the volatile athlete tail needs to be cached again. `README.md` was updated to describe the two cache segments.

## Verification

Ran a local mocked two-round `reply()` call in which the first response invokes `save_fact`. The check confirmed that:

- both system blocks carry ephemeral cache markers;
- the static block is byte-identical before and after the write, and across another athlete/date;
- only the athlete-context block changes and includes the new fact;
- the tool list remains unchanged within the tool loop.

No live API call was made, so new provider usage-token totals were not collected.

## Colleague's note

Applied:

- Split the system prompt into static instructions and volatile per-athlete context, with one ephemeral marker on each block.
- Kept the static block free of interpolated dates, names, counters, and memory.
- Kept the existing stable core tools and keyword-based tool filtering; no tool schemas were reordered or rewritten.
- Continued injecting all facts rather than adding per-message top-N selection.

Not applicable or not changed:

- The suggested filtering of tool schemas was already present and was left intact, as requested by `NOTES.md`.
- No per-message fact selection or other cache-defeating personalization was introduced.

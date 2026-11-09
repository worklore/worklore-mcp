# Cache fix

## What changed

`build_system()` in `bot.py` now returns two system text blocks instead of one:

1. `INSTRUCTIONS`, which is byte-identical across athletes, dates, and memory writes.
2. `athlete_context(a, today)`, which contains the date, profile, zones, goal, all long-term facts, and language.

Both blocks retain `cache_control: {"type": "ephemeral"}`. The first marker preserves the static-instruction prefix; the second caches the volatile athlete tail. A `save_fact` therefore changes only the second block, so the next request can read the instructions from cache and re-create only the athlete-context cache entry.

I also updated the prompt-caching description in `README.md`. Tool selection, fact storage, the tool loop, and usage logging are unchanged.

## Verification

I ran the full `reply()` flow with a local fake Claude client and temporary data/log files. The fake model called `save_fact`, and the test confirmed that:

- both requests contained exactly two cached system blocks;
- the instruction block was byte-identical before and after the write, including across different dates;
- only the athlete-context block changed, and it contained both existing and newly saved facts;
- the new fact was persisted and the reply completed normally.

No live API request was made, so new provider-side cache token counts were not measured.

## Which parts of the colleague's note applied

Applied:

- Split the system prompt into static instructions and a volatile per-athlete tail, with an ephemeral cache marker on each.
- Kept the static block free of interpolated dates, names, and counters.
- Kept all facts in the context rather than adding per-message top-N selection.
- Left the existing stable core tools and keyword-based tool grouping unchanged; no tool schemas were reordered or rewritten.
- Retained usage logging of `cache_creation_input_tokens` and `cache_read_input_tokens` for production verification.

Not newly applied:

- Tool filtering was already implemented and was left as-is.
- The note's example token counts and live five-minute-cache measurements were not reproduced; the local verification checked request structure and prefix stability only.

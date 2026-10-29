# Fix: memory writes no longer evict the static system prompt

## Cause
`build_system` (bot.py) sent one text block, `INSTRUCTIONS + athlete_context`, with a single `cache_control` marker.
`save_fact` changes the facts list. The next loop round rebuilds the block, so the prefix hash changes and the whole prompt
is re-created (see `logs/usage.jsonl`: `cache_read 0`, `cache_creation ~1060` right after each `save_fact`).

## Changes (bot.py)
1. `build_system` now returns two blocks, each with `cache_control: ephemeral`:
   - `INSTRUCTIONS`: static, byte-identical for every user and day.
   - `athlete_context(...)`: date, profile, zones, goal, facts, language. A memory write now invalidates only this tail.
2. I added a static "Reference" section (RPE scale, session types, return-from-break, heat, taper) to `INSTRUCTIONS`.
   This is not in the colleague's note. It is needed here. The whole prompt was only ~1046 tokens, and the
   tail is ~100 of those. The static prefix (tools + instructions) would have been about 930 tokens, under the 1024-token
   minimum cacheable length for Sonnet 4.5. Below that minimum the first marker is silently ignored, so the
   two-marker split alone would have changed nothing. The static prefix is now about 1500 tokens by my estimate (~3 chars/token, from the
   logged 1046 tokens vs ~3200 chars). The extra text is not free: it is written once per 5-minute window, then read at ~10%.

## Colleague's note: what applied
- Applied: two markers (static + per-user tail), keeping the static block free of interpolated values, and reading `usage` to verify.
- Already true / left alone: tool filtering by keyword stays as is. Tools sit above the system prompt, and the core set is constant, so within a message's loop the prefix is stable.
- Not applicable: top-N fact selection. The bot loads all facts, and I kept that, since selection would defeat the tail cache.
- Ignored: the numbers (780/240 tokens, 55 tools). They are for a different bot.

## Not verified
I did not call the API (no key, and the rules forbid external calls). To check, send two messages within 5 minutes, then one that triggers `save_fact`,
then another. Look at `logs/usage.jsonl`: after the write, `cache_read_input_tokens` should still cover about 1500 tokens and
`cache_creation_input_tokens` should be only about 100-150. If creation is still the full prompt, the static prefix is under the minimum; add more static text.
Note that a message that pulls in the `plan` or `race` tool group changes the tools prefix and costs one full re-read.

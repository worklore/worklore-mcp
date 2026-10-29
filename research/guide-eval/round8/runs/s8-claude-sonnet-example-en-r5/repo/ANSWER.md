# Fix: memory writes no longer evict the static instructions

## Cause
`build_system` (bot.py) sent one text block, `INSTRUCTIONS + athlete_context`, with a single
`cache_control` marker. `save_fact` changes the facts list, so the block's bytes change and the
whole prefix misses. That matches `logs/usage.jsonl`: after a `save_fact`, `cache_read` is 0 and
`cache_creation` is about 1000 again.

## Change
`build_system` now returns two blocks, each with its own `ephemeral` marker:
1. `INSTRUCTIONS`: static. It has no interpolation, so it is byte-identical for every user and day.
2. `athlete_context(...)`: the date, profile, zones, goal, facts and language. This is the only part a memory write changes.

Nothing else changed. Tool filtering is untouched, as NOTES.md asks. Tools sit above the system
prompt in the cached prefix, so I did not touch their order or wording.

Checked offline: after appending a fact, block 0 is identical and only block 1 differs.
I did not call the API, so the effect on real `cache_read` / `cache_creation` numbers is unverified.

## Caveat: the static prefix may be too small to cache
Sonnet 4.5 needs at least 1024 tokens before a breakpoint. My estimate for the static prefix
(tools plus `INSTRUCTIONS`) is about 730 tokens (2484 characters of instructions, about 620 tokens,
plus about 110 for the core tools). That is below the minimum, so the first marker may be silently
ignored. If so, a memory write would still re-create the whole prompt, because only the second
marker would cache and it covers everything.

To check, trigger a `save_fact`, then send another message, and read `usage` in `logs/usage.jsonl`:
`cache_read_input_tokens` should be about 730 or more, and `cache_creation_input_tokens` should be
only the tail, about 300. If `cache_read` is 0, the prefix is under the minimum.
The options are to grow the static part with real coaching content or to switch models.
I did not pad the prompt with invented rules.

## Colleague's note
Applied:
- The two-marker split.
- Keeping the static block free of dates, names and counters.
- Leaving the tools array stable.
- Reading `usage` to verify.

Not applicable:
- Top-N fact selection. The code already injects all facts, which is what the note recommends.
- The tool-filtering design. It already exists.
- The note's token counts (780 static / 240 tail). They don't carry over to this prompt because of the 1024 minimum above.

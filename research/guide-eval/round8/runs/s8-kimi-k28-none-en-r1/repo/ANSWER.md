# Fix: memory writes no longer evict the cached system prompt

## Root cause

`build_system()` in `bot.py` concatenated the static `INSTRUCTIONS` (the coaching
rules, ~1000 tokens) and the per-athlete context (profile, zones, goal,
long-term facts) into a single text block with one `cache_control` marker.
Anthropic prompt caching is prefix-based, so the cached entry is keyed on the
whole block. Every `save_fact` appends to the athlete's facts, which changes the
context and therefore the entire block — invalidating the cache for the static
instructions too. The next call then pays cache-creation price for the full
system prompt again. That is exactly the pattern in `logs/usage.jsonl`: every
round right after a `save_fact` shows `cache_read_input_tokens: 0` and
`cache_creation_input_tokens` back up at ~1000+.

## Change

`build_system()` (bot.py) now returns two cache-marked blocks instead of one:

1. `INSTRUCTIONS` — static, own `cache_control` breakpoint.
2. `athlete_context(a, today)` — dynamic, own `cache_control` breakpoint.

With separate breakpoints, a changed context block only invalidates the cache
from its own position onward. The instructions prefix still matches the cached
prefix, so after a `save_fact` the next call reads the ~1000 instruction tokens
from cache and only the small context block (~60 tokens and growing by one fact)
is re-created. The combined text is byte-identical to the old single block, so
model behavior is unchanged.

Also updated the stale "One block, cached as a whole" comment above
`build_system()` and the prompt-caching sentence in `README.md` to describe the
two-breakpoint setup.

## Verification

Ran a script (no test suite exists in the repo) that:

- builds the system for athlete 42 and asserts it is two blocks, both
  cache-marked, and that block texts joined equal the old single-block prompt;
- appends a fact (simulating `save_fact`) and asserts the instructions block is
  byte-identical while only the context block changes;
- rebuilds with the same record and asserts the blocks are identical
  (cache-stable within the TTL).

All assertions passed. End-to-end against the API was not run (no
`COACH_ANTHROPIC_KEY` in this environment); the effect should show up in
`logs/usage.jsonl` as `cache_read_input_tokens` staying high on the round after
a `save_fact` instead of dropping to 0.

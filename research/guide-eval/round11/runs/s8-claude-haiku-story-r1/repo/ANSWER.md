# Answer: save_fact evicts the static instructions

## Cause

`build_system()` returned one text block: `INSTRUCTIONS + athlete_context(...)`, with a single
`cache_control` marker at the end. The cache is a prefix hash, so the marker covers everything
before it. `save_fact` appends to `a.facts`, which is inside that block, so the prefix changes and
the whole prompt (instructions included) is re-cached on the next round. `logs/usage.jsonl` matches
this: after each `save_fact` the next call shows `cache_read_input_tokens: 0` and
`cache_creation_input_tokens` back at about the full prompt size (for example 1039 → 1054 → 1090 →
1104 across the log, with the same ~1000-token base).

## Change (bot.py, `build_system`)

The system prompt is now two text blocks, each with `cache_control: {"type": "ephemeral"}`:

1. `INSTRUCTIONS`: a constant string. It contains no date, name, id or fact, so it is byte-identical
   for every athlete and every day.
2. `athlete_context(a, today)`: the volatile tail (date, athlete, sport, zones, goal, facts, language).
   A `save_fact` write changes only this block.

Nothing else in the request changed. Tools are the same set and order as before.

## Tests (test_cache_split.py)

`python3 -m unittest test_cache_split -v`: 5 tests, all pass. They check that the request has exactly
two `cache_control` markers on the system blocks and none on tools; that block 1 is identical across
different athletes, days and fact lists; that block 1 has no volatile values; that adding a fact changes
only block 2; and that block 2 carries the date, profile, and language. Run against the original
`bot.py`, 4 of the 5 fail and 1 errors, so the tests detect the old behaviour.

## Not verified live

There is no `COACH_ANTHROPIC_KEY` in this environment and the `anthropic` SDK is not installed, so I
made no API calls. The cache behaviour is verified only by the structure tests above. Check it in
`logs/usage.jsonl` after the next deploy (see the open issue below).

## Open issue: the static block may be below the cache minimum

Anthropic only caches a prefix that is at least the model's minimum length, and that minimum is 1024
tokens for `claude-sonnet-4-5` (the MODEL in `bot.py`). The minimum applies to the whole prefix up to the
breakpoint, and in the request the tools come before the system prompt. Measured here:

- `INSTRUCTIONS`: 2,484 characters, about 600–700 tokens (estimate, no tokenizer available).
- Core tools (`save_fact`, `log_session`): 424 characters of JSON, about 120–150 tokens.
- The first log line with no facts (user 77) shows a `cache_creation` of 1024 for the whole prefix.
  With no facts the athlete tail is about 50 tokens, so tools plus instructions come to roughly
  950–1000 tokens.

So the marker after the instructions is probably below the minimum and would be silently ignored. Until
that prefix is at least 1024 tokens, the split does nothing on its own, and the first block is
effectively not cached. The second marker still caches everything up to the end, which is the old
behaviour. I did not pad the prompt to get over the limit, because that changes the prompt content and
cost, and that is your decision. Options:

1. Add real static content (about 200–300 tokens) to `INSTRUCTIONS`, for example worked session
   examples or a reference for the zone rules. The static block then caches and the fix takes effect.
   This costs a 1.25× write when it goes cold, then 10% reads.
2. Leave it. Caching then helps only the tool-loop rounds and follow-up messages, as before, and
   `save_fact` still costs a full re-cache.

I recommend option 1. In `usage.jsonl`, the rounds after a `save_fact` should show `cache_read` close
to the static size and `cache_creation` close to the tail size (about 200 tokens with facts). If
`cache_creation` is still about the full prompt size, the static block is still below the minimum.

## Other eviction sources, not changed

- Tool groups are chosen per message from keywords (`plan`, `race`, and so on). A message that adds a
  group changes the tools array, which sits before the system prompt, so it misses the whole prefix. The
  log shows this with `plan_week` (1305) and `predict_race` (1334). This is the tradeoff in the colleague
  note: it is acceptable because the default group covers most messages, and it was kept as is.

## Colleague note: what applied

- Applied: two `ephemeral` markers, one on the static instructions and one on the volatile tail.
- Applied: the static block must be byte-stable, with no interpolated values. The test checks this.
- Applied: keep the tools array stable within one message's loop. The tools are not changed per round.
- Applied as a check: verify with `usage` (`cache_read` and `cache_creation`) after deploy.
- Not applied: the claim that a ~780-token static block gets its own cache entry. That does not hold at this
  size on Sonnet 4.5. See the open issue above.
- Not applicable: top-N fact selection. This bot always injects all facts, so no change was needed.
- Not applicable: the 4-marker limit. We use 2.
- Not applied: the claim that tool filtering is harmless for the cache. Here it is a partial miss, as noted above.

## Files

- `bot.py`: `build_system()` now returns two cached blocks. No other code changed.
- `test_cache_split.py`: new, 5 tests.
- `ANSWER.md`: this file.

Nothing is committed.

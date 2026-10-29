# Fix: memory writes no longer evict the static instructions

## Cause
`build_system` (bot.py) concatenated `INSTRUCTIONS` and the per-athlete context
(date, profile, zones, goal, facts, language) into one block with a single
`cache_control` marker. `save_fact` changes the facts, so the block's hash changed
and the whole ~1000-token prompt was re-created (see `logs/usage.jsonl`:
`cache_read_input_tokens: 0`, `cache_creation_input_tokens` ~1050 right after each `save_fact`).

## Change
`build_system` now returns two text blocks, each with `cache_control: ephemeral`:
1. `INSTRUCTIONS` — static, byte-identical across users and days (no interpolation; I checked).
2. `athlete_context(a, today)` — the volatile tail.

A memory write now invalidates only the tail; the instructions block is still read from cache.
Two markers of the four allowed.

## Colleague's note
Applied: the two-segment split, and checking that the static block is byte-stable.
Applied as constraints (no code change): keep loading all facts (no top-N selection), and leave
the existing keyword tool filtering alone. Tools sit above the system prompt in the prefix, so a
message that adds a tool group re-reads everything once. That was already the case and is acceptable.
Not applicable: the note's token counts (~780/~240) and MCP/Telegram details. This repo has its own sizes.

## Not verified
I did not call the API. To check: send two messages, then a `save_fact`, then a third message.
The third should show `cache_read_input_tokens` covering the instructions and `cache_creation_input_tokens`
about the size of the tail only. Note the instruction block must be long enough to meet the model's
minimum cacheable prompt length, or it won't be cached on its own. It's roughly 700+ tokens here, so
check the minimum for your model.

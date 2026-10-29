# Fix: save_fact no longer evicts the static system prompt

## Cause
`build_system` (bot.py) returned one text block (instructions + athlete context) with a single
`cache_control` marker. `save_fact` changes the facts list, so the block's hash changed and the
whole ~1000-token prompt was re-created (see `cache_read_input_tokens: 0` after each `save_fact` in logs/usage.jsonl).

## Change
`build_system` now returns two blocks, each with `cache_control: ephemeral`:
1. `INSTRUCTIONS`, byte-stable (it has no interpolated values).
2. `athlete_context(...)`, with the date, profile, zones, goal, facts and language.

A memory write now only re-creates the second block; the instructions are still read from cache.
Two markers is within the limit of 4.

## From the colleague's note
- Used: the two-segment split, and the check that the static block has nothing interpolated.
- Used: keep everything above the system prompt stable. I left the tools array and keyword filtering
  unchanged (NOTES.md says to leave it). Tools come before the system prompt in the prefix, so a message
  that adds a tool group still re-reads everything once. The tools stay constant within one message's tool loop.
- Not used: top-N fact selection. It would vary the tail per message, and the code already injects all facts.
- Not needed: the tool-grouping part of the note. It already existed here (March).

## Not verified
I did not run the bot or call the API. To check: send two messages, then a `save_fact`, then a third.
The third should show `cache_read` covering the instructions and `cache_creation` only about the size of the tail.
Caveat: each cached block must reach the model's minimum cacheable length. If the instructions alone are
below it, they will not be cached on their own, so check `usage` after rollout.

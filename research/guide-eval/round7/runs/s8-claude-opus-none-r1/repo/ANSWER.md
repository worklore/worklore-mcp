# Why every `save_fact` paid for the whole system prompt, and the fix

## Cause
`build_system` sent the system prompt as **one** text block: the instructions, the
athlete context and the facts list (plus `Language:` after the facts), with `cache_control`
on that block. A prompt cache entry only matches an identical prefix, so when `save_fact`
appended a fact the block's text changed and the whole ~1000-token prefix (tools +
instructions + profile) missed. `reply()` rebuilds the system prompt every round, so the
miss came in the round right after the tool call. That is the
`cache_read_input_tokens: 0, cache_creation_input_tokens: ~1050–1100` row after each
`save_fact` in `logs/usage.jsonl`.

## Why not just add a breakpoint after the instructions
That's the obvious fix, but here it would silently do nothing. Tools + instructions come
to roughly 945 tokens. (From the log: the request with no facts cached exactly 1024
tokens, and ~80 of those are the date/profile lines.) Sonnet 4.5 won't cache a prefix
shorter than 1024 tokens, so a breakpoint there is ignored without any error.

## What changed (`bot.py`, `build_system` / `athlete_profile`)
- The system prompt is now a list of blocks:
  1. `INSTRUCTIONS` + the per-athlete head (date, name, sport, zones, goal, language,
     "Long-term facts" header). `save_fact` never changes any of this.
  2. One block per fact (`- <fact>`), in saved order.
- `cache_control` is on the **last** block (the last fact, or block 1 if there are none).
- Facts are append-only, so after a `save_fact` the new system prompt is the old one plus
  one block. Before writing, the API looks back over earlier block boundaries (up to ~20)
  for an existing entry. It finds the one written by the previous call at the old last
  fact, reads it, and writes only the new fact (~5–15 tokens). The prefix stays above the
  1024 minimum because it includes the profile and any facts.
- `Language:` moved above the facts, because anything after the facts would break the
  "old prompt is a prefix of the new one" property. The `- (none yet)` placeholder became a
  header note, for the same reason.
- The date stays in the head. It changes once a day, and a 5-minute cache never survives
  the night anyway. Without it, a brand-new athlete with no facts drops back under 1024.

Expected log pattern after a `save_fact`: the round-2 row shows `cache_read ≈ 1050`,
`cache_creation ≈ 15` instead of `0 / ≈1100`.

## Verified how
There's no API key here, and nothing was sent to any service. I ran an offline fake client
(in `/tmp`, not in the repo) that applies the cache rules (write at the breakpoint, look
back over up to 20 block boundaries, 1024 minimum) to `reply()` with scripted `save_fact`
calls. Every call after the first read the full prefix, and the calls after a save wrote
only 5–6 tokens. Please confirm on the real `logs/usage.jsonl` after deploying.

## Not changed / caveats
- Keyword tool filtering is unchanged, per NOTES.md. Tools come before the system prompt in
  the cache key, so a message that adds `plan_week` / `predict_race` still has its own
  cache entry (the 1305/1334 rows). That's separate from memory writes, and the plain
  entry stays warm.
- The fix relies on facts being append-only. If you add editing or deleting of facts, or
  cap the list by dropping old ones, the next call after that change does one full write.
  After that it's back to normal.

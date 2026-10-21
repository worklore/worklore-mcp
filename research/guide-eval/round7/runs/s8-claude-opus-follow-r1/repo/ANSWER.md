# Prompt caching fix: memory writes no longer evict the static instructions

## Problem
`build_system()` sent the whole system prompt (`INSTRUCTIONS` plus athlete context)
as **one** text block with a single `cache_control` marker. The cache works on a
prefix hash, so when `save_fact` appended a fact, the block's hash changed and the
whole cached prefix (about 1,050 tokens: tools, instructions, context) missed.
`logs/usage.jsonl` shows this: every call after a `save_fact` has
`cache_read_input_tokens: 0` and `cache_creation_input_tokens` ≈ the full prompt.

## Change (`bot.py`, `build_system`)
The system prompt is now two text blocks, each with `cache_control: {"type": "ephemeral"}`:

1. `INSTRUCTIONS`: static and byte-identical for every athlete and every day
   (nothing is interpolated into it).
2. `athlete_context(a, today)`: the volatile tail (date, profile, zones, goal,
   facts, language).

A memory write (or the date changing) now invalidates only segment 2. The
tools + instructions prefix stays cached. The request uses 2 of the 4 allowed markers.
Tool selection was left as it is. `select_tools` keeps a fixed order, so the
tools part of the prefix is byte-stable for a given keyword group. I also
updated the caching paragraph in `README.md`.

Checked offline (no API calls): segment 1 is identical across athletes 42 and
77, across dates, and before and after a fact is appended. Only segment 2 changes.

## ⚠ Caveat: the static segment may be below the minimum cacheable size
`claude-sonnet-4-5` caches a prefix only if it is **at least 1,024 tokens**.
Shorter prefixes are silently not cached, even when they carry a marker.
Estimate from the logs: athlete 77's whole prompt is exactly 1,024 tokens, and
athlete 42's is 1,046 with 3 facts at roughly 15 tokens per fact. The tail is
about 110–130 tokens. That puts **tools (core only) + instructions at about
900–930 tokens, under the limit**:

- Messages that pull in the `plan` or `race` tool group have a static prefix of
  roughly 1,100+ tokens, so the fix works for them.
- On core-only messages (most of them), marker 1 is probably ignored. A memory
  write would then still re-cache the full ~1,050 tokens.

I could not measure this precisely without calling the API (I didn't). Ways to
get the static prefix past 1,024 tokens, which I left for you to choose:
- always send `plan_week` and `predict_race`. That is about 150–250 more tokens,
  but they are read from cache at 10% price, and the tools become fully
  byte-stable. NOTES.md says to keep keyword filtering, so I didn't do this.
- add more genuinely static coaching content to `INSTRUCTIONS`.

Note also that Opus 4.5 and Haiku 4.5 have a 4,096-token minimum. Switching
`MODEL` to either would make both segments uncacheable.

## How to verify
Run `python3 bot.py 42` and look at `logs/usage.jsonl`:
1. Send two messages within 5 minutes. The second should show
   `cache_read_input_tokens` covering about the whole prompt.
2. Tell the bot a durable fact (this triggers `save_fact`). On the next call,
   `cache_read_input_tokens` should be about the static size (~900+) and
   `cache_creation_input_tokens` should be only the tail (~130).
   If `cache_creation` is still the full prompt, you are hitting the 1,024-token
   minimum described above.
